import { useEffect, useRef } from "react";
import { Bot } from "lucide-react";
import type { ChatMessage } from "../types";
import { MessageBubble } from "./MessageBubble";
import { EmptyState } from "./EmptyState";

function ThinkingIndicator() {
  return (
    <div className="flex animate-fade-in gap-3">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-cyan-400/30 bg-cyan-500/15 text-cyan-200">
        <Bot size={15} />
      </div>
      <div className="flex items-center gap-2 rounded-2xl rounded-tl-sm border border-[#24305c] bg-[#0f1533] px-4 py-3">
        <span className="flex gap-1">
          <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-indigo-400 [animation-delay:-0.3s]" />
          <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-indigo-400 [animation-delay:-0.15s]" />
          <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-indigo-400" />
        </span>
        <span className="text-[0.8rem] text-slate-400">
          Planning · hybrid retrieval · grading context…
        </span>
      </div>
    </div>
  );
}

export function ChatView({
  messages,
  isSending,
  animateId,
  onPick,
}: {
  messages: ChatMessage[];
  isSending: boolean;
  animateId: string | null;
  onPick: (prompt: string) => void;
}) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, isSending]);

  return (
    <div className="flex-1 overflow-y-auto px-4 py-5">
      {messages.length === 0 && !isSending ? (
        <EmptyState onPick={onPick} />
      ) : (
        <div className="mx-auto flex w-full max-w-3xl flex-col gap-6">
          {messages.map((message) => (
            <MessageBubble
              key={message.id}
              message={message}
              animate={message.id === animateId}
            />
          ))}
          {isSending && <ThinkingIndicator />}
          <div ref={endRef} />
        </div>
      )}
    </div>
  );
}
