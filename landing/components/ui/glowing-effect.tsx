"use client"

import { cn } from "@/lib/utils"

interface GlowingEffectProps {
  children: React.ReactNode
  className?: string
  glowClassName?: string
}

export function GlowingEffect({ children, className, glowClassName }: GlowingEffectProps) {
  return (
    <div className={cn("relative group h-full", className)}>
      <div
        className={cn(
          "absolute inset-0 rounded-lg bg-gradient-to-r from-purple-600 to-blue-600 opacity-75 blur-xl group-hover:opacity-100 transition duration-500",
          glowClassName
        )}
      />
      <div className="relative h-full">{children}</div>
    </div>
  )
}
