"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowRight, Dna, FlaskConical, MessagesSquare, Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { APP_NAME } from "@/components/layout/nav-items";
import { GoogleIcon } from "@/components/ui/brand-icons";
import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/form";

const MIN_PASSWORD_LENGTH = 8;

const loginSchema = z.object({
  email: z.email("Enter a valid email address"),
  password: z.string().min(MIN_PASSWORD_LENGTH, `Use at least ${MIN_PASSWORD_LENGTH} characters`),
});

type LoginValues = z.infer<typeof loginSchema>;

const HIGHLIGHTS = [
  { icon: Dna, text: "Break viral reels into a reusable format DNA" },
  { icon: FlaskConical, text: "Test 3 to 5 variants as Trial Reels before followers see them" },
  { icon: MessagesSquare, text: "Turn Roman Urdu and English comments into ideas" },
];

export function LoginPanel() {
  const router = useRouter();
  const form = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  // Supabase Auth replaces this in P1-01. The prototype goes straight to onboarding.
  const continueToApp = () => router.push("/onboarding");

  return (
    <div className="grid w-full max-w-5xl overflow-hidden lg:grid-cols-[1.1fr_1fr] glass p-0 sm:p-0">
      <div className="relative hidden flex-col justify-between gap-10 border-r border-edge bg-gradient-to-br from-accent/20 via-transparent to-glow-2/15 p-10 lg:flex">
        <div className="flex items-center gap-2.5">
          <span className="grid size-10 place-items-center rounded-xl bg-gradient-to-br from-accent to-glow-2 shadow-glow">
            <Sparkles aria-hidden className="size-5" />
          </span>
          <span className="text-xl font-semibold">{APP_NAME}</span>
        </div>
        <div>
          <h1 className="text-4xl leading-tight font-semibold tracking-tight">
            Know what will work <span className="text-gradient">before you post.</span>
          </h1>
          <ul className="mt-8 space-y-4">
            {HIGHLIGHTS.map(({ icon: Icon, text }) => (
              <li key={text} className="flex items-center gap-3 text-sm text-muted">
                <span className="glass-inset grid size-9 shrink-0 place-items-center rounded-xl text-accent">
                  <Icon aria-hidden className="size-4" />
                </span>
                {text}
              </li>
            ))}
          </ul>
        </div>
        <p className="text-xs text-subtle">Official Instagram APIs only. Your password is never stored.</p>
      </div>

      <div className="p-6 sm:p-10">
        <h2 className="text-2xl font-semibold tracking-tight">Welcome back</h2>
        <p className="mt-1 text-sm text-muted">Sign in to continue to your studio.</p>

        <Button variant="secondary" size="lg" className="mt-8 w-full" onClick={continueToApp}>
          <GoogleIcon className="size-5" />
          Continue with Google
        </Button>

        <div className="my-6 flex items-center gap-3 text-xs text-subtle">
          <span className="h-px flex-1 bg-edge" />
          or with email
          <span className="h-px flex-1 bg-edge" />
        </div>

        <form noValidate onSubmit={form.handleSubmit(continueToApp)} className="space-y-4">
          <Field label="Email" htmlFor="email" error={form.formState.errors.email?.message}>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              placeholder="you@example.com"
              aria-invalid={Boolean(form.formState.errors.email)}
              {...form.register("email")}
            />
          </Field>
          <Field label="Password" htmlFor="password" error={form.formState.errors.password?.message}>
            <Input
              id="password"
              type="password"
              autoComplete="current-password"
              placeholder="••••••••"
              aria-invalid={Boolean(form.formState.errors.password)}
              {...form.register("password")}
            />
          </Field>
          <Button type="submit" size="lg" className="w-full">
            Sign in
            <ArrowRight aria-hidden />
          </Button>
        </form>

        <p className="mt-6 text-center text-xs text-subtle">
          New here? Signing in creates your account. By continuing you agree to the pilot terms.
        </p>
      </div>
    </div>
  );
}
