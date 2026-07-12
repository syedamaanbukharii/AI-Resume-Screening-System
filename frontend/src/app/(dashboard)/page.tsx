"use client";

import { useEffect, useState } from "react";
import { Briefcase, Users, Activity, Target } from "lucide-react";
import { StatCard } from "@/components/dashboard/StatCard";
import { FunnelChart } from "@/components/dashboard/FunnelChart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { getDashboard } from "@/services/analyticsService";
import { formatScore } from "@/lib/utils";
import type { DashboardStats } from "@/types/analytics";

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDashboard().then(setStats).finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Dashboard</h1>
        <p className="text-sm text-muted-foreground">Screening activity across all jobs.</p>
      </div>

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-24" />)}
        </div>
      ) : stats ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Total jobs" value={stats.total_jobs} icon={<Briefcase className="h-5 w-5" />} />
            <StatCard label="Active jobs" value={stats.active_jobs} icon={<Activity className="h-5 w-5" />} />
            <StatCard label="Candidates" value={stats.total_candidates} icon={<Users className="h-5 w-5" />} />
            <StatCard label="Avg match" value={formatScore(stats.avg_score)} icon={<Target className="h-5 w-5" />} />
          </div>
          <Card>
            <CardHeader><CardTitle>Candidate funnel</CardTitle></CardHeader>
            <CardContent><FunnelChart funnel={stats.funnel} /></CardContent>
          </Card>
        </>
      ) : (
        <p className="text-sm text-muted-foreground">Could not load dashboard.</p>
      )}
    </div>
  );
}
