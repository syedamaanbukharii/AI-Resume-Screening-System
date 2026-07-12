import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Merge Tailwind class names, resolving conflicts. */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/** Format a 0-1 score as a percentage string. */
export function formatScore(score: number | null | undefined): string {
  if (score === null || score === undefined) return "—";
  return `${Math.round(score * 100)}%`;
}

/** Map a 0-1 score to a semantic quality band. */
export function scoreBand(score: number | null | undefined): "high" | "mid" | "low" | "none" {
  if (score === null || score === undefined) return "none";
  if (score >= 0.7) return "high";
  if (score >= 0.45) return "mid";
  return "low";
}
