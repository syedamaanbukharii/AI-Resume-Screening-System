"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { getCandidate } from "@/services/candidateService";
import type { CandidateProfile } from "@/types/candidate";

export default function CandidatePage() {
  const { id } = useParams<{ id: string }>();
  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getCandidate(id).then(setProfile).finally(() => setLoading(false));
  }, [id]);

  if (loading) return <Skeleton className="h-64" />;
  if (!profile) return <p className="text-sm text-muted-foreground">Candidate not found.</p>;

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-xl font-semibold">{profile.full_name}</h1>
        <p className="text-sm text-muted-foreground">{profile.email}</p>
      </div>
      <Card>
        <CardHeader><CardTitle>Contact</CardTitle></CardHeader>
        <CardContent className="space-y-2 text-sm">
          <Row label="Phone" value={profile.phone} />
          <Row label="LinkedIn" value={profile.linkedin_url} link />
          <Row label="GitHub" value={profile.github_url} link />
          <Row label="Portfolio" value={profile.portfolio_url} link />
        </CardContent>
      </Card>
    </div>
  );
}

function Row({ label, value, link }: { label: string; value: string | null; link?: boolean }) {
  return (
    <div className="flex justify-between">
      <span className="text-muted-foreground">{label}</span>
      {value ? (link ? <a href={value} className="text-primary hover:underline" target="_blank" rel="noreferrer">{value}</a> : <span>{value}</span>) : <span className="text-muted-foreground">—</span>}
    </div>
  );
}
