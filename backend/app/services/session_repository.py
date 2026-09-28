"""
Session repository interfaces and implementations.
Handles persistence of football coaching/training sessions.
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict
from datetime import datetime
from supabase import Client
from backend.app.schemas.session import Session


class SessionRepository(ABC):
    """Abstract interface for session persistence."""

    @abstractmethod
    def create_session(self, session: Session) -> Session:
        """Persist a new session record."""
        pass

    @abstractmethod
    def get_session(self, session_id: str) -> Optional[Session]:
        """Retrieve a session by its unique UUID."""
        pass

    @abstractmethod
    def list_sessions(self, limit: int = 50) -> List[Session]:
        """List sessions up to the specified limit."""
        pass


class SupabaseSessionRepository(SessionRepository):
    """Supabase PostgreSQL session repository implementation."""

    def __init__(self, client: Client):
        self._client = client

    def create_session(self, session: Session) -> Session:
        payload = {
            "id": session.id,
            "title": session.title,
            "coach_name": session.coach_name,
            "team_name": session.team_name,
            "notes": session.notes,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
        }
        res = self._client.table("sessions").insert(payload).execute()
        if not res.data:
            raise RuntimeError(f"Failed to insert session into Supabase: {res}")
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        res = self._client.table("sessions").select("*").eq("id", session_id).execute()
        if not res.data or len(res.data) == 0:
            return None
        row = res.data[0]
        return Session(
            id=row["id"],
            title=row["title"],
            coach_name=row.get("coach_name"),
            team_name=row.get("team_name"),
            notes=row.get("notes"),
            created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00")),
        )

    def list_sessions(self, limit: int = 50) -> List[Session]:
        res = self._client.table("sessions").select("*").order("created_at", desc=True).limit(limit).execute()
        if not res.data:
            return []
        return [
            Session(
                id=row["id"],
                title=row["title"],
                coach_name=row.get("coach_name"),
                team_name=row.get("team_name"),
                notes=row.get("notes"),
                created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00")),
            )
            for row in res.data
        ]


class InMemorySessionRepository(SessionRepository):
    """
    In-memory session repository implementation.
    FOR LOCAL CONTRACT AND UNIT TESTING ONLY.
    """

    def __init__(self):
        self._sessions: Dict[str, Session] = {}

    def create_session(self, session: Session) -> Session:
        self._sessions[session.id] = session
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        return self._sessions.get(session_id)

    def list_sessions(self, limit: int = 50) -> List[Session]:
        all_sessions = list(self._sessions.values())
        all_sessions.sort(key=lambda s: s.created_at, reverse=True)
        return all_sessions[:limit]

    def clear(self) -> None:
        self._sessions.clear()
