import { createFileRoute } from "@tanstack/react-router";
import { AlertTriangle, BrainCircuit, CheckCircle2, GitCompareArrows } from "lucide-react";
import { PageIntro, PlaceholderNote } from "@/components/tactical-ui";
import { methodologies } from "@/lib/tactical-data";
import { IDENTITY_STATUS, type IdentityStatus } from "@shared/constants/confidence";

export const Route = createFileRoute("/research")({
  head: () => ({
    meta: [
      { title: "Research & Methodology — Tactical Intelligence" },
      { name: "description", content: "Research methodology and scientific safety for AI football analysis." },
      { property: "og:title", content: "Research & Methodology" },
      { property: "og:description", content: "Methods, identity gates, and responsible interpretation for football analysis." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Research,
});

const states: IdentityStatus[] = [
  IDENTITY_STATUS.PASS_RELIABLE,
  IDENTITY_STATUS.FAIL_HIGH_FRAGMENTATION,
  IDENTITY_STATUS.FAIL_IDENTITY_CONFLICT,
  IDENTITY_STATUS.FAIL_UNSAFE_MERGE,
  IDENTITY_STATUS.FAIL_INVALID_OUTPUT,
  IDENTITY_STATUS.NOT_EVALUATED,
];

function Research() {
  return (
    <div className="mx-auto max-w-[1400px] px-4 py-10 lg:px-8">
      <PageIntro
        eyebrow="Academic foundation"
        title="Research / Methodology"
        description="A transparent account of the three processing strategies, validation boundaries, and identity-safety gate that protects player-level interpretation."
      />
      <div className="grid gap-4 lg:grid-cols-3">
        {methodologies.map((m) => (
          <article key={m.id} className="tactical-panel rounded-md p-5">
            <BrainCircuit className="h-5 w-5 text-ai" />
            <p className="mt-5 font-mono text-[10px] text-primary">METHOD {m.number}</p>
            <h2 className="mt-2 text-xl font-bold">{m.title}</h2>
            <p className="mt-3 font-mono text-xs">{m.stack.join(" + ")}</p>
            <p className="mt-4 text-sm leading-6 text-muted-foreground">{m.description}</p>
          </article>
        ))}
      </div>
      <section className="mt-8 grid gap-6 lg:grid-cols-[1fr_.8fr]">
        <div className="tactical-panel rounded-md p-6">
          <h2 className="flex items-center gap-2 text-xl font-bold uppercase">
            <GitCompareArrows className="text-ai" />
            Scientific safety gate
          </h2>
          <p className="mt-3 text-sm leading-7 text-muted-foreground">
            Player-level tactical conclusions appear only when persistent identity meets a defined reliability threshold. A failed gate is a valid completed outcome, not a processing crash.
          </p>
          <div className="mt-5 space-y-2">
            {states.map((s) => (
              <div key={s} className="flex items-center justify-between rounded-sm border border-border p-3">
                <span className="font-mono text-xs">{s}</span>
                {s === IDENTITY_STATUS.PASS_RELIABLE ? (
                  <CheckCircle2 className="h-4 w-4 text-primary" />
                ) : (
                  <AlertTriangle className="h-4 w-4 text-warning" />
                )}
              </div>
            ))}
          </div>
          <div className="mt-5">
            <PlaceholderNote>
              Withholding reasons remain visible while valid team-level, system-level, and engineering evidence stays available.
            </PlaceholderNote>
          </div>
        </div>
        <aside className="tactical-panel flex flex-col items-center justify-center rounded-md p-8 text-center">
          <p className="font-mono text-[10px] uppercase text-muted-foreground">Final Year Project</p>
          <p className="mt-6 text-2xl font-bold">University of London / Goldsmiths</p>
          <h2 className="mt-6 max-w-md text-lg font-bold">
            AI-Driven Football Tactical Analysis and Training Evaluation System
          </h2>
          <p className="mt-3 text-sm leading-6 text-muted-foreground">Institutional attribution</p>
        </aside>
      </section>
    </div>
  );
}
