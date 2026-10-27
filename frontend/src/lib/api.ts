import type { QueryResponse } from "../types";

/**
 * Dev: Vite proxies `/api/*` -> http://localhost:8000/* (no CORS needed).
 * Prod: set VITE_API_BASE_URL to the deployed backend origin.
 */
const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/+$/, "");
const ROOT = API_BASE ? API_BASE : "/api";

/** Root used to build links to backend endpoints (e.g. /docs, /graph). */
export const API_ROOT = ROOT;

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function queryBackend(
  question: string,
  threadId: string,
  signal?: AbortSignal,
): Promise<QueryResponse> {
  const response = await fetch(`${ROOT}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ q: question, thread_id: threadId }),
    signal,
  });

  if (!response.ok) {
    let detail = "";
    try {
      detail = await response.text();
    } catch {
      /* ignore */
    }
    throw new ApiError(
      `Backend responded ${response.status}${detail ? `: ${detail.slice(0, 300)}` : ""}`,
      response.status,
    );
  }

  return (await response.json()) as QueryResponse;
}

export async function checkHealth(signal?: AbortSignal): Promise<boolean> {
  try {
    const response = await fetch(`${ROOT}/`, { signal });
    return response.ok;
  } catch {
    return false;
  }
}
