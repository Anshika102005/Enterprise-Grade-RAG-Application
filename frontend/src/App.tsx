import { useState } from "react";
import { AlertTriangle, Menu, X } from "lucide-react";
import { useChat } from "./hooks/useChat";
import { Sidebar } from "./components/Sidebar";
import { ChatView } from "./components/ChatView";
import { Composer } from "./components/Composer";

export default function App() {
  const chat = useChat();
  const [menuOpen, setMenuOpen] = useState(false);

  const sidebar = (onClose?: () => void) => (
    <Sidebar
      connection={chat.connection}
      sessionId={chat.sessionId}
      messageCount={chat.messages.length}
      onReset={() => {
        chat.reset();
        onClose?.();
      }}
      onClose={onClose}
    />
  );

  return (
    <div className="flex h-full overflow-hidden">
      <div className="hidden lg:flex">{sidebar()}</div>

      {menuOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div
            className="absolute inset-0 bg-black/60"
            onClick={() => setMenuOpen(false)}
          />
          <div className="absolute inset-y-0 left-0 animate-fade-in">
            {sidebar(() => setMenuOpen(false))}
          </div>
        </div>
      )}

      <main className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center gap-3 border-b border-[#1b2650] bg-[#0b1020]/70 px-4 py-3 backdrop-blur">
          <button
            type="button"
            onClick={() => setMenuOpen(true)}
            className="rounded-lg p-1.5 text-slate-300 hover:bg-[#141c3b] lg:hidden"
            title="Open menu"
          >
            <Menu size={20} />
          </button>

          <div className="min-w-0">
            <h1 className="truncate text-[0.95rem] font-semibold text-slate-100">
              Enterprise Agentic Assistant
            </h1>
            <p className="truncate text-[0.7rem] text-slate-500">
              LangGraph · hybrid dense + BM25 retrieval · self-correcting generation
            </p>
          </div>

          <span className="ml-auto hidden items-center gap-1.5 rounded-full border border-[#2b3868] bg-[#141c3b] px-2.5 py-1 text-[0.68rem] text-slate-400 sm:flex">
            <span className="h-1.5 w-1.5 rounded-full bg-indigo-400" />
            Self-RAG
          </span>
        </header>

        {chat.error && (
          <div className="flex items-start gap-2.5 border-b border-red-500/30 bg-red-500/10 px-4 py-2.5 text-[0.8rem] text-red-200">
            <AlertTriangle size={15} className="mt-0.5 shrink-0" />
            <div className="min-w-0 flex-1">
              <p className="font-medium">Request failed</p>
              <p className="mt-0.5 break-words text-red-300/90">{chat.error}</p>
            </div>
            <button
              type="button"
              onClick={chat.dismissError}
              className="rounded p-1 text-red-300 hover:bg-red-500/20"
              title="Dismiss"
            >
              <X size={14} />
            </button>
          </div>
        )}

        <ChatView
          messages={chat.messages}
          isSending={chat.isSending}
          animateId={chat.animateId}
          onPick={chat.send}
        />

        <Composer
          onSend={chat.send}
          onStop={chat.stop}
          isSending={chat.isSending}
        />
      </main>
    </div>
  );
}
