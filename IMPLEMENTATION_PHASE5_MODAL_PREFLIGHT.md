# IMPLEMENTATION_PHASE5_MODAL_PREFLIGHT.md
# Modal Serverless Compute Packaging & Dependency Preflight

**Project**: AI-Driven Football Tactical Analysis and Training Evaluation System  
**Phase**: Implementation Phase 5 — Production Orchestration, Modal Packaging, Persistence & Product Pipeline Wiring  
**Contract Version**: `P0_ARCHITECTURE_CONTRACT_FREEZE_REV2A` (Approved)  
**Date**: 2026-09-27  

---

## 1. Executive Summary & Verification Status

The serverless compute infrastructure layer utilizes Modal (`modal>=1.5.0,<2.0.0`) for distributed analysis execution. Remote container connectivity has been tested and verified live against the active Modal workspace (`abd-azimmm/main`):

```
Live Modal Execution Verification:
- Workspace: abd-azimmm/main
- App Name: football-tactical-analysis
- Remote Python Version: 3.10.17 (Debian Slim Linux)
- Infrastructure Smoke: SUCCESS (Status: 200, CPU-only container initialization)
```

---

## 2. Container Environment & Software Specification

### 2.1 Software Stack Specification

| Component | Target Version | Deployment Image / Runtime | Purpose |
| :--- | :--- | :--- | :--- |
| **Base OS** | Debian Slim (Linux x86_64) | `modal.Image.debian_slim(python_version="3.10")` | Standard serverless runtime container |
| **Python** | 3.10.17 | Standard container Python | Runtime interpreter |
| **System FFmpeg** | 5.1+ / 6.0+ | `apt-get install -y ffmpeg` | Audio extraction and media probing |
| **PyTorch** | 2.2.0+ / 2.6.0 | PyTorch Linux wheels (CPU / CUDA 12.1) | Vision model execution (RF-DETR, OSNet, YOLO) |
| **Ultralytics** | 8.4.163 | `pip install ultralytics==8.4.163` | Method 1 detector / tracker |
| **RF-DETR** | 1.10.1 | `pip install rfdetr==1.10.1` | Method 2 detector (AUTO default) |
| **ONNX Runtime** | 1.30.0 | `pip install onnxruntime==1.30.0` | Method 3 detector (YOLO26n-reid) |
| **Faster-Whisper** | 1.2.1 | `pip install faster-whisper==1.2.1` | Audio transcription & tactical events |
| **CTranslate2** | 4.8.2 | Faster-Whisper dependency | Int8 CPU inference backend |
| **Supabase Client** | 2.13.0+ | `pip install supabase>=2.13.0` | Storage upload/download & job lifecycle |
| **Pydantic** | >= 2.7.0 | `pip install pydantic>=2.7.0` | Data contracts & validation |

---

## 3. Model Checkpoint Storage Strategy

To maintain sub-minute container spin-up times and eliminate redundant multi-gigabyte network transfers, production model artifacts are organized via a dedicated `modal.Volume`:

### 3.1 Dedicated Model Volume: `football-model-checkpoints`
- **Volume Mount Path**: `/models`
- **Directory Layout**:
  ```
  /models/
  ├── method_1/
  │   ├── best.pt                   (SHA-256: ad908a9caf757f3f2b68a92d260da85a8308fb115e220b91d1bdccef31393f8b)
  │   └── prtreid.pth               (SHA-256: 8529c383197ae4c468eda535d1b165f8b4162cf17bf5fbcff49c7cb6455bc0bb)
  ├── method_2/
  │   ├── checkpoint_best_total.pth (SHA-256: 7539cfb3eca3125136c1446d7a522a5a46abb14136d55f79aec8daececc00b85)
  │   └── sports_model.pth.tar-60   (SHA-256: 8d5b2fd8763db34c2aad69810466adf413f0426d9f8119d322227e0e639c5fbd)
  ├── method_3/
  │   ├── yolo26n-reid.onnx         (SHA-256: ea9b3e434ffd7c2ca7ebcd563497accd90e03cfc8da1e8e9fc883e4790199dbf)
  │   └── dinov3_patch16.pth        (SHA-256: 5f4f1fa2226680c26458872f6241b9a5355d6e29a405fda1acdbcb11874b32f8)
  └── whisper/
      └── base.en/                  (Frozen CTranslate2 model directory)
  ```

### 3.2 Hugging Face Offline Requirement for Method 3 (DINOv3)
If Method 3 is selected for execution:
- Snapshot `c6a5fb7d12bbd3cf3b0079253141c3332aaed7da` of `timm/vit_base_patch16_dinov3.lvd1689m` is pre-baked into the image or volume.
- `HF_HUB_OFFLINE=1` is exported in the container environment.
- Zero live external Hugging Face network downloads occur at runtime.

---

## 4. LLM Cloud Packaging Strategy

### 4.1 Deployment Mode Decision
Phase 4 verified local Ollama execution with exact model tag `llama3.1:8b` and full 64-character digest `46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e`.

In cloud execution, substituting unverified models, generic cloud API endpoints, or different quantizations is **STRICTLY FORBIDDEN**.

```
PHASE5_LLM_DEPLOYMENT_MODE: CONTROLLED_LOCAL_OR_DETERMINISTIC_FALLBACK
```

- When running in an environment with access to the verified Ollama daemon (local orchestrator or container with co-located Ollama), the pipeline invokes Llama 3.1 8B with frozen parameters and Patch 001 validation.
- When running in a lightweight serverless cloud container without an active co-located Ollama daemon, the pipeline **fail-safely engages `DeterministicReportService`**, producing a 100% grounded deterministic fallback report directly from `StructuredEvidencePayload`.
- No substitute LLMs (e.g. OpenAI, Gemini, Claude, or unpinned hosted endpoints) are ever invoked.

---

## 5. Security & Secrets Management

1. **Authentication**: All Modal worker operations authenticate via `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET` passed securely through container environment or Modal Secret mounts.
2. **Supabase Integration**: Storage and database access inside Modal workers use `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` via `modal.Secret.from_name("supabase-credentials")`.
3. **Internal Callbacks**: Progress callbacks to `/api/v1/internal/jobs/{job_id}/progress` are authenticated with constant-time HMAC tokens (`WORKER_CALLBACK_SECRET`).
4. **Data Hygiene**: Signed URLs expire in 120 seconds. Temporary container files are stored in `/tmp/job_{id}` and purged upon job finalization.
