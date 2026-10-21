import { LoaderCircle, Trophy } from "lucide-react";

import type { Variant, VariantStatus } from "@/lib/api/types";
import { cn } from "@/lib/utils";
import { Badge, type BadgeTone } from "@/components/ui/badge";

const STATUS: Record<VariantStatus, { label: string; tone: BadgeTone }> = {
  draft: { label: "Draft", tone: "neutral" },
  publishing: { label: "Publishing", tone: "accent" },
  live: { label: "Live", tone: "success" },
  failed: { label: "Failed", tone: "danger" },
};

export function VariantCard({ variant, isWinner }: { variant: Variant; isWinner: boolean }) {
  const status = STATUS[variant.status];

  return (
    <article
      className={cn(
        "glass-inset relative flex flex-col gap-3 p-4 transition-all",
        isWinner && "border-warning/60 bg-warning-soft shadow-[0_0_32px_rgb(251_191_36/0.15)]",
      )}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="grid size-8 place-items-center rounded-lg bg-surface-strong text-sm font-bold">{variant.label}</span>
        <div className="flex flex-wrap justify-end gap-1.5">
          {isWinner && (
            <Badge tone="warning">
              <Trophy aria-hidden />
              Winner
            </Badge>
          )}
          <Badge tone={status.tone}>
            {variant.status === "publishing" && <LoaderCircle aria-hidden className="animate-spin" />}
            {status.label}
          </Badge>
        </div>
      </div>
      <div>
        <p className="text-xs text-subtle">Hook line</p>
        <p dir="auto" className="font-medium">{variant.hook_line}</p>
      </div>
      <div>
        <p className="text-xs text-subtle">Opener</p>
        <p className="text-sm">{variant.opener}</p>
      </div>
      <div>
        <p className="text-xs text-subtle">Caption</p>
        <p dir="auto" className="text-sm text-muted">{variant.caption}</p>
      </div>
      <p className="mt-auto text-xs text-subtle">{variant.is_trial ? "Trial Reel · non-followers first" : "Normal reel"}</p>
    </article>
  );
}
