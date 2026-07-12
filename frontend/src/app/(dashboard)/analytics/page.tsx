"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { FunnelChart } from "@/components/dashboard/FunnelChart";
import { listJobs } from "@/services/jobService";
import { getJobAnalytics } from "@/services/analyticsService";
import type { Job } from "@/types/job";
import type { JobAnalytics } from "@/types/analytics";

const BAND_COLOR: Record<string, string> = {
  high: "bg-success", mid: "bg-warning", low: "bg-destructive", unscored: "bg-muted-foreground/40",
};

export default function AnalyticsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [data, setData] = useState<JobAnalytics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listJobs().then((j) => {
      setJobs(j);
      if (j.length) setSelected(j[0].id);
    }).finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (selected) getJobAnalytics(selected).then(setData).catch(() => setData(null));
  }, [selected]);

  if (loading) return <Skeleton className="h-64" />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Analytics</h1>
          <p className="text-sm text-muted-foreground">Score distribution and pipeline by job.</p>
        </div>
        <Select value={selected} onChange={(e) => setSelected(e.target.value)} className="w-56">
          {jobs.map((j) => <option key={j.id} value={j.id}>{j.title}</option>)}
        </Select>
      </div>

      {data && (
        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader><CardTitle>Score distribution</CardTitle></CardHeader>
            <CardContent className="space-y-2">
              {data.score_distribution.map(({ band, count }) => {
                const max = Math.max(1, ...data.score_distribution.map((d) => d.count));
                return (
                  <div key={band} className="flex items-center gap-3">
                    <span className="w-20 shrink-0 text-sm capitalize text-muted-foreground">{band}</span>
                    <div className="h-6 flex-1 overflow-hidden rounded bg-muted">
                      <div className={`flex h-full items-center rounded px-2 ${BAND_COLOR[band]}`} style={{ width: `${(count / max) * 100}%` }}>
                        {count > 0 && <span className="font-mono text-xs text-white">{count}</span>}
                      </div>
                    </div>
                  </div>
                );
              })}
            </CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle>Status breakdown</CardTitle></CardHeader>
            <CardContent><FunnelChart funnel={data.status_breakdown} /></CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
