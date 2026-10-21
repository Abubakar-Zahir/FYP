import type { Metadata } from "next";

import { OnboardingForm } from "@/components/onboarding/onboarding-form";
import { PageHeader } from "@/components/ui/page-header";

export const metadata: Metadata = { title: "Set up · Reelmind" };

export default function OnboardingPage() {
  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader
        eyebrow="Step 1 of 1"
        title="Tell us about your content"
        description="This shapes your scripts, hook scores and comment insights. You can change it later."
      />
      <OnboardingForm />
    </div>
  );
}
