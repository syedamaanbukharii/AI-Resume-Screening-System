import { Card, CardContent } from "@/components/ui/card";
import { type ReactNode } from "react";

/** A single dashboard metric with a monospace figure. */
export function StatCard({ label, value, icon }: { label: string; value: ReactNode; icon?: ReactNode }) {
  return (
    <Card>
      <CardContent className="flex items-center justify-between p-5">
        <div>
          <p className="text-xs uppercase tracking-wide text-muted-foreground">{label}</p>
          <p className="mt-1 font-mono text-2xl font-semibold tabular-nums">{value}</p>
        </div>
        {icon && <div className="text-muted-foreground">{icon}</div>}
      </CardContent>
    </Card>
  );
}
