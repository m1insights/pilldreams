"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

interface ScoreBreakdownItem {
  label: string
  value: number
  weight: number
}

interface ScoreGaugeProps {
  score: number
  max?: number
  breakdown?: ScoreBreakdownItem[]
  showBreakdown?: boolean
  size?: "sm" | "md" | "lg"
  className?: string
}

function getScoreTier(score: number): "high" | "medium" | "low" {
  if (score >= 70) return "high"
  if (score >= 40) return "medium"
  return "low"
}

function getScoreGradient(tier: "high" | "medium" | "low"): string {
  switch (tier) {
    case "high":
      return "bg-gradient-to-r from-[#e2e8f0] to-[#94a3b8]"
    case "medium":
      return "bg-gradient-to-r from-[#94a3b8] to-[#64748b]"
    case "low":
      return "bg-gradient-to-r from-[#64748b] to-[#475569]"
  }
}

function getScoreTextColor(tier: "high" | "medium" | "low"): string {
  switch (tier) {
    case "high":
      return "text-slate-200"
    case "medium":
      return "text-slate-400"
    case "low":
      return "text-slate-500"
  }
}

export function ScoreGauge({
  score,
  max = 100,
  breakdown,
  showBreakdown = false,
  size = "md",
  className,
}: ScoreGaugeProps) {
  const percentage = Math.min((score / max) * 100, 100)
  const tier = getScoreTier(score)

  const sizeClasses = {
    sm: { bar: "h-1.5", text: "text-lg", breakdown: "text-xs" },
    md: { bar: "h-2", text: "text-2xl", breakdown: "text-sm" },
    lg: { bar: "h-3", text: "text-3xl", breakdown: "text-base" },
  }

  const sizes = sizeClasses[size]

  return (
    <div className={cn("space-y-3", className)}>
      {/* Main score display */}
      <div className="flex items-center gap-4">
        <span className={cn("font-bold tabular-nums", sizes.text, getScoreTextColor(tier))}>
          {Math.round(score)}
        </span>
        <div className="flex-1">
          <div className={cn("w-full rounded-full bg-pd-border", sizes.bar)}>
            <div
              className={cn(
                "rounded-full transition-all duration-500 ease-out",
                sizes.bar,
                getScoreGradient(tier)
              )}
              style={{ width: `${percentage}%` }}
            />
          </div>
        </div>
        <span className="text-pd-text-muted text-sm">/{max}</span>
      </div>

      {/* Breakdown section */}
      {showBreakdown && breakdown && breakdown.length > 0 && (
        <div className="space-y-2 pl-4 border-l-2 border-pd-border-subtle">
          {breakdown.map((item) => {
            const itemTier = getScoreTier(item.value)
            const itemPercentage = Math.min((item.value / max) * 100, 100)

            return (
              <div key={item.label} className="space-y-1">
                <div className="flex justify-between items-center">
                  <span className={cn("text-pd-text-secondary", sizes.breakdown)}>
                    {item.label}
                    <span className="text-pd-text-muted ml-1">({item.weight}%)</span>
                  </span>
                  <span className={cn("font-medium tabular-nums", sizes.breakdown, getScoreTextColor(itemTier))}>
                    {Math.round(item.value)}
                  </span>
                </div>
                <div className="w-full h-1 rounded-full bg-pd-border">
                  <div
                    className={cn(
                      "h-full rounded-full transition-all duration-500 ease-out",
                      getScoreGradient(itemTier)
                    )}
                    style={{ width: `${itemPercentage}%` }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

export { getScoreTier, getScoreGradient, getScoreTextColor }
