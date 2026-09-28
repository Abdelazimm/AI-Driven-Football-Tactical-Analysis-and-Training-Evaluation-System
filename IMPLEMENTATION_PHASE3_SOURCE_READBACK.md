# IMPLEMENTATION_PHASE3_SOURCE_READBACK.md
# Source-First Readback & Lineage Audit for Implementation Phase 3

**Project**: AI-Driven Football Tactical Analysis and Training Evaluation System  
**Phase**: Implementation Phase 3 — Real ASR, Multimodal Fusion & Structured Evidence  
**Contract Version**: `P0_ARCHITECTURE_CONTRACT_FREEZE_REV2A` (Approved)  
**Authoritative Contracts Audited**:
- `ASR_SELECTED_MODEL_INTEGRATION_CONTRACT.json` (`methodology_comparison/asr/model_selection/`)
- `ASR_TEXT_NORMALIZATION_CONTRACT.json` (`methodology_comparison/asr/`)
- `evaluate_asr.py` (`methodology_comparison/asr/`)
- `G:\My Drive\Football_Training_Assistant_MVP\backend\pipeline\asr.py`
- `G:\My Drive\Football_Training_Assistant_MVP\backend\contracts\asr_contract.py`
- `G:\My Drive\Football_Training_Assistant_MVP\backend\pipeline\fusion.py`
- `G:\My Drive\Football_Training_Assistant_MVP\backend\contracts\fusion_contract.py`
- `backend/app/pipeline/audio.py` (production stub)
- `backend/app/pipeline/fusion.py` (production stub)
- `backend/app/pipeline/evidence.py` (production stub)

---

## 1. Audited Component Lineage & Reuse Classification

| Research / Production Component | Source Location | Classification | Rationale & Actions |
| :--- | :--- | :--- | :--- |
| **Audio Extraction (ffmpeg)** | `ASR_SELECTED_MODEL_INTEGRATION_CONTRACT.json` | **ALGORITHM_ONLY** | Reusable command line: `ffmpeg -y -v error -i {input_audio} -vn -ac 1 -ar 16000 -c:a pcm_s16le {output_wav}`. Must be wrapped in production service (`backend/app/services/asr_service.py`) with strict tempfile isolation and cleanup. |
| **faster-whisper base.en Engine** | `ASR_SELECTED_MODEL_INTEGRATION_CONTRACT.json` | **COPY_ADAPT** | Pinned configuration: `faster-whisper==1.2.1`, model `base.en`, CTranslate2 engine, CPU `int8`, 8 threads. Decode: `beam_size=5`, `word_timestamps=True`, `vad_filter=True`, `min_silence_duration_ms=500`, `condition_on_previous_text=False`. |
| **Text Normalization (`normalize_text`)** | `evaluate_asr.py::normalize_text`, `ASR_TEXT_NORMALIZATION_CONTRACT.json` | **COPY_ADAPT** | Complete rule set: lowercase, contraction expansion (`im`, `dont`, `youre`, `cant`, `its`, `were`, `theyre`, `wont`, `hes`, `shes`, `lets`), hyphens/underscores to whitespace, strip non-alphanumeric punctuation, cardinal digit expansion (0–10), and whitespace collapse. |
| **Tactical Keyword Extractor** | `ASR_SELECTED_MODEL_INTEGRATION_CONTRACT.json` (Section `category_rules`) | **COPY_ADAPT** | Exactly 5 frozen categories: Positioning / Hold Ground, Pressing, Passing, Defensive, Offensive. Deterministic substring matching against normalized segment text. Parent segment timestamps strictly inherited. |
| **ASR Event Schemas (`ASRResult`, `ASRSegment`, `TacticalEvent`)** | `contracts/asr_contract.py`, `schemas/transcript.py`, `schemas/instruction.py` | **REDESIGN_INTERFACE_ONLY** | Unify into production Pydantic schemas in `backend/app/schemas/transcript.py` and `backend/app/schemas/instruction.py`. Preserve segment ID, timestamps, normalized text, matched keyword, and fail-closed target resolution (`target_player = None`). |
| **Historical Raw Transcript Fallback** | `backend/pipeline/asr.py` lines 99–106 (`except: load 3v3_real_audio_whisper_raw.json`) | **DO_NOT_USE** | **STRICTLY PROHIBITED**. Broad try/except returning pre-recorded historical JSON must not exist in production. Failures must return typed `ASRFailure` allowing Vision-only execution with `COMPLETED_WITH_LIMITATIONS`. |
| **Research Ad-Hoc Keyword Lists** | `backend/pipeline/asr.py` lines 27–49 (`"stay at your zone"`, etc.) | **DO_NOT_USE** | Replaced strictly with authoritative rules from `ASR_SELECTED_MODEL_INTEGRATION_CONTRACT.json`. No unversioned vocabulary additions permitted. |
| **Legacy Fusion Evaluation Window** | `backend/pipeline/fusion.py` lines 79–81 (`[t_start - 2.0s, t_end + 5.0s]`) | **DO_NOT_USE** | **STRICTLY PROHIBITED**. Legacy pre-command window is deprecated. Replaced with frozen post-command reaction window: $[t_{\text{end}} + 2.0\text{s}, t_{\text{end}} + 6.0\text{s}]$. |
| **Research Mock Constants & Placeholders** | `backend/pipeline/fusion.py` lines 102–104 (`PLAYER_01`, `4.5m`, `8.2kmh`, `2500 rows`, `339.87s`) | **DO_NOT_USE** | **STRICTLY PROHIBITED**. All fabricated constants, synthetic player IDs, and hard-coded speeds are rejected. Fusion must consume actual real `SessionVisionResult` and actual `KinematicsService` outputs. |
| **Production Stubs** | `backend/app/pipeline/audio.py`, `fusion.py`, `evidence.py` | **REDESIGN_INTERFACE_ONLY** | Implement real production logic replacing `NotImplementedError` placeholders. |

