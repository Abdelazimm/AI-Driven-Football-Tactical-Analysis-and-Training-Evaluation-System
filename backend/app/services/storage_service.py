"""
Storage service interfaces and Supabase Storage implementation.
Manages scoped signed upload/download authorizations and object verification for private buckets.

CRITICAL: Infrastructure/network failures must NEVER be collapsed into "object not found".
All storage operations use typed error semantics.
"""
import os
from abc import ABC, abstractmethod
from typing import Optional, Dict
from enum import Enum
from supabase import Client
from backend.app.core.config import settings


# =============================================================================
# TYPED STORAGE ERROR HIERARCHY
# =============================================================================

class StorageErrorCode(str, Enum):
    """Machine-readable storage error codes for API consumers."""
    OBJECT_NOT_FOUND = "OBJECT_NOT_FOUND"
    STORAGE_AUTH_ERROR = "STORAGE_AUTH_ERROR"
    STORAGE_TIMEOUT = "STORAGE_TIMEOUT"
    STORAGE_UNAVAILABLE = "STORAGE_UNAVAILABLE"
    STORAGE_PROVIDER_ERROR = "STORAGE_PROVIDER_ERROR"


class StorageError(Exception):
    """Base typed storage error. Never silently swallow infrastructure failures."""
    def __init__(self, code: StorageErrorCode, message: str, cause: Optional[Exception] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.cause = cause


class StorageObjectNotFound(StorageError):
    """The requested object genuinely does not exist in the bucket."""
    def __init__(self, bucket: str, path: str, cause: Optional[Exception] = None):
        super().__init__(
            code=StorageErrorCode.OBJECT_NOT_FOUND,
            message=f"Object not found in bucket '{bucket}' at path '{path}'.",
            cause=cause,
        )
        self.bucket = bucket
        self.path = path


class StorageAuthError(StorageError):
    """Authentication or authorization failure when accessing storage."""
    def __init__(self, message: str = "Storage authentication failed.", cause: Optional[Exception] = None):
        super().__init__(code=StorageErrorCode.STORAGE_AUTH_ERROR, message=message, cause=cause)


class StorageTimeout(StorageError):
    """Storage operation timed out."""
    def __init__(self, message: str = "Storage operation timed out.", cause: Optional[Exception] = None):
        super().__init__(code=StorageErrorCode.STORAGE_TIMEOUT, message=message, cause=cause)


class StorageUnavailable(StorageError):
    """Storage service is temporarily unavailable (e.g. 503)."""
    def __init__(self, message: str = "Storage service is temporarily unavailable.", cause: Optional[Exception] = None):
        super().__init__(code=StorageErrorCode.STORAGE_UNAVAILABLE, message=message, cause=cause)


class StorageProviderError(StorageError):
    """Unexpected storage provider error (e.g. 5xx, SDK exception)."""
    def __init__(self, message: str = "Storage provider error.", cause: Optional[Exception] = None):
        super().__init__(code=StorageErrorCode.STORAGE_PROVIDER_ERROR, message=message, cause=cause)


# =============================================================================
# ABSTRACT INTERFACE
# =============================================================================

class StorageService(ABC):
    """Abstract interface for storage operations with typed error semantics."""

    @abstractmethod
    def create_signed_upload_url(self, bucket: str, path: str) -> Dict[str, str]:
        """
        Generate a temporary, scoped signed upload URL for a specific object path.
        Returns a dict containing 'signed_url', 'token', and 'path'.
        """
        pass

    @abstractmethod
    def create_signed_download_url(self, bucket: str, path: str, expires_in: int = 300) -> str:
        """
        Generate a short-lived signed download URL for server-side read access.
        Used by media probe to access private bucket objects without making them public.
        Returns the signed download URL string.
        Raises StorageError on infrastructure failures.
        """
        pass

    @abstractmethod
    def verify_object_exists(self, bucket: str, path: str) -> bool:
        """
        Verify whether an object exists in storage.
        Returns True if found, False ONLY if genuinely absent.
        Raises StorageError (not False) on infrastructure/auth failures.
        """
        pass

    @abstractmethod
    def get_object_size(self, bucket: str, path: str) -> Optional[int]:
        """
        Return the object size in bytes if present, None if genuinely absent.
        Raises StorageError on infrastructure/auth failures.
        """
        pass


# =============================================================================
# SUPABASE PRODUCTION IMPLEMENTATION
# =============================================================================

class SupabaseStorageService(StorageService):
    """
    Production Supabase Storage implementation with typed error semantics.
    
    Object verification uses exact-path list with prefix filtering
    instead of scanning arbitrary large folders.
    
    LIMITATION: Supabase Storage SDK does not expose a HEAD/metadata-only operation.
    We use list(folder, search=filename, limit=1) for exact-object lookup.
    """

    def __init__(self, client: Client):
        self._client = client

    def create_signed_upload_url(self, bucket: str, path: str) -> Dict[str, str]:
        res = self._client.storage.from_(bucket).create_signed_upload_url(path)
        # res can be a dict or a SignedUploadURL object with signed_url / url
        if isinstance(res, dict):
            signed_url = res.get("signed_url") or res.get("url") or res.get("signedURL")
            token = res.get("token", "")
        else:
            signed_url = getattr(res, "signed_url", getattr(res, "url", ""))
            token = getattr(res, "token", "")

        # If signed_url is relative, prefix with supabase URL
        if signed_url and signed_url.startswith("/"):
            signed_url = f"{settings.SUPABASE_URL.rstrip('/')}{signed_url}"

        return {
            "signed_url": signed_url,
            "token": token,
            "path": path,
        }

    def create_signed_download_url(self, bucket: str, path: str, expires_in: int = 300) -> str:
        """
        Generate a short-lived signed download URL for private bucket objects.
        Used by ffprobe to read container headers without exposing the bucket publicly.
        """
        try:
            res = self._client.storage.from_(bucket).create_signed_url(path, expires_in)
            if isinstance(res, dict):
                url = res.get("signedURL") or res.get("signed_url") or res.get("url")
            else:
                url = getattr(res, "signedURL", getattr(res, "signed_url", getattr(res, "url", "")))
            if not url:
                raise StorageProviderError(
                    f"Signed download URL generation returned empty for '{path}'."
                )
            return url
        except StorageError:
            raise
        except Exception as ex:
            raise self._classify_exception(ex, bucket, path) from ex

    def verify_object_exists(self, bucket: str, path: str) -> bool:
        """
        Exact-object existence check using targeted directory listing.
        Returns True if found, raises StorageError on infrastructure failures.
        """
        folder, filename = os.path.split(path)
        if not filename:
            return False
        try:
            # Exact-object lookup: list the parent folder with search filter
            # This avoids scanning arbitrarily large directories
            files = self._client.storage.from_(bucket).list(
                folder,
                {"search": filename, "limit": 5},
            )
            return any(f.get("name") == filename for f in files)
        except Exception as ex:
            raise self._classify_exception(ex, bucket, path) from ex

    def get_object_size(self, bucket: str, path: str) -> Optional[int]:
        """
        Retrieve exact object size using targeted listing.
        Returns None only if genuinely absent. Raises StorageError on failures.
        """
        folder, filename = os.path.split(path)
        if not filename:
            return None
        try:
            files = self._client.storage.from_(bucket).list(
                folder,
                {"search": filename, "limit": 5},
            )
            for f in files:
                if f.get("name") == filename:
                    metadata = f.get("metadata", {})
                    return metadata.get("size") or f.get("size")
            return None
        except Exception as ex:
            raise self._classify_exception(ex, bucket, path) from ex

    @staticmethod
    def _classify_exception(ex: Exception, bucket: str, path: str) -> StorageError:
        """
        Classify a raw storage SDK exception into a typed StorageError.
        CRITICAL: Infrastructure failures must NEVER become 'object not found'.
        """
        err_msg = str(ex).lower()
        err_type = type(ex).__name__.lower()

        # Authentication / Authorization
        if any(kw in err_msg for kw in ("401", "403", "unauthorized", "forbidden", "invalid api key")):
            return StorageAuthError(f"Storage auth error for '{bucket}/{path}': {ex}", cause=ex)

        # Timeout
        if any(kw in err_msg for kw in ("timeout", "timed out")) or "timeout" in err_type:
            return StorageTimeout(f"Storage timeout for '{bucket}/{path}': {ex}", cause=ex)

        # Service unavailable
        if any(kw in err_msg for kw in ("503", "502", "service unavailable", "bad gateway")):
            return StorageUnavailable(f"Storage unavailable for '{bucket}/{path}': {ex}", cause=ex)

        # Connection errors
        if any(kw in err_msg for kw in ("connection", "dns", "refused", "reset")) or "connection" in err_type:
            return StorageUnavailable(f"Storage connection error for '{bucket}/{path}': {ex}", cause=ex)

        # 404 / Not Found — this is object-level, map to genuine not found
        if any(kw in err_msg for kw in ("404", "not found", "object not found")):
            return StorageObjectNotFound(bucket, path, cause=ex)

        # Everything else is an opaque provider error
        return StorageProviderError(f"Storage provider error for '{bucket}/{path}': {ex}", cause=ex)


# =============================================================================
# IN-MEMORY TESTING IMPLEMENTATION
# =============================================================================

class InMemoryStorageService(StorageService):
    """
    In-memory storage service for isolated testing and development without live credentials.
    Supports typed error simulation.
    """

    def __init__(self):
        # Map of (bucket/path) -> size_bytes
        self._objects: Dict[str, int] = {}
        # Optional: simulate errors for specific operations
        self._forced_error: Optional[StorageError] = None

    def force_error(self, error: Optional[StorageError]) -> None:
        """Test helper: force all subsequent operations to raise this error."""
        self._forced_error = error

    def create_signed_upload_url(self, bucket: str, path: str) -> Dict[str, str]:
        if self._forced_error:
            raise self._forced_error
        key = f"{bucket}/{path}"
        return {
            "signed_url": f"http://localhost:8000/api/v1/mock-storage/{bucket}/{path}?token=mock_upload_token",
            "token": "mock_upload_token",
            "path": path,
        }

    def create_signed_download_url(self, bucket: str, path: str, expires_in: int = 300) -> str:
        if self._forced_error:
            raise self._forced_error
        key = f"{bucket}/{path}"
        if key not in self._objects:
            raise StorageObjectNotFound(bucket, path)
        return f"http://localhost:8000/api/v1/mock-storage/{bucket}/{path}?token=mock_download_token&expires={expires_in}"

    def simulate_upload(self, bucket: str, path: str, size_bytes: int = 1024) -> None:
        """Test helper to simulate completion of upload to storage."""
        self._objects[f"{bucket}/{path}"] = size_bytes

    def verify_object_exists(self, bucket: str, path: str) -> bool:
        if self._forced_error:
            raise self._forced_error
        return f"{bucket}/{path}" in self._objects

    def get_object_size(self, bucket: str, path: str) -> Optional[int]:
        if self._forced_error:
            raise self._forced_error
        return self._objects.get(f"{bucket}/{path}")

    def clear(self) -> None:
        self._objects.clear()
        self._forced_error = None
