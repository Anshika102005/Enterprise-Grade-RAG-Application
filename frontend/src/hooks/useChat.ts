import { useCallback, useEffect, useRef, useState } from "react";
import { checkHealth, queryBackend } from "../lib/api";
import type { ChatMessage, ConnectionState } from "../types";

const SESSION_KEY = "rag.sessionId";
const MESSAGES_KEY = "rag.messages.v1";

function newId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function loadSession(): string {
  try {
    const existing = localStorage.getItem(SESSION_KEY);
    if (existing) return existing;
  } catch {
    /* storage disabled */
  }
  const id = newId();
  try {
    localStorage.setItem(SESSION_KEY, id);
  } catch {
    /* ignore */
  }
  return id;
}

function loadMessages(): ChatMessage[] {
  try {
    const raw = localStorage.getItem(MESSAGES_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as ChatMessage[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export interface UseChat {
  messages: ChatMessage[];
  sessionId: string;
  isSending: boolean;
  connection: ConnectionState;
  error: string | null;
  animateId: string | null;
  send: (question: string) => Promise<void>;
  stop: () => void;
  reset: () => void;
  dismissError: () => void;
}

export function useChat(): UseChat {
  const [sessionId, setSessionId] = useState<string>(loadSession);
  const [messages, setMessages] = useState<ChatMessage[]>(loadMessages);
  const [isSending, setIsSending] = useState(false);
  const [connection, setConnection] = useState<ConnectionState>("checking");
  const [error, setError] = useState<string | null>(null);
  const [animateId, setAnimateId] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  // Persist conversation so a refresh keeps history + memory thread.
  useEffect(() => {
    try {
      localStorage.setItem(MESSAGES_KEY, JSON.stringify(messages.slice(-100)));
    } catch {
      /* ignore */
    }
  }, [messages]);

  useEffect(() => {
    try {
      localStorage.setItem(SESSION_KEY, sessionId);
    } catch {
      /* ignore */
    }
  }, [sessionId]);

  // Poll backend health so the sidebar can show a live status dot.
  useEffect(() => {
    let active = true;
    const controller = new AbortController();

    const poll = async () => {
      const ok = await checkHealth(controller.signal);
      if (active) setConnection(ok ? "online" : "offline");
    };

    setConnection("checking");
    void poll();
    const interval = window.setInterval(poll, 15000);
    return () => {
      active = false;
      controller.abort();
      window.clearInterval(interval);
    };
  }, []);

  const send = useCallback(
    async (question: string) => {
      const trimmed = question.trim();
      if (!trimmed || isSending) return;

      setError(null);
      setMessages((prev) => [
        ...prev,
        { id: newId(), role: "user", content: trimmed, createdAt: Date.now() },
      ]);
      setIsSending(true);

      const controller = new AbortController();
      abortRef.current = controller;
      const startedAt = performance.now();

      try {
        const data = await queryBackend(trimmed, sessionId, controller.signal);
        const latencyMs = Math.round(performance.now() - startedAt);
        const assistant: ChatMessage = {
          id: newId(),
          role: "assistant",
          content: data.answer || "No response.",
          createdAt: Date.now(),
          meta: {
            thoughtProcess: data.thought_process ?? [],
            sources: data.sources ?? [],
            status: data.status ?? "",
            grade: data.retrieval_grade,
            confidence: data.retrieval_confidence,
            retries: data.retrieval_retries,
            retrievalError: data.retrieval_error ?? null,
            latencyMs,
          },
        };
        setMessages((prev) => [...prev, assistant]);
        setAnimateId(assistant.id);
      } catch (err) {
        if (controller.signal.aborted) {
          // User pressed Stop — leave a subtle marker, no error banner.
          setMessages((prev) => [
            ...prev,
            {
              id: newId(),
              role: "assistant",
              content: "_Generation stopped._",
              createdAt: Date.now(),
              meta: {
                thoughtProcess: [],
                sources: [],
                status: "Cancelled",
              },
            },
          ]);
        } else {
          const message = err instanceof Error ? err.message : String(err);
          setError(message);
          setMessages((prev) => [
            ...prev,
            {
              id: newId(),
              role: "assistant",
              content: `**Request failed.** ${message}`,
              createdAt: Date.now(),
              meta: {
                thoughtProcess: [],
                sources: [],
                status: "error",
                error: true,
              },
            },
          ]);
        }
      } finally {
        setIsSending(false);
        abortRef.current = null;
      }
    },
    [isSending, sessionId],
  );

  const stop = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    setMessages([]);
    setAnimateId(null);
    setError(null);
    setSessionId(newId());
  }, []);

  const dismissError = useCallback(() => setError(null), []);

  return {
    messages,
    sessionId,
    isSending,
    connection,
    error,
    animateId,
    send,
    stop,
    reset,
    dismissError,
  };
}
