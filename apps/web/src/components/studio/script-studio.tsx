"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { PenLine, WandSparkles } from "lucide-react";
import { useSearchParams } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { useDnaRecords, useGenerateScript, useJob, useScript } from "@/lib/api/hooks";
import type { DnaRecord, GenerateScriptRequest } from "@/lib/api/types";
import { HOOK_TYPE_LABEL } from "@/lib/utils/labels";
import { Button } from "@/components/ui/button";
import { CardHeader, GlassCard } from "@/components/ui/card";
import { ChoiceChip, Field, Input, Select } from "@/components/ui/form";
import { JobProgress } from "@/components/ui/job-progress";
import { EmptyState, ErrorState, LoadingBlock, QueryState } from "@/components/ui/states";

import { ScriptResult } from "./script-result";

const LANGUAGES: { value: GenerateScriptRequest["language"]; label: string }[] = [
  { value: "english", label: "English" },
  { value: "roman_urdu", label: "Roman Urdu" },
  { value: "mixed", label: "Mix" },
];

const scriptRequestSchema = z.object({
  template_id: z.string().min(1, "Pick a format"),
  topic: z.string().trim().min(3, "Give a topic of at least 3 characters"),
  language: z.enum(["english", "roman_urdu", "mixed"]),
});

type ScriptJobResult = { script_id: string };

function ScriptForm({
  records,
  defaultTemplateId,
  submitting,
  onSubmit,
}: {
  records: DnaRecord[];
  defaultTemplateId: string;
  submitting: boolean;
  onSubmit: (request: GenerateScriptRequest) => void;
}) {
  const form = useForm<GenerateScriptRequest>({
    resolver: zodResolver(scriptRequestSchema),
    defaultValues: { template_id: defaultTemplateId, topic: "", language: "roman_urdu" },
  });
  const errors = form.formState.errors;
  const templates = records.filter((record) => record.is_template);
  const others = records.filter((record) => !record.is_template);

  return (
    <GlassCard className="lg:sticky lg:top-6">
      <CardHeader title="Brief" />
      <form noValidate onSubmit={form.handleSubmit(onSubmit)} className="space-y-5">
        <Field label="Format template" htmlFor="template" error={errors.template_id?.message}>
          <Select id="template" aria-invalid={Boolean(errors.template_id)} {...form.register("template_id")}>
            {templates.length > 0 && (
              <optgroup label="Saved templates">
                {templates.map((record) => (
                  <option key={record.id} value={record.id}>{record.title} · {HOOK_TYPE_LABEL[record.hook_type]}</option>
                ))}
              </optgroup>
            )}
            <optgroup label="Other analysed reels">
              {others.map((record) => (
                <option key={record.id} value={record.id}>{record.title} · {HOOK_TYPE_LABEL[record.hook_type]}</option>
              ))}
            </optgroup>
          </Select>
        </Field>

        <Field label="Topic or rough idea" htmlFor="topic" error={errors.topic?.message}>
          <Input id="topic" dir="auto" placeholder="Gol gappay at Liberty Market" aria-invalid={Boolean(errors.topic)} {...form.register("topic")} />
        </Field>

        <fieldset>
          <legend className="mb-2 text-sm font-medium">Language</legend>
          <div className="flex flex-wrap gap-2">
            {LANGUAGES.map((language) => (
              <ChoiceChip key={language.value} type="radio" value={language.value} label={language.label} {...form.register("language")} />
            ))}
          </div>
        </fieldset>

        <Button type="submit" size="lg" className="w-full" disabled={submitting}>
          <WandSparkles aria-hidden />
          {submitting ? "Generating…" : "Generate script"}
        </Button>
      </form>
    </GlassCard>
  );
}

function GeneratedScript({ jobId, onRetry }: { jobId: string; onRetry: () => void }) {
  const job = useJob<ScriptJobResult>(jobId);
  const scriptId = job.data?.status === "done" ? (job.data.result?.script_id ?? null) : null;
  const script = useScript(scriptId);

  if (!scriptId) {
    return <JobProgress label="Writing hooks, angles and script" job={job.data} requestError={job.error} onRetry={onRetry} />;
  }
  return (
    <QueryState query={script} loading={<GlassCard><LoadingBlock label="Loading script" /></GlassCard>}>
      {(data) => <ScriptResult script={data} />}
    </QueryState>
  );
}

export function ScriptStudio() {
  const searchParams = useSearchParams();
  const records = useDnaRecords();
  const generate = useGenerateScript();
  const [lastRequest, setLastRequest] = useState<GenerateScriptRequest | null>(null);

  function start(request: GenerateScriptRequest) {
    setLastRequest(request);
    generate.mutate(request);
  }

  const jobId = generate.data?.job_id ?? null;

  return (
    <div className="grid items-start gap-4 lg:grid-cols-[22rem_1fr]">
      <QueryState
        query={records}
        loading={<GlassCard><LoadingBlock label="Loading formats" /></GlassCard>}
        isEmpty={(page) => page.items.length === 0}
        empty={
          <GlassCard>
            <EmptyState title="No formats yet" description="Analyse at least one reel in the DNA library to use it as a template." />
          </GlassCard>
        }
      >
        {(page) => (
          <ScriptForm
            records={page.items}
            defaultTemplateId={searchParams.get("template") ?? page.items.find((record) => record.is_template)?.id ?? page.items[0].id}
            submitting={generate.isPending}
            onSubmit={start}
          />
        )}
      </QueryState>

      <div className="min-w-0 space-y-4">
        {generate.isError && (
          <GlassCard>
            <ErrorState error={generate.error} onRetry={lastRequest ? () => start(lastRequest) : undefined} />
          </GlassCard>
        )}
        {jobId && <GeneratedScript key={jobId} jobId={jobId} onRetry={() => lastRequest && start(lastRequest)} />}
        {!jobId && !generate.isError && (
          <GlassCard>
            <EmptyState
              icon={PenLine}
              title="Your script appears here"
              description="Each hook gets a 0 to 100 score with the top 3 reasons, so you know why one beats another."
            />
          </GlassCard>
        )}
      </div>
    </div>
  );
}
