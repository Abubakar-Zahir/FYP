/** Slow-moving colored glows that give the glass panels something to blur. */
export function AmbientBackground() {
  return (
    <div aria-hidden className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      <div className="absolute -top-32 -left-24 size-[28rem] rounded-full bg-glow-1/40 blur-[110px] animate-[float_18s_ease-in-out_infinite]" />
      <div className="absolute top-1/3 -right-32 size-[26rem] rounded-full bg-glow-2/30 blur-[120px] animate-[float_22s_ease-in-out_infinite_reverse]" />
      <div className="absolute -bottom-40 left-1/3 size-[30rem] rounded-full bg-glow-3/25 blur-[120px] animate-[float_26s_ease-in-out_infinite]" />
    </div>
  );
}
