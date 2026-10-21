import { Play } from "lucide-react";

import type { EditOptions } from "@/lib/api/types";
import { cn } from "@/lib/utils";

import { CAPTION_STYLES, SAMPLE_CAPTION_WORDS } from "./caption-styles";

type PhonePreviewProps = {
  options: EditOptions;
  videoUrl: string | null;
  hookText: string;
};

/** 9:16 frame that shows the chosen caption style over the creator's own clip, or a placeholder. */
export function PhonePreview({ options, videoUrl, hookText }: PhonePreviewProps) {
  const style = CAPTION_STYLES.find((item) => item.value === options.caption_style) ?? CAPTION_STYLES[0];

  return (
    <div className="mx-auto w-full max-w-[17rem]">
      <div className="relative aspect-[9/16] overflow-hidden rounded-[2rem] border-4 border-edge-strong bg-canvas shadow-glass">
        {videoUrl ? (
          <video src={videoUrl} className="absolute inset-0 size-full object-cover" muted loop autoPlay playsInline />
        ) : (
          <div className="absolute inset-0 bg-gradient-to-br from-glow-1/60 via-glow-2/40 to-glow-3/50">
            <div className="absolute inset-0 grid place-items-center">
              <Play aria-hidden className="size-10 text-ink/70" />
            </div>
          </div>
        )}

        {options.hook_overlay && (
          <div className="absolute inset-x-4 top-10 rounded-xl border border-edge-strong bg-canvas/50 px-3 py-2 text-center text-sm font-bold backdrop-blur-md">
            <span dir="auto">{hookText}</span>
          </div>
        )}

        <div className="absolute inset-x-3 bottom-24 flex justify-center">
          <p className={cn("flex flex-wrap justify-center gap-x-1.5 text-center", style.className)}>
            {SAMPLE_CAPTION_WORDS.map((word) => (
              <span key={word}>{word}</span>
            ))}
          </p>
        </div>

        {options.progress_bar && (
          <div className="absolute inset-x-0 bottom-0 h-1.5 bg-ink/20">
            <div className="h-full w-2/5 bg-accent" />
          </div>
        )}
      </div>
    </div>
  );
}
