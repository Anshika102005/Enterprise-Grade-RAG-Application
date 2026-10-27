import { useState } from "react";
import { Brain, ChevronDown } from "lucide-react";

export function ReasoningTimeline({ steps }: { steps: string[] }) {
  const [open, setOpen] = useState(false);
  if (steps.length === 0) return null;

  return (
    <div className="overflow-hidden rounded-xl border border-[#24305c] bg-[#0f1533]">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-2 px-3 py-2 text-left text-[0.78rem] font-medium text-slate-300 transition hover:bg-[#141c3b]"
      >
        <Brain size={14} className="text-indigo-300" />
        Agent reasoning
        <span className="rounded-full bg-[#1a2445] px-2 py-0.5 text-[0.68rem] text-slate-400">
          {steps.length}
        </span>
        <ChevronDown
          size={15}
          className={`ml-auto text-slate-400 transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>

      {open && (
        <ol className="animate-fade-in space-y-0 border-t border-[#24305c] px-3 py-2.5">
          {steps.map((step, index) => (
            <li key={`${index}-${step}`} className="relative flex gap-3 pb-2.5 last:pb-0">
              {index < steps.length - 1 && (
                <span className="absolute left-[6px] top-4 h-full w-px bg-[#2b3868]" />
              )}
              <span className="relative mt-1.5 h-[7px] w-[7px] shrink-0 rounded-full bg-indigo-400 ring-4 ring-indigo-500/10" />
              <span className="font-mono text-[0.76rem] leading-relaxed text-slate-300">
                {step}
              </span>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
