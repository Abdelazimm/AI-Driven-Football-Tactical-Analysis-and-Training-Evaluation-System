/**
 * React Query hooks for analysis workflows and methodology telemetry.
 */
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient, ApiClientError } from "@/lib/api-client";
import type { CreateAnalysisJobRequest } from "@shared/schemas/job";

export function useMethodologies() {
  return useQuery({
    queryKey: ["methodologies"],
    queryFn: () => apiClient.getMethodologies(),
    staleTime: 5 * 60 * 1000,
  });
}

export function useAnalysisJob(jobId: string | undefined) {
  return useQuery({
    queryKey: ["analysisJob", jobId],
    queryFn: () => {
      if (!jobId) throw new Error("jobId is required");
      return apiClient.getAnalysisJob(jobId);
    },
    enabled: Boolean(jobId),
    retry: (failureCount, error) => {
      if (error instanceof ApiClientError && error.status === 404) return false;
      return failureCount < 2;
    },
  });
}

export function useCreateAnalysisJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: CreateAnalysisJobRequest) => apiClient.createAnalysisJob(request),
    onSuccess: (newJob) => {
      queryClient.setQueryData(["analysisJob", newJob.id], newJob);
    },
  });
}

export function useCreateSession() {
  return useMutation({
    mutationFn: (data?: { title?: string; coach_name?: string; team_name?: string; notes?: string }) =>
      apiClient.createSession(data),
  });
}

export function useUploadIntent() {
  return useMutation({
    mutationFn: ({ sessionId, intent }: { sessionId: string; intent: Parameters<typeof apiClient.createUploadIntent>[1] }) =>
      apiClient.createUploadIntent(sessionId, intent),
  });
}

export function useCompleteUpload() {
  return useMutation({
    mutationFn: ({
      sessionId,
      mediaId,
      payload,
    }: {
      sessionId: string;
      mediaId: string;
      payload?: Parameters<typeof apiClient.completeUpload>[2];
    }) => apiClient.completeUpload(sessionId, mediaId, payload),
  });
}

export function useSessionMedia(sessionId: string | undefined) {
  return useQuery({
    queryKey: ["sessionMedia", sessionId],
    queryFn: () => {
      if (!sessionId) throw new Error("sessionId is required");
      return apiClient.getSessionMedia(sessionId);
    },
    enabled: Boolean(sessionId),
  });
}

export function useAnalysisResult(jobId: string | undefined) {
  return useQuery({
    queryKey: ["analysisResult", jobId],
    queryFn: async () => {
      if (!jobId) throw new Error("jobId is required");
      try {
        const result = await apiClient.getAnalysisResult(jobId);
        return { isReady: true, result, notReadyError: null };
      } catch (err) {
        if (err instanceof ApiClientError && err.status === 409) {
          return { isReady: false, result: null, notReadyError: err };
        }
        throw err;
      }
    },
    enabled: Boolean(jobId),
    retry: false,
  });
}

