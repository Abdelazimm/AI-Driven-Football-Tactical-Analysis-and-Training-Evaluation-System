import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";
import { Download, FileText, ArrowLeft, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PageIntro, StatusBadge } from "@/components/tactical-ui";
import { CoachReportPresentation } from "@/components/coach-report";
import { useAnalysisJob, useAnalysisResult } from "@/hooks/use-analysis";
import { apiClient } from "@/lib/api-client";
import { VALIDATED_DEMO_JOB_ID } from "@/lib/demo";
import type { AnalysisResult } from "@shared/schemas/result";

export const Route = createFileRoute("/analysis/$jobId/results")({
  head: () => ({ meta: [{ title: "Job Results — Tactical Intelligence" }] }),
  component: JobResults,
});

type EvidenceItem = {
  evidence_id?: string; source_event_id?: string; scope?: string; event_category?: string;
  event_action?: string; observations_count?: number; spatial_context?: unknown;
  limitations?: string[]; window_start_s?: number; window_end_s?: number;
};

function evidenceItems(result: AnalysisResult): EvidenceItem[] {
  const value: unknown = result.structured_evidence?.evidence_items;
  return Array.isArray(value) ? value as EvidenceItem[] : [];
}

function validSeekTime(video: HTMLVideoElement, requestedSeconds: number) {
  return Number.isFinite(video.duration)
    ? Math.min(Math.max(requestedSeconds, 0), video.duration)
    : Math.max(requestedSeconds, 0);
}

