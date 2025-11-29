"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { useWatchlist, WatchlistItem } from "@/lib/hooks/useWatchlist"
import { drugsApi } from "@/lib/api"
import type { DrugSummary } from "@/lib/api/types"
import { ScoreBadge } from "@/components/data"
import { cn } from "@/lib/utils"

// Phase badge component
function PhaseBadge({ phase }: { phase: number | null }) {
  if (!phase) return <span className="text-pd-text-muted">-</span>

  const colors: Record<number, string> = {
    4: "bg-green-900/30 text-green-400 border-green-800",
    3: "bg-blue-900/30 text-blue-400 border-blue-800",
    2: "bg-yellow-900/30 text-yellow-400 border-yellow-800",
    1: "bg-orange-900/30 text-orange-400 border-orange-800",
  }

  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border",
        colors[phase] || "bg-pd-border text-pd-text-secondary"
      )}
    >
      Phase {phase}
    </span>
  )
}

// Drug card for watchlist
function WatchlistDrugCard({
  drug,
  onRemove,
}: {
  drug: DrugSummary
  onRemove: () => void
}) {
  return (
    <div className="pd-card p-4 relative group">
      <button
        onClick={(e) => {
          e.preventDefault()
          onRemove()
        }}
        className="absolute top-2 right-2 p-1.5 rounded-lg bg-pd-secondary border border-pd-border text-pd-text-muted hover:text-red-400 hover:border-red-400/50 opacity-0 group-hover:opacity-100 transition-all"
        title="Remove from watchlist"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>

      <Link href={`/drug/${drug.id}`} className="block">
        <div className="flex items-start justify-between mb-3">
          <div>
            <h3 className="font-medium text-pd-accent hover:underline mb-1">
              {drug.name}
            </h3>
            <div className="flex items-center gap-2">
              <PhaseBadge phase={drug.max_phase} />
              {drug.fda_approved && (
                <span className="text-xs px-2 py-0.5 rounded bg-pd-score-high/20 text-pd-score-high">
                  Approved
                </span>
              )}
            </div>
          </div>
          {drug.total_score !== null && (
            <ScoreBadge score={drug.total_score} size="lg" />
          )}
        </div>

        <div className="grid grid-cols-3 gap-2 mt-4">
          <div className="text-center">
            <div className="text-xs text-pd-text-muted mb-1">Bio</div>
            <div className="text-sm font-medium text-blue-400">
              {drug.bio_score?.toFixed(0) ?? "-"}
            </div>
          </div>
          <div className="text-center">
            <div className="text-xs text-pd-text-muted mb-1">Chem</div>
            <div className="text-sm font-medium text-purple-400">
              {drug.chem_score?.toFixed(0) ?? "-"}
            </div>
          </div>
          <div className="text-center">
            <div className="text-xs text-pd-text-muted mb-1">Tract</div>
            <div className="text-sm font-medium text-green-400">
              {drug.tractability_score?.toFixed(0) ?? "-"}
            </div>
          </div>
        </div>
      </Link>
    </div>
  )
}

// Empty state
function EmptyWatchlist() {
  return (
    <div className="pd-card p-12 text-center">
      <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-pd-secondary flex items-center justify-center">
        <svg
          className="w-8 h-8 text-pd-text-muted"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
          />
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
          />
        </svg>
      </div>
      <h3 className="text-lg font-medium text-pd-text-primary mb-2">
        Your watchlist is empty
      </h3>
      <p className="text-pd-text-muted mb-6 max-w-md mx-auto">
        Start tracking drugs and targets by clicking the Watch button on any
        asset page. Your watchlist is stored locally and will persist across
        sessions.
      </p>
      <div className="flex gap-4 justify-center">
        <Link
          href="/explore/drugs"
          className="px-4 py-2 rounded-lg bg-pd-accent text-white text-sm font-medium hover:bg-pd-accent/90 transition-colors"
        >
          Explore Drugs
        </Link>
        <Link
          href="/explore/targets"
          className="px-4 py-2 rounded-lg bg-pd-secondary border border-pd-border text-pd-text-secondary text-sm font-medium hover:border-pd-accent/50 transition-colors"
        >
          Explore Targets
        </Link>
      </div>
    </div>
  )
}

