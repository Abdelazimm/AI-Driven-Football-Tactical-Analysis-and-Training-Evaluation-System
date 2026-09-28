import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowRight, BrainCircuit, Layers3, ShieldCheck, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PlaceholderNote, TacticalPitch } from "@/components/tactical-ui";
import { VALIDATED_DEMO_JOB_ID } from "@/lib/demo";
import { useAnalysisResult } from "@/hooks/use-analysis";

export const Route = createFileRoute("/")({
  head: () => ({ meta: [
    { title: "AI-Driven Football Tactical Analysis and Training Evaluation System" }, { name: "description", content: "AI-driven football tactical analysis and training evaluation dashboard." },
    { property: "og:title", content: "AI-Driven Football Tactical Analysis and Training Evaluation System" }, { property: "og:description", content: "Football performance analysis and training evaluation." }, { property: "og:type", content: "website" }, { name: "twitter:card", content: "summary_large_image" },
  ]}), component: Dashboard,
});

function Dashboard() {
  const { data } = useAnalysisResult(VALIDATED_DEMO_JOB_ID);
  const result = data?.result;
  const stats = [
    { title: "Full-session job", value: result ? "Completed" : "—", note: result?.job_status ?? "Read-only result unavailable", icon: Layers3 },
    { title: "Tactical events", value: result ? String(result.instruction_events.length) : "—", note: "From persisted Phase 6 result", icon: BrainCircuit },
    { title: "Player-level analysis", value: result?.identity_evaluation.player_level_analysis_allowed ? "Allowed" : "Withheld", note: "Formal identity safety gate", icon: ShieldCheck },
    { title: "Validated showcase", value: "03", note: "Oracle-assisted cases", icon: Sparkles },
  ];
  return <div>
    <section className="relative overflow-hidden border-b border-border px-4 py-10 sm:py-16 lg:px-8">
      <div className="mx-auto grid max-w-[1500px] items-center gap-12 lg:grid-cols-[.85fr_1.15fr]">
        <div className="relative z-10 min-w-0">
          <div className="mb-6"><p className="font-mono text-xs text-ai">AI × FOOTBALL PERFORMANCE</p><p className="mt-1 text-xs text-muted-foreground">Research-grade analysis environment</p></div>
          <h1 className="max-w-3xl text-3xl font-extrabold leading-tight sm:text-4xl lg:text-5xl xl:text-6xl">AI-Driven Football Tactical Analysis and Training Evaluation System</h1>
          <p className="mt-6 max-w-xl text-base leading-7 text-muted-foreground">Advanced AI analysis for modern football training.</p>
          <div className="mt-8 flex flex-wrap gap-3"><Button asChild variant="command" size="xl" className="w-full max-w-full whitespace-normal text-center sm:w-auto"><Link to="/analysis/$jobId/results" params={{jobId: VALIDATED_DEMO_JOB_ID}}>View Validated Full-Session Result <ArrowRight/></Link></Button><Button asChild variant="tactical" size="xl"><Link to="/showcase">View Validated Showcase</Link></Button><Button asChild variant="outline" size="xl"><Link to="/analysis/new">New Analysis</Link></Button></div>
          <p className="mt-3 text-xs text-muted-foreground">Opens an existing completed result. No upload or inference starts.</p>
        </div>
        <div className="relative"><div className="absolute -inset-6 bg-primary/5 blur-3xl"/><TacticalPitch/></div>
      </div>
    </section>
    <section className="px-4 py-10 lg:px-8"><div className="mx-auto max-w-[1500px]"><div className="mb-5 flex items-end justify-between"><div><p className="font-mono text-[10px] uppercase text-ai">Presentation snapshot</p><h2 className="mt-1 text-xl font-bold uppercase">Validated evidence</h2></div><span className="font-mono text-[10px] text-muted-foreground">EXISTING RESULT · NO NEW INFERENCE</span></div><div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{stats.map(({title,value,note,icon:Icon},i)=><article key={title} className="tactical-panel rounded-md p-5"><div className="flex items-center justify-between"><Icon className="h-5 w-5 text-ai"/><span className="font-mono text-[9px] text-muted-foreground">0{i+1}</span></div><p className="mt-8 text-xs font-semibold uppercase text-muted-foreground">{title}</p><p className="mt-2 text-2xl font-bold">{value}</p><p className="mt-2 text-xs text-muted-foreground">{note}</p></article>)}</div><div className="mt-4"><PlaceholderNote>The full-session job and showcase are read-only. Player-level findings remain withheld by the formal identity gate.</PlaceholderNote></div></div></section>
  </div>;
}