function downloadReport(result: AnalysisResult) {
  if (!result.report_markdown) return;
  const url = URL.createObjectURL(new Blob([result.report_markdown], { type: "text/markdown;charset=utf-8" }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `coach-report-${result.job_id}.md`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return <section className="tactical-panel rounded-md p-5 sm:p-6"><h2 className="mb-4 flex items-center gap-2 text-lg font-bold uppercase"><FileText className="h-4 w-4 text-ai" />{title}</h2><div className="text-sm leading-7 text-muted-foreground">{children}</div></section>;
}

function JobResults() {
  const { jobId } = Route.useParams();
  const [activeTab, setActiveTab] = useState("summary");
  const [pendingSeek, setPendingSeek] = useState<number | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<string | null>(null);
  const [videoPlaybackError, setVideoPlaybackError] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const videoPanelRef = useRef<HTMLDivElement>(null);
  const refreshAttemptedRef = useRef(false);
  const { data: job, isLoading: jobLoading, error: jobError } = useAnalysisJob(jobId);
  const { data: resultState, isLoading: resultLoading, error: resultError } = useAnalysisResult(jobId);
  const { data: inputVideo, error: inputVideoError, refetch: refreshVideo } = useQuery({
    queryKey: ["demoInputVideo", jobId], queryFn: () => apiClient.getDemoInputVideo(jobId),
    enabled: jobId === VALIDATED_DEMO_JOB_ID, staleTime: 10 * 60_000, retry: false,
  });

  const seekWhenReady = useCallback(() => {
    const video = videoRef.current;
    if (pendingSeek === null || !video || video.readyState < HTMLMediaElement.HAVE_METADATA) return;
    const target = validSeekTime(video, pendingSeek);
    if (Math.abs(video.currentTime - target) < 0.25) {
      setPendingSeek(null);
      return;
    }
    video.currentTime = target;
  }, [pendingSeek]);

  useEffect(() => {
    if (activeTab !== "video" || pendingSeek === null) return;
    videoPanelRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    seekWhenReady();
  }, [activeTab, inputVideo, pendingSeek, seekWhenReady]);

  function viewEventInVideo(eventId: string, startSeconds: number) {
    setSelectedEvent(eventId);
    setPendingSeek(startSeconds);
    setActiveTab("video");
    if (videoPlaybackError || !inputVideo) void refreshVideo();
  }

  if (jobLoading || resultLoading) return <div className="mx-auto max-w-[1500px] px-4 py-16 text-center text-sm">Checking persisted results...</div>;
  if (jobError || resultError) return <div className="mx-auto max-w-[1500px] px-4 py-10"><Panel title="Results unavailable"><p>The local backend could not retrieve this job. {String((jobError || resultError) instanceof Error ? (jobError || resultError)!.message : "Check the API connection.")}</p></Panel></div>;
  if (!resultState?.isReady || !resultState.result) return <div className="mx-auto max-w-[1500px] px-4 py-10"><PageIntro eyebrow="Job Results" title="Result not ready" description={`Job ${jobId} · ${job?.status ?? "Status unavailable"}`} /><Panel title="Processing status"><p>The result has not been persisted yet. Current stage: {job?.current_stage ?? "Unavailable"}.</p></Panel></div>;

  const result = resultState.result;
  const evidence = evidenceItems(result);
  const playerAnalysisWithheld = !result.identity_evaluation.player_level_analysis_allowed;
  const noMetricCalibration = result.calibration_mode === "NO_METRIC_CALIBRATION";
  const missingWindows = evidence.filter((item) => item.limitations?.some((code) => code === "NO_TRACKS_DETECTED_IN_RESPONSE_WINDOW" || code === "NO_VISUAL_OBSERVATIONS_IN_RESPONSE_WINDOW"));
  const overlay = result.artifact_references.find((artifact) => artifact.kind === "OVERLAY_VIDEO");
  const manifest = result.execution_manifest as Record<string, unknown> | undefined;
  const mediaMetadata = manifest?.['media_metadata'] as Record<string, unknown> | undefined;
  const reportSummary: string[] = [];
  if (result.job_status === "COMPLETED_WITH_LIMITATIONS" && result.instruction_events.length > 0) {
    reportSummary.push(`This session analysis completed with limitations and recorded ${result.instruction_events.length} tactical coaching events.`);
  } else {
    reportSummary.push(`The persisted session status is ${result.job_status.replaceAll("_", " ").toLowerCase()}.`);
    if (result.instruction_events.length > 0) reportSummary.push(`${result.instruction_events.length} tactical coaching events are available for review.`);
  }
  if (playerAnalysisWithheld) {
    reportSummary.push(result.identity_evaluation.method_formal_identity_status === "FAIL_UNSAFE_MERGE"
      ? "Persistent player identity was not established safely in the formal benchmark, so individual player conclusions are withheld."
      : "Individual player conclusions are withheld under the persisted identity evaluation.");
  }
  if (noMetricCalibration) reportSummary.push("Physical distance and speed are unavailable because this session did not use an approved metric calibration.");
  if (missingWindows.length > 0) reportSummary.push(`${missingWindows.length} instruction response windows have insufficient visual evidence.`);
  const tabs = [
    ["summary", "Session Details"], ["events", "Tactical Events"], ["video", "Video / Media"],
    ["spatial", "Radar / Spatial View"], ["kinematics", "Kinematics"], ["identity", "Identity Safety"],
    ["report", "Full Coach Report"], ["artifacts", "Artifacts / Provenance"],
  ] as const;

  return <div className="mx-auto max-w-[1500px] px-4 py-10 lg:px-8">
    <div className="flex flex-wrap items-start justify-between gap-4">
      <PageIntro eyebrow="Automated session analysis" title="Full-Session Analysis" description={`Job ${jobId}`} />
      <Button asChild size="sm" variant="tactical"><Link to="/analysis/$jobId" params={{ jobId }}><ArrowLeft className="mr-2 h-4 w-4" />Job telemetry</Link></Button>
    </div>
    <div className="mb-5 flex flex-wrap gap-2"><StatusBadge tone="warning">{result.job_status === "COMPLETED_WITH_LIMITATIONS" ? "Completed with limitations" : result.job_status.replaceAll("_", " ").toLowerCase()}</StatusBadge>{playerAnalysisWithheld && <StatusBadge tone="warning">Player-level findings withheld</StatusBadge>}{noMetricCalibration && <StatusBadge tone="muted">Physical metrics unavailable</StatusBadge>}</div>
    <section aria-labelledby="coach-overview-title" className="tactical-panel rounded-md border-l-4 border-l-ai p-5 sm:p-7">
      <p className="mb-2 text-xs font-bold uppercase tracking-wide text-ai">Automated session analysis</p>
      <h2 id="coach-overview-title" className="text-xl font-bold text-foreground sm:text-2xl">Coach Overview</h2>
      <p className="mt-2 text-sm leading-6 text-muted-foreground">{result.job_status === "COMPLETED_WITH_LIMITATIONS" ? "The session completed with limitations." : `Session status: ${result.job_status}.`} Review the detected tactical events alongside the analyzed session video.</p>
      <div className="mt-5 grid gap-3 md:grid-cols-3">
        <div className="rounded-md border border-border p-4"><p className="text-2xl font-bold text-foreground">{result.instruction_events.length}</p><p className="text-sm font-semibold">Tactical instruction events</p><p className="mt-1 text-xs text-muted-foreground">Select an event to review its existing video timestamp.</p></div>
        <div className="rounded-md border border-warning/40 bg-warning/5 p-4"><p className="text-sm font-bold text-foreground">{playerAnalysisWithheld ? "Player-specific analysis withheld" : "Player-level analysis allowed"}</p><p className="mt-2 text-sm leading-6 text-muted-foreground">{playerAnalysisWithheld ? "Persistent physical-player identity was not established safely in the formal benchmark. Player-level accumulated analytics are therefore withheld." : "The persisted identity evaluation permits player-level analysis for this result. Review the Identity Safety tab for the evidence basis."}</p></div>
        <div className="rounded-md border border-border p-4"><p className="text-sm font-bold text-foreground">{noMetricCalibration ? "Physical distance and speed unavailable" : "Calibration details"}</p><p className="mt-2 text-sm leading-6 text-muted-foreground">{noMetricCalibration ? "This analysis did not use an approved metric calibration, so metre and km/h values are not reported." : `Calibration mode: ${result.calibration_mode}. Review the persisted metrics and calibration evidence before interpreting physical values.`}</p></div>
      </div>
      <p className="mt-4 text-xs text-muted-foreground">This is an automated full-session result. The C03, C04 and C06 <Link to="/showcase" className="font-semibold text-primary underline">capability showcase</Link> uses manually verified examples.</p>
    </section>
    <Tabs value={activeTab} onValueChange={setActiveTab} className="mt-6">
      <TabsList className="h-auto w-full justify-start gap-1 overflow-x-auto rounded-md border border-border bg-card p-1">{tabs.map(([value, label]) => <TabsTrigger key={value} value={value} className="shrink-0 data-[state=active]:bg-accent data-[state=active]:text-primary">{label}</TabsTrigger>)}</TabsList>

      <TabsContent value="summary" className="mt-5"><div className="grid gap-5 lg:grid-cols-2">
        <Panel title="What this result can show"><ul className="list-disc space-y-2 pl-5"><li>{result.instruction_events.length} tactical instruction events are available for review.</li><li>{evidence.length} structured evidence items are retained in the persisted result.</li><li>{result.report_status === "DETERMINISTIC_FALLBACK" ? "An evidence-based report is available." : "The persisted coach report is available."}</li></ul>{missingWindows.length > 0 && <p className="mt-4 rounded-sm border border-warning/40 bg-warning/5 p-3 text-warning">{missingWindows.length} instruction response windows have insufficient visual evidence. No zero movement is inferred.</p>}</Panel>
        <Panel title="Interpretation boundary"><p className="text-foreground">Persistent physical-player identity was not established safely in the formal benchmark. Player-level accumulated analytics are therefore withheld.</p><p className="mt-4">{result.identity_evaluation.withholding_reason}</p><details className="mt-5 rounded-md border border-border p-4"><summary className="cursor-pointer font-semibold text-foreground">Technical details and provenance</summary><dl className="mt-4 grid gap-3 sm:grid-cols-2">{[["Method", result.methodology_id], ["Job status", result.job_status], ["Report mode", result.report_status], ["Formal identity", result.identity_evaluation.method_formal_identity_status || result.identity_evaluation.identity_status], ["Calibration", result.calibration_mode], ["Tactical events", String(result.instruction_events.length)], ["Structured evidence", `${evidence.length} items`], ["Player-level analysis", result.identity_evaluation.player_level_analysis_allowed ? "Allowed" : "WITHHELD"]].map(([label, value]) => <div key={label} className="min-w-0 border-b border-border pb-2"><dt className="text-xs">{label}</dt><dd className="break-all font-mono text-xs font-semibold text-foreground">{value}</dd></div>)}</dl></details></Panel>
      </div></TabsContent>

      <TabsContent value="events" className="mt-5"><Panel title="Coach tactical events"><p className="mb-4">{result.instruction_events.length} events from the persisted result. Unresolved targets remain unresolved.</p><div className="grid gap-3 md:grid-cols-2">{result.instruction_events.map((event) => {const item = evidence.find((entry) => entry.source_event_id === event.id && entry.scope === "EVENT"); const missing = item?.limitations?.some((code) => code.includes("NO_TRACKS") || code.includes("NO_VISUAL")); return <article key={event.id} className="rounded-md border border-border p-4"><p className="font-mono text-xs text-ai">{event.start_s.toFixed(2)}–{event.end_s.toFixed(2)} s · {event.id}</p><h3 className="mt-2 font-bold text-foreground">{event.category} · {event.action || "Action unavailable"}</h3><p className="mt-2 text-xs">Target: {event.is_target_resolved ? event.target_player_pseudonym : "Unresolved"}</p>{missing && <p className="mt-2 text-xs text-warning">Insufficient visual evidence was available in this response window.</p>}{jobId === VALIDATED_DEMO_JOB_ID && <Button type="button" size="sm" variant="tactical" className="mt-4" onClick={() => viewEventInVideo(event.id, event.start_s)} aria-label={`View ${event.category} event at ${event.start_s.toFixed(2)} seconds in video`}><Play className="mr-2 h-3.5 w-3.5" />View in video</Button>}</article>})}</div></Panel></TabsContent>

      <TabsContent value="video" className="mt-5"><div ref={videoPanelRef}><Panel title="Analyzed Session Video">{selectedEvent && <p className="mb-3 rounded-sm border border-ai/40 bg-ai/5 p-3 text-foreground">Reviewing tactical event {selectedEvent}{pendingSeek !== null ? ` · seeking to ${pendingSeek.toFixed(2)} s` : ""}.</p>}{inputVideo ? <><video ref={videoRef} key={inputVideo.media_id} controls preload="metadata" className="aspect-video w-full rounded-md bg-black" src={inputVideo.url} aria-label="Analyzed Session Video" onLoadedMetadata={() => { refreshAttemptedRef.current = false; setVideoPlaybackError(false); seekWhenReady(); }} onSeeked={() => { if (pendingSeek !== null && videoRef.current && Math.abs(videoRef.current.currentTime - validSeekTime(videoRef.current, pendingSeek)) < 0.5) setPendingSeek(null); }} onError={() => { setVideoPlaybackError(true); if (!refreshAttemptedRef.current) { refreshAttemptedRef.current = true; void refreshVideo(); } }} /><p className="mt-2 text-xs">Private, short-lived playback URL for the persisted transport input. <button type="button" className="underline" onClick={() => { refreshAttemptedRef.current = false; setVideoPlaybackError(false); void refreshVideo(); }}>Refresh playback link</button></p>{videoPlaybackError && <p role="alert" className="mt-2 text-sm text-warning">Playback could not load. Refresh the playback link and try again.</p>}</> : <p>{inputVideoError ? <>Private input playback could not be loaded from storage. <button type="button" className="underline" onClick={() => void refreshVideo()}>Retry playback link</button>.</> : "Loading private input playback..."}</p>}<p className="mt-4 rounded-sm border border-border p-3">{overlay ? "Annotated output artifact is registered for this job." : "An annotated output video was not generated for this run. Analysis results are shown in the Events, Evidence, Identity, and Report tabs."}</p></Panel></div></TabsContent>

      <TabsContent value="spatial" className="mt-5"><Panel title="Spatial evidence"><p>No calibrated pitch radar was generated for this run. Calibration is {result.calibration_mode}, so pixel observations are not labelled in metres.</p><div className="mt-4 grid gap-3 md:grid-cols-2">{evidence.filter((item) => item.spatial_context).slice(0, 12).map((item) => <div key={item.evidence_id} className="rounded-sm border border-border p-3"><span className="font-mono text-xs text-ai">{item.scope || "Evidence"}</span><p className="font-semibold text-foreground">{item.event_category || "Spatial observation"}{item.event_action ? ` · ${item.event_action}` : ""}</p><p>{item.observations_count ? "Tracked observations available" : "No tracked observations available"}</p></div>)}</div></Panel></TabsContent>

      <TabsContent value="kinematics" className="mt-5"><Panel title="Movement and speed"><p>{Object.keys(result.metrics).length === 0 ? "No metric kinematics were emitted for this non-metric run. Distance and speed values are unavailable." : "Movement metrics are present in the persisted result; interpret them according to their calibration and identity gates."}</p></Panel></TabsContent>

      <TabsContent value="identity" className="mt-5"><Panel title="Identity safety gate"><p className="text-foreground">Persistent physical-player identity was not established safely in the formal benchmark. Player-level accumulated analytics are therefore withheld.</p><dl className="mt-5 grid gap-3 sm:grid-cols-2">{[["Formal status", result.identity_evaluation.method_formal_identity_status], ["Formal basis", result.identity_evaluation.method_formal_identity_evidence_basis], ["Runtime diagnostic", result.identity_evaluation.runtime_identity_status], ["Runtime basis", result.identity_evaluation.runtime_identity_evidence_basis], ["Player-level analysis", result.identity_evaluation.player_level_analysis_allowed ? "Allowed" : "WITHHELD"]].map(([label, value]) => <div key={label} className="border-b border-border pb-2"><dt className="text-xs">{label}</dt><dd className="font-mono text-xs font-semibold text-foreground">{value || "Unavailable"}</dd></div>)}</dl><p className="mt-5">{result.identity_evaluation.withholding_reason}</p></Panel></TabsContent>

      <TabsContent value="report" className="mt-5"><Panel title="Full Coach Report">{result.report_markdown ? <><CoachReportPresentation markdown={result.report_markdown} scope="automated" summarySentences={reportSummary} /><p className="mt-5 text-xs text-muted-foreground">{result.report_status === "DETERMINISTIC_FALLBACK" ? "Evidence-based report" : "Persisted coach report"} · Report mode: {result.report_status}</p><Button variant="tactical" className="mt-6" onClick={() => downloadReport(result)}><Download className="mr-2 h-4 w-4" />Download Markdown report</Button></> : <p>No persisted report text is available.</p>}</Panel></TabsContent>

      <TabsContent value="artifacts" className="mt-5"><Panel title="Artifacts and provenance"><dl className="grid gap-3 sm:grid-cols-2">{[["Input role", manifest?.['input_asset_role']], ["Authoritative source SHA-256", manifest?.['authoritative_source_sha256']], ["Transport copy SHA-256", manifest?.['transport_copy_sha256']], ["Input duration", mediaMetadata?.['duration_seconds']], ["Input resolution", mediaMetadata?.['resolution_width'] && mediaMetadata?.['resolution_height'] ? `${mediaMetadata['resolution_width']}×${mediaMetadata['resolution_height']}` : undefined]].map(([label, value]) => <div key={String(label)} className="min-w-0 border-b border-border pb-2"><dt className="text-xs">{String(label)}</dt><dd className="break-all font-mono text-xs text-foreground">{value == null ? "Unavailable" : String(value)}</dd></div>)}</dl><h3 className="mt-6 font-bold text-foreground">Persisted artifacts</h3><ul className="mt-3 space-y-2">{result.artifact_references.map((artifact) => <li key={artifact.id} className="rounded-sm border border-border p-3"><strong className="text-foreground">{artifact.kind}</strong><span className="ml-2 font-mono text-xs">{artifact.file_size_bytes.toLocaleString()} bytes</span></li>)}</ul></Panel></TabsContent>
    </Tabs>
  </div>;
}
