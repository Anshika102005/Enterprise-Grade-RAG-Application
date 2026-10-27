/** Response shape returned by POST /query on the FastAPI backend. */
export interface QueryResponse {
  question: string;
  answer: string;
  thought_process: string[];
  status: string;
  sources: string[];
  /** Self-RAG telemetry (optional — older backends omit these). */
  retrieval_grade?: "relevant" | "irrelevant" | "unavailable" | "";
  retrieval_confidence?: number;
  retrieval_retries?: number;
  /**
   * Non-null when the vector store itself was unreachable. Distinct from
   * "no relevant documents were found" — the query was never searched.
   */
  retrieval_error?: string | null;
}

export interface MessageMeta {
  thoughtProcess: string[];
  sources: string[];
  status: string;
  grade?: string;
  confidence?: number;
  retries?: number;
  retrievalError?: string | null;
  /** Wall-clock latency of the backend call, in milliseconds. */
  latencyMs?: number;
  error?: boolean;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  createdAt: number;
  meta?: MessageMeta;
}

export type ConnectionState = "checking" | "online" | "offline";
