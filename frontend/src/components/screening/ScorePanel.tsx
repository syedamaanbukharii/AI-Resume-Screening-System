import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScoreBar } from "@/components/shared/ScoreBar";
import { SCORE_FACTORS } from "@/lib/constants";
import { formatScore } from "@/lib/utils";
import type { RankedCandidate } from "@/types/candidate";

/** The deterministic score breakdown, five factors plus composite. */
export function ScorePanel({ candidate }: { candidate: RankedCandidate }) {
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle>Match breakdown</CardTitle>
        <span className="font-mono text-2xl font-semibold tabular-nums">{formatScore(candidate.overall_score)}</span>
      </CardHeader>
      <CardContent className="space-y-2.5">
        {SCORE_FACTORS.map(({ key, label }) => (
          <ScoreBar key={key} label={label} score={candidate[key as keyof RankedCandidate] as number | null} />
        ))}
      </CardContent>
    </Card>
  );
}
