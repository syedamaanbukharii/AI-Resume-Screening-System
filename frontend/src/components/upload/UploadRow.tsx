"use client";

import { CheckCircle2, XCircle, Loader2 } from "lucide-react";
import { useTaskPolling } from "@/hooks/useTaskPolling";
import type { UploadResult } from "@/types/candidate";

/** One uploaded file with live parse status via task polling. */
export function UploadRow({ result }: { result: UploadResult }) {
  const status = useTaskPolling(result.task_id);
  const state = status?.status ?? "pending";

  const icon =
    state === "completed" ? <CheckCircle2 className="h-4 w-4 text-success" /> :
    state === "failed" ? <XCircle className="h-4 w-4 text-destructive" /> :
    <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />;

  return (
    <div className="flex items-center justify-between rounded-md border px-3 py-2 text-sm">
      <span className="truncate">{result.filename}</span>
      <span className="flex items-center gap-2 text-xs text-muted-foreground">
        {state === "completed" ? "Parsed" : state === "failed" ? (status?.error_message ?? "Failed") : "Parsing…"}
        {icon}
      </span>
    </div>
  );
}
