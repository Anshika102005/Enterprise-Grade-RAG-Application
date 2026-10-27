import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";

const components: Components = {
  a: ({ children, ...props }) => (
    <a target="_blank" rel="noreferrer noopener" {...props}>
      {children}
    </a>
  ),
  code: ({ className, children, ...props }) => {
    const isBlock = /language-/.test(className ?? "");
    if (isBlock) {
      return (
        <code className={className} {...props}>
          {children}
        </code>
      );
    }
    return (
      <code
        className="rounded bg-[#182243] px-1.5 py-0.5 font-mono text-[0.85em] text-indigo-200"
        {...props}
      >
        {children}
      </code>
    );
  },
  pre: ({ children }) => (
    <pre className="my-3 overflow-x-auto rounded-xl border border-[#24305c] bg-[#0d1330] p-3.5 font-mono text-[0.82rem] leading-relaxed">
      {children}
    </pre>
  ),
};

export function Markdown({ content }: { content: string }) {
  return (
    <div className="prose-rag">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {content}
      </ReactMarkdown>
    </div>
  );
}