---

## 2. Detailed Lineage Audit of Research & Integration Artifacts

### 2.1 ASR Contract Specifications (`ASR_SELECTED_MODEL_INTEGRATION_CONTRACT.json`)
The authoritative model selection contract defines:
- Library: `faster-whisper==1.2.1`
- Engine: `CTranslate2`
- Model checkpoint: `base.en` (`Systran/faster-whisper-base.en`, ~74M parameters)
- Primary runtime: `device="cpu"`, `compute_type="int8"`, `cpu_threads=8`, `num_workers=1`
- Audio input: 16 kHz, 1 channel (mono), 16-bit PCM WAV
- FFmpeg command: `ffmpeg -y -v error -i {input_audio} -vn -ac 1 -ar 16000 -c:a pcm_s16le {output_wav}`
- Decode parameters:
  - `task="transcribe"`
  - `language="en"`
  - `beam_size=5`
  - `word_timestamps=True`
  - `vad_filter=True`
  - `vad_parameters={"min_silence_duration_ms": 500}`
  - `condition_on_previous_text=False`

### 2.2 Text Normalization Contract (`ASR_TEXT_NORMALIZATION_CONTRACT.json`)
Text normalization policy governs both acoustic word recognition evaluation and keyword matching:
1. `text.lower().strip()`
2. Contraction mapping:
   - `\bi'm\b` $\rightarrow$ `im`
   - `\bdon't\b` $\rightarrow$ `dont`
   - `\byou're\b` $\rightarrow$ `youre`
   - `\bcan't\b` $\rightarrow$ `cant`
   - `\bit's\b` $\rightarrow$ `its`
   - `\bwe're\b` $\rightarrow$ `were`
   - `\bthey're\b` $\rightarrow$ `theyre`
   - `\bwon't\b` $\rightarrow$ `wont`
   - `\bhe's\b` $\rightarrow$ `hes`
   - `\bshe's\b` $\rightarrow$ `shes`
   - `\blet's\b` $\rightarrow$ `lets`
3. Hyphens and underscores: `re.sub(r"[-_]", " ", norm)`
4. Punctuation stripping: `re.sub(r"[^\w\s]", "", norm)`
5. Number token expansion: standalone digits `0` through `10` expanded to cardinal words (`zero` to `ten`)
6. Whitespace collapse: `re.sub(r"\s+", " ", norm).strip()`

### 2.3 Exact Tactical Taxonomy Rules
The authoritative keyword dictionary contains exactly 5 categories:
```python
FROZEN_TACTICAL_TAXONOMY = {
    "Positioning / Hold Ground": [
        "hold your position",
        "hold position",
        "hold your ground",
        "stay in position",
        "stick to your zone",
        "stay in your zone",
        "keep your shape",
    ],
    "Pressing": [
        "press",
        "close down",
        "pressure",
        "sprint",
    ],
    "Passing": [
        "pass",
        "play the ball",
        "switch the ball",
    ],
    "Defensive": [
        "defend",
        "defence",
        "defense",
        "drop back",
        "mark",
        "cover",
    ],
    "Offensive": [
        "attack",
        "shoot",
        "go forward",
        "make a run",
        "run forward",
    ],
}
```

Categories like `COVERAGE`, `TRANSITION`, and `TACTICAL_DISCIPLINE` are NOT in the frozen model contract and are strictly excluded.

### 2.4 Timestamp Inheritance and Target Resolution Rules
- **Timestamp Inheritance**: Tactical events inherit `t_start` and `t_end` directly from the parent Whisper speech segment. No sub-segment interpolation is performed.
- **Target Resolution**: For all automated runs, `target_player = None`, `target_resolution_status = "UNRESOLVED_TARGET"`. Target player identities must never be inferred from track IDs or spatial proximity.

### 2.5 Deprecated Research Fallbacks & Prohibitions
1. **Fallback Removal**: The try/except block in the research `backend/pipeline/asr.py` that loaded `data/custom/audio/3v3_real_audio_whisper_raw.json` on any transcription failure is explicitly purged. Production ASR fails cleanly with typed `ASRFailure`.
2. **Mock Constant Removal**: All mock values (`PLAYER_01`, `4.5m`, `8.2kmh`, `2500 rows`, `339.87s`) from `backend/pipeline/fusion.py` are completely replaced by dynamic calculations querying `SessionVisionResult` and `KinematicsService`.
3. **Evaluation Window**: The old window $[t_{\text{start}} - 2.0\text{s}, t_{\text{end}} + 5.0\text{s}]$ is replaced by the approved post-command reaction window $[t_{\text{end}} + 2.0\text{s}, t_{\text{end}} + 6.0\text{s}]$.
