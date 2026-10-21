import type { CaptionStyle } from "@/lib/api/types";

export const CAPTION_STYLES: { value: CaptionStyle; label: string; className: string }[] = [
  {
    value: "bold_pop",
    label: "Bold pop",
    className: "text-lg font-black uppercase tracking-tight text-ink [text-shadow:0_2px_0_rgb(0_0_0/0.8),0_0_12px_rgb(0_0_0/0.6)]",
  },
  {
    value: "karaoke",
    label: "Karaoke",
    className: "text-base font-extrabold text-ink [text-shadow:0_2px_6px_rgb(0_0_0/0.8)] [&>span:nth-child(2)]:animate-[karaoke_1.2s_ease-in-out_infinite]",
  },
  {
    value: "minimal",
    label: "Minimal",
    className: "text-sm font-medium text-ink [text-shadow:0_1px_4px_rgb(0_0_0/0.9)]",
  },
  {
    value: "boxed",
    label: "Boxed",
    className: "rounded-md bg-canvas/80 px-2 py-0.5 text-sm font-bold text-ink",
  },
];

export const SAMPLE_CAPTION_WORDS = ["Sab", "se", "crispy", "chaat?"];
