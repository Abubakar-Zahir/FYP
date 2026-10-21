"use client";

import { ArrowLeft, Megaphone, PenLine, Quote, Timer, Type, Zap } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";

import { useDnaRecord } from "@/lib/api/hooks";
import type { DnaRecord } from "@/lib/api/types";
import { HOOK_TYPE_LABEL, outlierTone } from "@/lib/utils/labels";
import { Badge } from "@/components/ui/badge";
import { ButtonLink } from "@/components/ui/button";
import { CardHeader, GlassCard, InsetTile } from "@/components/ui/card";
import { PageHeader } from "@/components/ui/page-header";
import { LoadingBlock, QueryState } from "@/components/ui/states";

import { BeatTimeline } from "./beat-timeline";

function KeyFacts({ record }: { record: DnaRecord }) {
  const facts = [
    { icon: Quote, label: "Hook type", value: HOOK_TYPE_LABEL[record.hook_type] },
    { icon: Zap, label: "Pacing", value: `${record.pacing_cuts_per_10s} cuts / 10 s` },
    { icon: Timer, label: "Length", value: `${record.length_s} s` },
    { icon: Megaphone, label: "Outlier", value: `${record.outlier_score.toFixed(1)}× median` },
  ];
  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {facts.map(({ icon: Icon, label, value }) => (
        <InsetTile key={label}>
          <p className="flex items-center gap-1.5 text-xs text-subtle">
            <Icon aria-hidden className="size-3.5" />
            {label}
          </p>
          <p className="mt-1 font-semibold">{value}</p>
        </InsetTile>
      ))}
    </div>
  );
}

function DnaRecordView({ record }: { record: DnaRecord }) {
  return (
    <>
      <PageHeader
        eyebrow={`${record.source === "own" ? "Your reel" : "Reference reel"} · schema v${record.schema_version}`}
        title={record.title}
        actions={
          <ButtonLink href={`/studio?template=${record.id}`}>
            <PenLine aria-hidden />
            Write a script with this
          </ButtonLink>
        }
      />
      <div className="space-y-4">
        <GlassCard>
          <div className="mb-5 flex flex-wrap items-center gap-2">
            <Badge tone="accent">{HOOK_TYPE_LABEL[record.hook_type]}</Badge>
            <Badge tone={outlierTone(record.outlier_score)}>{record.outlier_score.toFixed(1)}× median</Badge>
          </div>
          <p dir="auto" className="text-xl font-medium sm:text-2xl">“{record.hook_text}”</p>
          <div className="mt-6">
            <KeyFacts record={record} />
          </div>
        </GlassCard>

        <GlassCard>
          <CardHeader title="Structure" description="Beats in order, sized by time on screen." />
          <BeatTimeline beats={record.beats} lengthSeconds={record.length_s} />
        </GlassCard>

        <div className="grid gap-4 lg:grid-cols-2">
          <GlassCard>
            <CardHeader title="On-screen text" />
            <ol className="space-y-2">
              {record.overlays.map((overlay) => (
                <li key={`${overlay.at_s}-${overlay.text}`} className="glass-inset flex items-center gap-3 px-4 py-2.5 text-sm">
                  <span className="w-10 shrink-0 font-mono text-xs text-subtle tabular-nums">{overlay.at_s}s</span>
                  <Type aria-hidden className="size-4 shrink-0 text-accent" />
                  <span dir="auto">{overlay.text}</span>
                </li>
              ))}
            </ol>
            <div className="mt-5">
              <p className="text-xs font-medium tracking-wider text-subtle uppercase">Call to action</p>
              <p dir="auto" className="mt-1 text-sm">{record.cta}</p>
            </div>
          </GlassCard>

          <GlassCard>
            <CardHeader title="Transcript" description="Whisper, word-level timestamps" />
            <p dir="auto" className="text-sm leading-relaxed text-muted">{record.transcript}</p>
          </GlassCard>
        </div>
      </div>
    </>
  );
}

export function DnaDetail() {
  const { id } = useParams<{ id: string }>();
  const record = useDnaRecord(id);

  return (
    <>
      <Link href="/dna" className="mb-4 inline-flex items-center gap-1.5 rounded-lg text-sm text-muted hover:text-ink">
        <ArrowLeft aria-hidden className="size-4" />
        DNA library
      </Link>
      <QueryState
        query={record}
        loading={<GlassCard><LoadingBlock label="Loading DNA record" /></GlassCard>}
      >
        {(data) => <DnaRecordView record={data} />}
      </QueryState>
    </>
  );
}
