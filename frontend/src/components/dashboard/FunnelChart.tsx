"use client";

import { CANDIDATE_STATUSES } from "@/lib/constants";

/** A horizontal funnel of candidate counts by pipeline status. */
export function FunnelChart({ funnel }: { funnel: Record<string, number> }) {
  const max = Math.max(1, ...Object.values(funnel));
  return (
    <div className="space-y-2">
      {CANDIDATE_STATUSES.map((status) => {
        const count = funnel[status] ?? 0;
        return (
          <div key={status} className="flex items-center gap-3">
            <span className="w-24 shrink-0 text-sm capitalize text-muted-foreground">{status}</span>
            <div className="h-6 flex-1 overflow-hidden rounded bg-muted">
              <div className="flex h-full items-center rounded bg-primary/80 px-2" style={{ width: `${(count / max) * 100}%` }}>
                {count > 0 && <span className="font-mono text-xs text-primary-foreground">{count}</span>}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
