"""
Pipeline Stage: Short-Term Tracking
Source Research: 01_vision_pipeline.ipynb, configs/botsort_football_fallback_C.yaml

Responsibilities:
- Ingest ordered frame detections
- Associate bounding boxes across temporal frames using Ultralytics BoT-SORT
- Emit TrackObservation records with short-term track IDs and bottom-center footpoints

NOTE: Integration placeholder.
"""
from typing import List
from backend.app.schemas.detection import Detection
from backend.app.schemas.tracking import TrackObservation


class TrackingPipeline:
    def __init__(self, tracker_config_path: str):
        self.tracker_config_path = tracker_config_path

    def process_detections(self, detections: List[Detection]) -> List[TrackObservation]:
        """Placeholder for short-term tracking association."""
        raise NotImplementedError("Tracking pipeline extraction will occur in a later controlled step.")
