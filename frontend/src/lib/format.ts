const CONTENT_PREFIX = "CONTENT: ";

/** Strip the retriever's "CONTENT: " prefix from a source chunk. */
export function cleanSource(raw: string): string {
  const trimmed = raw.trim();
  return trimmed.startsWith(CONTENT_PREFIX)
    ? trimmed.slice(CONTENT_PREFIX.length).trim()
    : trimmed;
}

export function sourcePreview(raw: string, max = 90): string {
  const text = cleanSource(raw).replace(/\s+/g, " ").trim();
  return text.length > max ? `${text.slice(0, max)}…` : text;
}

export function formatTime(ts: number): string {
  return new Date(ts).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function shortId(id: string): string {
  return id.slice(0, 8);
}
