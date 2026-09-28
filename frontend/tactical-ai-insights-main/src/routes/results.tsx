import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowRight } from "lucide-react";
import { PageIntro } from "@/components/tactical-ui";
import { VALIDATED_DEMO_JOB_ID } from "@/lib/demo";

export const Route = createFileRoute("/results")({
  head: () => ({ meta: [{ title: "Results — Tactical Intelligence" }] }), component: Results,
});

function Results() {
  return <div className="mx-auto max-w-[1000px] px-4 py-10 lg:px-8">
    <PageIntro eyebrow="Results" title="Open a Persisted Result" description="The prior design preview has been retired for the local presentation. Use the validated full-session product result below." />
    <Link to="/analysis/$jobId/results" params={{ jobId: VALIDATED_DEMO_JOB_ID }} className="tactical-panel mt-6 inline-flex items-center gap-3 rounded-md p-5 text-sm font-semibold text-primary hover:border-primary">
      View validated full-session result <ArrowRight className="h-4 w-4" />
    </Link>
  </div>;
}
