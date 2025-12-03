"use client";
import React, { useRef } from "react";
import {
  motion,
  useMotionTemplate,
  useScroll,
  useTransform,
} from "motion/react";
import { cn } from "@/lib/utils";
import Balancer from "react-wrap-balancer";
import Link from "next/link";
import { Button } from "./button";

export function Hero() {
  const parentRef = useRef<HTMLDivElement>(
    null
  ) as React.RefObject<HTMLDivElement>;

  const { scrollY } = useScroll({
    target: parentRef,
  });

  const translateY = useTransform(scrollY, [0, 100], [0, -20]);
  const scale = useTransform(scrollY, [0, 100], [1, 0.96]);

  const blurPx = useTransform(scrollY, [0, 150], [0, 5]);

  const filterBlurPx = useMotionTemplate`blur(${blurPx}px)`;

  const opacity = useTransform(scrollY, [0, 150], [1, 0]);

  return (
    <div
      ref={parentRef}
      className="relative flex min-h-screen flex-col items-center justify-center overflow-visible px-4 pt-20 md:px-8 md:pt-40 bg-black"
    >
      <div className="text-balance relative z-20 mx-auto mb-4 mt-4 max-w-4xl text-center text-4xl font-semibold tracking-tight text-neutral-300 md:text-7xl">
        <motion.h2
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          style={{
            y: translateY,
            scale,
            filter: filterBlurPx,
            opacity,
          }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className={cn(
            "inline-block bg-[radial-gradient(61.17%_178.53%_at_38.83%_-13.54%,#3B3B3B_0%,#888787_12.61%,#FFFFFF_50%,#888787_80%,#3B3B3B_100%)]",
            "bg-clip-text text-transparent pb-2"
          )}
        >
          <Balancer>Epigenetic Oncology Intelligence</Balancer>
        </motion.h2>
      </div>
      <motion.p
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, delay: 0.5 }}
        className="relative z-20 mx-auto mt-4 max-w-xl px-4 text-center text-base/6 text-gray-500  sm:text-base"
      >
        Mechanism-aware intelligence on epigenetic cancer programs. Score targets, drugs, and pipelines using biology, chemistry, and tractability data.
      </motion.p>
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, delay: 0.7 }}
        className="mb-8 mt-6 sm:mb-10 sm:mt-8 flex w-full flex-col items-center justify-center gap-4 px-4 sm:px-8 sm:flex-row md:mb-20"
      >
        <Button
          as={Link}
          href="#search"
          variant="primary"
          className="w-full sm:w-48 h-12 rounded-full flex items-center justify-center"
        >
          Explore Targets
        </Button>
      </motion.div>

    </div>
  );
}
