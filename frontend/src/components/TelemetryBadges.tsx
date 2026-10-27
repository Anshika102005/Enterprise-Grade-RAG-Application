import type { ReactNode } from "react";
import { Clock, Gauge, RefreshCw, ServerCrash, ShieldAlert, ShieldCheck } from "lucide-react";
import type { MessageMeta } from "../types";

function Chip({
  children,
  tone,
  title,
}: {
  children: ReactNode;
  tone: "good" | "warn" | "neutral";
  title?: string;
}) {
  const tones: Record<string, string> = {
    good: "border-emerald-500/30 bg-emerald-500/10 text-emerald-300",
    warn: "border-amber-500/30 bg-amber-500/10 text-amber-300",
    neutral: "border-[#2b3868] bg-[#141c3b] text-slate-300",
  };
  return (
    <span
      title={title}
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[0.72rem] font-medium ${tones[tone]}`}
    >
      {children}
    </span>
  );
}

export function TelemetryBadges({ meta }: { meta: MessageMeta }) {
  // A vector-store outage is not a relevance verdict — showing "Low-relevance
  // context / 0% confidence" here would blame the query for an infra failure.
  const unavailable = Boolean(meta.retrievalError);
  const hasGrade = Boolean(meta.grade) && !unavailable;
  const hasConfidence = typeof meta.confidence === "number" && !unavailable;
  const hasRetries = typeof meta.retries === "number" && meta.retries > 0;
  const hasLatency = typeof meta.latencyMs === "number";

  if (!unavailable && !hasGrade && !hasConfidence && !hasRetries && !hasLatency) {
    return null;
  }

  const relevant = meta.grade === "relevant";

  return (
    <div className="flex flex-wrap items-center gap-2">
      {unavailable && (
        <Chip
          tone="warn"
          title={meta.retrievalError || "The knowledge base could not be reached"}
        >
          <ServerCrash size={12} />
          Retrieval unavailable
        </Chip>
      )}
      {hasGrade && (
        <Chip
          tone={relevant ? "good" : "warn"}
          title="Self-RAG retrieval grader verdict"
        >
          {relevant ? <ShieldCheck size={12} /> : <ShieldAlert size={12} />}
          {relevant ? "Context verified" : "Low-relevance context"}
        </Chip>
      )}
      {hasConfidence && (
        <Chip
          tone="neutral"
          title={`Grader confidence: ${Math.round((meta.confidence ?? 0) * 100)}%`}
        >
          <Gauge size={12} />
          {Math.round((meta.confidence ?? 0) * 100)}% confidence
        </Chip>
      )}
      {hasRetries && (
        <Chip tone="warn" title="Query was rewritten and retrieval retried">
          <RefreshCw size={12} />
          {meta.retries} {meta.retries === 1 ? "rewrite" : "rewrites"}
        </Chip>
      )}
      {hasLatency && (
        <Chip tone="neutral" title="End-to-end backend latency">
          <Clock size={12} />
          {(meta.latencyMs! / 1000).toFixed(2)}s
        </Chip>
      )}
    </div>
  );
}
