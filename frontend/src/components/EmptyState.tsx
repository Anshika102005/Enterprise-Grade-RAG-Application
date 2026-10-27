import { Sparkles } from "lucide-react";

const EXAMPLES: { title: string; prompt: string }[] = [
  {
    title: "Kubernetes",
    prompt: "How does a Kubernetes rolling update work for a Deployment?",
  },
  {
    title: "Intel hardware",
    prompt: "What is Intel SR-IOV and how does it improve network performance?",
  },
  {
    title: "Networking",
    prompt: "How does BGP choose the best path to a destination prefix?",
  },
  {
    title: "Troubleshooting",
    prompt: "What is the difference between a liveness and a readiness probe?",
  },
];

export function EmptyState({ onPick }: { onPick: (prompt: string) => void }) {
  return (
    <div className="mx-auto flex h-full w-full max-w-3xl flex-col items-center justify-center px-6 text-center">
      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500/25 to-cyan-500/20 ring-1 ring-indigo-400/30">
        <Sparkles className="text-indigo-200" size={26} />
      </div>
      <h1 className="bg-gradient-to-r from-white to-slate-400 bg-clip-text text-2xl font-semibold text-transparent">
        Enterprise Agentic Assistant
      </h1>
      <p className="mt-2 max-w-lg text-sm text-slate-400">
        Ask a technical question. The agent plans, retrieves with hybrid search,
        grades its own context, and corrects itself before answering.
      </p>

      <div className="mt-7 grid w-full gap-2.5 sm:grid-cols-2">
        {EXAMPLES.map((example) => (
          <button
            key={example.prompt}
            type="button"
            onClick={() => onPick(example.prompt)}
            className="group rounded-xl border border-[#24305c] bg-[#0f1533] p-3.5 text-left transition hover:border-indigo-500/50 hover:bg-[#141c3b]"
          >
            <span className="text-[0.68rem] font-medium uppercase tracking-wide text-indigo-300">
              {example.title}
            </span>
            <span className="mt-1 block text-[0.85rem] leading-snug text-slate-300 group-hover:text-slate-100">
              {example.prompt}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
