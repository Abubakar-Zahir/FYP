"use client";

import { ArrowRight, Unplug } from "lucide-react";
import { useSearchParams } from "next/navigation";
import { useEffect, useRef } from "react";

import { useFinishInstagramConnect, useJob } from "@/lib/api/hooks";
import { ButtonLink } from "@/components/ui/button";
import { CardHeader, GlassCard } from "@/components/ui/card";
import { JobProgress } from "@/components/ui/job-progress";
import { EmptyState, LoadingBlock } from "@/components/ui/states";

type ImportResult = { reels: number; comments: number };

function ImportProgress({ jobId, username }: { jobId: string; username: string }) {
  const job = useJob<ImportResult>(jobId);
  const result = job.data?.status === "done" ? job.data.result : null;
  return (
    <div className="space-y-4">
      <p className="text-sm text-muted">
        Connected <span className="font-medium text-ink">@{username}</span>. Your reels are being imported in the
        background, so you can carry on.
      </p>
      <JobProgress
        label={result ? `Imported ${result.reels} reels and ${result.comments} comments` : "Importing reels, insights and comments"}
        job={job.data}
        requestError={job.error}
        onRetry={() => void job.refetch()}
      />
      <ButtonLink href="/onboarding">
        Back to setup
        <ArrowRight aria-hidden />
      </ButtonLink>
    </div>
  );
}

/** Instagram redirects here with `code` and `state`. The API checks both and stores the token encrypted. */
export function InstagramCallback() {
  const params = useSearchParams();
  const code = params.get("code");
  const state = params.get("state");
  const deniedOnInstagram = !code || !state;
  const { mutate, ...finish } = useFinishInstagramConnect();
  const started = useRef(false);

  useEffect(() => {
    // A code works once, and Strict Mode runs effects twice.
    if (started.current || !code || !state) return;
    started.current = true;
    mutate({ code, state });
  }, [code, state, mutate]);

  return (
    <GlassCard className="mx-auto max-w-xl">
      <CardHeader title="Connecting Instagram" />
      {finish.isSuccess ? (
        <ImportProgress jobId={finish.data.job_id} username={finish.data.instagram.username} />
      ) : finish.isError || deniedOnInstagram ? (
        <EmptyState
          icon={Unplug}
          title="Instagram didn't connect"
          description={finish.isError ? finish.error.message : "Access was not given on Instagram. Try again when you're ready."}
          action={<ButtonLink href="/onboarding" variant="secondary">Back to setup</ButtonLink>}
        />
      ) : (
        <LoadingBlock label="Checking with Instagram" />
      )}
    </GlassCard>
  );
}
