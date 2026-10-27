import { useState } from "react";
import { Bot, Check, Copy, User } from "lucide-react";
import type { ChatMessage } from "../types";
import { Markdown } from "./Markdown";
import { useTypewriter } from "../hooks/useTypewriter";
import { TelemetryBadges } from "./TelemetryBadges";
import { ReasoningTimeline } from "./ReasoningTimeline";
import { SourcesPanel } from "./SourcesPanel";
import { formatTime } from "../lib/format";

export function MessageBubble({
  message,
  animate,
}: {
  message: ChatMessage;
  animate: boolean;
}) {
  const isUser = message.role === "user";
  const { displayed, done } = useTypewriter(message.content, animate && !isUser);
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard unavailable */
    }
  };

  return (
    <div className={`flex animate-fade-up gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      <div
        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full border ${
          isUser
            ? "border-indigo-400/40 bg-indigo-500/20 text-indigo-200"
            : "border-cyan-400/30 bg-cyan-500/15 text-cyan-200"
        }`}
        aria-hidden
      >
        {isUser ? <User size={15} /> : <Bot size={15} />}
      </div>

      <div className="min-w-0 max-w-[min(780px,88%)]">
        <div
          className={`rounded-2xl px-4 py-3 ${
            isUser
              ? "rounded-tr-sm bg-gradient-to-br from-indigo-600 to-indigo-500 text-white shadow-lg shadow-indigo-950/40"
              : message.meta?.error
                ? "rounded-tl-sm border border-red-500/40 bg-red-500/10"
                : "rounded-tl-sm border border-[#24305c] bg-[#0f1533]"
          }`}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap text-[0.95rem] leading-relaxed">
              {message.content}
            </p>
          ) : (
            <>
              <Markdown content={displayed} />
              {!done && (
                <span className="ml-0.5 inline-block animate-caret text-indigo-300">
                  ▌
                </span>
              )}
            </>
          )}
        </div>

        {!isUser && message.meta && (
          <div className="mt-2.5 space-y-2.5">
            <TelemetryBadges meta={message.meta} />
            <ReasoningTimeline steps={message.meta.thoughtProcess} />
            {!message.meta.error && (
              <SourcesPanel
                sources={message.meta.sources}
                retrievalError={message.meta.retrievalError}
              />
            )}
          </div>
        )}

        <div
          className={`mt-1.5 flex items-center gap-3 text-[0.7rem] text-slate-500 ${
            isUser ? "justify-end" : ""
          }`}
        >
          <span>{formatTime(message.createdAt)}</span>
          {!isUser && (
            <button
              type="button"
              onClick={copy}
              className="inline-flex items-center gap-1 transition hover:text-slate-300"
            >
              {copied ? <Check size={12} /> : <Copy size={12} />}
              {copied ? "Copied" : "Copy"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
