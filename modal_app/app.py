"""
Modal Application Scaffold.
Defines the Modal application and container environments.
In accordance with P0_ARCHITECTURE_CONTRACT_FREEZE_REV2A.
"""
import modal

# Primary application definition
app = modal.App(name="football-tactical-analysis")
model_volume = modal.Volume.from_name("football-model-checkpoints")
worker_secret = modal.Secret.from_name("football-worker-secrets")

# Lightweight CPU image for infrastructure verification and dispatch routing
cpu_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "pydantic>=2.0.0",
        "httpx>=0.24.0",
    )
)

# Full analysis worker image for pipeline execution
worker_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg", "libgl1", "libglib2.0-0")
    .pip_install(
        "torch==2.14.0", "torchvision==0.29.0",
        "rfdetr==1.10.1", "ultralytics==8.4.163",
        "numpy>=2.3,<2.5", "scipy>=1.16,<1.18", "scikit-learn>=1.7,<1.9",
        "lap==0.5.13", "loguru==0.7.3", "matplotlib>=3.10,<3.11",
        "seaborn==0.13.2", "tqdm==4.70.1", "pillow>=11,<13",
        "opencv-python-headless>=4.12,<5",
        "faster-whisper==1.2.1", "ctranslate2==4.8.2",
        "supabase==2.31.0", "fastapi==0.141.1", "httpx>=0.28.0",
        "python-multipart", "pyyaml",
    )
    .env({"PYTHONPATH": "/root", "M2_MODEL_ROOT": "/data/models/m2"})
    .add_local_dir("backend", remote_path="/root/backend", copy=True,
                   ignore=["**/__pycache__/**", "**/*.pyc", "tests/**"])
    .add_local_dir("modal_app", remote_path="/root/modal_app", copy=True,
                   ignore=["**/__pycache__/**", "**/*.pyc"])
)
