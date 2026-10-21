const NICHES = [
  "Lahore street food",
  "Skincare",
  "Tech reviews",
  "Cricket edits",
  "Modest fashion",
  "Paisa & finance",
  "Desi comedy",
  "Home cooking",
  "Travel Pakistan",
  "Fitness",
];

function NicheRow({ hidden }: { hidden?: boolean }) {
  return (
    <ul aria-hidden={hidden} className="flex shrink-0 items-center">
      {NICHES.map((niche, index) => (
        <li key={niche} className="flex items-center whitespace-nowrap">
          <span
            className={
              index % 2 === 0
                ? "px-6 text-2xl font-semibold tracking-tight text-ink/90 sm:text-4xl"
                : "px-6 font-display text-3xl text-muted italic sm:text-5xl"
            }
          >
            {niche}
          </span>
          <span className="text-accent">✦</span>
        </li>
      ))}
    </ul>
  );
}

export function NicheMarquee() {
  return (
    <section aria-label="Made for every niche" className="border-y border-edge bg-surface/40 py-7 backdrop-blur-sm">
      <div className="flex overflow-hidden [mask-image:linear-gradient(90deg,transparent,black_12%,black_88%,transparent)]">
        <div className="flex animate-[marquee_45s_linear_infinite] motion-reduce:animate-none">
          <NicheRow />
          <NicheRow hidden />
        </div>
      </div>
    </section>
  );
}
