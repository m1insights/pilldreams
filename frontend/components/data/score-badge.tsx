"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { getScoreTier, getScoreGradient, getScoreTextColor } from "./score-gauge"

interface ScoreBadgeProps {
  score: number
  size?: "xs" | "sm" | "md" | "lg"
  showBar?: boolean
  className?: string
}

export function ScoreBadge({
  score,
  size = "md",
  showBar = false,
  className,
}: ScoreBadgeProps) {
  const tier = getScoreTier(score)

  const sizeClasses = {
    xs: "text-xs px-1.5 py-0.5 min-w-[28px]",
    sm: "text-sm px-2 py-0.5 min-w-[32px]",
    md: "text-base px-2.5 py-1 min-w-[40px]",
    lg: "text-lg px-3 py-1.5 min-w-[48px]",
  }

  const barSizes = {
    xs: "h-0.5 w-8",
    sm: "h-1 w-10",
    md: "h-1 w-12",
    lg: "h-1.5 w-16",
  }

  return (
    <div className={cn("inline-flex flex-col items-center gap-1", className)}>
      <span
        className={cn(
          "inline-flex items-center justify-center rounded font-semibold tabular-nums",
          "bg-pd-card border border-pd-border",
          sizeClasses[size],
          getScoreTextColor(tier)
        )}
      >
        {Math.round(score)}
      </span>
      {showBar && (
        <div className={cn("rounded-full bg-pd-border", barSizes[size])}>
          <div
            className={cn(
              "h-full rounded-full transition-all duration-300",
              getScoreGradient(tier)
            )}
            style={{ width: `${Math.min(score, 100)}%` }}
          />
        </div>
      )}
    </div>
  )
}
