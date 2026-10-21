import type { ComponentProps, ReactNode } from "react";

import { cn } from "@/lib/utils";

const FIELD_CLASSES =
  "w-full rounded-xl border border-edge bg-surface px-3.5 text-sm text-ink placeholder:text-subtle transition-colors hover:border-edge-strong focus:border-accent focus:outline-none aria-[invalid=true]:border-danger";

export function Input({ className, ...props }: ComponentProps<"input">) {
  return <input className={cn(FIELD_CLASSES, "h-11", className)} {...props} />;
}

export function Textarea({ className, ...props }: ComponentProps<"textarea">) {
  return <textarea className={cn(FIELD_CLASSES, "min-h-24 py-3", className)} {...props} />;
}

export function Select({ className, ...props }: ComponentProps<"select">) {
  return <select className={cn(FIELD_CLASSES, "h-11 [&>option]:bg-canvas", className)} {...props} />;
}

type FieldProps = {
  label: string;
  htmlFor: string;
  error?: string;
  hint?: string;
  children: ReactNode;
};

export function Field({ label, htmlFor, error, hint, children }: FieldProps) {
  return (
    <div className="space-y-1.5">
      <label htmlFor={htmlFor} className="block text-sm font-medium text-ink">
        {label}
      </label>
      {children}
      {error ? (
        <p role="alert" className="text-xs text-danger">
          {error}
        </p>
      ) : (
        hint && <p className="text-xs text-subtle">{hint}</p>
      )}
    </div>
  );
}

type ChoiceChipProps = Omit<ComponentProps<"input">, "type"> & {
  type: "radio" | "checkbox";
  label: ReactNode;
};

/** Radio or checkbox styled as a glass chip. The native input stays for keyboard and screen readers. */
export function ChoiceChip({ label, className, ...inputProps }: ChoiceChipProps) {
  return (
    <label
      className={cn(
        "relative inline-flex cursor-pointer items-center gap-2 rounded-pill border border-edge bg-surface px-4 py-2 text-sm text-muted transition-all",
        "hover:border-edge-strong hover:text-ink",
        "has-[:checked]:border-accent/60 has-[:checked]:bg-accent-soft has-[:checked]:text-ink",
        "has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-accent has-[:focus-visible]:outline-offset-2",
        className,
      )}
    >
      <input {...inputProps} className="peer sr-only" />
      {label}
    </label>
  );
}

export function Switch({ label, description, ...inputProps }: Omit<ComponentProps<"input">, "type"> & { label: string; description?: string }) {
  return (
    <label className="flex cursor-pointer items-center justify-between gap-4 py-2">
      <span>
        <span className="block text-sm font-medium text-ink">{label}</span>
        {description && <span className="block text-xs text-subtle">{description}</span>}
      </span>
      <span className="relative inline-flex shrink-0">
        <input type="checkbox" role="switch" className="peer sr-only" {...inputProps} />
        <span className="h-6 w-11 rounded-pill border border-edge bg-surface-strong transition-colors peer-checked:border-accent/60 peer-checked:bg-accent/60 peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-accent" />
        <span className="absolute top-1 left-1 size-4 rounded-full bg-ink transition-transform peer-checked:translate-x-5" />
      </span>
    </label>
  );
}
