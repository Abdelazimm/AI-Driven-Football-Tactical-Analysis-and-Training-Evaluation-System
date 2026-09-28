import os
from pathlib import Path
from typing import Optional, List


def _load_env_file() -> None:
    current = Path(__file__).resolve()
    for parent in [current.parent, current.parent.parent, current.parent.parent.parent, current.parent.parent.parent.parent]:
        env_file = parent / ".env"
        if env_file.exists():
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    if k and k not in os.environ:
                        os.environ[k] = v
            break


_load_env_file()


class Settings:
    PROJECT_NAME: str = "AI-Driven Football Tactical Analysis and Training Evaluation System"
    API_V1_STR: str = "/api/v1"
    MAX_VIDEO_DURATION_SECONDS: float = float(os.getenv("MAX_VIDEO_DURATION_SECONDS", "360.0"))
    
    # LLM Inference Timeouts (Revision 2A Contract)
    FORMAL_LLM_BENCHMARK_TIMEOUT_SECONDS: int = 120
    PRODUCTION_LLM_TIMEOUT_SECONDS: int = 120
    LLM_TIMEOUT_SECONDS: int = int(os.getenv("LLM_TIMEOUT_SECONDS", "120"))
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = [
        origin.strip()
        for origin in os.getenv(
            "BACKEND_CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"
        ).split(",")
        if origin.strip()
    ]

    # Supabase configuration
    SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL", os.getenv("NEXT_PUBLIC_SUPABASE_URL"))
    SUPABASE_ANON_KEY: Optional[str] = os.getenv("SUPABASE_ANON_KEY", os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY"))
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    # Storage Buckets (Private by default)
    STORAGE_BUCKET_INPUTS: str = os.getenv("STORAGE_BUCKET_INPUTS", "analysis-inputs")
    STORAGE_BUCKET_OUTPUTS: str = os.getenv("STORAGE_BUCKET_OUTPUTS", "analysis-outputs")
    MAX_UPLOAD_SIZE_BYTES: int = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", str(1024 * 1024 * 1024)))  # 1 GB default
    PRESENTATION_DEMO_JOB_ID: str = os.getenv("PRESENTATION_DEMO_JOB_ID", "9b01f139-5411-4a6d-9f9b-85e6a6fb4cdc")

    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Modal serverless compute configuration
    MODAL_TOKEN_ID: Optional[str] = os.getenv("MODAL_TOKEN_ID")
    MODAL_TOKEN_SECRET: Optional[str] = os.getenv("MODAL_TOKEN_SECRET")
    MODAL_ENVIRONMENT: Optional[str] = os.getenv("MODAL_ENVIRONMENT", "main")

    # Worker Callback Secret (Internal serverless worker authentication)
    WORKER_CALLBACK_SECRET: str = os.getenv(
        "WORKER_CALLBACK_SECRET",
        "dev-worker-callback-secret-change-in-production"
    )


settings = Settings()

