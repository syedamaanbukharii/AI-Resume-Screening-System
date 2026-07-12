import { Badge } from "@/components/ui/badge";

const STATUS_VARIANT: Record<string, "default" | "secondary" | "success" | "warning" | "destructive" | "outline"> = {
  new: "secondary",
  screened: "outline",
  shortlisted: "default",
  interview: "warning",
  hired: "success",
  rejected: "destructive",
  active: "success",
  draft: "secondary",
  closed: "outline",
  archived: "secondary",
};

/** Render a candidate or job status as a semantically-colored badge. */
export function StatusBadge({ status }: { status: string }) {
  return <Badge variant={STATUS_VARIANT[status] ?? "secondary"}>{status}</Badge>;
}
