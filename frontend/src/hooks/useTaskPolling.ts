"use client";

import { useEffect, useRef, useState } from "react";
import { getTask } from "@/services/candidateService";
import type { TaskStatus } from "@/types/candidate";

/** Poll a background task until it reaches a terminal state. */
export function useTaskPolling(taskId: string | null, intervalMs = 2000) {
  const [status, setStatus] = useState<TaskStatus | null>(null);
  const timer = useRef<ReturnType<typeof setInterval>>();

  useEffect(() => {
    if (!taskId) return;
    const tick = async () => {
      try {
        const t = await getTask(taskId);
        setStatus(t);
        if (t.status === "completed" || t.status === "failed") {
          clearInterval(timer.current);
        }
      } catch {
        clearInterval(timer.current);
      }
    };
    void tick();
    timer.current = setInterval(tick, intervalMs);
    return () => clearInterval(timer.current);
  }, [taskId, intervalMs]);

  return status;
}
