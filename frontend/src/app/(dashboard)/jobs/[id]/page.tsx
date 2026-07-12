"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { Upload, ListChecks, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Select } from "@/components/ui/select";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { Skeleton } from "@/components/ui/skeleton";
import { getJob, changeJobStatus, rankJob } from "@/services/jobService";
import { JOB_STATUSES } from "@/lib/constants";
import type { Job } from "@/types/job";

export default function JobDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [ranking, setRanking] = useState(false);
  const [rankMsg, setRankMsg] = useState<string | null>(null);

  useEffect(() => {
    getJob(id).then(setJob).finally(() => setLoading(false));
  }, [id]);

  const onStatus = async (status: string) => {
    const updated = await changeJobStatus(id, status);
    setJob(updated);
  };

  const onRank = async () => {
    setRanking(true);
    setRankMsg(null);
    try {
      const res = await rankJob(id);
      setRankMsg(`Ranked ${res.ranked_count} candidate(s).`);
    } catch {
      setRankMsg("Ranking failed. Ensure resumes have finished parsing.");
    } finally {
      setRanking(false);
    }
  };

  if (loading) return <Skeleton className="h-64" />;
  if (!job) return <p className="text-sm text-muted-foreground">Job not found.</p>;

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-semibold">{job.title}</h1>
            <StatusBadge status={job.status} />
          </div>
          <p className="text-sm text-muted-foreground">{job.department || "No department"}</p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={job.status} onChange={(e) => void onStatus(e.target.value)} className="w-32">
            {JOB_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
          </Select>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        <Button asChild><Link href={`/jobs/${id}/upload`} className="flex items-center gap-2"><Upload className="h-4 w-4" /> Upload resumes</Link></Button>
        <Button variant="outline" asChild><Link href={`/jobs/${id}/candidates`} className="flex items-center gap-2"><ListChecks className="h-4 w-4" /> View candidates</Link></Button>
        <Button variant="secondary" onClick={() => void onRank()} disabled={ranking}>
          <Play className="h-4 w-4" /> {ranking ? "Ranking…" : "Run ranking"}
        </Button>
      </div>
      {rankMsg && <p className="text-sm text-muted-foreground">{rankMsg}</p>}

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Requirements</CardTitle></CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div>
              <p className="mb-1 text-xs uppercase tracking-wide text-muted-foreground">Required skills</p>
              <div className="flex flex-wrap gap-1.5">
                {job.required_skills.length ? job.required_skills.map((s) => <Badge key={s} variant="secondary">{s}</Badge>) : <span className="text-muted-foreground">None</span>}
              </div>
            </div>
            <div>
              <p className="mb-1 text-xs uppercase tracking-wide text-muted-foreground">Preferred skills</p>
              <div className="flex flex-wrap gap-1.5">
                {job.preferred_skills.length ? job.preferred_skills.map((s) => <Badge key={s} variant="outline">{s}</Badge>) : <span className="text-muted-foreground">None</span>}
              </div>
            </div>
            <div className="flex gap-6 pt-1">
              <div><p className="text-xs uppercase tracking-wide text-muted-foreground">Min experience</p><p className="font-mono">{job.min_experience_years ?? "—"} yrs</p></div>
              <div><p className="text-xs uppercase tracking-wide text-muted-foreground">Education</p><p>{job.education_level || "—"}</p></div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Description</CardTitle></CardHeader>
          <CardContent><p className="whitespace-pre-wrap text-sm text-muted-foreground">{job.description_raw}</p></CardContent>
        </Card>
      </div>
    </div>
  );
}
