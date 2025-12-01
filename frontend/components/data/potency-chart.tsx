"use client"

import * as React from "react"
import { useState } from "react"
import { cn } from "@/lib/utils"

interface TargetActivity {
  target_chembl_id: string
  target_name: string
  target_type?: string
  best_pact: number | null
  median_pact?: number | null
  best_value_nm: number | null
  n_activities: number
  activity_types?: string[]
  is_primary_target?: boolean
}

interface PotencyChartProps {
  activities: TargetActivity[]
  maxPact?: number
  initialLimit?: number
  className?: string
}

function formatNanomolar(nm: number | null): string {
  if (nm === null) return "-"
  if (nm < 0.001) return `${(nm * 1000000).toFixed(1)} fM`
  if (nm < 1) return `${(nm * 1000).toFixed(1)} pM`
  if (nm < 1000) return `${nm.toFixed(1)} nM`
  return `${(nm / 1000).toFixed(1)} µM`
}

function getPotencyTier(pact: number | null): "excellent" | "good" | "moderate" | "weak" {
  if (pact === null) return "weak"
  if (pact >= 9) return "excellent"  // < 1 nM
  if (pact >= 7) return "good"       // 1-100 nM
  if (pact >= 5) return "moderate"   // 100 nM - 10 µM
  return "weak"
}

function getPotencyGradient(tier: "excellent" | "good" | "moderate" | "weak"): string {
  switch (tier) {
    case "excellent":
      return "bg-gradient-to-r from-blue-400 to-blue-300"
    case "good":
      return "bg-gradient-to-r from-slate-300 to-slate-400"
    case "moderate":
      return "bg-gradient-to-r from-slate-500 to-slate-600"
    case "weak":
      return "bg-gradient-to-r from-slate-700 to-slate-800"
  }
}

function truncateTargetName(name: string, maxLen: number = 35): string {
  if (name.length <= maxLen) return name
  return name.substring(0, maxLen - 3) + "..."
}

// Single activity row component
function ActivityRow({
  activity,
  idx,
  maxPact
}: {
  activity: TargetActivity
  idx: number
  maxPact: number
}) {
  const pact = activity.best_pact || 0
  const percentage = Math.min((pact / maxPact) * 100, 100)
  const tier = getPotencyTier(activity.best_pact)

  return (
    <div key={activity.target_chembl_id || idx} className="group">
      <div className="flex items-center gap-3">
        {/* Target name */}
        <div className="w-[180px] min-w-[180px]">
          <span
            className={cn(
              "text-sm truncate block",
              idx === 0 ? "text-blue-400 font-medium" : "text-pd-text-secondary"
            )}
            title={activity.target_name}
          >
            {truncateTargetName(activity.target_name)}
          </span>
          {activity.is_primary_target && (
            <span className="text-xs text-blue-500">(Primary)</span>
          )}
        </div>

        {/* Bar + values */}
        <div className="flex-1 flex items-center gap-3">
          {/* Bar */}
          <div className="flex-1 h-5 bg-pd-border rounded-sm relative overflow-hidden">
            <div
              className={cn(
                "h-full rounded-sm transition-all duration-500 ease-out",
                getPotencyGradient(tier)
              )}
              style={{ width: `${percentage}%` }}
            />
            {/* pXC50 value overlay */}
            {activity.best_pact && percentage > 25 && (
              <span className="absolute left-2 top-1/2 -translate-y-1/2 text-xs font-medium text-black/70">
                {activity.best_pact.toFixed(1)}
              </span>
            )}
          </div>

          {/* Values */}
          <span className="w-12 text-right text-sm font-mono text-pd-text-secondary">
            {activity.best_pact?.toFixed(1) || "-"}
          </span>
          <span className="w-16 text-right text-xs text-pd-text-muted">
            {formatNanomolar(activity.best_value_nm)}
          </span>
          <span className="w-6 text-right text-xs text-pd-text-muted">
            {activity.n_activities}
          </span>
        </div>
      </div>

      {/* Activity types tooltip on hover */}
      {activity.activity_types && activity.activity_types.length > 0 && (
        <div className="hidden group-hover:block text-xs text-pd-text-muted pl-[180px] pt-1">
          Types: {activity.activity_types.join(", ")}
        </div>
      )}
    </div>
  )
}

export function PotencyChart({
  activities,
  maxPact = 12,
  initialLimit = 10,
  className,
}: PotencyChartProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  if (!activities || activities.length === 0) {
    return (
      <div className={cn("text-pd-text-muted text-sm italic", className)}>
        No activity data available
      </div>
    )
  }

  // Sort by best_pact descending (highest potency first)
  const sorted = [...activities].sort((a, b) => (b.best_pact || 0) - (a.best_pact || 0))

  // Split into visible and hidden
  const hasMore = sorted.length > initialLimit
  const visibleActivities = hasMore && !isExpanded ? sorted.slice(0, initialLimit) : sorted
  const hiddenCount = sorted.length - initialLimit

  return (
    <div className={cn("space-y-3", className)}>
      {/* Header */}
      <div className="flex items-center justify-between text-xs text-pd-text-muted border-b border-pd-border-subtle pb-2">
        <span className="font-medium">Target</span>
        <div className="flex items-center gap-4">
          <span className="w-20 text-right">pXC50</span>
          <span className="w-20 text-right">IC50/Ki</span>
          <span className="w-8 text-right">#</span>
        </div>
      </div>

      {/* Activity bars */}
      <div className="space-y-2">
        {visibleActivities.map((activity, idx) => (
          <ActivityRow
            key={activity.target_chembl_id || idx}
            activity={activity}
            idx={idx}
            maxPact={maxPact}
          />
        ))}
      </div>

      {/* Expand/Collapse button */}
      {hasMore && (
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-2 text-sm text-pd-accent hover:text-pd-accent/80 transition-colors pt-1"
        >
          <svg
            className={cn(
              "w-4 h-4 transition-transform duration-200",
              isExpanded ? "rotate-180" : ""
            )}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
          {isExpanded ? (
            <span>Show less</span>
          ) : (
            <span>Show {hiddenCount} more target{hiddenCount > 1 ? "s" : ""}</span>
          )}
        </button>
      )}

      {/* Legend */}
      <div className="flex items-center gap-4 pt-2 border-t border-pd-border-subtle">
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-sm bg-gradient-to-r from-blue-400 to-blue-300" />
          <span className="text-xs text-pd-text-muted">{"<1 nM"}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-sm bg-gradient-to-r from-slate-300 to-slate-400" />
          <span className="text-xs text-pd-text-muted">1-100 nM</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-sm bg-gradient-to-r from-slate-500 to-slate-600" />
          <span className="text-xs text-pd-text-muted">100 nM-10 µM</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-sm bg-gradient-to-r from-slate-700 to-slate-800" />
          <span className="text-xs text-pd-text-muted">{">10 µM"}</span>
        </div>
      </div>
    </div>
  )
}

export { formatNanomolar, getPotencyTier }
