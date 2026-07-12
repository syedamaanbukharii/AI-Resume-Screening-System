"use client";

import { useEffect, useState } from "react";
import { Sparkles, Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useStreamGenerate } from "@/hooks/useStreamGenerate";
import { getQuestions } from "@/services/candidateService";
import type { InterviewQuestion } from "@/types/candidate";

const DIFFICULTY_VARIANT: Record<string, "secondary" | "warning" | "destructive"> = {
  easy: "secondary",
  medium: "warning",
  hard: "destructive",
};

/** Generates interview questions via SSE, showing live graph progress. */
export function InterviewPanel({ jobId, candidateId }: { jobId: string; candidateId: string }) {
  const path = `/api/v1/jobs/${jobId}/candidates/${candidateId}/questions`;
  const stream = useStreamGenerate(path);
  const [saved, setSaved] = useState<InterviewQuestion[]>([]);

  useEffect(() => {
    getQuestions(jobId, candidateId).then(setSaved).catch(() => setSaved([]));
  }, [jobId, candidateId]);

  useEffect(() => {
    if (stream.status === "done") {
      getQuestions(jobId, candidateId).then(setSaved).catch(() => {});
    }
  }, [stream.status, jobId, candidateId]);

  const progressFrames = stream.events.filter((e) => e.event === "progress");

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle>Interview questions</CardTitle>
        <Button size="sm" onClick={stream.start} disabled={stream.status === "streaming"}>
          {stream.status === "streaming" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
          {stream.status === "streaming" ? "Generating…" : saved.length ? "Regenerate" : "Generate"}
        </Button>
      </CardHeader>
      <CardContent className="space-y-4">
        {stream.status === "streaming" && (
          <div className="rounded-md border bg-accent/40 p-3">
            <div className="flex items-center gap-2 text-sm font-medium">
              <span className="h-2 w-2 animate-pulse-dot rounded-full bg-primary" />
              Interview agent running
            </div>
            <div className="mt-2 space-y-1">
              {progressFrames.map((f, i) => {
                const d = f.data as { node?: string; questions_generated?: number };
                return (
                  <p key={i} className="font-mono text-xs text-muted-foreground">
                    → {d.node} {d.questions_generated ? `(+${d.questions_generated})` : ""}
                  </p>
                );
              })}
            </div>
          </div>
        )}
        {stream.error && <p className="text-sm text-destructive">{stream.error}</p>}

        {saved.length === 0 && stream.status === "idle" && (
          <p className="text-sm text-muted-foreground">No questions yet. Generate to probe skills and gaps.</p>
        )}

        <div className="space-y-3">
          {saved.map((q) => (
            <div key={q.id} className="rounded-md border p-3">
              <div className="mb-1 flex items-center gap-2">
                <Badge variant="outline">{q.category}</Badge>
                <Badge variant={DIFFICULTY_VARIANT[q.difficulty] ?? "secondary"}>{q.difficulty}</Badge>
              </div>
              <p className="text-sm">{q.question}</p>
              {q.evaluation_criteria && (
                <p className="mt-1 text-xs text-muted-foreground">Evaluates: {q.evaluation_criteria}</p>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
