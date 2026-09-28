/**
 * Typed HTTP Client for the FastAPI backend service.
 * Normalizes API error responses and handles request dispatch.
 */
import type { ApiError } from "@shared/schemas/error";
import type { MethodologyMetadata } from "@shared/schemas/methodology";
import type { AnalysisJob, CreateAnalysisJobRequest } from "@shared/schemas/job";
import type { AnalysisResult } from "@shared/schemas/result";
import type { Session } from "@shared/schemas/session";
import type { MediaAsset } from "@shared/schemas/media";
import type {
  UploadIntentRequest,
  UploadIntentResponse,
  CompleteUploadRequest,
} from "@shared/schemas/upload";

const configuredApiBaseUrl = import.meta.env['VITE_API_BASE_URL'] as string | undefined;
const API_BASE_URL = (
  configuredApiBaseUrl || (import.meta.env.DEV && typeof window !== "undefined" ? "" : "http://127.0.0.1:8000")
).replace(/\/+$/, "");

export interface ShowcaseResponse {
  showcase_status: string;
  showcase_mode: string;
  scientific_automated_status: string;
  disclaimer: string;
  badges: string[];
  cards: Array<{ id: string; title: string; player: string; instructions: string[]; time: string; response_summary: string; primary_metrics: Array<{ label: string; value: string }> }>;
  resolved_media: Record<string, { media_type: string; sha256: string; file_size_bytes: number }>;
  full_coach_report_markdown: string;
  limitations: string[];
  methodology_note: string;
}

export interface DemoVideoAccess { url: string; label: string; expires_in_seconds: number; media_id: string }

export class ApiClientError extends Error {
  public readonly code: string;
  public readonly status: number;
  public readonly details?: Record<string, unknown> | null | undefined;

  constructor(status: number, errorData: ApiError) {
    super(errorData.message || `API error ${status}`);
    this.name = "ApiClientError";
    this.code = errorData.code || "UNKNOWN_ERROR";
    this.status = status;
    this.details = errorData.details ?? undefined;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;
  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && options.body && typeof options.body === "string") {
    headers.set("Content-Type", "application/json");
  }
  if (!headers.has("Accept")) {
    headers.set("Accept", "application/json");
  }

  let response: Response;
  try {
    response = await fetch(url, { ...options, headers });
  } catch {
    throw new ApiClientError(0, { code: "BACKEND_UNREACHABLE", message: "Could not reach the analysis backend. Check that the local API is running and the browser is allowed to connect." });
  }

  if (!response.ok) {
    let errorPayload: ApiError;
    try {
      errorPayload = (await response.json()) as ApiError;
    } catch {
      errorPayload = {
        code: `HTTP_${response.status}`,
        message: response.statusText || `Request failed with status ${response.status}`,
      };
    }
    throw new ApiClientError(response.status, errorPayload);
  }

  return (await response.json()) as T;
}

export const apiClient = {
  get<T>(path: string): Promise<T> {
    return request<T>(path, { method: "GET" });
  },

  post<T, B = unknown>(path: string, body: B): Promise<T> {
    return request<T>(path, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  // Sessions API
  createSession(data: { title?: string; coach_name?: string; team_name?: string; notes?: string } = {}): Promise<Session> {
    return apiClient.post<Session>("/api/v1/sessions", {
      title: data.title || "Tactical Training Session",
      coach_name: data.coach_name,
      team_name: data.team_name,
      notes: data.notes,
    });
  },

  getSession(sessionId: string): Promise<Session> {
    return apiClient.get<Session>(`/api/v1/sessions/${encodeURIComponent(sessionId)}`);
  },

  // Media & Uploads API
  createUploadIntent(sessionId: string, payload: UploadIntentRequest): Promise<UploadIntentResponse> {
    return apiClient.post<UploadIntentResponse, UploadIntentRequest>(
      `/api/v1/sessions/${encodeURIComponent(sessionId)}/media/upload-intent`,
      payload
    );
  },

  uploadToSignedUrl(
    signedUrl: string,
    file: File,
    onProgress?: (loaded: number, total: number, percent: number) => void
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open("PUT", signedUrl, true);
      xhr.setRequestHeader("Content-Type", file.type || "application/octet-stream");

      if (xhr.upload && onProgress) {
        xhr.upload.onprogress = (e) => {
          if (e.lengthComputable && e.total > 0) {
            const percent = Math.min(100, Math.round((e.loaded / e.total) * 100));
            onProgress(e.loaded, e.total, percent);
          }
        };
      }

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve();
        } else {
          reject(
            new ApiClientError(xhr.status, {
              code: xhr.status === 413 ? "STORAGE_SIZE_LIMIT" : "STORAGE_UPLOAD_FAILED",
              message: xhr.status === 413
                ? "Storage rejected this file because it exceeds the current project limit. The current demo project accepted a 48 MB file and rejected a 64 MiB probe."
                : `Storage transfer failed with status ${xhr.status}: ${xhr.statusText || "Error"}`,
            })
          );
        }
      };

      xhr.onerror = () => {
        reject(
          new ApiClientError(0, {
            code: "NETWORK_ERROR",
            message: "Could not transfer to private storage. Check the network connection and browser CORS access.",
          })
        );
      };

      xhr.send(file);
    });
  },

  completeUpload(sessionId: string, mediaId: string, payload: CompleteUploadRequest = {}): Promise<MediaAsset> {
    return apiClient.post<MediaAsset, CompleteUploadRequest>(
      `/api/v1/sessions/${encodeURIComponent(sessionId)}/media/${encodeURIComponent(mediaId)}/complete`,
      payload
    );
  },

  getSessionMedia(sessionId: string): Promise<MediaAsset[]> {
    return apiClient.get<MediaAsset[]>(`/api/v1/sessions/${encodeURIComponent(sessionId)}/media`);
  },

  // Canonical methodology & job endpoints
  getMethodologies(): Promise<MethodologyMetadata[]> {
    return apiClient.get<MethodologyMetadata[]>("/api/v1/methodologies");
  },

  createAnalysisJob(payload: CreateAnalysisJobRequest): Promise<AnalysisJob> {
    return apiClient.post<AnalysisJob, CreateAnalysisJobRequest>("/api/v1/analysis/jobs", payload);
  },

  getAnalysisJob(jobId: string): Promise<AnalysisJob> {
    return apiClient.get<AnalysisJob>(`/api/v1/analysis/jobs/${encodeURIComponent(jobId)}`);
  },

  getAnalysisResult(jobId: string): Promise<AnalysisResult> {
    return apiClient.get<AnalysisResult>(`/api/v1/analysis/jobs/${encodeURIComponent(jobId)}/result`);
  },

  getDemoInputVideo(jobId: string): Promise<DemoVideoAccess> {
    return apiClient.get<DemoVideoAccess>(`/api/v1/analysis/jobs/${encodeURIComponent(jobId)}/demo-input-video`);
  },

  getShowcase(): Promise<ShowcaseResponse> {
    return apiClient.get<ShowcaseResponse>("/api/v1/showcase");
  },

  showcaseMediaUrl(caseId: string): string {
    return `${API_BASE_URL}/api/v1/showcase/media/${encodeURIComponent(caseId)}`;
  },
};
