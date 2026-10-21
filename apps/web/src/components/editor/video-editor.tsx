"use client";

import { ArrowRight, CircleCheck, Film, RotateCcw, Scissors, Upload, WandSparkles } from "lucide-react";
import { useRef, useState } from "react";

import { useJob, useStartEdit } from "@/lib/api/hooks";
import type { EditOptions, EditResult } from "@/lib/api/types";
import { cn, formatSeconds } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button, ButtonLink } from "@/components/ui/button";
import { CardHeader, GlassCard, InsetTile } from "@/components/ui/card";
import { Switch } from "@/components/ui/form";
import { JobProgress } from "@/components/ui/job-progress";
import { ErrorState } from "@/components/ui/states";

import { CAPTION_STYLES } from "./caption-styles";
import { PhonePreview } from "./phone-preview";
import { MAX_DURATION_S, useMockUpload, type UploadState } from "./use-mock-upload";

const MOCK_VIDEO_ID = "vid_01";
const SAMPLE_HOOK = "Sab se crispy chaat?";

const DEFAULT_OPTIONS: EditOptions = {
  caption_style: "bold_pop",
  cut_silences: true,
  progress_bar: true,
  hook_overlay: true,
};

function UploadStep({ state, onFile, onSample, onReset }: {
  state: UploadState;
  onFile: (file: File) => void;
  onSample: () => void;
  onReset: () => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  if (state.status === "uploading" || state.status === "uploaded") {
    const percent = state.status === "uploading" ? Math.round(state.progress * 100) : 100;
    return (
      <InsetTile className="flex items-center gap-4">
        <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-accent-soft text-accent">
          {state.status === "uploaded" ? <CircleCheck aria-hidden className="size-5" /> : <Film aria-hidden className="size-5" />}
        </span>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium">{state.fileName}</p>
          <div
            role="progressbar"
            aria-label="Upload progress"
            aria-valuenow={percent}
            aria-valuemin={0}
            aria-valuemax={100}
            className="mt-2 h-1.5 overflow-hidden rounded-pill bg-surface-strong"
          >
            <div className="h-full rounded-pill bg-accent transition-[width]" style={{ width: `${percent}%` }} />
          </div>
          <p className="mt-1 text-xs text-subtle">
            {state.status === "uploaded" ? `Uploaded · ${formatSeconds(state.durationS)}` : `Uploading… ${percent}%`}
          </p>
        </div>
        <Button variant="ghost" size="sm" onClick={onReset} aria-label="Remove clip">
          <RotateCcw aria-hidden />
        </Button>
      </InsetTile>
    );
  }

  return (
    <div>
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setDragging(false);
          const file = event.dataTransfer.files[0];
          if (file) onFile(file);
        }}
        className={cn(
          "flex w-full flex-col items-center gap-3 rounded-2xl border-2 border-dashed px-6 py-10 text-center transition-colors",
          dragging ? "border-accent bg-accent-soft" : "border-edge-strong hover:border-accent/60 hover:bg-surface",
        )}
      >
        <span className="grid size-12 place-items-center rounded-2xl bg-accent-soft text-accent">
          <Upload aria-hidden className="size-5" />
        </span>
        <span className="font-medium">Drop your clip or click to browse</span>
        <span className="text-xs text-subtle">Vertical MP4 or MOV, up to {MAX_DURATION_S} s</span>
      </button>
      <input
        ref={inputRef}
        type="file"
        accept="video/mp4,video/quicktime"
        className="sr-only"
        tabIndex={-1}
        aria-hidden
        onChange={(event) => {
          const file = event.target.files?.[0];
          if (file) onFile(file);
          event.target.value = "";
        }}
      />
      {state.status === "invalid" && <p role="alert" className="mt-2 text-sm text-danger">{state.message}</p>}
      <Button variant="ghost" size="sm" className="mt-3" onClick={onSample}>
        No clip handy? Use a sample
      </Button>
    </div>
  );
}

