"use client";

import { Lightbulb, MessagesSquare, PenLine } from "lucide-react";

import { useCommentThemes } from "@/lib/api/hooks";
import type { CommentTheme } from "@/lib/api/types";
import { COMMENT_LABEL } from "@/lib/utils/labels";
import { Badge } from "@/components/ui/badge";
import { ButtonLink } from "@/components/ui/button";
import { CardHeader, GlassCard } from "@/components/ui/card";
import { EmptyState, LoadingBlock, QueryState } from "@/components/ui/states";

function ThemeCard({ theme, rank }: { theme: CommentTheme; rank: number }) {
  const label = COMMENT_LABEL[theme.dominant_label];
  return (
    <article className="glass-inset p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="flex items-center gap-2 font-medium">
          <span className="text-xs text-subtle tabular-nums">#{rank}</span>
          {theme.theme}
        </h3>
        <div className="flex gap-1.5">
          <Badge tone={label.tone}>{label.label}</Badge>
          <Badge>{theme.size} comments</Badge>
        </div>
      </div>
      <ul className="mt-3 flex flex-wrap gap-2">
        {theme.examples.map((example) => (
          <li key={example} dir="auto" className="rounded-xl border border-edge bg-surface px-3 py-1.5 text-sm text-muted">
            {example}
          </li>
        ))}
      </ul>
      <div className="mt-3 flex flex-col gap-3 rounded-xl bg-accent-soft p-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="flex gap-2 text-sm">
          <Lightbulb aria-hidden className="mt-0.5 size-4 shrink-0 text-warning" />
          {theme.idea}
        </p>
        <ButtonLink href="/studio" size="sm" variant="secondary" className="shrink-0">
          <PenLine aria-hidden />
          Script it
        </ButtonLink>
      </div>
    </article>
  );
}

export function CommentThemes() {
  const themes = useCommentThemes();

  return (
    <GlassCard>
      <CardHeader title="Themes" description="Ranked by how many comments fall into each" />
      <QueryState
        query={themes}
        loading={<LoadingBlock label="Loading themes" />}
        isEmpty={(page) => page.items.length === 0}
        empty={
          <EmptyState
            icon={MessagesSquare}
            title="No themes yet"
            description="We need about 50 comments to find themes. Sync comments or post a few more reels."
          />
        }
      >
        {(page) => (
          <ol className="space-y-3">
            {page.items.map((theme, index) => (
              <li key={theme.id}>
                <ThemeCard theme={theme} rank={index + 1} />
              </li>
            ))}
          </ol>
        )}
      </QueryState>
    </GlassCard>
  );
}
