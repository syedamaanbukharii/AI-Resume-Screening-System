"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { ScorePanel } from "@/components/screening/ScorePanel";
import { InterviewPanel } from "@/components/screening/InterviewPanel";
import { ReportPanel } from "@/components/screening/ReportPanel";
import { getCandidateForJob, getCandidate, updateCandidateStatus, updateCandidateNotes } from "@/services/candidateService";
import { CANDIDATE_STATUSES } from "@/lib/constants";
import type { RankedCandidate, CandidateProfile } from "@/types/candidate";

export default function ScreeningPage() {
  const { jobId, candidateId } = useParams<{ jobId: string; candidateId: string }>();
  const [ranked, setRanked] = useState<RankedCandidate | null>(null);
  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [notes, setNotes] = useState("");

  useEffect(() => {
    Promise.all([getCandidateForJob(jobId, candidateId), getCandidate(candidateId)])
      .then(([r, p]) => { setRanked(r); setProfile(p); setNotes(r.recruiter_notes ?? ""); })
      .finally(() => setLoading(false));
  }, [jobId, candidateId]);

  const onStatus = async (status: string) => {
    const updated = await updateCandidateStatus(jobId, candidateId, status);
    setRanked(updated);
  };

  const saveNotes = async () => {
    const updated = await updateCandidateNotes(jobId, candidateId, notes);
    setRanked(updated);
  };

  if (loading) return <div className="space-y-4"><Skeleton className="h-24" /><Skeleton className="h-64" /></div>;
  if (!ranked || !profile) return <p className="text-sm text-muted-foreground">Candidate not found.</p>;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-semibold">{profile.full_name}</h1>
            <StatusBadge status={ranked.status} />
          </div>
          <p className="text-sm text-muted-foreground">{profile.email}</p>
          <div className="mt-1 flex gap-3 text-xs text-muted-foreground">
            {profile.linkedin_url && <a href={profile.linkedin_url} className="hover:text-primary" target="_blank" rel="noreferrer">LinkedIn</a>}
            {profile.github_url && <a href={profile.github_url} className="hover:text-primary" target="_blank" rel="noreferrer">GitHub</a>}
            {profile.portfolio_url && <a href={profile.portfolio_url} className="hover:text-primary" target="_blank" rel="noreferrer">Portfolio</a>}
          </div>
        </div>
        <Select value={ranked.status} onChange={(e) => void onStatus(e.target.value)} className="w-40">
          {CANDIDATE_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
        </Select>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <ScorePanel candidate={ranked} />
        <Card>
          <CardHeader><CardTitle>Recruiter notes</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <Textarea rows={5} value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Observations, next steps…" />
            <Button size="sm" onClick={() => void saveNotes()}>Save notes</Button>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <InterviewPanel jobId={jobId} candidateId={candidateId} />
        <ReportPanel jobId={jobId} candidateId={candidateId} />
      </div>
    </div>
  );
}