export default function WatchlistPage() {
  const { items, isLoaded, removeItem, clearAll, drugCount, targetCount } = useWatchlist()
  const [drugsData, setDrugsData] = useState<Record<string, DrugSummary>>({})
  const [loading, setLoading] = useState(true)

  // Fetch drug data for all watched drugs
  useEffect(() => {
    async function loadDrugs() {
      if (!isLoaded) return

      const drugItems = items.filter((i) => i.type === "drug")
      if (drugItems.length === 0) {
        setLoading(false)
        return
      }

      try {
        // Fetch all drugs and filter to watched ones
        const allDrugs = await drugsApi.list()
        const drugMap: Record<string, DrugSummary> = {}
        allDrugs.forEach((drug) => {
          drugMap[drug.id] = drug
        })
        setDrugsData(drugMap)
      } catch (err) {
        console.error("Failed to load drug data:", err)
      } finally {
        setLoading(false)
      }
    }

    loadDrugs()
  }, [items, isLoaded])

  const watchedDrugs = items
    .filter((i) => i.type === "drug")
    .map((item) => ({
      item,
      data: drugsData[item.id],
    }))
    .sort((a, b) => {
      // Sort by score descending
      const scoreA = a.data?.total_score ?? -1
      const scoreB = b.data?.total_score ?? -1
      return scoreB - scoreA
    })

  const watchedTargets = items.filter((i) => i.type === "target")

  if (!isLoaded) {
    return (
      <div className="min-h-screen bg-pd-primary flex items-center justify-center">
        <div className="text-pd-text-muted">Loading watchlist...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-pd-primary">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-start justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold text-pd-text-primary mb-2">
              Watchlist
            </h1>
            <p className="text-pd-text-secondary">
              Track your most important drugs and targets
            </p>
          </div>
          {items.length > 0 && (
            <button
              onClick={clearAll}
              className="px-4 py-2 rounded-lg text-sm font-medium bg-pd-secondary border border-pd-border text-pd-text-muted hover:text-red-400 hover:border-red-400/50 transition-colors"
            >
              Clear All
            </button>
          )}
        </div>

        {/* Stats */}
        {items.length > 0 && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <div className="pd-card p-4">
              <div className="text-pd-text-muted text-sm mb-1">Total Items</div>
              <div className="text-3xl font-bold text-pd-text-primary">
                {items.length}
              </div>
            </div>
            <div className="pd-card p-4">
              <div className="text-pd-text-muted text-sm mb-1">Drugs</div>
              <div className="text-3xl font-bold text-pd-accent">{drugCount}</div>
            </div>
            <div className="pd-card p-4">
              <div className="text-pd-text-muted text-sm mb-1">Targets</div>
              <div className="text-3xl font-bold text-blue-400">{targetCount}</div>
            </div>
            <div className="pd-card p-4">
              <div className="text-pd-text-muted text-sm mb-1">Avg Score</div>
              <div className="text-3xl font-bold text-green-400">
                {watchedDrugs.length > 0
                  ? (
                      watchedDrugs.reduce(
                        (sum, d) => sum + (d.data?.total_score ?? 0),
                        0
                      ) /
                      watchedDrugs.filter((d) => d.data?.total_score).length
                    ).toFixed(0)
                  : "-"}
              </div>
            </div>
          </div>
        )}

        {/* Empty State */}
        {items.length === 0 ? (
          <EmptyWatchlist />
        ) : (
          <div className="space-y-8">
            {/* Drugs Section */}
            {watchedDrugs.length > 0 && (
              <section>
                <h2 className="text-xl font-semibold text-pd-text-primary mb-4 flex items-center gap-2">
                  <svg
                    className="w-5 h-5 text-pd-accent"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"
                    />
                  </svg>
                  Drugs ({watchedDrugs.length})
                </h2>
                {loading ? (
                  <div className="text-pd-text-muted">Loading drug data...</div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                    {watchedDrugs.map(({ item, data }) =>
                      data ? (
                        <WatchlistDrugCard
                          key={item.id}
                          drug={data}
                          onRemove={() => removeItem(item.id, "drug")}
                        />
                      ) : (
                        <div
                          key={item.id}
                          className="pd-card p-4 text-pd-text-muted"
                        >
                          {item.name} (data unavailable)
                        </div>
                      )
                    )}
                  </div>
                )}
              </section>
            )}

            {/* Targets Section */}
            {watchedTargets.length > 0 && (
              <section>
                <h2 className="text-xl font-semibold text-pd-text-primary mb-4 flex items-center gap-2">
                  <svg
                    className="w-5 h-5 text-blue-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                    />
                  </svg>
                  Targets ({watchedTargets.length})
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                  {watchedTargets.map((item) => (
                    <div key={item.id} className="pd-card p-4 relative group">
                      <button
                        onClick={() => removeItem(item.id, "target")}
                        className="absolute top-2 right-2 p-1.5 rounded-lg bg-pd-secondary border border-pd-border text-pd-text-muted hover:text-red-400 hover:border-red-400/50 opacity-0 group-hover:opacity-100 transition-all"
                        title="Remove from watchlist"
                      >
                        <svg
                          className="w-4 h-4"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M6 18L18 6M6 6l12 12"
                          />
                        </svg>
                      </button>
                      <Link href={`/target/${item.id}`} className="block">
                        <h3 className="font-medium text-pd-accent hover:underline">
                          {item.name}
                        </h3>
                        <p className="text-xs text-pd-text-muted mt-1">
                          Added {new Date(item.addedAt).toLocaleDateString()}
                        </p>
                      </Link>
                    </div>
                  ))}
                </div>
              </section>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
