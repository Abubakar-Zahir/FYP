"use client";

import { useQueryClient } from "@tanstack/react-query";
import { Upload } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { isAcceptedVideo, queryKeys, useJob, useUploadReference } from "@/lib/api/hooks";
import { Button } from "@/components/ui/button";
import { JobProgress } from "@/components/ui/job-progress";

// rules.md 6.3. The API checks again, and the worker checks the 90-second limit.
const MAX_UPLOAD_BYTES = 200 * 1024 * 1024;

type AnalyseResult = { dna_id: string };

function AnalysisProgress({ jobId, onRetry }: { jobId: string; onRetry: () => void }) {
  const queryClient = useQueryClient();
  const job = useJob<AnalyseResult>(jobId);
  const done = job.data?.status === "done";

  useEffect(() => {
    if (done) void queryClient.invalidateQueries({ queryKey: queryKeys.dna });
  }, [done, queryClient]);

  return (
    <div className="w-72 max-w-full">
      <JobProgress label="Analysing the reel's DNA" job={job.data} requestError={job.error} onRetry={onRetry} />
    </div>
  );
}

/** Reference reels are uploaded files, never links (CLAUDE.md hard constraint 1). */
export function UploadReferenceButton() {
  const inputRef = useRef<HTMLInputElement>(null);
  const lastFile = useRef<File | null>(null);
  const upload = useUploadReference();
  const [rejected, setRejected] = useState<string | null>(null);

  function start(file: File | undefined) {
    if (!file) return;
    upload.reset();
    if (!isAcceptedVideo(file)) return setRejected("Upload an MP4 or MOV video.");
    if (file.size > MAX_UPLOAD_BYTES) return setRejected("The video is over 200 MB. Trim it and try again.");
    setRejected(null);
    lastFile.current = file;
    upload.mutate(file);
  }

  return (
    <div className="flex flex-col items-end gap-2">
      <input
        ref={inputRef}
        type="file"
        accept="video/mp4,video/quicktime"
        className="sr-only"
        tabIndex={-1}
        aria-hidden
        onChange={(event) => start(event.target.files?.[0])}
      />
      <Button onClick={() => inputRef.current?.click()} disabled={upload.isPending}>
        <Upload aria-hidden />
        {upload.isPending ? "Uploading…" : "Upload reference reel"}
      </Button>
      {rejected && <p role="alert" className="text-xs text-danger">{rejected}</p>}
      {!rejected && upload.isError && <p role="alert" className="max-w-72 text-xs text-danger">{upload.error.message}</p>}
      {upload.isSuccess && (
        <AnalysisProgress
          key={upload.data.job_id}
          jobId={upload.data.job_id}
          onRetry={() => lastFile.current && start(lastFile.current)}
        />
      )}
    </div>
  );
}
