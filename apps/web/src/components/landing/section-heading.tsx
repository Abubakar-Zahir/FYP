import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

type SectionHeadingProps = {
  title: ReactNode;
  kicker?: string;
  body?: string;
  align?: "center" | "left";
  tone?: "light" | "dark";
  className?: string;
};

/** Large section heading. Inter 64px / 600 on desktop, tight tracking. */
export function SectionHeading({ title, kicker, body, align = "center", tone = "light", className }: SectionHeadingProps) {
  return (
    <div className={cn("reveal", align === "center" && "mx-auto text-center", className)}>
      {kicker && (
        <p className={cn("text-[13px] font-semibold tracking-wide uppercase", tone === "dark" ? "text-accent-glow" : "text-accent")}>
          {kicker}
        </p>
      )}
      <h2
        className={cn(
          "mt-3 text-[clamp(2.125rem,5vw,4rem)] leading-[1.02] font-semibold tracking-[-0.045em] text-balance",
          tone === "dark" && "text-on-dark",
        )}
      >
        {title}
      </h2>
      {body && (
        <p
          className={cn(
            "mt-5 max-w-xl text-[17px] leading-[1.5] text-balance",
            align === "center" && "mx-auto",
            tone === "dark" ? "text-on-dark-soft" : "text-muted",
          )}
        >
          {body}
        </p>
      )}
    </div>
  );
}

/** Second line of a heading, in the softer grey. */
export function Soft({ children }: { children: ReactNode }) {
  return <span className="text-subtle">{children}</span>;
}
