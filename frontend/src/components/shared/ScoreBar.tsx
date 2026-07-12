import { formatScore, scoreBand, cn } from "@/lib/utils";

const BAND_COLOR: Record<string, string> = {
  high: "bg-success",
  mid: "bg-warning",
  low: "bg-destructive",
  none: "bg-muted-foreground/30",
};

/** A compact horizontal score bar with a monospace percentage label. */
export function ScoreBar({ score, label }: { score: number | null | undefined; label?: string }) {
  const band = scoreBand(score);
  const pct = score != null ? Math.round(score * 100) : 0;
  return (
    <div className="flex items-center gap-2">
      {label && <span className="w-20 shrink-0 text-xs text-muted-foreground">{label}</span>}
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
        <div className={cn("h-full rounded-full transition-all", BAND_COLOR[band])} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-10 shrink-0 text-right font-mono text-xs tabular-nums">{formatScore(score)}</span>
    </div>
  );
}
