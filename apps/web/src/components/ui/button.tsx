import Link from "next/link";
import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

const VARIANT_CLASSES = {
  primary:
    "bg-accent text-on-accent shadow-glow hover:bg-accent-strong hover:text-ink disabled:bg-accent/40 disabled:shadow-none",
  secondary: "border border-edge bg-surface-strong text-ink hover:bg-surface-hover hover:border-edge-strong",
  ghost: "text-muted hover:bg-surface-strong hover:text-ink",
  danger: "border border-danger/40 bg-danger-soft text-danger hover:bg-danger/25",
} as const;

const SIZE_CLASSES = {
  sm: "h-8 gap-1.5 px-3 text-xs",
  md: "h-10 gap-2 px-4 text-sm",
  lg: "h-12 gap-2 px-6 text-base",
} as const;

type ButtonStyleProps = {
  variant?: keyof typeof VARIANT_CLASSES;
  size?: keyof typeof SIZE_CLASSES;
};

function buttonClasses({ variant = "primary", size = "md" }: ButtonStyleProps, className?: string): string {
  return cn(
    "inline-flex items-center justify-center rounded-pill font-medium whitespace-nowrap transition-all",
    "disabled:cursor-not-allowed disabled:opacity-60 [&_svg]:size-4 [&_svg]:shrink-0",
    VARIANT_CLASSES[variant],
    SIZE_CLASSES[size],
    className,
  );
}

export function Button({ variant, size, className, type = "button", ...props }: ComponentProps<"button"> & ButtonStyleProps) {
  return <button type={type} className={buttonClasses({ variant, size }, className)} {...props} />;
}

export function ButtonLink({ variant, size, className, ...props }: ComponentProps<typeof Link> & ButtonStyleProps) {
  return <Link className={buttonClasses({ variant, size }, className)} {...props} />;
}
