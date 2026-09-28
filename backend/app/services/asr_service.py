"""
Real Frozen ASR Service & Audio Extraction for Implementation Phase 3.
Governed by:
- ASR_SELECTED_MODEL_INTEGRATION_CONTRACT.json
- ASR_TEXT_NORMALIZATION_CONTRACT.json
- P0_ARCHITECTURE_CONTRACT_FREEZE_REV2A
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from backend.app.schemas.asr import (
    ASRFailure,
    ASRResult,
    ASRSegment,
    TacticalEvent,
)


# ==============================================================================
# 1. FROZEN TAXONOMY & NORMALIZATION CONTRACTS
# ==============================================================================

# Governed by ASR_TEXT_NORMALIZATION_CONTRACT.json & evaluate_asr.py
NUMBER_MAP: Dict[str, str] = {
    "0": "zero",
    "1": "one",
    "2": "two",
    "3": "three",
    "4": "four",
    "5": "five",
    "6": "six",
    "7": "seven",
    "8": "eight",
    "9": "nine",
    "10": "ten",
}

CONTRACTION_MAP: Dict[str, str] = {
    r"\bi'm\b": "im",
    r"\bdon't\b": "dont",
    r"\byou're\b": "youre",
    r"\bcan't\b": "cant",
    r"\bit's\b": "its",
    r"\bwe're\b": "were",
    r"\bthey're\b": "theyre",
    r"\bwon't\b": "wont",
    r"\bhe's\b": "hes",
    r"\bshe's\b": "shes",
    r"\blet's\b": "lets",
}

# Exactly five frozen categories from P0_ARCHITECTURE_CONTRACT_FREEZE_REV2A
FROZEN_TACTICAL_CATEGORIES: List[str] = [
    "Defensive",
    "Offensive",
    "Pressing",
    "Passing",
    "Positioning / Hold Ground",
]

# Governed by P0_ARCHITECTURE_CONTRACT_FREEZE_REV2A tactical_taxonomy.keyword_mappings
FROZEN_TACTICAL_TAXONOMY: Dict[str, List[str]] = {
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
    "Positioning / Hold Ground": [
        "hold your position",
        "hold position",
        "hold your ground",
        "stay in position",
        "stick to your zone",
        "stay in your zone",
        "keep your shape",
    ],
}


def normalize_text(text: Optional[str]) -> str:
    """
    Applies the frozen text normalization contract (ASR_TEXT_NORMALIZATION_CONTRACT.json):
    1. Lowercase and trim
    2. Contraction apostrophe removal ('i'm' -> 'im', 'don't' -> 'dont')
    3. Hyphens and underscores to space ('drop-back' -> 'drop back')
    4. Remove punctuation except alphanumeric characters and whitespace
    5. Expand standalone cardinal digits 0 through 10 ('2' -> 'two')
    6. Collapse whitespace to single space
    """
    if not text:
        return ""

    norm = text.lower().strip()

    # Contractions
    for pattern, repl in CONTRACTION_MAP.items():
        norm = re.sub(pattern, repl, norm)

    # Hyphens and underscores to space
    norm = re.sub(r"[-_]", " ", norm)

    # Remove all punctuation except alphanumeric and spaces
    norm = re.sub(r"[^\w\s]", "", norm)

    # Number token expansion (standalone digits 0-10)
    for digit, word in NUMBER_MAP.items():
        norm = re.sub(rf"\b{digit}\b", word, norm)

    # Collapse whitespace
    norm = re.sub(r"\s+", " ", norm).strip()

    return norm


# ==============================================================================
# 2. AUDIO EXTRACTION SERVICE
# ==============================================================================

def get_ffmpeg_binary() -> str:
    """Resolves the ffmpeg executable from PATH or bundled imageio-ffmpeg."""
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        raise RuntimeError("No ffmpeg executable found on system PATH or via imageio-ffmpeg.")


class AudioExtractionService:
    """
    Production audio extractor using FFmpeg.
    Converts video/audio files to 16 kHz mono 16-bit PCM WAV in isolated job workspaces.
    """

    def __init__(self, ffmpeg_path: Optional[str] = None):
        self._ffmpeg_path = ffmpeg_path or get_ffmpeg_binary()

    def extract_pcm_wav(
        self,
        input_path: Union[str, Path],
        output_wav_path: Optional[Union[str, Path]] = None,
        job_dir: Optional[Union[str, Path]] = None,
    ) -> Tuple[Optional[Path], Optional[ASRFailure]]:
        """
        Extracts 16 kHz mono PCM WAV from input media file.
        Returns (output_path, None) on success, or (None, ASRFailure) on failure.
        """
        src = Path(input_path)
        if not src.exists():
            return None, ASRFailure(
                error_type="NO_USABLE_AUDIO",
                error_message=f"Input file does not exist: {input_path}",
                recoverable_vision_only=True,
                details={"input_path": str(input_path)},
            )

        if src.stat().st_size == 0:
            return None, ASRFailure(
                error_type="ASR_EMPTY",
                error_message=f"Input file is zero bytes: {input_path}",
                recoverable_vision_only=True,
                details={"input_path": str(input_path)},
            )

        # Determine target path
        if output_wav_path:
            dst = Path(output_wav_path)
            dst.parent.mkdir(parents=True, exist_ok=True)
        elif job_dir:
            job_p = Path(job_dir)
            job_p.mkdir(parents=True, exist_ok=True)
            dst = job_p / f"{src.stem}_extracted_16k_mono.wav"
        else:
            # Temporary file with clean lifecycle
            temp_fd, temp_path = tempfile.mkstemp(prefix="audio_extract_", suffix=".wav")
            os.close(temp_fd)
            dst = Path(temp_path)

        cmd = [
            self._ffmpeg_path,
            "-y",
            "-v", "error",
            "-i", str(src),
            "-vn",
            "-ac", "1",
            "-ar", "16000",
            "-c:a", "pcm_s16le",
            str(dst),
        ]

        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
            if res.returncode != 0:
                if dst.exists():
                    try:
                        dst.unlink()
                    except OSError:
                        pass
                return None, ASRFailure(
                    error_type="AUDIO_EXTRACTION_FAILED",
                    error_message=f"FFmpeg extraction failed with return code {res.returncode}: {res.stderr.strip()}",
                    recoverable_vision_only=True,
                    details={"returncode": res.returncode, "stderr": res.stderr.strip()},
                )

            if not dst.exists() or dst.stat().st_size == 0:
                if dst.exists():
                    try:
                        dst.unlink()
                    except OSError:
                        pass
                return None, ASRFailure(
                    error_type="NO_USABLE_AUDIO",
                    error_message="FFmpeg produced an empty or missing audio file (media may contain no audio stream).",
                    recoverable_vision_only=True,
                    details={"input_path": str(input_path)},
                )

            return dst, None

        except Exception as ex:
            if dst.exists():
                try:
                    dst.unlink()
                except OSError:
                    pass
            return None, ASRFailure(
                error_type="AUDIO_EXTRACTION_FAILED",
                error_message=f"Exception during audio extraction: {str(ex)}",
                recoverable_vision_only=True,
                details={"exception": str(ex)},
            )


# ==============================================================================
# 3. REAL FROZEN ASR SERVICE
# ==============================================================================

class ASRService:
    """
    Frozen Production ASR Service using faster-whisper 1.2.1.
    Preserves exact model checkpoint, CPU int8 runtime, and deterministic keyword extraction.
    """

    def __init__(
        self,
        model_id: str = "base.en",
        device: str = "cpu",
        compute_type: str = "int8",
        cpu_threads: int = 8,
    ):
        # Strict contract enforcement: default to frozen parameters
        self.model_id = model_id
        self.device = device
        self.compute_type = compute_type
        self.cpu_threads = cpu_threads
        self._model = None

    def _get_model(self):
        """Lazy loader for faster-whisper WhisperModel."""
        if self._model is None:
            try:
                import faster_whisper
                self._model = faster_whisper.WhisperModel(
                    self.model_id,
                    device=self.device,
                    compute_type=self.compute_type,
                    cpu_threads=self.cpu_threads,
                )
            except Exception as ex:
                raise RuntimeError(
                    f"Failed to load faster-whisper model '{self.model_id}' on {self.device}/{self.compute_type}: {ex}"
                )
        return self._model

    def extract_tactical_events(
        self,
        segments: List[ASRSegment],
    ) -> List[TacticalEvent]:
        """
        Deterministically extracts tactical events from normalized ASR segments.
        Inherits parent-segment timestamps.
        Enforces target_player = None and target_resolution_status = 'UNRESOLVED_TARGET'.
        """
        events: List[TacticalEvent] = []
        event_counter = 0

        for seg in segments:
            norm_text = seg.normalized_text
            if not norm_text:
                continue

            # Check categories in authoritative frozen order
            for category in FROZEN_TACTICAL_CATEGORIES:
                keywords = FROZEN_TACTICAL_TAXONOMY.get(category, [])
                # Sort keywords by length descending so longer phrases match first
                sorted_keywords = sorted(keywords, key=len, reverse=True)
                
                matched_action = None
                for kw in sorted_keywords:
                    # Match with word boundaries
                    pattern = rf"\b{re.escape(kw)}\b"
                    if re.search(pattern, norm_text):
                        matched_action = kw
                        break

                if matched_action is not None:
                    # Parent segment timestamp inheritance
                    t_start = round(seg.start_s, 2)
                    t_end = round(seg.end_s, 2)
                    
                    # Multimodal reaction window: [t_end + 2.0s, t_end + 6.0s]
                    eval_start = round(t_end + 2.0, 2)
                    eval_end = round(t_end + 6.0, 2)

                    movement_profile = (
                        "High Intensity" if category == "Pressing"
                        else "Hold Zone / Low Speed" if category == "Positioning / Hold Ground"
                        else "Context Dependent"
                    )

                    events.append(
                        TacticalEvent(
                            event_id=f"evt_{event_counter}",
                            category=category,
                            action=matched_action,
                            t_start=t_start,
                            t_end=t_end,
                            source_segment_id=seg.segment_id,
                            source_text=seg.raw_text,
                            target_player=None,
                            target_resolution_status="UNRESOLVED_TARGET",
                            alignment_window_start_s=eval_start,
                            alignment_window_end_s=eval_end,
                            expected_movement_profile=movement_profile,
                        )
                    )
                    event_counter += 1

        return events

    def transcribe(
        self,
        audio_path: Union[str, Path],
        session_id: str = "session",
        source_offset_s: float = 0.0,
    ) -> Union[ASRResult, ASRFailure]:
        """
        Transcribes the given 16 kHz WAV audio and extracts deterministic tactical events.
        Applies source_offset_s to align timestamps with absolute session timeline.
        NO historical transcript fallback is ever executed.
        """
        src = Path(audio_path)
        if not src.exists():
            return ASRFailure(
                error_type="NO_USABLE_AUDIO",
                error_message=f"Audio file does not exist: {audio_path}",
                recoverable_vision_only=True,
                details={"audio_path": str(audio_path)},
            )

        if src.stat().st_size == 0:
            return ASRFailure(
                error_type="ASR_EMPTY",
                error_message="Audio file is empty (0 bytes).",
                recoverable_vision_only=True,
                details={"audio_path": str(audio_path)},
            )

        try:
            model = self._get_model()
        except Exception as ex:
            return ASRFailure(
                error_type="WHISPER_INFERENCE_FAILED",
                error_message=f"Model loading error: {str(ex)}",
                recoverable_vision_only=True,
                details={"exception": str(ex)},
            )

        # Frozen decoding parameters from ASR_SELECTED_MODEL_INTEGRATION_CONTRACT.json
        try:
            raw_segments_generator, info = model.transcribe(
                str(src),
                task="transcribe",
                language="en",
                beam_size=5,
                word_timestamps=True,
                vad_filter=True,
                vad_parameters={"min_silence_duration_ms": 500},
                condition_on_previous_text=False,
            )
            raw_segments = list(raw_segments_generator)
        except Exception as ex:
            return ASRFailure(
                error_type="WHISPER_INFERENCE_FAILED",
                error_message=f"Whisper transcription failed during inference: {str(ex)}",
                recoverable_vision_only=True,
                details={"exception": str(ex)},
            )

        # Distinct empty audio check
        if not raw_segments:
            return ASRFailure(
                error_type="ASR_EMPTY",
                error_message="No speech detected in audio segment (VAD / whisper returned zero segments).",
                recoverable_vision_only=True,
                details={"audio_duration_probed": getattr(info, "duration", 0.0)},
            )

        # Convert to typed ASRSegment list with offset restoration
        segments: List[ASRSegment] = []
        raw_text_list = []
        norm_text_list = []

        for seg in raw_segments:
            # Absolute timeline timestamp adjustment
            start_s = round(seg.start + source_offset_s, 2)
            end_s = round(seg.end + source_offset_s, 2)
            raw_txt = seg.text.strip()
            norm_txt = normalize_text(raw_txt)

            raw_text_list.append(raw_txt)
            norm_text_list.append(norm_txt)

            word_list = []
            if getattr(seg, "words", None):
                for w in seg.words:
                    word_list.append({
                        "word": w.word,
                        "start_s": round(w.start + source_offset_s, 2),
                        "end_s": round(w.end + source_offset_s, 2),
                        "probability": round(w.probability, 4) if getattr(w, "probability", None) is not None else 1.0,
                    })

            segments.append(
                ASRSegment(
                    segment_id=seg.id,
                    start_s=start_s,
                    end_s=end_s,
                    raw_text=raw_txt,
                    normalized_text=norm_txt,
                    words=word_list,
                    avg_logprob=round(seg.avg_logprob, 4) if getattr(seg, "avg_logprob", None) is not None else None,
                    no_speech_prob=round(seg.no_speech_prob, 4) if getattr(seg, "no_speech_prob", None) is not None else None,
                )
            )

        # Extract deterministic tactical events
        tactical_events = self.extract_tactical_events(segments)

        audio_duration = round(getattr(info, "duration", 0.0), 2)
        if audio_duration == 0.0 and segments:
            audio_duration = segments[-1].end_s - source_offset_s

        return ASRResult(
            session_id=session_id,
            audio_path=str(audio_path),
            audio_duration_s=audio_duration,
            model_id=self.model_id,
            device=self.device,
            compute_type=self.compute_type,
            cpu_threads=self.cpu_threads,
            source_offset_s=source_offset_s,
            segments=segments,
            events=tactical_events,
            raw_transcript=" ".join(raw_text_list),
            normalized_transcript=" ".join(norm_text_list),
            limitations=[
                "Automatic transcript text requires manual verification before quotation as ground truth.",
                "Tactical commands extracted with deterministic rule-based keyword taxonomy.",
                "All coaching event targets remain unresolved without reliable player association.",
            ],
            provenance={
                "model": f"faster-whisper {self.model_id}",
                "backend": "CTranslate2",
                "device": self.device,
                "compute_type": self.compute_type,
                "cpu_threads": self.cpu_threads,
                "beam_size": 5,
                "vad_filter": True,
                "condition_on_previous_text": False,
            },
        )
