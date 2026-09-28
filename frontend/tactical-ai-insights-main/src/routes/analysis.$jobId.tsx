import { createFileRoute, Link, Outlet, useLocation } from "@tanstack/react-router";
import { Check, Clock3, Radio, Video, AlertCircle, ArrowRight, ShieldAlert } from "lucide-react";
import { PageIntro, PlaceholderNote, StatusBadge, TacticalPitch } from "@/components/tactical-ui";
import { Button } from "@/components/ui/button";
import { pipeline } from "@/lib/tactical-data";
import { useAnalysisJob } from "@/hooks/use-analysis";
import { ApiClientError } from "@/lib/api-client";

export const Route = createFileRoute("/analysis/$jobId")({
  head: () => ({
    meta: [
      { title: "Processing Job — Tactical Intelligence" },
      { name: "description", content: "Inspect analysis pipeline job telemetry." },
      { property: "og:title", content: "Analysis Job Processing" },
      { property: "og:type", content: "website" },
    ],
  }),
  component: JobRoute,
});

function JobRoute() {
  const pathname = useLocation({ select: (location) => location.pathname });
  return pathname.endsWith("/results") ? <Outlet /> : <JobProcessing />;
}

function JobProcessing() {
  const { jobId } = Route.useParams();
  const { data: job, isLoading, error } = useAnalysisJob(jobId);

  if (isLoading) {
    return (
      <div className="mx-auto max-w-[1400px] px-4 py-16 lg:px-8 text-center">
        <div className="tactical-panel mx-auto max-w-md rounded-md p-8">
          <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          <p className="mt-4 font-mono text-xs uppercase text-muted-foreground">Connecting to analysis backend...</p>
          <p className="mt-2 text-sm font-semibold">Retrieving job {jobId}</p>
        </div>
      </div>
    );
  }

  if (error || !job) {
    const isNotFound = error instanceof ApiClientError && error.status === 404;
    return (
      <div className="mx-auto max-w-[1400px] px-4 py-16 lg:px-8 text-center">
        <div className="tactical-panel mx-auto max-w-md rounded-md p-8 border-destructive/50">
          <AlertCircle className="mx-auto h-10 w-10 text-destructive" />
          <h2 className="mt-4 text-xl font-bold uppercase">{isNotFound ? "Job Not Found" : "Error Loading Job"}</h2>
          <p className="mt-2 font-mono text-xs text-muted-foreground">ID: {jobId}</p>
          <p className="mt-4 text-sm leading-6 text-muted-foreground">
            {isNotFound
              ? "The requested job was not found in the development repository. Process memory resets on server restarts."
              : (error as Error)?.message || "Failed to retrieve job."}
          </p>
          <div className="mt-6">
            <Button asChild variant="command">
              <Link to="/analysis/new">Create New Analysis</Link>
            </Button>
          </div>
        </div>
      </div>
    );
  }

  const currentStageIndex = pipeline.indexOf(job.current_stage as any);
  const activeIndex = currentStageIndex >= 0 ? currentStageIndex : 0;

  return (
    <div className="mx-auto max-w-[1400px] px-4 py-10 lg:px-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <PageIntro
          eyebrow="Job Telemetry"
          title={`Job ${job.id}`}
          description={`Session ID: ${job.session_id} · Mode: ${job.mode.replaceAll("_", " ")}`}
        />
        <div className="flex items-center gap-3">
          <StatusBadge tone={job.current_stage === "UPLOADED" ? "muted" : "warning"}>
            {job.current_stage.replaceAll("_", " ")}
          </StatusBadge>
          <Button asChild size="sm" variant="tactical">
            <Link to="/analysis/$jobId/results" params={{ jobId: job.id }}>
              View Results <ArrowRight className="ml-1 h-3.5 w-3.5" />
            </Link>
          </Button>
        </div>
      </div>

      <div className="mb-5 grid gap-3 sm:grid-cols-3">
        <Info icon={<Radio />} label="Methodology" value={job.methodology_id.replaceAll("_", " ")} />
        <Info
          icon={<Clock3 />}
          label="Created At"
          value={new Date(job.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        />
        <Info icon={<Video />} label="Calibration Mode" value={job.calibration_mode.replaceAll("_", " ")} />
      </div>

      <div className="h-1.5 overflow-hidden rounded-full bg-muted">
        <div
          className="h-full bg-primary shadow-[0_0_14px_var(--primary)] transition-all duration-500"
          style={{ width: `${Math.max(job.progress_percent, 2)}%` }}
        />
      </div>
      <div className="mt-3 flex justify-between font-mono text-[10px]">
        <span className="text-primary font-bold">
          {job.progress_percent.toFixed(1)}% · {job.current_stage}
        </span>
        <span className="text-muted-foreground">{job.stage_message || "Awaiting pipeline trigger"}</span>
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-[.85fr_1.15fr]">
        <section className="tactical-panel rounded-md p-5">
          <h2 className="mb-5 text-sm font-bold uppercase">Pipeline Sequence</h2>
          <div className="max-h-[560px] overflow-auto pr-2">
            {pipeline.map((stage, i) => {
              const isCompleted = i < activeIndex;
              const isCurrent = i === activeIndex;
              return (
                <div key={stage} className="relative flex gap-3 pb-4 last:pb-0">
                  <div
                    className={`relative z-10 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border ${
                      isCompleted
                        ? "border-primary bg-primary text-primary-foreground"
                        : isCurrent
                        ? "animate-pulse border-ai bg-ai/10 text-ai"
                        : "border-border bg-card text-muted-foreground"
                    }`}
                  >
                    {isCompleted ? <Check className="h-3.5 w-3.5" /> : <span className="text-[9px]">{String(i + 1).padStart(2, "0")}</span>}
                  </div>
                  {i < pipeline.length - 1 && (
                    <div className={`absolute left-[11px] top-6 h-full w-px ${isCompleted ? "bg-primary" : "bg-border"}`} />
                  )}
                  <div>
                    <p
                      className={`font-mono text-[11px] ${
                        isCurrent ? "font-bold text-ai" : isCompleted ? "text-foreground" : "text-muted-foreground"
                      }`}
                    >
                      {stage.replaceAll("_", " ")}
                    </p>
                    <p className="mt-1 text-[10px] text-muted-foreground">
                      {isCompleted ? "Completed" : isCurrent ? (job.stage_message || "Active stage") : "Pending"}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        <section>
          <div className="tactical-panel rounded-md p-3">
            <TacticalPitch />
          </div>
          <div className="mt-4">
            <PlaceholderNote>
              The pitch animation communicates expected spatial tracking activity. Live session bounding boxes and trajectories will attach upon pipeline processing.
            </PlaceholderNote>
          </div>
        </section>
      </div>
    </div>
  );
}

function Info({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="tactical-panel flex items-center gap-3 rounded-md p-4">
      <span className="text-ai [&_svg]:h-4 [&_svg]:w-4">{icon}</span>
      <div>
        <p className="text-[10px] uppercase text-muted-foreground">{label}</p>
        <p className="mt-1 text-sm font-semibold truncate">{value}</p>
      </div>
    </div>
  );
}
