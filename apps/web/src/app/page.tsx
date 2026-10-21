import { AudienceSection } from "@/components/landing/audience-section";
import { CommentsSection } from "@/components/landing/comments-section";
import { DnaSection } from "@/components/landing/dna-section";
import { Hero } from "@/components/landing/hero";
import { NicheMarquee } from "@/components/landing/niche-marquee";
import { PilotSection } from "@/components/landing/pilot-section";
import { ScriptSection } from "@/components/landing/script-section";
import { SiteFooter } from "@/components/landing/site-footer";
import { SiteHeader } from "@/components/landing/site-header";
import { TrialSection } from "@/components/landing/trial-section";

export default function LandingPage() {
  return (
    <div className="relative overflow-x-clip">
      <div aria-hidden className="grain pointer-events-none fixed inset-0 z-[60]" />
      <SiteHeader />
      <main>
        <Hero />
        <NicheMarquee />
        <DnaSection />
        <ScriptSection />
        <TrialSection />
        <CommentsSection />
        <AudienceSection />
        <PilotSection />
      </main>
      <SiteFooter />
    </div>
  );
}
