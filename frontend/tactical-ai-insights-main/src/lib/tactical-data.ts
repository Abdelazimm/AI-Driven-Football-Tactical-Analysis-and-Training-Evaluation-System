import {
  MethodologyId,
  METHODOLOGY_IDS,
  IdentityStatus,
  IDENTITY_STATUS,
  AnalysisStage,
  ANALYSIS_STAGES,
  ReportStatus,
  REPORT_STATUS,
} from "@shared/constants";
import type { EvaluationMetrics, AnalysisResult } from "@shared/schemas";

export type { MethodologyId, IdentityStatus, AnalysisStage, ReportStatus, EvaluationMetrics, AnalysisResult };
export type MethodId = MethodologyId;

export interface Methodology {
  id: MethodologyId;
  number: number;
  title: string;
  stack: string[];
  badge: string;
  description: string;
}

export interface Metric {
  label: string;
  value?: string;
  reason?: string;
}

export const methodologies: Methodology[] = [
  {
    id: METHODOLOGY_IDS.METHOD_1_YOLO11_BOTSORT,
    number: 1,
    title: "Original Hybrid",
    stack: ["YOLO11m", "BoT-SORT", "Constrained Reconciliation"],
    badge: "Original Project Method",
    description: "Hybrid player detection, short-term tracking and constrained tracklet reconciliation.",
  },
  {
    id: METHODOLOGY_IDS.METHOD_2_RFDETR_GTATRACK,
    number: 2,
    title: "Global Association",
    stack: ["RF-DETR-L", "Deep-EIoU", "GTA"],
    badge: "Modified GTATrack-based",
    description: "Transformer-based detection with sports-oriented tracking and global tracklet association.",
  },
  {
    id: METHODOLOGY_IDS.METHOD_3_YOLO26_SRITRACK,
    number: 3,
    title: "Re-entry Focused",
    stack: ["YOLO26m", "SRITrack", "DINOv3 ReID"],
    badge: "Modified SRITrack-based",
    description: "Re-entry-focused sports tracking designed to improve player identity recovery after leaving and returning to the frame.",
  },
];

export const resultMetrics: Metric[] = [
  { label: "Players Detected", value: "Not available", reason: "Awaiting backend result" },
  { label: "Raw Track IDs", value: "Not available", reason: "Awaiting backend result" },
  { label: "Final Identities", value: "Not available", reason: "Identity gate not evaluated" },
  { label: "Fragmentation Ratio", value: "Not available", reason: "Identity ground truth required" },
  { label: "Identity Reliability", value: IDENTITY_STATUS.NOT_EVALUATED, reason: "Demonstration state" },
  { label: "Runtime", value: "Not available", reason: "No processing run attached" },
  { label: "Effective FPS", value: "Not available", reason: "No processing run attached" },
];

export const pipeline: AnalysisStage[] = [
  ANALYSIS_STAGES.UPLOADED,
  ANALYSIS_STAGES.VALIDATING,
  ANALYSIS_STAGES.PREPROCESSING,
  ANALYSIS_STAGES.DETECTING,
  ANALYSIS_STAGES.TRACKING,
  ANALYSIS_STAGES.IDENTITY_EVALUATION,
  ANALYSIS_STAGES.CALIBRATING,
  ANALYSIS_STAGES.KINEMATICS,
  ANALYSIS_STAGES.AUDIO_EXTRACTION,
  ANALYSIS_STAGES.TRANSCRIBING,
  ANALYSIS_STAGES.INSTRUCTION_PARSING,
  ANALYSIS_STAGES.FUSION,
  ANALYSIS_STAGES.GENERATING_EVIDENCE,
  ANALYSIS_STAGES.GENERATING_REPORT,
  ANALYSIS_STAGES.RENDERING,
  ANALYSIS_STAGES.UPLOADING_RESULTS,
];