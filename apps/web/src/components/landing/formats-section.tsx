import { ArrowRight } from "lucide-react";
import Link from "next/link";

import { cn } from "@/lib/utils";

import { SectionHeading, Soft } from "./section-heading";

type FormatTile = { niche: string; hook: string; format: string; scene: string };

// Gradients stand in for footage, so the page ships no video or image files
const SCENES = [
  "bg-[radial-gradient(circle_at_30%_70%,#f59e0b_0,transparent_40%),linear-gradient(160deg,#3b1d0f,#120806)]",
  "bg-[radial-gradient(circle_at_70%_30%,#ff4fae_0,transparent_45%),linear-gradient(200deg,#2a0f1f,#0b0610)]",
  "bg-[radial-gradient(circle_at_40%_40%,#38bdf8_0,transparent_45%),linear-gradient(180deg,#0c1a2a,#05080d)]",
  "bg-[radial-gradient(circle_at_60%_65%,#4ade80_0,transparent_40%),linear-gradient(170deg,#0f2416,#050a06)]",
  "bg-[radial-gradient(circle_at_50%_50%,#fb923c_0,transparent_42%),linear-gradient(190deg,#2b0b08,#0a0504)]",
  "bg-[radial-gradient(circle_at_30%_30%,#c084fc_0,transparent_45%),linear-gradient(160deg,#1e0f2e,#08050d)]",
];

const ROW_ONE: FormatTile[] = [
  { niche: "Street food", hook: "Sab se crispy chaat?", format: "Question hook" },
  { niche: "Skincare", hook: "3 mistakes in your routine", format: "Listicle" },
  { niche: "Tech", hook: "Rs 30K phone vs Rs 300K", format: "Versus" },
  { niche: "Cricket", hook: "Ye catch dekha?", format: "Reaction" },
  { niche: "Fashion", hook: "1 kurta, 4 looks", format: "Transformation" },
  { niche: "Finance", hook: "Salary aate hi ye karo", format: "How-to" },
  { niche: "Comedy", hook: "Ammi when WiFi is slow", format: "Skit" },
].map((tile, index) => ({ ...tile, scene: SCENES[index % SCENES.length] }));

const ROW_TWO: FormatTile[] = [
  { niche: "Home cooking", hook: "10 minute daal", format: "Recipe" },
  { niche: "Travel", hook: "Hunza in Rs 25K", format: "Budget" },
  { niche: "Fitness", hook: "No gym, no excuses", format: "Challenge" },
  { niche: "Street food", hook: "30 saal purana stall", format: "Story" },
  { niche: "Tech", hook: "Ye setting off karo", format: "Tip" },
  { niche: "Fashion", hook: "Eid outfit under 5K", format: "Haul" },
  { niche: "Comedy", hook: "Every desi wedding", format: "POV" },
].map((tile, index) => ({ ...tile, scene: SCENES[(index + 3) % SCENES.length] }));

function Tile({ tile }: { tile: FormatTile }) {
  return (
    <li className={cn("relative aspect-[9/14] w-36 shrink-0 overflow-hidden rounded-2xl text-white shadow-glass sm:w-44", tile.scene)}>
      <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-black/20" />
      <span className="absolute top-2.5 left-2.5 rounded-pill bg-white/15 px-2 py-0.5 text-[10px] font-medium backdrop-blur-md">
        {tile.format}
      </span>
      <p className="absolute inset-x-3 top-[42%] text-center text-sm leading-tight font-black uppercase [text-shadow:0_2px_0_rgb(0_0_0/0.7)]">
        {tile.hook}
      </p>
      <p className="absolute inset-x-3 bottom-3 text-[11px] text-white/75">{tile.niche}</p>
    </li>
  );
}

function Row({ tiles, reverse }: { tiles: FormatTile[]; reverse?: boolean }) {
  return (
    <div className="flex overflow-hidden [mask-image:linear-gradient(90deg,transparent,black_8%,black_92%,transparent)]">
      <div
        className={cn(
          "flex animate-[marquee_60s_linear_infinite] gap-3 pr-3 hover:[animation-play-state:paused] motion-reduce:animate-none",
          reverse && "[animation-direction:reverse]",
        )}
      >
        <ul className="flex gap-3">
          {tiles.map((tile) => (
            <Tile key={tile.hook} tile={tile} />
          ))}
        </ul>
        <ul aria-hidden className="flex gap-3">
          {tiles.map((tile) => (
            <Tile key={tile.hook} tile={tile} />
          ))}
        </ul>
      </div>
    </div>
  );
}

export function FormatsSection() {
  return (
    <section className="py-20 sm:py-28">
      <SectionHeading
        className="px-4"
        title={
          <>
            Make endless reels,
            <br />
            <Soft>based on formats that already work.</Soft>
          </>
        }
      />
      <p className="mt-3 text-center text-[9.5px] font-extrabold tracking-[0.1em] text-subtle uppercase">
        Example formats, not real accounts
      </p>

      <div className="mt-12 space-y-3">
        <Row tiles={ROW_ONE} />
        <Row tiles={ROW_TWO} reverse />
      </div>

      <div className="reveal mx-auto mt-20 max-w-3xl px-4 text-center">
        <p className="text-[clamp(1.75rem,3.6vw,2.75rem)] leading-[1.12] font-medium tracking-[-0.03em] text-balance">
          Made for how Pakistan posts: English, Urdu and Roman Urdu in the same reel.
        </p>
        <Link
          href="/login"
          className="bg-cta mt-8 inline-flex h-12 items-center gap-2 rounded-xl px-7 font-bold tracking-[-0.01em] text-white shadow-glow transition-transform hover:scale-[1.02]"
        >
          Try it in the pilot
          <ArrowRight aria-hidden className="size-4" />
        </Link>
      </div>
    </section>
  );
}
