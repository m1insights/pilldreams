"use client";
import React from "react";
import { cn } from "@/lib/utils";
import Balancer from "react-wrap-balancer";

export function SpotlightLogoCloud() {
  const dataSources = [
    { name: "Open Targets", abbr: "OT" },
    { name: "ChEMBL", abbr: "ChEMBL" },
    { name: "UniProt", abbr: "UniProt" },
    { name: "ClinicalTrials.gov", abbr: "CT.gov" },
  ];

  return (
    <div className="relative w-full py-12 md:py-20 overflow-hidden">
      <div className="text-balance relative z-20 mx-auto mb-4 max-w-4xl text-center text-lg font-semibold tracking-tight text-neutral-300 md:text-3xl px-4">
        <Balancer>
          <h2
            className={cn(
              "inline-block bg-[radial-gradient(61.17%_178.53%_at_38.83%_-13.54%,#3B3B3B_0%,#888787_12.61%,#FFFFFF_50%,#888787_80%,#3B3B3B_100%)]",
              "bg-clip-text text-transparent"
            )}
          >
            Powered by Trusted Data Sources
          </h2>
        </Balancer>
      </div>
      <p className="text-center max-w-lg mx-auto text-base md:text-lg font-sans text-neutral-500 mt-4 mb-8 md:mb-10 px-4">
        Aggregating intelligence from the gold standard databases in drug discovery and genomics
      </p>
      <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-4 gap-6 md:gap-10 w-full max-w-3xl mx-auto relative px-4">
        {dataSources.map((source, idx) => (
          <div
            key={source.name + idx}
            className="flex flex-col items-center justify-center p-4 rounded-lg bg-neutral-900/50 border border-neutral-800"
          >
            <span className="text-2xl font-bold text-white mb-1">{source.abbr}</span>
            <span className="text-xs text-neutral-500">{source.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
