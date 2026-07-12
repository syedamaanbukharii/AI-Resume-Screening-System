"use client";

import { useCallback, useRef, useState } from "react";
import { streamSSE } from "@/lib/sse";

export interface StreamState {
  status: "idle" | "streaming" | "done" | "error";
  events: { event: string; data: unknown }[];
  result: unknown | null;
  error: string | null;
}

const INITIAL: StreamState = {
  status: "idle",
  events: [],
  result: null,
  error: null,
};

/**
 * Drive an SSE generation endpoint (interview or report), exposing live
 * progress frames and the final `complete` payload.
 *
 * Because the backend authenticates with a Bearer token, this uses the
 * fetch-based streamSSE client rather than native EventSource.
 */
export function useStreamGenerate(path: string) {
  const [state, setState] = useState<StreamState>(INITIAL);
  const abortRef = useRef<(() => void) | null>(null);

  const start = useCallback(() => {
    setState({ ...INITIAL, status: "streaming" });
    abortRef.current = streamSSE(path, {
      onEvent: (event, data) => {
        setState((prev) => {
          const events = [...prev.events, { event, data }];
          if (event === "complete") {
            return { ...prev, events, result: data, status: "done" };
          }
          if (event === "error") {
            const msg = typeof data === "object" && data && "detail" in data
              ? String((data as { detail: unknown }).detail)
              : "Generation failed";
            return { ...prev, events, status: "error", error: msg };
          }
          return { ...prev, events };
        });
      },
      onError: (message) =>
        setState((prev) => ({ ...prev, status: "error", error: message })),
      onDone: () =>
        setState((prev) =>
          prev.status === "streaming" ? { ...prev, status: "done" } : prev,
        ),
    });
  }, [path]);

  const reset = useCallback(() => {
    abortRef.current?.();
    setState(INITIAL);
  }, []);

  return { ...state, start, reset };
}
