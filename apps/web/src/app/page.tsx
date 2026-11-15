import { CommentsMarquee } from "@/components/landing/comments-marquee";
import { ComparisonSection } from "@/components/landing/comparison-section";
import { ExampleSection } from "@/components/landing/example-section";
import { FaqSection } from "@/components/landing/faq-section";
import { FeaturesGrid } from "@/components/landing/features-grid";
import { FormatsSection } from "@/components/landing/formats-section";
import { Hero } from "@/components/landing/hero";
import { HowItWorks } from "@/components/landing/how-it-works";
import { PilotSection } from "@/components/landing/pilot-section";
import { SiteFooter } from "@/components/landing/site-footer";
import { SiteHeader } from "@/components/landing/site-header";

export default function LandingPage() {
  return (
    <div className="relative overflow-x-clip bg-canvas">
      <SiteHeader />
      <main>
        <Hero />
        <FormatsSection />
        <HowItWorks />
        <ExampleSection />
        <CommentsMarquee />
        <PilotSection />
        <FeaturesGrid />
        <ComparisonSection />
        <FaqSection />
      </main>
      <SiteFooter />
    </div>
  );
}
