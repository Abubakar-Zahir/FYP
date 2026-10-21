import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

const TONE_CLASSES = {
  neutral: "border-edge bg-surface-strong text-muted",
  accent: "border-accent/40 bg-accent-soft text-accent",
  success: "border-success/40 bg-success-soft text-success",
  warning: "border-warning/40 bg-warning-soft text-warning",
  danger: "border-danger/40 bg-danger-soft text-danger",
} as const;

export type BadgeTone = keyof typeof TONE_CLASSES;

export function Badge({ tone = "neutral", className, ...props }: ComponentProps<"span"> & { tone?: BadgeTone }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-pill border px-2.5 py-0.5 text-xs font-medium whitespace-nowrap [&_svg]:size-3",
        TONE_CLASSES[tone],
        className,
      )}
      {...props}
    />
  );
}
