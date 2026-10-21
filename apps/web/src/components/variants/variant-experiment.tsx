"use client";

import { useQueryClient } from "@tanstack/react-query";
import { Brain, FlaskConical, Info, Rocket, Send, Trophy } from "lucide-react";
import { useEffect } from "react";

import { queryKeys, useExperiment, useJob, useMe, usePublishExperiment, useShareWinner } from "@/lib/api/hooks";
import type { Experiment } from "@/lib/api/types";
import { Button } from "@/components/ui/button";
import { CardHeader, GlassCard } from "@/components/ui/card";
import { JobProgress } from "@/components/ui/job-progress";
import { EmptyState, LoadingBlock, QueryState } from "@/components/ui/states";

import { InsightsTable } from "./insights-table";
import { VariantCard } from "./variant-card";

const MOCK_EXPERIMENT_ID = "exp_01";

function EligibilityNotice() {
  const me = useMe();
  if (!me.data?.instagram || me.data.instagram.trial_reels_eligible) return null;
  return (
    <div className="glass-inset mb-4 flex gap-3 border-warning/40 p-4 text-sm">
      <Info aria-hidden className="mt-0.5 size-4 shrink-0 text-warning" />
      <p className="text-muted">
        Your account can&apos;t post Trial Reels yet. Variants will go out as normal reels, spaced across days, and still
        feed the learner (FR-6.8).
      </p>
    </div>
  );
}

function PublishProgress({ jobId, experimentId, onRetry }: { jobId: string; experimentId: string; onRetry: () => void }) {
  const queryClient = useQueryClient();
  const job = useJob(jobId);
  const done = job.data?.status === "done";

  useEffect(() => {
    if (done) void queryClient.invalidateQueries({ queryKey: queryKeys.experiment(experimentId) });
  }, [done, experimentId, queryClient]);

  if (done) return null;
  return <JobProgress label="Publishing variants as Trial Reels" job={job.data} requestError={job.error} onRetry={onRetry} />;
}

function LearnerNote({ experiment }: { experiment: Experiment }) {
  const winner = experiment.variants.find((variant) => variant.id === experiment.winner_variant_id);
  if (!winner) return null;
  return (
    <GlassCard>
      <CardHeader title="What the learner took from this" description="Thompson sampling over hook, opener and caption features" />
      <div className="flex gap-3 text-sm">
        <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-accent-soft text-accent">
          <Brain aria-hidden className="size-4" />
        </span>
        <p className="text-muted">
          Opener <span className="font-medium text-ink">“{winner.opener}”</span> won with a clear margin. Its share of your
          next variant sets goes up, and the shared prior for food creators gets a small nudge too.
        </p>
      </div>
    </GlassCard>
  );
}

function ExperimentView({ experiment }: { experiment: Experiment }) {
  const publish = usePublishExperiment(experiment.id);
  const shareWinner = useShareWinner(experiment.id);
  const allDraft = experiment.variants.every((variant) => variant.status === "draft");
  const hasInsights = experiment.variants.some((variant) => variant.insights.length > 0);
  const jobId = publish.data?.job_id ?? null;
  const startPublish = () => publish.mutate();

  return (
    <div className="space-y-4">
      <GlassCard>
        <CardHeader
          title={experiment.video_title}
          description={`${experiment.variants.length} variants · different hook line, opener and caption`}
          action={
            experiment.winner_variant_id ? (
              <Button onClick={() => shareWinner.mutate()} disabled={shareWinner.isPending || shareWinner.isSuccess}>
                <Send aria-hidden />
                {shareWinner.isSuccess ? "Shared to followers" : "Share winner to followers"}
              </Button>
            ) : (
              allDraft && (
                <Button onClick={startPublish} disabled={publish.isPending || jobId !== null}>
                  <Rocket aria-hidden />
                  Publish as Trial Reels
                </Button>
              )
            )
          }
        />
        <EligibilityNotice />
        {publish.isError && <p role="alert" className="mb-3 text-sm text-danger">{publish.error.message}</p>}
        {jobId && (
          <div className="mb-4">
            <PublishProgress key={jobId} jobId={jobId} experimentId={experiment.id} onRetry={startPublish} />
          </div>
        )}
        <div className="grid gap-3 md:grid-cols-3">
          {experiment.variants.map((variant) => (
            <VariantCard key={variant.id} variant={variant} isWinner={variant.id === experiment.winner_variant_id} />
          ))}
        </div>
      </GlassCard>

      <GlassCard>
        <CardHeader title="Insights" description="Pulled from Instagram at 24 h and 72 h after publishing" />
        {hasInsights ? (
          <InsightsTable experiment={experiment} />
        ) : (
          <EmptyState
            icon={Trophy}
            title="No insights yet"
            description="Publish the variants. The first numbers arrive 24 hours later, and the winner is picked at 72 hours."
          />
        )}
      </GlassCard>

      <LearnerNote experiment={experiment} />
    </div>
  );
}

export function VariantExperiment() {
  const experiment = useExperiment(MOCK_EXPERIMENT_ID);

  return (
    <QueryState
      query={experiment}
      loading={<GlassCard><LoadingBlock label="Loading experiment" /></GlassCard>}
      isEmpty={(data) => data.variants.length === 0}
      empty={
        <GlassCard>
          <EmptyState icon={FlaskConical} title="No variants yet" description="Render a video in the editor, then create 3 to 5 variants from it." />
        </GlassCard>
      }
    >
      {(data) => <ExperimentView experiment={data} />}
    </QueryState>
  );
}
