"use client";
import { cn } from "@/lib/utils";
import Link from "next/link";

const LogoIcon = () => (
  <div
    className={cn(
      "w-8 h-8 bg-black border border-neutral-400 rounded-full",
      "inline-flex items-center justify-center border border-solid", // Changed to flex for alignment
      "[border-image-source:linear-gradient(180deg,#1F1F1F_0%,#858585_100%),linear-gradient(180deg,#1F1F1F_0%,#858585_100%)]",
      "[background:linear-gradient(0deg,#151515,#151515),linear-gradient(180deg,rgba(21,21,21,0)_66.3%,rgba(255,255,255,0.5)_100%),linear-gradient(183.22deg,rgba(255,255,255,0.5)_2.62%,rgba(21,21,21,0)_52.03%)]",
      "shadow-[inset_0px_6px_8px_0px_#FAFAFA40,inset_0px_-6px_8px_0px_#FAFAFA40,0px_0px_0px_0px_#FAFAFA40,0px_0px_0px_0px_#FAFAFA40]",
      "text-white"
    )}
  ></div>
);

export const Logo = () => {
  return (
    <Link
      href="/"
      className="font-normal flex gap-2 items-center text-sm text-black px-2 py-1 shrink-0 relative z-20"
    >
      <LogoIcon />

      <span className="font-medium text-white">CryptGen</span>
    </Link>
  );
};
