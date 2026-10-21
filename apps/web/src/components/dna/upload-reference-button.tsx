"use client";

import { Upload } from "lucide-react";
import { useRef, useState } from "react";

import { Button } from "@/components/ui/button";

const MAX_REFERENCE_REELS = 10;

/** Reference reels are uploaded files, never links (CLAUDE.md hard constraint 1). Upload is mocked in the prototype. */
export function UploadReferenceButton() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [fileName, setFileName] = useState<string | null>(null);

  return (
    <div className="flex items-center gap-3">
      {fileName && <span className="max-w-40 truncate text-xs text-muted" aria-live="polite">Queued: {fileName}</span>}
      <input
        ref={inputRef}
        type="file"
        accept="video/mp4,video/quicktime"
        className="sr-only"
        tabIndex={-1}
        aria-hidden
        onChange={(event) => setFileName(event.target.files?.[0]?.name ?? null)}
      />
      <Button onClick={() => inputRef.current?.click()} title={`Up to ${MAX_REFERENCE_REELS} reference reels`}>
        <Upload aria-hidden />
        Upload reference reel
      </Button>
    </div>
  );
}
