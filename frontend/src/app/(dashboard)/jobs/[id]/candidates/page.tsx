"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Users } from "lucide-react";
import { CandidateTable } from "@/components/candidates/CandidateTable";
import { EmptyState } from "@/components/shared/EmptyState";
import { Skeleton } from "@/components/ui/skeleton";
import { Select } from "@/components/ui/select";
import { listRankedCandidates } from "@/services/candidateService";
import { CANDIDATE_STATUSES } from "@/lib/constants";
import type { RankedCandidate } from "@/types/candidate";

export default function CandidatesPage() {
  const { id } = useParams<{ id: string }>();
  const [candidates, setCandidates] = useState<RankedCandidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("all");

  useEffect(() => {
    listRankedCandidates(id).then(setCandidates).finally(() => setLoading(false));
  }, [id]);

  const shown = filter === "all" ? candidates : candidates.filter((c) => c.status === filter);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Ranked candidates</h1>
          <p className="text-sm text-muted-foreground">Sorted by composite match score.</p>
        </div>
        <Select value={filter} onChange={(e) => setFilter(e.target.value)} className="w-40">
          <option value="all">All statuses</option>
          {CANDIDATE_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
        </Select>
      </div>

      {loading ? (
        <Skeleton className="h-64" />
      ) : shown.length === 0 ? (
        <EmptyState
          icon={<Users className="h-8 w-8" />}
          title="No ranked candidates"
          description="Upload resumes and run ranking on the job page to populate this list."
        />
      ) : (
        <CandidateTable jobId={id} candidates={shown} />
      )}
    </div>
  );
}
