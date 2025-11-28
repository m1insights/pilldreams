import { Search } from "@/components/search";
import { Hero } from "@/components/hero";
import CTA from "@/components/cta";
import { FrequentlyAskedQuestions } from "@/components/faq";
import { Features } from "@/components/features";
import { SpotlightLogoCloud } from "@/components/logos-cloud";
import { Pricing } from "@/components/pricing";
import { Testimonials } from "@/components/testimonials";

export default function Home() {
  return (
    <div className="min-h-screen bg-background">
      <Hero />
      <div id="search" className="container mx-auto py-12 relative z-10">
        <h2 className="text-3xl font-bold text-center mb-8">Epigenetics Oncology Intelligence</h2>
        <Search />
      </div>
      <SpotlightLogoCloud />
      <Features />
      <Testimonials />
      <Pricing />
      <FrequentlyAskedQuestions />
      <CTA />
    </div>
  );
}

