import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState, useRef, type ChangeEvent } from "react";
import { ArrowRight, Check, FileAudio, SlidersHorizontal, UploadCloud, AlertCircle, RefreshCw, X, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PageIntro, PlaceholderNote } from "@/components/tactical-ui";
import { methodologies } from "@/lib/tactical-data";
import { METHODOLOGY_IDS, type MethodologyId } from "@shared/constants/methodology";
import { CALIBRATION_MODES, type CalibrationMode, AUDIO_MODES, type AudioMode } from "@shared/constants/modes";
import { useMethodologies } from "@/hooks/use-analysis";
import { apiClient, ApiClientError } from "@/lib/api-client";

export const Route = createFileRoute("/analysis/new")({
  head: () => ({
    meta: [
      { title: "New Analysis — Tactical Intelligence" },
      { name: "description", content: "Configure a football training video analysis workflow." },
      { property: "og:title", content: "New Tactical Analysis" },
      { property: "og:description", content: "Upload and configure a football training analysis session." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: NewAnalysis,
});

interface MediaUploadState {
  file: File | null;
  status: "IDLE" | "VALIDATING" | "UPLOADING" | "UPLOADED" | "ERROR";
  progress: number; // 0 to 100
  errorMessage: string | null;
  mediaId: string | null;
  durationSeconds: number | null;
}

const initialMediaState: MediaUploadState = {
  file: null,
  status: "IDLE",
  progress: 0,
  errorMessage: null,
  mediaId: null,
  durationSeconds: null,
};

const MAX_DURATION_SECONDS = 360; // 6 minutes
function uploadError(error: unknown, stage: string): string {
  if (error instanceof ApiClientError) return `${stage}: ${error.message}`;
  return `${stage}: ${error instanceof Error ? error.message : "Connection failed. Check the local API and network."}`;
}

function NewAnalysis() {
  const navigate = useNavigate();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [videoState, setVideoState] = useState<MediaUploadState>(initialMediaState);
  const [audioState, setAudioState] = useState<MediaUploadState>(initialMediaState);

  const [audioMode, setAudioMode] = useState<AudioMode>(AUDIO_MODES.EXTRACT_FROM_VIDEO);
  const [method, setMethod] = useState<MethodologyId>(METHODOLOGY_IDS.METHOD_1_YOLO11_BOTSORT);
  const [calibration, setCalibration] = useState<CalibrationMode>(CALIBRATION_MODES.NO_METRIC_CALIBRATION);
  const [isSubmittingJob, setIsSubmittingJob] = useState(false);
  const [jobSubmitError, setJobSubmitError] = useState<string | null>(null);

  const videoInputRef = useRef<HTMLInputElement>(null);
  const audioInputRef = useRef<HTMLInputElement>(null);

  const { data: serverMethods } = useMethodologies();

  // Helper to ensure a server session exists
  const ensureSession = async (): Promise<string> => {
    if (sessionId) return sessionId;
    const session = await apiClient.createSession({
      title: videoState.file ? `Training Session: ${videoState.file.name}` : "Tactical Training Session",
    });
    setSessionId(session.id);
    return session.id;
  };

  // Video validation & upload flow
  const handleVideoSelect = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Reset state
    setVideoState({
      file,
      status: "VALIDATING",
      progress: 0,
      errorMessage: null,
      mediaId: null,
      durationSeconds: null,
    });
    setJobSubmitError(null);

    // 1. Format check
    const validFormats = ["video/mp4", "video/quicktime"];
    if (!validFormats.includes(file.type) && !file.name.endsWith(".mp4") && !file.name.endsWith(".mov")) {
      setVideoState({
        file,
        status: "ERROR",
        progress: 0,
        errorMessage: "Unsupported video format. Please select an MP4 or QuickTime MOV file.",
        mediaId: null,
        durationSeconds: null,
      });
      return;
    }

    // Duration check via HTML5 video probe
    try {
      const duration = await probeVideoDuration(file);
      if (duration > MAX_DURATION_SECONDS) {
        setVideoState({
          file,
          status: "ERROR",
          progress: 0,
          errorMessage: `Video duration (${duration.toFixed(1)}s) exceeds the maximum allowed limit of 360 seconds (6 minutes).`,
          mediaId: null,
          durationSeconds: duration,
        });
        return;
      }

      // Valid! Proceed to upload
      await uploadVideoFile(file, duration);
    } catch {
      // Fallback if browser metadata probe cannot decode: proceed to upload with server validation
      await uploadVideoFile(file, null);
    }
  };

  const uploadVideoFile = async (file: File, duration: number | null) => {
    let stage = "Creating session";
    setVideoState({
      file,
      status: "UPLOADING",
      progress: 0,
      errorMessage: null,
      mediaId: null,
      durationSeconds: duration,
    });

    try {
      const currentSessionId = await ensureSession();

      // Get upload intent & scoped signed URL
      stage = "Requesting upload intent";
      const intent = await apiClient.createUploadIntent(currentSessionId, {
        media_type: "VIDEO",
        filename: file.name,
        mime_type: file.type || "video/mp4",
        size_bytes: file.size,
        duration_seconds: duration ?? undefined,
      });

      // Perform direct transfer with real byte progress
      stage = "Transferring to private storage";
      await apiClient.uploadToSignedUrl(intent.signed_upload_url, file, (_loaded, _total, percent) => {
        setVideoState((prev) => ({ ...prev, progress: percent }));
      });

      // Confirm authoritative completion
      stage = "Validating uploaded media";
      await apiClient.completeUpload(currentSessionId, intent.media_id, {
        size_bytes: file.size,
      });

      setVideoState((prev) => ({
        ...prev,
        status: "UPLOADED",
        progress: 100,
        mediaId: intent.media_id,
      }));
    } catch (err) {
      const message = uploadError(err, stage);
      setVideoState((prev) => ({
        ...prev,
        status: "ERROR",
        errorMessage: message,
      }));
    }
  };

  // Audio validation & upload flow
  const handleAudioSelect = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    let stage = "Creating session";

    setAudioState({
      file,
      status: "VALIDATING",
      progress: 0,
      errorMessage: null,
      mediaId: null,
      durationSeconds: null,
    });

    const validAudioMimes = ["audio/wav", "audio/x-wav", "audio/mpeg", "audio/mp3", "audio/m4a", "audio/x-m4a", "audio/aac"];
    const isWav = file.name.endsWith(".wav");
    const isMp3 = file.name.endsWith(".mp3");
    const isM4a = file.name.endsWith(".m4a");
    const isAac = file.name.endsWith(".aac");

    if (!validAudioMimes.includes(file.type) && !isWav && !isMp3 && !isM4a && !isAac) {
      setAudioState({
        file,
        status: "ERROR",
        progress: 0,
        errorMessage: "Unsupported audio format. Supported formats: WAV, MP3, M4A, AAC.",
        mediaId: null,
        durationSeconds: null,
      });
      return;
    }

    try {
      setAudioState((prev) => ({ ...prev, status: "UPLOADING", progress: 0 }));
      const currentSessionId = await ensureSession();

      stage = "Requesting audio upload intent";
      const intent = await apiClient.createUploadIntent(currentSessionId, {
        media_type: "COACH_AUDIO",
        filename: file.name,
        mime_type: file.type || "audio/wav",
        size_bytes: file.size,
      });

      stage = "Transferring coach audio to private storage";
      await apiClient.uploadToSignedUrl(intent.signed_upload_url, file, (_loaded, _total, percent) => {
        setAudioState((prev) => ({ ...prev, progress: percent }));
      });

      stage = "Confirming coach audio upload";
      await apiClient.completeUpload(currentSessionId, intent.media_id, {
        size_bytes: file.size,
      });

      setAudioState((prev) => ({
        ...prev,
        status: "UPLOADED",
        progress: 100,
        mediaId: intent.media_id,
      }));
    } catch (err) {
      const message = uploadError(err, stage);
      setAudioState((prev) => ({
        ...prev,
        status: "ERROR",
        errorMessage: message,
      }));
    }
  };

  // Start analysis job submission
  const handleStartAnalysis = async () => {
    if (!sessionId || videoState.status !== "UPLOADED") return;
    if (audioMode === AUDIO_MODES.SEPARATE_AUDIO_FILE && audioState.status !== "UPLOADED") return;
    if (calibration === CALIBRATION_MODES.DEMO_FIXED_CALIBRATION) return;

    setIsSubmittingJob(true);
    setJobSubmitError(null);

    try {
      const job = await apiClient.createAnalysisJob({
        session_id: sessionId,
        methodology_id: method,
        calibration_mode: calibration,
        audio_mode: audioMode,
        video_file_name: videoState.file?.name,
      });

      // Navigate to job telemetry route
      navigate({
        to: "/analysis/$jobId",
        params: { jobId: job.id },
      });
    } catch (err) {
      setIsSubmittingJob(false);
      const message = uploadError(err, "Registering analysis job");
      setJobSubmitError(message);
    }
  };

  const isVideoReady = videoState.status === "UPLOADED";
  const isAudioReady = audioMode !== AUDIO_MODES.SEPARATE_AUDIO_FILE || audioState.status === "UPLOADED";
  const isCalibrationValid = calibration !== CALIBRATION_MODES.DEMO_FIXED_CALIBRATION;
  const canStart = isVideoReady && isAudioReady && isCalibrationValid && !isSubmittingJob;

  return (
    <div className="mx-auto max-w-[1400px] px-4 py-10 lg:px-8">
      <div className="flex items-start justify-between gap-6">
        <PageIntro
          eyebrow="Analysis setup"
          title="New Analysis"
          description="Upload your football training footage, select the pipeline methodology, and launch verified session analysis."
        />
        <div aria-hidden="true" className="hidden h-24 w-20 items-center justify-center rounded-sm bg-foreground font-mono text-2xl font-black text-background sm:flex">TI</div>
      </div>

      <div className="mb-8 grid grid-cols-4 gap-2">
        {["Upload", "Configure", "Analyse", "Results"].map((s, i) => (
          <div
            key={s}
            className={`border-t-2 pt-3 ${
              i === 0 ? "border-primary text-foreground" : "border-border text-muted-foreground"
            }`}
          >
            <span className="font-mono text-[10px]">0{i + 1}</span>
            <p className="mt-1 text-xs font-bold uppercase">{s}</p>
          </div>
        ))}
      </div>

      {/* 1. Video Upload Section */}
      <section className="tactical-panel rounded-md p-5 sm:p-7">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <UploadCloud className="text-primary" />
            <div>
              <h2 className="text-lg font-bold uppercase">Upload Training Session</h2>
              <p className="text-xs text-muted-foreground">MP4 or QuickTime MOV · Maximum 6 minutes (360s) · Current demo storage accepted 48 MB and rejected 64 MiB; exact limit is unconfirmed.</p>
            </div>
          </div>
          {videoState.file && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setVideoState(initialMediaState);
                if (videoInputRef.current) videoInputRef.current.value = "";
              }}
              className="text-xs"
            >
              <X className="mr-1 h-3.5 w-3.5" /> Remove
            </Button>
          )}
        </div>

        {videoState.status === "IDLE" && (
          <label className="mt-6 flex min-h-44 cursor-pointer flex-col items-center justify-center rounded-md border border-dashed border-ai/40 bg-ai/5 p-6 text-center transition-colors hover:border-primary">
            <input
              ref={videoInputRef}
              type="file"
              accept="video/mp4,video/quicktime"
              className="sr-only"
              onChange={handleVideoSelect}
            />
            <UploadCloud className="h-8 w-8 text-ai" />
            <p className="mt-3 font-semibold">Drop a training video or select a file</p>
            <p className="mt-2 font-mono text-[10px] text-muted-foreground">Direct secure browser upload to private storage</p>
          </label>
        )}

        {videoState.status === "VALIDATING" && (
          <div className="mt-6 flex min-h-36 flex-col items-center justify-center rounded-md border border-border bg-card/40 p-6 text-center">
            <Loader2 className="h-6 w-6 animate-spin text-ai" />
            <p className="mt-3 text-sm font-semibold">Validating media format & duration...</p>
            <p className="mt-1 font-mono text-xs text-muted-foreground">{videoState.file?.name}</p>
          </div>
        )}

        {videoState.status === "UPLOADING" && (
          <div className="mt-6 rounded-md border border-border bg-card/40 p-6">
            <div className="flex items-center justify-between text-sm">
              <span className="font-semibold">{videoState.file?.name}</span>
              <span className="font-mono text-xs text-primary">{videoState.progress}%</span>
            </div>
            <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-border">
              <div
                className="h-full bg-primary transition-all duration-200"
                style={{ width: `${videoState.progress}%` }}
              />
            </div>
            <p className="mt-2 font-mono text-[10px] text-muted-foreground">
              Transferring directly to private Supabase storage...
            </p>
          </div>
        )}

        {videoState.status === "UPLOADED" && (
          <div className="mt-6 flex items-center justify-between rounded-md border border-primary/40 bg-primary/10 p-5">
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground">
                <Check className="h-4 w-4" />
              </div>
              <div>
                <p className="text-sm font-semibold">{videoState.file?.name}</p>
                <p className="font-mono text-xs text-muted-foreground">
                  {((videoState.file?.size ?? 0) / 1048576).toFixed(1)} MB · Confirmed in private storage
                  {videoState.durationSeconds && ` · ${videoState.durationSeconds.toFixed(1)}s`}
                </p>
              </div>
            </div>
            <span className="font-mono text-xs font-semibold uppercase text-primary">UPLOADED</span>
          </div>
        )}

        {videoState.status === "ERROR" && (
          <div className="mt-6 rounded-md border border-destructive/50 bg-destructive/10 p-5">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-destructive shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-semibold text-destructive">Upload Failed</p>
                <p className="mt-1 text-xs text-muted-foreground">{videoState.errorMessage}</p>
              </div>
              {videoState.file && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => uploadVideoFile(videoState.file!, videoState.durationSeconds)}
                  className="text-xs shrink-0"
                >
                  <RefreshCw className="mr-1 h-3 w-3" /> Retry
                </Button>
              )}
            </div>
          </div>
        )}
      </section>

      {/* 2. Coach Audio Section */}
      <section className="mt-4 tactical-panel rounded-md p-5 sm:p-7">
        <div className="flex items-center gap-3">
          <FileAudio className="text-ai" />
          <h2 className="text-lg font-bold uppercase">Coach Audio</h2>
        </div>
        <div className="mt-5 grid gap-2 lg:grid-cols-3">
          {(
            [
              [AUDIO_MODES.EXTRACT_FROM_VIDEO, "Use audio from uploaded video"],
              [AUDIO_MODES.SEPARATE_AUDIO_FILE, "Upload separate coach audio file"],
              [AUDIO_MODES.NO_AUDIO, "No coach audio available"],
            ] as const
          ).map(([v, l]) => (
            <label
              key={v}
              className={`cursor-pointer rounded-md border p-4 text-sm transition-all ${
                audioMode === v ? "border-ai bg-ai/10" : "border-border bg-background/30"
              }`}
            >
              <input
                type="radio"
                name="audio"
                value={v}
                checked={audioMode === v}
                onChange={() => setAudioMode(v)}
                className="mr-3 accent-primary"
              />
              {l}
            </label>
          ))}
        </div>

        {audioMode === AUDIO_MODES.EXTRACT_FROM_VIDEO && (
          <p className="mt-4 text-sm text-muted-foreground">
            Coach audio will be extracted automatically from the uploaded video track during pipeline execution.
          </p>
        )}

        {audioMode === AUDIO_MODES.NO_AUDIO && (
          <p className="mt-4 text-sm text-muted-foreground">
            No audio processing will be performed. Pure spatial and tactical movement analysis only.
          </p>
        )}

        {audioMode === AUDIO_MODES.SEPARATE_AUDIO_FILE && (
          <div className="mt-4">
            {audioState.status === "IDLE" && (
              <label className="flex cursor-pointer items-center justify-between rounded-md border border-dashed border-border p-4 text-sm hover:border-ai">
                <div className="flex items-center gap-3">
                  <FileAudio className="text-ai" />
                  <span>Choose separate coach audio file (WAV, MP3, M4A, AAC)</span>
                </div>
                <input
                  ref={audioInputRef}
                  type="file"
                  accept="audio/*"
                  className="sr-only"
                  onChange={handleAudioSelect}
                />
                <Button size="sm" variant="tactical" asChild>
                  <span>Select</span>
                </Button>
              </label>
            )}

            {audioState.status === "UPLOADING" && (
              <div className="rounded-md border border-border bg-card/40 p-4">
                <div className="flex items-center justify-between text-sm">
                  <span>{audioState.file?.name}</span>
                  <span className="font-mono text-xs text-primary">{audioState.progress}%</span>
                </div>
                <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-border">
                  <div
                    className="h-full bg-primary transition-all duration-200"
                    style={{ width: `${audioState.progress}%` }}
                  />
                </div>
              </div>
            )}

            {audioState.status === "UPLOADED" && (
              <div className="flex items-center justify-between rounded-md border border-primary/40 bg-primary/10 p-4">
                <div className="flex items-center gap-3">
                  <Check className="h-4 w-4 text-primary" />
                  <span className="text-sm font-semibold">{audioState.file?.name}</span>
                </div>
                <span className="font-mono text-xs text-primary uppercase">UPLOADED</span>
              </div>
            )}

            {audioState.status === "ERROR" && (
              <div className="flex items-center justify-between rounded-md border border-destructive/50 bg-destructive/10 p-4 text-xs text-destructive">
                <span>{audioState.errorMessage}</span>
                {audioState.file && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      if (audioInputRef.current) audioInputRef.current.value = "";
                      setAudioState(initialMediaState);
                    }}
                    className="text-xs"
                  >
                    Reset
                  </Button>
                )}
              </div>
            )}
          </div>
        )}
      </section>

      {/* 3. Methodology Selection Section */}
      <section className="mt-4">
        <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="font-mono text-[10px] text-primary">PROCESSING METHODOLOGY</p>
            <h2 className="mt-1 text-xl font-bold uppercase">Select the analysis pipeline</h2>
          </div>
          <Link to="/comparisons" className="text-xs font-semibold text-ai hover:text-primary">
            Compare methodologies →
          </Link>
        </div>

        <div className="grid gap-3 lg:grid-cols-3">
          {methodologies.map((m) => {
            const serverMeta = serverMethods?.find((sm) => sm.id === m.id);
            const isExperimental = serverMeta?.availability === "EXPERIMENTAL";
            return (
              <label
                key={m.id}
                className={`tactical-panel relative cursor-pointer rounded-md p-5 transition-all ${
                  method === m.id
                    ? "scale-[1.01] border-primary shadow-[0_0_30px_color-mix(in_oklab,var(--primary)_12%,transparent)]"
                    : "hover:border-ai/50"
                }`}
              >
                <input
                  type="radio"
                  name="method"
                  value={m.id}
                  checked={method === m.id}
                  onChange={() => setMethod(m.id)}
                  className="sr-only"
                />
                <div className="flex items-start justify-between">
                  <span className="font-mono text-xs text-ai">METHOD {m.number}</span>
                  {method === m.id && <Check className="h-4 w-4 text-primary" />}
                </div>
                <h3 className="mt-4 text-xl font-bold">{m.title}</h3>
                <div className="mt-4 font-mono text-xs font-semibold leading-6 text-foreground">
                  {m.stack.map((x, i) => (
                    <span key={x}>
                      {x}
                      {i < m.stack.length - 1 && <b className="mx-2 text-primary">+</b>}
                    </span>
                  ))}
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  <span className="inline-block rounded-sm border border-border px-2 py-1 text-[10px] text-muted-foreground">
                    {m.badge}
                  </span>
                  {serverMeta && (
                    <span
                      className={`inline-block rounded-sm px-2 py-1 font-mono text-[10px] uppercase ${
                        isExperimental
                          ? "border border-warning/40 bg-warning/10 text-warning"
                          : "border border-primary/40 bg-primary/10 text-primary"
                      }`}
                    >
                      {serverMeta.availability}
                    </span>
                  )}
                </div>
                <p
                  className={`overflow-hidden text-sm leading-6 text-muted-foreground transition-all ${
                    method === m.id ? "mt-5 max-h-28 opacity-100" : "max-h-0 opacity-0"
                  }`}
                >
                  {serverMeta?.availability_reason || m.description}
                </p>
              </label>
            );
          })}
        </div>
      </section>

      {/* 4. Metric Calibration Section */}
      <section className="mt-4 tactical-panel rounded-md p-5 sm:p-7">
        <div className="flex items-center gap-3">
          <SlidersHorizontal className="text-ai" />
          <div>
            <p className="font-mono text-[10px] text-muted-foreground">ADVANCED SETTINGS</p>
            <h2 className="text-lg font-bold uppercase">Metric Calibration</h2>
          </div>
        </div>

        <div className="mt-5 grid gap-2 md:grid-cols-3">
          {(
            [
              [CALIBRATION_MODES.NO_METRIC_CALIBRATION, "No Metric Calibration", "Pixel-space analysis only (Default safe)"],
              [CALIBRATION_MODES.CUSTOM_PITCH_CALIBRATION, "Custom Pitch Calibration", "Requires pitch keypoints geometry"],
              [CALIBRATION_MODES.DEMO_FIXED_CALIBRATION, "Validated Demo Calibration", "Demo-specific · Rejected for uploaded videos"],
            ] as const
          ).map(([v, l, d]) => (
            <label
              key={v}
              className={`rounded-md border p-4 ${
                calibration === v ? "border-primary bg-primary/5" : "border-border"
              }`}
            >
              <input
                type="radio"
                name="cal"
                checked={calibration === v}
                onChange={() => setCalibration(v)}
                className="mr-3 accent-primary"
              />
              <span className="text-sm font-semibold">{l}</span>
              <p className="ml-6 mt-2 text-xs text-muted-foreground">{d}</p>
            </label>
          ))}
        </div>

        {calibration === CALIBRATION_MODES.DEMO_FIXED_CALIBRATION && (
          <div className="mt-4">
            <PlaceholderNote>
              Scientific Guardrail: Validated Demo Calibration is strictly reserved for frozen demonstration footage.
              It cannot be applied to arbitrary uploaded videos. Please select No Metric Calibration.
            </PlaceholderNote>
          </div>
        )}

        {calibration === CALIBRATION_MODES.CUSTOM_PITCH_CALIBRATION && (
          <div className="mt-4">
            <PlaceholderNote>
              Custom Pitch Calibration requires 4 pitch geometry landmarks. Metric estimation will be configured once
              keypoint annotation is supported.
            </PlaceholderNote>
          </div>
        )}
      </section>

      {/* 5. Summary & Action Section */}
      <section className="mt-6 border-t border-border pt-6">
        <div className="grid gap-4 lg:grid-cols-[1fr_auto] lg:items-end">
          <div>
            <p className="font-mono text-[10px] text-ai">ANALYSIS SUMMARY</p>
            <dl className="mt-3 grid gap-3 text-sm sm:grid-cols-2 xl:grid-cols-4">
              {[
                ["Video", videoState.file?.name ?? "Not selected"],
                [
                  "Coach Audio",
                  audioMode === AUDIO_MODES.EXTRACT_FROM_VIDEO
                    ? "Extract from video"
                    : audioMode === AUDIO_MODES.NO_AUDIO
                    ? "None"
                    : audioState.file?.name ?? "Not selected",
                ],
                ["Methodology", methodologies.find((m) => m.id === method)?.title ?? "—"],
                [
                  "Calibration",
                  calibration === CALIBRATION_MODES.NO_METRIC_CALIBRATION
                    ? "No Metric Calibration"
                    : calibration === CALIBRATION_MODES.CUSTOM_PITCH_CALIBRATION
                    ? "Custom Pitch Calibration"
                    : "Demo only (Invalid for uploads)",
                ],
              ].map(([k, v]) => (
                <div key={k}>
                  <dt className="text-xs text-muted-foreground">{k}</dt>
                  <dd className="mt-1 font-semibold">{v}</dd>
                </div>
              ))}
            </dl>
          </div>

          <Button
            size="xl"
            variant="command"
            disabled={!canStart}
            onClick={handleStartAnalysis}
            title={
              !isVideoReady
                ? "Upload training video to proceed"
                : !isAudioReady
                ? "Upload coach audio to proceed"
                : !isCalibrationValid
                ? "Select a valid calibration mode"
                : "Register analysis job"
            }
          >
            {isSubmittingJob ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Registering Job...
              </>
            ) : (
              <>
                Start Analysis <ArrowRight className="ml-2 h-4 w-4" />
              </>
            )}
          </Button>
        </div>

        {jobSubmitError && (
          <p className="mt-4 text-xs font-semibold text-destructive">{jobSubmitError}</p>
        )}

        <p className="mt-4 text-xs text-muted-foreground">
          {!isVideoReady
            ? "Upload your training session video to enable analysis job creation."
            : !isAudioReady
            ? "Upload the separate coach audio file to continue."
            : !isCalibrationValid
            ? "Validated Demo Calibration is not permitted for arbitrary user uploads. Select No Metric Calibration."
            : "Media assets are securely persisted. Starting analysis will create a verified job record."}
        </p>
      </section>
    </div>
  );
}

// Utility: probe video duration using browser HTML5 video decoding
function probeVideoDuration(file: File): Promise<number> {
  return new Promise((resolve, reject) => {
    const videoEl = document.createElement("video");
    videoEl.preload = "metadata";
    const objectUrl = URL.createObjectURL(file);

    videoEl.onloadedmetadata = () => {
      URL.revokeObjectURL(objectUrl);
      resolve(videoEl.duration);
    };

    videoEl.onerror = () => {
      URL.revokeObjectURL(objectUrl);
      reject(new Error("Failed to load video metadata."));
    };

    videoEl.src = objectUrl;
  });
}
