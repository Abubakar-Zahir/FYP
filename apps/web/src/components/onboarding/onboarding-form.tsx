"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowRight, CircleCheck, LoaderCircle } from "lucide-react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { useConnectInstagram, useMe, useUpdateProfile } from "@/lib/api/hooks";
import type { Language, Profile } from "@/lib/api/types";
import { Badge } from "@/components/ui/badge";
import { InstagramIcon } from "@/components/ui/brand-icons";
import { Button } from "@/components/ui/button";
import { CardHeader, GlassCard } from "@/components/ui/card";
import { ChoiceChip, Field, Input, Select, Textarea } from "@/components/ui/form";
import { ErrorState, LoadingBlock } from "@/components/ui/states";

const LANGUAGE_OPTIONS: { value: Language; label: string }[] = [
  { value: "english", label: "English" },
  { value: "urdu", label: "Urdu" },
  { value: "roman_urdu", label: "Roman Urdu" },
];

const TONE_OPTIONS = ["Friendly and funny", "Calm and informative", "High energy", "Honest reviewer", "Storyteller"];

const profileSchema = z.object({
  role: z.enum(["creator", "brand"]),
  niche: z.string().trim().min(2, "Tell us your niche"),
  language_mix: z.array(z.enum(["english", "urdu", "roman_urdu"])).min(1, "Pick at least one language"),
  tone: z.string().min(1, "Pick a tone"),
  goals: z.string().trim().min(5, "A short goal helps us rank ideas"),
});

function InstagramConnect() {
  const me = useMe();
  const connect = useConnectInstagram();
  const account = me.data?.instagram;

  return (
    <GlassCard>
      <CardHeader
        title="Connect Instagram"
        description="We import your last 30 to 50 reels, their insights and comments. Professional accounts only."
      />
      {account ? (
        <div className="glass-inset flex flex-wrap items-center justify-between gap-3 p-4">
          <div className="flex items-center gap-3">
            <span className="grid size-10 place-items-center rounded-xl bg-gradient-to-br from-glow-2 to-warning text-ink">
              <InstagramIcon className="size-5" />
            </span>
            <div>
              <p className="font-medium">@{account.username}</p>
              <p className="text-xs text-subtle">{account.account_type.toLowerCase()} account</p>
            </div>
          </div>
          <Badge tone={account.trial_reels_eligible ? "success" : "warning"}>
            <CircleCheck aria-hidden />
            {account.trial_reels_eligible ? "Trial Reels available" : "Normal reels only"}
          </Badge>
        </div>
      ) : (
        <div className="space-y-3">
          <Button variant="secondary" onClick={() => connect.mutate()} disabled={connect.isPending}>
            {connect.isPending ? <LoaderCircle aria-hidden className="animate-spin" /> : <InstagramIcon />}
            {connect.isPending ? "Connecting…" : "Connect with Instagram"}
          </Button>
          {connect.isError && <p role="alert" className="text-sm text-danger">{connect.error.message}</p>}
          <p className="text-xs text-subtle">We never see or store your Instagram password.</p>
        </div>
      )}
    </GlassCard>
  );
}

function ProfileForm({ initial }: { initial: Profile | null }) {
  const router = useRouter();
  const updateProfile = useUpdateProfile();
  const form = useForm<Profile>({
    resolver: zodResolver(profileSchema),
    defaultValues: initial ?? { role: "creator", niche: "", language_mix: ["english", "roman_urdu"], tone: "", goals: "" },
  });
  const errors = form.formState.errors;

  function submit(profile: Profile) {
    updateProfile.mutate(profile, { onSuccess: () => router.push("/dashboard") });
  }

  return (
    <form noValidate onSubmit={form.handleSubmit(submit)} className="space-y-4">
      <GlassCard className="space-y-6">
        <fieldset>
          <legend className="mb-2 text-sm font-medium">I am a</legend>
          <div className="flex flex-wrap gap-2">
            <ChoiceChip type="radio" value="creator" label="Creator" {...form.register("role")} />
            <ChoiceChip type="radio" value="brand" label="Brand" {...form.register("role")} />
          </div>
        </fieldset>

        <Field label="Niche" htmlFor="niche" error={errors.niche?.message} hint="For example: Lahore street food, tech reviews, skincare">
          <Input id="niche" placeholder="Lahore street food" aria-invalid={Boolean(errors.niche)} {...form.register("niche")} />
        </Field>

        <fieldset>
          <legend className="mb-2 text-sm font-medium">Languages you post in</legend>
          <div className="flex flex-wrap gap-2">
            {LANGUAGE_OPTIONS.map((option) => (
              <ChoiceChip key={option.value} type="checkbox" value={option.value} label={option.label} {...form.register("language_mix")} />
            ))}
          </div>
          {errors.language_mix && <p role="alert" className="mt-1.5 text-xs text-danger">{errors.language_mix.message}</p>}
        </fieldset>

        <Field label="Tone" htmlFor="tone" error={errors.tone?.message}>
          <Select id="tone" aria-invalid={Boolean(errors.tone)} {...form.register("tone")}>
            <option value="">Choose a tone</option>
            {TONE_OPTIONS.map((tone) => (
              <option key={tone}>{tone}</option>
            ))}
          </Select>
        </Field>

        <Field label="Goals for the next 2 months" htmlFor="goals" error={errors.goals?.message}>
          <Textarea
            id="goals"
            placeholder="Grow to 20K, get more saves, land a food brand deal"
            aria-invalid={Boolean(errors.goals)}
            {...form.register("goals")}
          />
        </Field>
      </GlassCard>

      <InstagramConnect />

      <div className="flex flex-col-reverse items-stretch gap-3 sm:flex-row sm:items-center sm:justify-end">
        {updateProfile.isError && <p role="alert" className="text-sm text-danger">{updateProfile.error.message}</p>}
        <Button type="submit" size="lg" disabled={updateProfile.isPending}>
          {updateProfile.isPending ? <LoaderCircle aria-hidden className="animate-spin" /> : null}
          Save and go to dashboard
          <ArrowRight aria-hidden />
        </Button>
      </div>
    </form>
  );
}

export function OnboardingForm() {
  const me = useMe();
  if (me.isPending) return <GlassCard><LoadingBlock label="Loading your profile" /></GlassCard>;
  if (me.isError) return <GlassCard><ErrorState error={me.error} onRetry={() => void me.refetch()} /></GlassCard>;
  return <ProfileForm initial={me.data.profile} />;
}
