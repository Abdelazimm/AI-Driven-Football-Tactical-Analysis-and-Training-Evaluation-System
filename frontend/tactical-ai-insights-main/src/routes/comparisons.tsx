import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowRight } from "lucide-react";
import { PageIntro } from "@/components/tactical-ui";
import { methodologies } from "@/lib/tactical-data";
import { useAnalysisResult } from "@/hooks/use-analysis";
import { VALIDATED_DEMO_JOB_ID } from "@/lib/demo";

export const Route = createFileRoute("/comparisons")({
  head: () => ({ meta: [{ title: "Methodology Comparison — Tactical Intelligence" }] }), component: Comparisons,
});

function Comparisons() {
  const { data } = useAnalysisResult(VALIDATED_DEMO_JOB_ID);
  const result = data?.result;
  const evidenceItems: unknown = result?.structured_evidence?.evidence_items;
  const evidenceCount = Array.isArray(evidenceItems) ? evidenceItems.length : undefined;
  return <div className="mx-auto max-w-[1500px] px-4 py-10 lg:px-8">
    <PageIntro eyebrow="Scientific evidence" title="Methodology Comparison" description="Compare the configured processing approaches and inspect the one persisted full-session product run. Formal benchmark values are kept separate." />
    <div className="grid gap-4 lg:grid-cols-3">{methodologies.map((method) => <article key={method.id} className="tactical-panel rounded-md p-5"><span className="font-mono text-xs text-ai">METHOD {method.number}</span><h2 className="mt-2 text-xl font-bold">{method.title}</h2><p className="mt-2 font-mono text-xs text-primary">{method.stack.join(" → ")}</p><p className="mt-4 text-sm leading-6 text-muted-foreground">{method.description}</p></article>)}</div>
    <section className="tactical-panel mt-7 rounded-md p-5 sm:p-7"><h2 className="text-xl font-bold uppercase">Persisted full-session product evidence</h2>{result ? <><p className="mt-3 text-sm text-muted-foreground">The existing Phase 6 job ran {result.methodology_id}. This is a product result for one session, not a controlled cross-method benchmark.</p><dl className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{[["Job status",result.job_status],["Coach events",String(result.instruction_events.length)],["Structured evidence",evidenceCount == null ? "Unavailable" : `${evidenceCount} items`],["Formal identity",result.identity_evaluation.method_formal_identity_status || result.identity_evaluation.identity_status]].map(([label,value])=><div key={label} className="rounded-sm border border-border p-3"><dt className="text-xs text-muted-foreground">{label}</dt><dd className="mt-1 font-mono text-xs font-semibold">{value}</dd></div>)}</dl></> : <p className="mt-3 text-sm text-muted-foreground">The existing result is temporarily unavailable from the local API.</p>}<Link to="/analysis/$jobId/results" params={{jobId:VALIDATED_DEMO_JOB_ID}} className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-primary">Open complete result <ArrowRight className="h-4 w-4" /></Link></section>
    <p className="mt-5 rounded-md border border-warning/40 p-4 text-sm text-muted-foreground">Detector precision, HOTA, IDF1, fragmentation, runtime, and related formal measures require their frozen evaluation context. This page does not rank M1, M2, or M3 from the single Phase 6 product run.</p>
  </div>;
}
