import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, ShieldCheck } from "lucide-react";
import { PageIntro, StatusBadge } from "@/components/tactical-ui";
import { CoachReportPresentation } from "@/components/coach-report";
import { apiClient } from "@/lib/api-client";
import type { ShowcaseResponse } from "@/lib/api-client";
import { VALIDATED_DEMO_JOB_ID } from "@/lib/demo";

export const Route = createFileRoute("/showcase")({
  head: () => ({ meta: [{ title: "Validated Capability Showcase — Tactical Intelligence" }] }),
  component: Showcase,
});

function firstRecordedSentence(responseSummary: string) {
  return responseSummary.match(/^[^.!?]+[.!?]/u)?.[0] ?? responseSummary;
}

function coachMeaningFromFrozenResponse(card: ShowcaseResponse["cards"][number]) {
  const response = card.response_summary;
  const caseId = card.id.split("_")[0];
  if (caseId === "C03" && response.includes("entered it") && response.includes("remained inside")) {
    return "The manually verified player entered the intended tactical zone and remained there during the evaluated period.";
  }
  if (caseId === "C04" && response.includes("reduced ground-plane separation") && response.includes("follow-up median separation remained lower")) {
    return "The manually verified player moved closer to the opponent during the marking sequence, and the later separation remained lower than before the instruction.";
  }
  if (caseId === "C06" && response.includes("reduced separation") && response.includes("both pressing events")) {
    return "The manually verified player moved closer to the checked opponents in both pressing events.";
  }
  return firstRecordedSentence(response);
}

function Showcase() {
  const { data, isLoading, error } = useQuery({ queryKey: ["showcase"], queryFn: apiClient.getShowcase, staleTime: 60_000 });
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const card = data?.cards.find((item) => item.id === selectedId) ?? data?.cards[0];
  const caseId = card?.id.split("_")[0] ?? "";
  const media = data?.resolved_media[caseId];
  const caseSummary = card ? [
    `This is a manually verified ${card.title.toLowerCase()} example.`,
    coachMeaningFromFrozenResponse(card),
    "These manual checks do not certify automated persistent player identity.",
  ] : [];

  return <div className="mx-auto max-w-[1500px] px-4 py-10 lg:px-8">
    <PageIntro eyebrow="Manually verified capability demonstration" title="Validated Capability Showcase" description="Three frozen, oracle-assisted cases with manually verified instruction targets, player identities, opponent relationships, and tactical meaning." />
    <div className="mb-7 rounded-md border-l-4 border-l-warning border-y border-r border-warning/40 bg-warning/5 p-5 text-sm leading-6">
      <p className="mb-2 text-xs font-bold uppercase tracking-wide text-warning">Manually verified capability demonstration</p>
      <strong className="text-warning">Scientific boundary:</strong> {data?.disclaimer ?? "These examples use manually verified identities and instruction targets. They do not certify automated persistent identity."}
    </div>
    <Link to="/analysis/$jobId/results" params={{ jobId: VALIDATED_DEMO_JOB_ID }} className="mb-7 inline-flex items-center gap-2 rounded-md border border-primary/40 px-4 py-3 text-sm font-semibold text-primary hover:bg-primary/10">
      View existing validated full-session result <ArrowRight className="h-4 w-4" />
    </Link>
    {isLoading && <p className="text-sm text-muted-foreground">Loading verified showcase fixtures...</p>}
    {error && <p className="rounded-md border border-destructive p-5 text-sm">Showcase fixtures are unavailable from the local backend. {error instanceof Error ? error.message : "Check the API connection."}</p>}
    {data && <>
      <div className="grid gap-4 lg:grid-cols-3">
        {data.cards.map((item) => <button key={item.id} type="button" onClick={() => setSelectedId(item.id)} aria-pressed={card?.id === item.id} className={`tactical-panel rounded-md p-5 text-left transition-colors hover:border-primary ${card?.id === item.id ? "border-primary" : ""}`}>
          <span className="font-mono text-xs text-primary">{item.id.split("_")[0]}</span><span className="ml-3 text-[10px] font-bold uppercase tracking-wide text-warning">Manually verified</span>
          <h2 className="mt-2 text-xl font-bold">{item.title}</h2>
          <p className="mt-3 text-sm leading-6 text-muted-foreground">{item.response_summary}</p>
          <p className="mt-4 text-xs font-semibold text-ai">Open verified case →</p>
        </button>)}
      </div>
      {card && <section className="tactical-panel mt-6 rounded-md p-5 sm:p-7" aria-label={`${caseId} case details`}>
        <div className="flex flex-wrap items-center gap-3"><h2 className="text-2xl font-bold">{caseId} — {card.title}</h2><StatusBadge tone="warning">MANUALLY VERIFIED CAPABILITY DEMONSTRATION</StatusBadge></div>
        <p className="mt-2 font-mono text-xs text-muted-foreground">{data.showcase_mode} · {card.time} · verified pseudonym {card.player}</p>
        <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1.35fr)_minmax(300px,1fr)]">
          <div>
            {media?.media_type === "video/mp4" ? <video key={caseId} controls preload="metadata" className="w-full rounded-md bg-black" src={apiClient.showcaseMediaUrl(caseId)} aria-label={`${caseId} validated overlay video`} /> :
              media?.media_type === "image/png" ? <img className="w-full rounded-md border border-border" src={apiClient.showcaseMediaUrl(caseId)} alt={`${caseId} validated response contact sheet`} /> :
              <p className="rounded-md border border-border p-5 text-sm">No verified media is available for this case.</p>}
            {media && <p className="mt-2 break-all font-mono text-[10px] text-muted-foreground">Verified fixture SHA-256: {media.sha256}</p>}
          </div>
          <div className="space-y-5 text-sm">
            <div><h3 className="font-bold uppercase">Verified instruction</h3><ul className="mt-2 list-disc space-y-1 pl-5 text-muted-foreground">{card.instructions.map((instruction, i) => <li key={i}>{instruction}</li>)}</ul></div>
            <div><h3 className="font-bold uppercase">Observed response</h3><p className="mt-2 leading-6 text-muted-foreground">{card.response_summary}</p></div>
            <div><h3 className="font-bold uppercase">Frozen case evidence</h3><dl className="mt-2 grid gap-2 sm:grid-cols-2">{card.primary_metrics.map((metric) => <div key={metric.label} className="rounded-sm border border-border p-3"><dt className="text-xs text-muted-foreground">{metric.label}</dt><dd className="mt-1 font-semibold">{metric.value}</dd></div>)}</dl></div>
          </div>
        </div>
      </section>}
      {card && <section className="tactical-panel mt-6 rounded-md p-5 sm:p-7" aria-label={`${caseId} coaching report`}>
        <h2 className="mb-4 text-xl font-bold text-foreground">Coach report</h2>
        <CoachReportPresentation markdown={data.full_coach_report_markdown} scope="manually-verified" summarySentences={caseSummary} collapsedDetails detailLabel="Detailed Coaching Report — C03, C04 and C06" />
        <p className="mt-5 flex items-center gap-2 text-xs text-warning"><ShieldCheck className="h-4 w-4" /> Automated identity remains {data.scientific_automated_status}; showcased identities were manually verified.</p>
      </section>}
    </>}
  </div>;
}
