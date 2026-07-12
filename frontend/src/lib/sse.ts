/**
 * SSE client built on fetch + ReadableStream.
 *
 * The native EventSource API cannot set an Authorization header, and this
 * backend authenticates every request with a Bearer token — so a POST that
 * streams `text/event-stream` must be consumed manually. This parses the SSE
 * wire format (`event:` / `data:` frames separated by blank lines) from the
 * response body stream and dispatches typed events to callbacks.
 */

import { getAccessToken } from "./api";

export interface SSEHandlers {
  onEvent: (event: string, data: unknown) => void;
  onError?: (message: string) => void;
  onDone?: () => void;
}

/**
 * Open an authenticated POST SSE stream and dispatch frames.
 *
 * Returns an abort function to cancel the stream (e.g. on unmount).
 */
export function streamSSE(
  path: string,
  handlers: SSEHandlers,
  init?: RequestInit,
): () => void {
  const controller = new AbortController();
  const token = getAccessToken();

  const headers = new Headers(init?.headers);
  headers.set("Accept", "text/event-stream");
  if (token) headers.set("Authorization", `Bearer ${token}`);

  (async () => {
    try {
      const res = await fetch(path, {
        method: "POST",
        ...init,
        headers,
        signal: controller.signal,
      });

      if (!res.ok || !res.body) {
        handlers.onError?.(`Stream failed with status ${res.status}`);
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      // Read chunks and split on the SSE frame delimiter (blank line).
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        let sep: number;
        while ((sep = buffer.indexOf("\n\n")) !== -1) {
          const rawFrame = buffer.slice(0, sep);
          buffer = buffer.slice(sep + 2);
          dispatchFrame(rawFrame, handlers);
        }
      }
      // Flush any trailing frame.
      if (buffer.trim()) dispatchFrame(buffer, handlers);
      handlers.onDone?.();
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        handlers.onError?.((err as Error).message);
      }
    }
  })();

  return () => controller.abort();
}

/** Parse one SSE frame ("event: x\ndata: {...}") and dispatch it. */
function dispatchFrame(raw: string, handlers: SSEHandlers): void {
  let event = "message";
  const dataLines: string[] = [];
  for (const line of raw.split("\n")) {
    if (line.startsWith("event:")) event = line.slice(6).trim();
    else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
  }
  if (dataLines.length === 0) return;
  const dataStr = dataLines.join("\n");
  let parsed: unknown = dataStr;
  try {
    parsed = JSON.parse(dataStr);
  } catch {
    /* leave as string */
  }
  handlers.onEvent(event, parsed);
}
