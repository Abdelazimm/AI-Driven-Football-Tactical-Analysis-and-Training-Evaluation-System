"""
Pipeline Stage: Audio Extraction & Speech Recognition
Source Research: 02_audio_pipeline.ipynb
Governing Contract: ASR_SELECTED_MODEL_INTEGRATION_CONTRACT.json

Responsibilities:
- Extract 16 kHz mono PCM WAV via FFmpeg
- Transcribe speech using faster-whisper base.en CPU int8
- Extract word-level timestamps and VAD segments (500 ms min silence)
- Extract deterministic tactical coaching events (Positioning, Pressing, Passing, Defensive, Offensive)
- Enforce privacy boundary: raw ASR outputs tagged private
- Fail closed with typed ASRFailure (never substitute historical transcripts)
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple, Union

from backend.app.schemas.asr import (
    ASRFailure,
    ASRResult,
    ASRSegment,
    TacticalEvent,
)
from backend.app.schemas.transcript import TranscriptSegment, WordTimestamp
from backend.app.services.asr_service import (
    AudioExtractionService,
    ASRService,
    normalize_text,
)


class AudioPipeline:
    """
    Production Audio Pipeline orchestrating audio extraction and faster-whisper ASR.
    """

    def __init__(
        self,
        model_size: str = "base.en",
        device: str = "cpu",
        compute_type: str = "int8",
        cpu_threads: int = 8,
        ffmpeg_path: Optional[str] = None,
    ):
        self.extractor = AudioExtractionService(ffmpeg_path=ffmpeg_path)
        self.asr_service = ASRService(
            model_id=model_size,
            device=device,
            compute_type=compute_type,
            cpu_threads=cpu_threads,
        )

    def extract_audio(
        self,
        video_path: Union[str, Path],
        output_wav_path: Optional[Union[str, Path]] = None,
        job_dir: Optional[Union[str, Path]] = None,
    ) -> Tuple[Optional[str], Optional[ASRFailure]]:
        """
        Extracts 16 kHz mono PCM WAV from input video/audio.
        Returns (output_path, None) or (None, ASRFailure).
        """
        dst, err = self.extractor.extract_pcm_wav(
            input_path=video_path,
            output_wav_path=output_wav_path,
            job_dir=job_dir,
        )
        if err is not None:
            return None, err
        return str(dst) if dst else None, None

    def process_audio(
        self,
        audio_path: Union[str, Path],
        session_id: str = "session",
        source_offset_s: float = 0.0,
    ) -> Union[ASRResult, ASRFailure]:
        """
        Processes WAV audio directly using the frozen ASR service.
        """
        return self.asr_service.transcribe(
            audio_path=audio_path,
            session_id=session_id,
            source_offset_s=source_offset_s,
        )

    def process_video(
        self,
        video_path: Union[str, Path],
        session_id: str = "session",
        job_dir: Optional[Union[str, Path]] = None,
        source_offset_s: float = 0.0,
    ) -> Union[ASRResult, ASRFailure]:
        """
        End-to-end extraction and transcription of video file.
        Cleans up temporary audio files if generated in temporary directory.
        """
        extracted_path, err = self.extract_audio(video_path=video_path, job_dir=job_dir)
        if err is not None:
            return err

        try:
            return self.process_audio(
                audio_path=extracted_path,
                session_id=session_id,
                source_offset_s=source_offset_s,
            )
        finally:
            # If a temporary file was created (not in a caller-managed job_dir), clean it up
            if extracted_path and not job_dir and Path(extracted_path).exists():
                try:
                    Path(extracted_path).unlink()
                except OSError:
                    pass

    def transcribe(self, wav_path: str) -> List[TranscriptSegment]:
        """
        Legacy compatibility method returning List[TranscriptSegment].
        """
        res = self.process_audio(audio_path=wav_path)
        if isinstance(res, ASRFailure):
            return []

        segments: List[TranscriptSegment] = []
        for seg in res.segments:
            words = [
                WordTimestamp(
                    word=w["word"],
                    start_s=w["start_s"],
                    end_s=w["end_s"],
                    probability=w.get("probability", 1.0),
                )
                for w in seg.words
            ]
            segments.append(
                TranscriptSegment(
                    segment_id=seg.segment_id,
                    start_s=seg.start_s,
                    end_s=seg.end_s,
                    text=seg.raw_text,
                    confidence=1.0 - (seg.no_speech_prob or 0.0),
                    words=words,
                    is_private=True,
                )
            )
        return segments
