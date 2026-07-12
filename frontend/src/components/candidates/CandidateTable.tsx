"use client";

import Link from "next/link";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ScoreBar } from "@/components/shared/ScoreBar";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { formatScore } from "@/lib/utils";
import type { RankedCandidate } from "@/types/candidate";

/** Ranked candidate table, sorted by composite score (backend-ordered). */
export function CandidateTable({ jobId, candidates }: { jobId: string; candidates: RankedCandidate[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-10">#</TableHead>
          <TableHead>Match</TableHead>
          <TableHead>Skills</TableHead>
          <TableHead>Experience</TableHead>
          <TableHead>Semantic</TableHead>
          <TableHead>Status</TableHead>
          <TableHead className="text-right">Action</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {candidates.map((c, i) => (
          <TableRow key={c.candidate_id}>
            <TableCell className="font-mono text-xs text-muted-foreground">{i + 1}</TableCell>
            <TableCell className="w-48"><ScoreBar score={c.overall_score} /></TableCell>
            <TableCell className="font-mono text-xs tabular-nums">{formatScore(c.skill_score)}</TableCell>
            <TableCell className="font-mono text-xs tabular-nums">{formatScore(c.experience_score)}</TableCell>
            <TableCell className="font-mono text-xs tabular-nums">{formatScore(c.semantic_score)}</TableCell>
            <TableCell><StatusBadge status={c.status} /></TableCell>
            <TableCell className="text-right">
              <Link href={`/screening/${jobId}/${c.candidate_id}`} className="text-sm text-primary hover:underline">
                Screen
              </Link>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