function CaptionStylePicker({ value, onChange }: { value: EditOptions["caption_style"]; onChange: (style: EditOptions["caption_style"]) => void }) {
  return (
    <fieldset>
      <legend className="mb-2 text-sm font-medium">Caption style</legend>
      <div className="grid grid-cols-2 gap-2">
        {CAPTION_STYLES.map((style) => (
          <label
            key={style.value}
            className={cn(
              "cursor-pointer rounded-xl border p-3 text-center transition-all",
              "has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-offset-2 has-[:focus-visible]:outline-accent",
              value === style.value ? "border-accent/60 bg-accent-soft" : "border-edge bg-surface hover:border-edge-strong",
            )}
          >
            <input type="radio" name="caption-style" value={style.value} checked={value === style.value} onChange={() => onChange(style.value)} className="sr-only" />
            <span className="grid h-10 place-items-center rounded-lg bg-gradient-to-br from-glow-1/50 to-glow-3/40">
              <span className={style.className}>Aa</span>
            </span>
            <span className="mt-2 block text-xs text-muted">{style.label}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}

function RenderStatus({ jobId, onRetry }: { jobId: string; onRetry: () => void }) {
  const job = useJob<EditResult>(jobId);
  const result = job.data?.status === "done" ? job.data.result : null;

  if (!result) {
    return <JobProgress label="Transcribing, cutting silences, burning captions" job={job.data} requestError={job.error} onRetry={onRetry} />;
  }
  return (
    <InsetTile className="space-y-3">
      <p className="flex items-center gap-2 text-sm font-medium">
        <CircleCheck aria-hidden className="size-4 text-success" />
        Render ready
      </p>
      <div className="flex flex-wrap gap-2">
        <Badge>{formatSeconds(result.duration_s)} final</Badge>
        <Badge tone="success">
          <Scissors aria-hidden />
          {result.removed_silence_s}s silence cut
        </Badge>
      </div>
      <ButtonLink href="/variants" className="w-full">
        Create 3 variants
        <ArrowRight aria-hidden />
      </ButtonLink>
    </InsetTile>
  );
}

export function VideoEditor() {
  const upload = useMockUpload();
  const [options, setOptions] = useState<EditOptions>(DEFAULT_OPTIONS);
  const startEdit = useStartEdit(MOCK_VIDEO_ID);

  const uploaded = upload.state.status === "uploaded";
  const previewUrl = upload.state.status === "uploading" || upload.state.status === "uploaded" ? upload.state.previewUrl : null;
  const jobId = startEdit.data?.job_id ?? null;

  function setOption<K extends keyof EditOptions>(key: K, value: EditOptions[K]) {
    setOptions((current) => ({ ...current, [key]: value }));
  }

  const render = () => startEdit.mutate(options);

  return (
    <div className="grid items-start gap-4 lg:grid-cols-[1fr_20rem]">
      <div className="space-y-4">
        <GlassCard>
          <CardHeader title="1. Upload footage" />
          <UploadStep state={upload.state} onFile={(file) => void upload.uploadFile(file)} onSample={upload.loadSampleClip} onReset={upload.reset} />
        </GlassCard>

        <GlassCard className={cn(!uploaded && "opacity-60")} aria-disabled={!uploaded}>
          <CardHeader title="2. Style and options" />
          <fieldset disabled={!uploaded} className="space-y-5">
            <CaptionStylePicker value={options.caption_style} onChange={(style) => setOption("caption_style", style)} />
            <div className="divide-y divide-edge">
              <Switch label="Cut silences" description="Removes pauses longer than 0.6 s" checked={options.cut_silences} onChange={(event) => setOption("cut_silences", event.target.checked)} />
              <Switch label="Hook text overlay" description="Shows your hook line for the first 3 s" checked={options.hook_overlay} onChange={(event) => setOption("hook_overlay", event.target.checked)} />
              <Switch label="Progress bar" description="Thin bar along the bottom edge" checked={options.progress_bar} onChange={(event) => setOption("progress_bar", event.target.checked)} />
            </div>
            <Button size="lg" className="w-full sm:w-auto" onClick={render} disabled={!uploaded || startEdit.isPending}>
              <WandSparkles aria-hidden />
              {startEdit.isPending ? "Starting…" : "Render"}
            </Button>
          </fieldset>
        </GlassCard>
      </div>

      <GlassCard className="space-y-4 lg:sticky lg:top-6">
        <CardHeader title="Preview" className="mb-0" />
        <PhonePreview options={options} videoUrl={previewUrl} hookText={SAMPLE_HOOK} />
        {startEdit.isError && <ErrorState error={startEdit.error} onRetry={render} />}
        {jobId && <RenderStatus key={jobId} jobId={jobId} onRetry={render} />}
      </GlassCard>
    </div>
  );
}
