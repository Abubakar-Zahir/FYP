import { Crown, Eye, MessageCircle, TrendingUp } from "lucide-react";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

type PhoneScene = {
  label: string;
  hook: string;
  views: string;
  // Layered gradients that read as warm street-food footage without shipping images
  scene: string;
  winner?: boolean;
  className: string;
};

const PHONES: PhoneScene[] = [
  {
    label: "A",
    hook: "Sab se crispy chaat?",
    views: "11.8K",
    scene:
      "bg-[radial-gradient(circle_at_30%_70%,#f59e0b_0,transparent_38%),radial-gradient(circle_at_75%_35%,#b91c1c_0,transparent_45%),linear-gradient(160deg,#3b1d0f,#120806)]",
    className: "left-0 top-10 z-10 [--tilt:-9deg] animate-[drift_9s_ease-in-out_infinite]",
  },
  {
    label: "B",
    hook: "Best Rs 150 in Lahore?",
    views: "7.3K",
    scene:
      "bg-[radial-gradient(circle_at_65%_60%,#fbbf24_0,transparent_35%),radial-gradient(circle_at_20%_25%,#7c2d12_0,transparent_50%),linear-gradient(200deg,#1f1308,#0b0604)]",
    className: "right-0 top-14 z-10 [--tilt:9deg] animate-[drift_10s_ease-in-out_infinite_reverse]",
  },
  {
    label: "C",
    hook: "30 saal purana stall",
    views: "15.9K",
    winner: true,
    scene:
      "bg-[radial-gradient(circle_at_50%_62%,#fb923c_0,transparent_36%),radial-gradient(circle_at_28%_28%,#db2777_0,transparent_42%),radial-gradient(circle_at_80%_20%,#7c3aed_0,transparent_40%),linear-gradient(180deg,#2a0f1f,#0b0610)]",
    className: "left-1/2 top-0 z-20 -translate-x-1/2 [--tilt:0deg] animate-[drift_8s_ease-in-out_infinite]",
  },
];

function Phone({ phone }: { phone: PhoneScene }) {
  return (
    <div className={cn("absolute w-[44%] max-w-[15rem]", phone.className)}>
      <div
        className={cn(
          "relative aspect-[9/19] overflow-hidden rounded-[2.2rem] border border-white/15 p-1.5 shadow-[0_30px_80px_-20px_rgb(0_0_0/0.8)]",
          "bg-gradient-to-b from-white/20 to-white/5",
          phone.winner && "ring-2 ring-warning/70 shadow-[0_30px_100px_-10px_rgb(251_191_36/0.35)]",
        )}
      >
        <div className={cn("relative size-full overflow-hidden rounded-[1.8rem]", phone.scene)}>
          <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-black/30" />
          <div className="absolute top-3 left-1/2 h-4 w-16 -translate-x-1/2 rounded-pill bg-black/80" />
          <div className="absolute top-10 left-3 flex items-center gap-1.5 rounded-pill bg-black/40 px-2 py-1 text-[10px] font-medium backdrop-blur-md">
            <span className="size-1.5 rounded-full bg-success" />
            Trial · {phone.label}
          </div>
          <p className="absolute inset-x-3 top-[46%] text-center text-[clamp(0.8rem,1.6vw,1.05rem)] leading-tight font-black uppercase [text-shadow:0_2px_0_rgb(0_0_0/0.8)]">
            {phone.hook}
          </p>
          <div className="absolute inset-x-3 bottom-4 flex items-center justify-between text-[11px]">
            <span className="flex items-center gap-1 font-semibold">
              <Eye aria-hidden className="size-3.5" />
              {phone.views}
            </span>
            {phone.winner && (
              <span className="flex items-center gap-1 rounded-pill bg-warning px-2 py-0.5 font-bold text-on-accent">
                <Crown aria-hidden className="size-3" />
                Winner
              </span>
            )}
          </div>
          <div className="absolute inset-x-0 bottom-0 h-1 bg-white/20">
            <div className={cn("h-full bg-white", phone.winner ? "w-4/5" : "w-2/5")} />
          </div>
        </div>
      </div>
    </div>
  );
}

function FloatingChip({ className, children }: { className: string; children: ReactNode }) {
  return (
    <div
      className={cn(
        "glass absolute z-30 flex items-center gap-2.5 rounded-2xl px-3.5 py-2.5 text-xs shadow-[0_20px_50px_-15px_rgb(0_0_0/0.7)] sm:text-sm",
        className,
      )}
    >
      {children}
    </div>
  );
}

/** Hero visual: three Trial Reel variants racing, with the signals the product reads around them. */
export function PhoneStack() {
  return (
    <div aria-hidden className="relative mx-auto aspect-[1/1] w-full max-w-[34rem] sm:aspect-[6/5]">
      <div className="absolute inset-[12%] rounded-full bg-[radial-gradient(circle,rgb(251_146_60/0.35),rgb(124_58_237/0.2)_45%,transparent_70%)] blur-2xl" />
      {PHONES.map((phone) => (
        <Phone key={phone.label} phone={phone} />
      ))}

      <FloatingChip className="top-[8%] -left-1 animate-[drift_7s_ease-in-out_infinite] sm:-left-6">
        <span className="relative grid size-9 place-items-center">
          <svg viewBox="0 0 36 36" className="absolute inset-0 -rotate-90">
            <circle cx="18" cy="18" r="15" fill="none" stroke="var(--color-edge-strong)" strokeWidth="3" />
            <circle cx="18" cy="18" r="15" fill="none" stroke="var(--color-success)" strokeWidth="3" strokeLinecap="round" strokeDasharray="79 94" />
          </svg>
          <span className="text-[11px] font-bold">84</span>
        </span>
        <span>
          <span className="block font-semibold">Hook score</span>
          <span className="block text-[11px] text-muted">+ question hook</span>
        </span>
      </FloatingChip>

      <FloatingChip className="top-[44%] -right-1 animate-[drift_8s_ease-in-out_infinite_reverse] sm:-right-8">
        <span className="grid size-8 place-items-center rounded-lg bg-success-soft text-success">
          <TrendingUp className="size-4" />
        </span>
        <span>
          <span className="block font-semibold">3.4× your median</span>
          <span className="block text-[11px] text-muted">variant C, 72 h</span>
        </span>
      </FloatingChip>

      <FloatingChip className="bottom-[2%] left-[2%] hidden max-w-[15rem] animate-[drift_9s_ease-in-out_infinite] sm:-left-4 sm:flex">
        <span className="grid size-8 shrink-0 place-items-center rounded-full bg-accent-soft text-accent">
          <MessageCircle className="size-4" />
        </span>
        <span className="min-w-0">
          <span className="block truncate font-medium">Ye kahan hai exact location? 📍</span>
          <span className="block text-[11px] text-muted">Question · 412 people asked this</span>
        </span>
      </FloatingChip>
    </div>
  );
}
