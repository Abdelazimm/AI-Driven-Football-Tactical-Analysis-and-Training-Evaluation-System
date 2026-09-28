import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";

/** Presentation of the persisted report; the source string is never rewritten. */
export function CoachReport({ markdown }: { markdown: string }) {
  return <div className="mx-auto max-w-4xl text-sm leading-7 text-foreground">
    <Markdown skipHtml remarkPlugins={[remarkGfm]} components={{
      h1: ({ children }) => <h1 className="mb-6 border-b border-border pb-4 text-2xl font-bold leading-tight sm:text-3xl">{children}</h1>,
      h2: ({ children }) => <h2 className="mb-3 mt-9 text-xl font-bold leading-snug text-primary first:mt-0">{children}</h2>,
      h3: ({ children }) => <h3 className="mb-2 mt-6 text-base font-bold leading-snug">{children}</h3>,
      p: ({ children }) => <p className="mb-4 break-words">{children}</p>,
      ul: ({ children }) => <ul className="mb-5 list-disc space-y-2 pl-6">{children}</ul>,
      ol: ({ children }) => <ol className="mb-5 list-decimal space-y-2 pl-6">{children}</ol>,
      li: ({ children }) => <li className="pl-1">{children}</li>,
      strong: ({ children }) => <strong className="font-bold">{children}</strong>,
      em: ({ children }) => <em className="italic">{children}</em>,
      blockquote: ({ children }) => <blockquote className="my-5 border-l-4 border-ai bg-accent/40 px-4 py-3 italic">{children}</blockquote>,
      hr: () => <hr className="my-8 border-border" />,
      table: ({ children }) => <div className="my-5 overflow-x-auto rounded-md border border-border"><table className="w-full min-w-[420px] border-collapse text-left">{children}</table></div>,
      th: ({ children }) => <th className="border-b border-border bg-accent/50 px-3 py-2 font-bold">{children}</th>,
      td: ({ children }) => <td className="border-b border-border px-3 py-2 align-top">{children}</td>,
      code: ({ children, className }) => <code className={`${className ?? ""} break-all rounded-sm bg-accent/60 px-1 py-0.5 font-mono text-xs`}>{children}</code>,
      pre: ({ children }) => <pre className="my-4 overflow-x-auto rounded-md border border-border bg-accent/40 p-4 leading-6">{children}</pre>,
      a: ({ children, href }) => <a href={href} className="font-medium text-primary underline underline-offset-2">{children}</a>,
    }}>{markdown}</Markdown>
  </div>;
}

type CoachReportPresentationProps = {
  markdown: string;
  scope: "automated" | "manually-verified";
  summarySentences: string[];
  collapsedDetails?: boolean;
  detailLabel?: string;
};

/** A UI-only brief followed by the unchanged persisted or frozen report. */
export function CoachReportPresentation({ markdown, scope, summarySentences, collapsedDetails = false, detailLabel = "Detailed Coaching Report" }: CoachReportPresentationProps) {
  const scopeText = scope === "automated" ? "Automated session analysis" : "Manually verified capability demonstration";
  const detailedReport = <div className="mt-5"><CoachReport markdown={markdown} /></div>;

  return <div className="space-y-6">
    <p className={`inline-flex rounded-sm border px-3 py-1.5 text-xs font-bold uppercase tracking-wide ${scope === "automated" ? "border-ai/50 bg-ai/5 text-ai" : "border-warning/50 bg-warning/5 text-warning"}`}>{scopeText}</p>
    <section aria-label="Coach-Friendly Summary" className="rounded-md border border-ai/35 bg-accent/30 p-5 sm:p-6">
      <h3 className="text-lg font-bold text-foreground">Coach-Friendly Summary</h3>
      <p className="mt-1 text-xs text-muted-foreground">A short non-technical explanation of the verified evidence below.</p>
      <div className="mt-4 space-y-2 text-sm leading-7 text-foreground">{summarySentences.map((sentence) => <p key={sentence}>{sentence}</p>)}</div>
    </section>
    {collapsedDetails
      ? <details className="rounded-md border border-border p-4 sm:p-5"><summary className="cursor-pointer font-bold text-foreground">{detailLabel}</summary>{detailedReport}</details>
      : <section aria-label={detailLabel}><h3 className="mb-5 text-sm font-bold uppercase tracking-wide text-foreground">{detailLabel}</h3><CoachReport markdown={markdown} /></section>}
  </div>;
}
