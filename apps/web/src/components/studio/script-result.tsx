import { ArrowRight, Clapperboard, Lightbulb } from "lucide-react";

import type { Script } from "@/lib/api/types";
import { Badge } from "@/components/ui/badge";
import { ButtonLink } from "@/components/ui/button";
import { CardHeader, GlassCard, InsetTile } from "@/components/ui/card";

import { HookScoreCard } from "./hook-score-card";

export function ScriptResult({ script }: { script: Script }) {
  const sortedHooks = [...script.hooks].sort((a, b) => b.score - a.score);

  return (
    <>
      <GlassCard>
        <CardHeader
          title="5 hooks, scored"
          description="Predicted performance for your account. Bars show what pushed the score up or down."
          action={<Badge>{script.model_version}</Badge>}
        />
        <ol className="space-y-3">
          {sortedHooks.map((hook, index) => (
            <li key={hook.text}>
              <HookScoreCard hook={hook} rank={index + 1} />
            </li>
          ))}
        </ol>
      </GlassCard>

      <GlassCard>
        <CardHeader title="3 angles" />
        <div className="grid gap-3 md:grid-cols-3">
          {script.angles.map((angle) => (
            <InsetTile key={angle.title}>
              <Lightbulb aria-hidden className="mb-2 size-4 text-warning" />
              <p className="font-medium">{angle.title}</p>
              <p className="mt-1 text-sm text-muted">{angle.summary}</p>
            </InsetTile>
          ))}
        </div>
      </GlassCard>

      <GlassCard>
        <CardHeader
          title="Full script"
          description="Follows the template beats. Shot notes are suggestions."
          action={
            <ButtonLink href="/editor" size="sm">
              <Clapperboard aria-hidden />
              Film and edit
              <ArrowRight aria-hidden />
            </ButtonLink>
          }
        />
        <ol className="space-y-2">
          {script.body.map((beat) => (
            <li key={beat.beat} className="glass-inset grid gap-1 p-4 sm:grid-cols-[6rem_1fr] sm:gap-4">
              <span className="text-xs font-semibold tracking-wider text-accent uppercase">{beat.beat}</span>
              <div>
                <p dir="auto" className="font-medium">{beat.line}</p>
                <p className="mt-1 text-xs text-subtle">🎥 {beat.shot}</p>
              </div>
            </li>
          ))}
        </ol>
      </GlassCard>
    </>
  );
}
