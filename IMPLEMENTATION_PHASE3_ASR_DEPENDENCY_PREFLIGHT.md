# IMPLEMENTATION_PHASE3_ASR_DEPENDENCY_PREFLIGHT.md
# ASR Dependency Preflight & Runtime Verification for Phase 3

**Project**: AI-Driven Football Tactical Analysis and Training Evaluation System  
**Phase**: Implementation Phase 3 — Real ASR, Multimodal Fusion & Structured Evidence  
**Contract Version**: `P0_ARCHITECTURE_CONTRACT_FREEZE_REV2A` (Approved)  
**Governing Contract**: `ASR_SELECTED_MODEL_INTEGRATION_CONTRACT.json`  
**Preflight Timestamp**: 2026-09-27T01:43:00+03:00  
**Overall Readiness Classification**: `ASR_READY_WITH_PACKAGING_REQUIREMENT`

---

## 1. Executive Summary & Verification Classification

The speech recognition execution environment has been configured and validated in accordance with the authoritative `ASR_SELECTED_MODEL_INTEGRATION_CONTRACT.json`:
- `faster-whisper == 1.2.1` installed and verified.
- `CTranslate2 == 4.8.2` installed with official Windows AMD64 wheel.
- `ffmpeg` 7.1 essentials binary verified and operational.
- Model `base.en` (`Systran/faster-whisper-base.en`) downloaded, verified, and operational on CPU `int8` with 8 threads.
- Real acoustic inference tested on both synthetic silence and real 3v3 match audio (C03 coach command at 78s).

**Formal Preflight Verdict**: `ASR_READY_WITH_PACKAGING_REQUIREMENT`.

---

## 2. Dependency Matrix & Installed Versions

| Component | Contract Requirement | Installed Version | Status |
| :--- | :--- | :--- | :--- |
| **Python** | Compatible runtime | `3.13.12` | **VERIFIED** |
| **faster-whisper** | `== 1.2.1` | `1.2.1` (`faster_whisper-1.2.1-py3-none-any.whl`) | **VERIFIED** |
| **CTranslate2** | Compatible engine | `4.8.2` (`ctranslate2-4.8.2-cp313-cp313-win_amd64.whl`) | **VERIFIED** |
| **FFmpeg** | $\ge 4.0$, PCM 16kHz conversion | `7.1-essentials_build` (via `imageio-ffmpeg 0.6.0`) | **VERIFIED** |
| **ONNX Runtime** | Compatible | `1.30.0` | **VERIFIED** |
| **NumPy** | Compatible array runtime | `2.5.3` | **VERIFIED** |
| **PyAV (`av`)** | $\ge 11.0$ | `18.1.0` | **VERIFIED** |

---

## 3. Faster-Whisper Model Checkpoint & Provenance

### Model Identification & Cache Details
- **Model Checkpoint**: `base.en` (~74M parameters, English-only acoustic model)
- **Hugging Face Hub Repository**: `Systran/faster-whisper-base.en`
- **Pinned Commit / Revision**: `3d3d5dee26484f91867d81cb899cfcf72b96be6c` (ref `main`)
- **Local Cache Location**:
  `C:\Users\Abdelazim\.cache\huggingface\hub\models--Systran--faster-whisper-base.en\snapshots\3d3d5dee26484f91867d81cb899cfcf72b96be6c\`
- **Snapshot Contents**:
  - `config.json` (model architecture and tokenizer hyperparameters)
  - `model.bin` (CTranslate2 int8 quantized model weights, ~140 MB)
  - `tokenizer.json` (Byte-level BPE tokenizer)
  - `vocabulary.txt` (vocabulary token map)

### Production Runtime Configuration
- **Device**: `cpu`
- **Compute Type**: `int8` (CTranslate2 integer 8-bit quantization)
- **CPU Threads**: `8`
- **Num Workers**: `1`
- **Decoding Parameters**:
  - `task = "transcribe"`
  - `language = "en"`
  - `beam_size = 5`
  - `word_timestamps = True`
  - `vad_filter = True`
  - `min_silence_duration_ms = 500`
  - `condition_on_previous_text = False`

---

## 4. Cold-Cache Behavior & Phase 5 Packaging Requirement

### Cold-Cache Risk
When `faster_whisper.WhisperModel("base.en", ...)` is called on a machine without a pre-populated cache:
- It makes an unauthenticated HTTPS call to `huggingface.co/Systran/faster-whisper-base.en`.
- If the host environment has no internet access, or if Hugging Face Hub experiences rate-limiting, initialization fails immediately with an HTTP/network exception.

### Mandatory Phase 5 Container Packaging Declaration
To ensure hermetic, reproducible execution in cloud container environments (Modal / Docker):

```
PHASE5_PACKAGING_REQUIREMENT:
Container build image must pre-bake the Hugging Face Hub snapshot:
Repository: Systran/faster-whisper-base.en
Snapshot Commit: 3d3d5dee26484f91867d81cb899cfcf72b96be6c
Location: /root/.cache/huggingface/hub/models--Systran--faster-whisper-base.en/
Environment: Set HF_HUB_OFFLINE=1 at container runtime to guarantee zero network traffic.
```

---

## 5. FFmpeg Audio Extraction Pipeline Verification

### Conversion Specification
In accordance with `ASR_SELECTED_MODEL_INTEGRATION_CONTRACT.json`:
```bash
ffmpeg -y -v error -i {input_audio} -vn -ac 1 -ar 16000 -c:a pcm_s16le {output_wav}
```
- Sample Rate: `16,000 Hz`
- Channels: `1` (mono)
- Encoding: `pcm_s16le` (16-bit uncompressed linear PCM)
- Video: stripped (`-vn`)

### Binary Availability
The standalone Windows binary is resolved via `imageio_ffmpeg.get_ffmpeg_exe()`:
`D:\Final project videos transcripts\AI-Driven Football Tactical Analysis and Training Evaluation System\.venv\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe`
- Version: `ffmpeg 7.1-essentials_build-www.gyan.dev`
- Verification: Process execution confirmed returncode 0 on test audio extraction.

---

## 6. Functional Smoke Test Outcomes

1. **Synthetic Silence Smoke**:
   - Audio: 1.0 second of 16 kHz mono silence (`pcm_s16le`).
   - Outcome: `segments == []`, `duration == 1.0s`, exit code 0 in 3.1 seconds.
   - VAD correctly suppressed silent audio.

2. **Real Match Audio Bounded Smoke (C03: 78s–90s)**:
   - Source: `3v3_real_audio_16k_mono.wav` (frames 78s–90s).
   - Segments Transcribed:
     - `[0.00s -> 1.88s]`: `" Yes, he in hold your position"`
     - `[2.82s -> 4.16s]`: `" How do you position?"`
     - `[8.68s -> 11.84s]`: `" Yes, he in hold your position and stay at your zone"`
   - Keyword Match: `"hold your position"` recognized and categorized as `Positioning / Hold Ground`.
   - Latency: ~7.8 seconds for 12 seconds of real audio on CPU (RTF $\approx 0.65\times$, faster than real-time).

---

## 7. Preflight Disposition

```
=============================================================================
PREFLIGHT DISPOSITION:
ASR_READY_WITH_PACKAGING_REQUIREMENT
=============================================================================
```
Preflight is complete. Real production ASR service implementation may proceed.
