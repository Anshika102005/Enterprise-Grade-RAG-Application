import { useState } from "react";
import { ChevronDown, FileText } from "lucide-react";
import { cleanSource, sourcePreview } from "../lib/format";

function Chunk({ index, raw }: { index: number; raw: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="rounded-lg border border-[#24305c] bg-[#0d1330]">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-start gap-2.5 px-3 py-2 text-left transition hover:bg-[#141c3b]"
      >
        <span className="mt-0.5 rounded-md bg-indigo-500/15 px-1.5 py-0.5 font-mono text-[0.68rem] text-indigo-300">
          {index + 1}
        </span>
        <span className="flex-1 text-[0.8rem] leading-snug text-slate-300">
          {open ? "Collapse chunk" : sourcePreview(raw)}
        </span>
        <ChevronDown
          size={15}
          className={`mt-0.5 shrink-0 text-slate-400 transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>
      {open && (
        <div className="animate-fade-in border-t border-[#24305c] px-3 py-2.5">
          <p className="whitespace-pre-wrap font-mono text-[0.76rem] leading-relaxed text-slate-300">
            {cleanSource(raw)}
          </p>
        </div>
      )}
    </div>
  );
}

export function SourcesPanel({
  sources,
  retrievalError,
}: {
  sources: string[];
  retrievalError?: string | null;
}) {
  const [open, setOpen] = useState(false);
  if (sources.length === 0) {
    return (
      <p className="text-[0.76rem] text-slate-500">
        {retrievalError
          ? "Document retrieval failed — the knowledge base was unreachable."
          : "No context retrieved — answered conversationally."}
      </p>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-[#24305c] bg-[#0f1533]">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-2 px-3 py-2 text-left text-[0.78rem] font-medium text-slate-300 transition hover:bg-[#141c3b]"
      >
        <FileText size={14} className="text-cyan-300" />
        Retrieved context
        <span className="rounded-full bg-[#1a2445] px-2 py-0.5 text-[0.68rem] text-slate-400">
          {sources.length} chunks
        </span>
        <ChevronDown
          size={15}
          className={`ml-auto text-slate-400 transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>

      {open && (
        <div className="animate-fade-in space-y-2 border-t border-[#24305c] p-2.5">
          {sources.map((raw, index) => (
            <Chunk key={index} index={index} raw={raw} />
          ))}
        </div>
      )}
    </div>
  );
}
