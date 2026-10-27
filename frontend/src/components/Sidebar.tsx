import {
  Activity,
  BookOpen,
  ExternalLink,
  Layers,
  Trash2,
  Wifi,
  WifiOff,
  X,
} from "lucide-react";
import type { ConnectionState } from "../types";
import { API_ROOT } from "../lib/api";
import { shortId } from "../lib/format";

const STATUS: Record<
  ConnectionState,
  { label: string; dot: string; text: string }
> = {
  checking: {
    label: "Connecting…",
    dot: "bg-amber-400 animate-pulse",
    text: "text-amber-300",
  },
  online: {
    label: "Backend online",
    dot: "bg-emerald-400",
    text: "text-emerald-300",
  },
  offline: {
    label: "Backend offline",
    dot: "bg-red-500",
    text: "text-red-300",
  },
};

export function Sidebar({
  connection,
  sessionId,
  messageCount,
  onReset,
  onClose,
}: {
  connection: ConnectionState;
  sessionId: string;
  messageCount: number;
  onReset: () => void;
  onClose?: () => void;
}) {
  const status = STATUS[connection];

  return (
    <aside className="flex h-full w-72 shrink-0 flex-col border-r border-[#1b2650] bg-[#0a0f24]/80 backdrop-blur">
      <div className="flex items-center justify-between px-4 py-4">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-cyan-500 text-white shadow-lg shadow-indigo-950/40">
            <Layers size={18} />
          </div>
          <div>
            <p className="text-sm font-semibold leading-tight text-slate-100">
              Agent OS
            </p>
            <p className="text-[0.68rem] text-slate-500">Agentic RAG console</p>
          </div>
        </div>
        {onClose && (
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-[#141c3b] lg:hidden"
            title="Close menu"
          >
            <X size={18} />
          </button>
        )}
      </div>

      <div className="space-y-2.5 px-4">
        <div className="flex items-center gap-2 rounded-xl border border-[#24305c] bg-[#0f1533] px-3 py-2.5 text-[0.78rem]">
          {connection === "offline" ? (
            <WifiOff size={14} className={status.text} />
          ) : (
            <Wifi size={14} className={status.text} />
          )}
          <span className="text-slate-300">API</span>
          <span className={`ml-auto flex items-center gap-1.5 ${status.text}`}>
            <span className={`h-1.5 w-1.5 rounded-full ${status.dot}`} />
            {status.label}
          </span>
        </div>

        <div className="flex items-center justify-between rounded-xl border border-[#24305c] bg-[#0f1533] px-3 py-2.5 text-[0.78rem]">
          <span className="flex items-center gap-2 text-slate-400">
            <Activity size={14} />
            Memory thread
          </span>
          <span className="font-mono text-[0.72rem] text-indigo-300">
            {shortId(sessionId)}
          </span>
        </div>

        <div className="flex items-center justify-between rounded-xl border border-[#24305c] bg-[#0f1533] px-3 py-2.5 text-[0.78rem]">
          <span className="text-slate-400">Messages</span>
          <span className="font-mono text-[0.72rem] text-slate-200">
            {messageCount}
          </span>
        </div>
      </div>

      <div className="mt-4 space-y-2 px-4">
        <a
          href={`${API_ROOT}/docs`}
          target="_blank"
          rel="noreferrer noopener"
          className="flex items-center gap-2.5 rounded-xl px-3 py-2 text-[0.82rem] text-slate-300 transition hover:bg-[#141c3b]"
        >
          <BookOpen size={15} className="text-cyan-300" />
          API reference
          <ExternalLink size={12} className="ml-auto text-slate-500" />
        </a>
        <a
          href={`${API_ROOT}/graph`}
          target="_blank"
          rel="noreferrer noopener"
          className="flex items-center gap-2.5 rounded-xl px-3 py-2 text-[0.82rem] text-slate-300 transition hover:bg-[#141c3b]"
        >
          <Layers size={15} className="text-indigo-300" />
          Agent graph
          <ExternalLink size={12} className="ml-auto text-slate-500" />
        </a>
      </div>

      <div className="mt-auto p-4">
        <button
          type="button"
          onClick={onReset}
          className="flex w-full items-center justify-center gap-2 rounded-xl border border-red-500/30 bg-red-500/10 px-3 py-2.5 text-[0.82rem] font-medium text-red-300 transition hover:bg-red-500/20"
        >
          <Trash2 size={15} />
          New chat & clear memory
        </button>
        <p className="mt-3 text-center text-[0.66rem] leading-relaxed text-slate-600">
          Clearing starts a fresh memory thread on the backend.
        </p>
      </div>
    </aside>
  );
}
