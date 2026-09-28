import { AlertTriangle, Check, CircleDashed, Info, LockKeyhole } from "lucide-react";
import type { Metric } from "@/lib/tactical-data";

export function PageIntro({ eyebrow, title, description }: { eyebrow: string; title: string; description: string }) {
  return <header className="mb-8 max-w-3xl"><p className="mb-3 font-mono text-[11px] font-semibold uppercase text-primary">// {eyebrow}</p><h1 className="text-3xl font-extrabold uppercase leading-[1.05] sm:text-5xl">{title}</h1><p className="mt-4 max-w-2xl text-sm leading-7 text-muted-foreground sm:text-base">{description}</p></header>;
}

export function MetricCard({ metric }: { metric: Metric }) {
  const unavailable = !metric.value || metric.value.toLowerCase().includes("not available") || metric.value === "NOT EVALUATED";
  return <article className="tactical-panel rounded-md p-4 transition-all hover:-translate-y-0.5 hover:border-ai/50"><div className="flex items-center justify-between"><p className="text-xs font-semibold uppercase text-muted-foreground">{metric.label}</p><span className={`h-1.5 w-1.5 rounded-full ${unavailable ? "bg-warning" : "bg-primary"}`}/></div><p className={`mt-4 text-xl font-bold ${unavailable ? "text-foreground" : "text-primary"}`}>{metric.value ?? "Not available"}</p>{metric.reason && <p className="mt-2 text-xs leading-5 text-muted-foreground">{metric.reason}</p>}</article>;
}

export function LimitationPanel({
  reason,
  statusLabel = "COMPLETED WITH LIMITATIONS",
}: {
  reason?: string;
  statusLabel?: string;
} = {}) {
  const displayReason =
    reason ||
    "The selected automated tracking methodology did not establish sufficiently safe persistent physical-player identity under the formal dense-GT benchmark. Therefore, accumulated player-level analytics are withheld. Runtime diagnostics on the current upload are heuristic only.";

  return (
    <div className="rounded-md border border-warning/40 bg-warning/5 p-5">
      <div className="flex gap-4">
        <LockKeyhole className="mt-1 h-5 w-5 shrink-0 text-warning" />
        <div>
          <p className="font-bold uppercase text-warning">Player-level analysis withheld</p>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">{displayReason}</p>
          <p className="mt-2 font-mono text-[11px] text-warning">{statusLabel}</p>
        </div>
      </div>
    </div>
  );
}

export function TacticalPitch({ compact = false }: { compact?: boolean }) {
  const players = [[18,24],[31,44],[20,72],[46,25],[52,64],[67,45],[78,22],[82,70]];
  return <div className={`relative overflow-hidden rounded-md border border-primary/25 bg-card ${compact ? "aspect-[16/8]" : "aspect-[16/10]"}`}>
    <svg viewBox="0 0 100 62" className="h-full w-full" role="img" aria-label="Schematic football pitch illustration, not session data">
      <defs><pattern id="grid" width="5" height="5" patternUnits="userSpaceOnUse"><path d="M 5 0 L 0 0 0 5" fill="none" stroke="currentColor" strokeWidth=".12"/></pattern></defs>
      <rect width="100" height="62" fill="url(#grid)" className="text-ai opacity-30"/><rect x="3" y="3" width="94" height="56" fill="none" stroke="currentColor" strokeWidth=".4" className="text-primary opacity-60"/><line x1="50" y1="3" x2="50" y2="59" stroke="currentColor" strokeWidth=".35" className="text-primary opacity-50"/><circle cx="50" cy="31" r="9" fill="none" stroke="currentColor" strokeWidth=".35" className="text-primary opacity-50"/><path d="M18 24 Q27 17 31 44 T52 64 M46 25 Q59 17 67 45 T82 70" fill="none" stroke="currentColor" strokeWidth=".6" strokeDasharray="2 2" className="text-ai"/>
      {players.map(([x,y],i)=><g key={i}><circle cx={x} cy={y} r="1.8" fill="currentColor" className={i<4?"text-primary":"text-ai"}/><circle cx={x} cy={y} r="3.2" fill="none" stroke="currentColor" strokeWidth=".3" className={i<4?"text-primary":"text-ai"}/></g>)}
    </svg><div className="absolute left-3 top-3 rounded-sm border border-ai/30 bg-background/80 px-2 py-1 font-mono text-[9px] text-ai">SCHEMATIC · NOT SESSION DATA</div>
  </div>;
}

export function StatusBadge({ tone="success", children }: { tone?: "success"|"warning"|"muted"; children: React.ReactNode }) { const Icon=tone==="success"?Check:tone==="warning"?AlertTriangle:CircleDashed; return <span className={`inline-flex items-center gap-1.5 rounded-sm border px-2 py-1 font-mono text-[10px] font-semibold ${tone==="success"?"border-success/30 bg-success/10 text-success":tone==="warning"?"border-warning/30 bg-warning/10 text-warning":"border-border bg-muted text-muted-foreground"}`}><Icon className="h-3 w-3"/>{children}</span> }

export function PlaceholderNote({ children }: {children: React.ReactNode}) { return <div className="flex items-start gap-2 rounded-sm border border-ai/20 bg-ai/5 px-3 py-2 text-xs leading-5 text-muted-foreground"><Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-ai"/>{children}</div> }
