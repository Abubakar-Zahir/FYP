import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

type SectionHeadingProps = {
  number: string;
  kicker: string;
  title: ReactNode;
  body?: string;
  className?: string;
};

/** Numbered editorial heading. `title` may hold a <Serif> accent word. */
export function SectionHeading({ number, kicker, title, body, className }: SectionHeadingProps) {
  return (
    <div className={cn("reveal max-w-3xl", className)}>
      <p className="flex items-center gap-3 font-mono text-xs tracking-widest text-subtle uppercase">
        <span className="text-accent">{number}</span>
        <span className="h-px w-8 bg-edge-strong" />
        {kicker}
      </p>
      <h2 className="mt-5 text-[clamp(2.1rem,4.6vw,3.9rem)] leading-[0.98] font-semibold tracking-[-0.035em]">{title}</h2>
      {body && <p className="mt-5 max-w-xl text-base leading-relaxed text-muted sm:text-lg">{body}</p>}
    </div>
  );
}

export function Serif({ children, className }: { children: ReactNode; className?: string }) {
  return <span className={cn("font-display font-normal tracking-[-0.01em] italic", className)}>{children}</span>;
}
