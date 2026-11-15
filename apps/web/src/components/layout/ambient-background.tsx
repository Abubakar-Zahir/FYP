/** Soft warm glows at the top of every page. Decoration only. */
export function AmbientBackground() {
  return (
    <div aria-hidden className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      <div className="absolute -top-48 left-1/2 h-[32rem] w-[60rem] -translate-x-1/2 rounded-full bg-[radial-gradient(closest-side,rgb(255_142_224/0.35),rgb(255_196_160/0.25)_50%,transparent)] blur-3xl" />
    </div>
  );
}
