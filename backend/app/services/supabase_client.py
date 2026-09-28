"""
Supabase client factory.
Manages the server-side Supabase client using service-role credentials.
CRITICAL: Service-role credentials must NEVER be exposed to frontend clients.
"""
from typing import Optional
from supabase import create_client, Client
from backend.app.core.config import settings

_supabase_client: Optional[Client] = None


def is_supabase_configured() -> bool:
    """Check if Supabase connection credentials are present in settings."""
    return bool(settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY)


def get_supabase_client() -> Optional[Client]:
    """
    Get or initialize the singleton Supabase Client.
    Returns None if credentials are not configured (e.g. during offline unit tests).
    """
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    if not is_supabase_configured():
        return None

    try:
        _supabase_client = create_client(
            supabase_url=settings.SUPABASE_URL,
            supabase_key=settings.SUPABASE_SERVICE_ROLE_KEY,
        )
        return _supabase_client
    except Exception as e:
        # Avoid crashing startup if connection or initialization fails
        return None


def reset_supabase_client() -> None:
    """Reset the singleton instance (useful for testing)."""
    global _supabase_client
    _supabase_client = None
