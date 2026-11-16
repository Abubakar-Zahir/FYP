import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

const compactFormatter = new Intl.NumberFormat("en", {
  notation: "compact",
  maximumFractionDigits: 1,
});

/** Shown when the API has no value yet. Null means unavailable, not zero. */
export const NO_VALUE = "—";

export function formatCompact(value: number | null): string {
  return value === null ? NO_VALUE : compactFormatter.format(value);
}

export function formatPercent(value: number): string {
  const sign = value > 0 ? "+" : "";
  return `${sign}${Math.round(value * 100)}%`;
}

export function formatSeconds(totalSeconds: number | null): string {
  if (totalSeconds === null) return NO_VALUE;
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = Math.round(totalSeconds % 60);
  return minutes > 0 ? `${minutes}m ${seconds}s` : `${seconds}s`;
}

const dateFormatter = new Intl.DateTimeFormat("en", { day: "numeric", month: "short" });

export function formatShortDate(isoDate: string | null): string {
  return isoDate === null ? NO_VALUE : dateFormatter.format(new Date(isoDate));
}

/** A reel's views over the account median, for example "2.4×". Null with too few reels to compare. */
export function formatOutlier(score: number | null): string {
  return score === null ? NO_VALUE : `${score.toFixed(1)}×`;
}
