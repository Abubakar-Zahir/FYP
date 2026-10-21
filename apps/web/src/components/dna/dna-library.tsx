"use client";

import { Bookmark, BookmarkCheck, ChevronRight, Dna, Timer, Zap } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { useDnaRecords, useSaveTemplate } from "@/lib/api/hooks";
import type { DnaRecord, HookType } from "@/lib/api/types";
import { HOOK_TYPE_LABEL, outlierTone } from "@/lib/utils/labels";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { GlassCard } from "@/components/ui/card";
import { ChoiceChip } from "@/components/ui/form";
import { EmptyState, QueryState, Skeleton } from "@/components/ui/states";

type Filter = HookType | "all";

const GRID = "grid gap-4 sm:grid-cols-2 xl:grid-cols-3";

function SaveTemplateButton({ record }: { record: DnaRecord }) {
  const save = useSaveTemplate();
  if (record.is_template) {
    return (
      <Badge tone="success">
        <BookmarkCheck aria-hidden />
        Template
      </Badge>
    );
  }
  return (
    <Button variant="secondary" size="sm" onClick={() => save.mutate(record.id)} disabled={save.isPending}>
      <Bookmark aria-hidden />
      {save.isPending ? "Saving…" : "Save as template"}
    </Button>
  );
}

function DnaCard({ record }: { record: DnaRecord }) {
  return (
    <GlassCard className="group relative flex flex-col gap-4 p-5 transition-all hover:-translate-y-0.5 hover:border-edge-strong">
      <div className="flex items-start justify-between gap-3">
        <Badge tone="accent">{HOOK_TYPE_LABEL[record.hook_type]}</Badge>
        <Badge tone={outlierTone(record.outlier_score)}>{record.outlier_score.toFixed(1)}× median</Badge>
      </div>
      <div>
        <h2 className="font-semibold">
          <Link href={`/dna/${record.id}`} className="after:absolute after:inset-0 after:rounded-glass">
            {record.title}
          </Link>
        </h2>
        <p dir="auto" className="mt-1.5 line-clamp-2 text-sm text-muted">“{record.hook_text}”</p>
      </div>
      <div className="flex gap-1" aria-hidden>
        {record.beats.map((beat) => (
          <span key={beat.label} className="h-1.5 flex-1 rounded-pill bg-accent/40 first:bg-accent" />
        ))}
      </div>
      <div className="mt-auto flex items-center justify-between gap-2 text-xs text-subtle">
        <span className="flex items-center gap-3">
          <span className="flex items-center gap-1"><Timer aria-hidden className="size-3.5" />{record.length_s}s</span>
          <span className="flex items-center gap-1"><Zap aria-hidden className="size-3.5" />{record.pacing_cuts_per_10s} cuts/10s</span>
        </span>
        <span className="flex items-center gap-1 capitalize">
          {record.source}
          <ChevronRight aria-hidden className="size-3.5 transition-transform group-hover:translate-x-0.5" />
        </span>
      </div>
      <div className="relative z-10">
        <SaveTemplateButton record={record} />
      </div>
    </GlassCard>
  );
}

function HookFilter({ value, onChange }: { value: Filter; onChange: (filter: Filter) => void }) {
  const options: Filter[] = ["all", ...(Object.keys(HOOK_TYPE_LABEL) as HookType[]).filter((type) => type !== "other")];
  return (
    <fieldset className="mb-5">
      <legend className="sr-only">Filter by hook type</legend>
      <div className="flex flex-wrap gap-2">
        {options.map((option) => (
          <ChoiceChip
            key={option}
            type="radio"
            name="hook-filter"
            checked={value === option}
            onChange={() => onChange(option)}
            label={option === "all" ? "All" : HOOK_TYPE_LABEL[option]}
            className="py-1.5 text-xs"
          />
        ))}
      </div>
    </fieldset>
  );
}

export function DnaLibrary() {
  const records = useDnaRecords();
  const [filter, setFilter] = useState<Filter>("all");

  return (
    <QueryState
      query={records}
      loading={
        <div className={GRID} role="status" aria-label="Loading DNA records">
          {[1, 2, 3].map((key) => <Skeleton key={key} className="h-64 rounded-glass" />)}
        </div>
      }
      isEmpty={(page) => page.items.length === 0}
      empty={
        <GlassCard>
          <EmptyState
            icon={Dna}
            title="No reels analysed yet"
            description="Upload a reference reel or import your own reels. We will extract the hook, pacing, beats and CTA."
          />
        </GlassCard>
      }
    >
      {(page) => {
        const visible = filter === "all" ? page.items : page.items.filter((record) => record.hook_type === filter);
        return (
          <>
            <HookFilter value={filter} onChange={setFilter} />
            {visible.length === 0 ? (
              <GlassCard>
                <EmptyState title="No reels with this hook type" description="Try another filter or analyse more reels." />
              </GlassCard>
            ) : (
              <div className={GRID}>
                {visible.map((record) => <DnaCard key={record.id} record={record} />)}
              </div>
            )}
          </>
        );
      }}
    </QueryState>
  );
}
