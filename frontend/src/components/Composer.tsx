import { useEffect, useRef, useState } from "react";
import { ArrowUp, Square } from "lucide-react";

export function Composer({
  onSend,
  onStop,
  isSending,
  disabled,
}: {
  onSend: (value: string) => void;
  onStop: () => void;
  isSending: boolean;
  disabled?: boolean;
}) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }, [value]);

  const submit = () => {
    const trimmed = value.trim();
    if (!trimmed || isSending || disabled) return;
    onSend(trimmed);
    setValue("");
  };

  return (
    <div className="border-t border-[#1b2650] bg-[#0b1020]/85 px-4 py-3 backdrop-blur">
      <div className="mx-auto flex w-full max-w-3xl items-end gap-2 rounded-2xl border border-[#24305c] bg-[#0f1533] p-2 shadow-lg shadow-black/20 focus-within:border-indigo-500/60">
        <textarea
          ref={textareaRef}
          rows={1}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit();
            }
          }}
          disabled={disabled}
          placeholder="Ask about your documentation…  (Enter to send, Shift+Enter for newline)"
          className="max-h-[200px] flex-1 resize-none bg-transparent px-2 py-2 text-[0.95rem] text-slate-100 outline-none placeholder:text-slate-500 disabled:opacity-50"
        />

        {isSending ? (
          <button
            type="button"
            onClick={onStop}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-700 text-slate-100 transition hover:bg-slate-600"
            title="Stop generating"
          >
            <Square size={15} />
          </button>
        ) : (
          <button
            type="button"
            onClick={submit}
            disabled={disabled || value.trim().length === 0}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-500 text-white transition hover:from-indigo-400 hover:to-violet-400 disabled:cursor-not-allowed disabled:opacity-40"
            title="Send"
          >
            <ArrowUp size={17} />
          </button>
        )}
      </div>
      <p className="mx-auto mt-2 max-w-3xl text-center text-[0.68rem] text-slate-600">
        Hybrid retrieval · self-correcting generation · guarded by NeMo rails
      </p>
    </div>
  );
}
