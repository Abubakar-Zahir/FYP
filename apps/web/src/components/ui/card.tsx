import type { ComponentProps, ReactNode } from "react";

import { cn } from "@/lib/utils";

export function GlassCard({ className, ...props }: ComponentProps<"section">) {
  return <section className={cn("glass p-5 sm:p-6", className)} {...props} />;
}

type CardHeaderProps = {
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
};

export function CardHeader({ title, description, action, className }: CardHeaderProps) {
  return (
    <header className={cn("mb-4 flex flex-col items-start gap-3 sm:flex-row sm:justify-between", className)}>
      <div className="min-w-0">
        <h2 className="text-base font-semibold text-ink">{title}</h2>
        {description && <p className="mt-0.5 text-sm text-muted">{description}</p>}
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </header>
  );
}

export function InsetTile({ className, ...props }: ComponentProps<"div">) {
  return <div className={cn("glass-inset p-4", className)} {...props} />;
}
