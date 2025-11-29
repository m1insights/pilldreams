"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { drugsApi } from "@/lib/api"
import type { DrugSummary } from "@/lib/api/types"
import { DataTable } from "@/components/data"
import { ScoreBadge } from "@/components/data"
import { cn } from "@/lib/utils"

// Drug status filter pills
const STATUS_FILTERS = [
  { key: "all", label: "All" },
  { key: "approved", label: "FDA Approved" },
  { key: "pipeline", label: "Pipeline" },
]

// Phase filter pills
const PHASE_FILTERS = [
  { key: "all", label: "All Phases" },
  { key: "4", label: "Phase 4" },
  { key: "3", label: "Phase 3" },
  { key: "2", label: "Phase 2" },
  { key: "1", label: "Phase 1" },
]

// Mini Score Bar component for inline visualization
function ScoreBar({ label, value, color }: { label: string; value: number | null; color: string }) {
  const width = value ? Math.min(100, value) : 0
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-12 text-pd-text-muted">{label}</span>
      <div className="flex-1 h-2 bg-pd-border rounded-full overflow-hidden">
        <div
          className={cn("h-full rounded-full transition-all", color)}
          style={{ width: `${width}%` }}
        />
      </div>
      <span className="w-8 text-right text-pd-text-secondary">{value?.toFixed(0) ?? "-"}</span>
    </div>
  )
}

// Score Breakdown Mini Chart
function ScoreBreakdown({ drug }: { drug: DrugSummary }) {
  return (
    <div className="space-y-1.5 min-w-[180px]">
      <ScoreBar label="Bio" value={drug.bio_score} color="bg-blue-500" />
      <ScoreBar label="Chem" value={drug.chem_score} color="bg-purple-500" />
      <ScoreBar label="Tract" value={drug.tractability_score} color="bg-green-500" />
    </div>
  )
}

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
    <span className={cn(
      "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border",
      colors[phase] || "bg-pd-border text-pd-text-secondary"
    )}>
      Phase {phase}
    </span>
  )
}

// Comparison Panel Component
function ComparisonPanel({
  drugs,
  onRemove,
  onClear
}: {
  drugs: DrugSummary[];
  onRemove: (id: string) => void;
  onClear: () => void;
}) {
  if (drugs.length === 0) return null

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-pd-card border-t border-pd-border shadow-2xl z-50">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-pd-text-primary">
            Comparing {drugs.length} Drug{drugs.length > 1 ? 's' : ''}
          </h3>
          <button
            onClick={onClear}
            className="text-sm text-pd-text-muted hover:text-pd-accent"
          >
            Clear All
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {drugs.map((drug) => (
            <div key={drug.id} className="bg-pd-secondary rounded-lg p-4 relative">
              <button
                onClick={() => onRemove(drug.id)}
                className="absolute top-2 right-2 text-pd-text-muted hover:text-red-400"
              >
                ×
              </button>
              <Link href={`/drug/${drug.id}`} className="block">
                <h4 className="font-medium text-pd-accent hover:underline mb-1">{drug.name}</h4>
                <div className="flex items-center gap-2 mb-3">
                  <PhaseBadge phase={drug.max_phase} />
                  {drug.fda_approved && (
                    <span className="text-xs px-2 py-0.5 rounded bg-pd-score-high/20 text-pd-score-high">
                      Approved
                    </span>
                  )}
                </div>
              </Link>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-pd-text-muted">Bio</span>
                  <span className="text-blue-400 font-medium">{drug.bio_score?.toFixed(0) ?? "-"}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-pd-text-muted">Chem</span>
                  <span className="text-purple-400 font-medium">{drug.chem_score?.toFixed(0) ?? "-"}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-pd-text-muted">Tract</span>
                  <span className="text-green-400 font-medium">{drug.tractability_score?.toFixed(0) ?? "-"}</span>
                </div>
                <div className="flex justify-between text-sm pt-2 border-t border-pd-border">
                  <span className="text-pd-text-primary font-medium">Total</span>
                  <span className="text-pd-accent font-bold text-lg">{drug.total_score?.toFixed(0) ?? "-"}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default function DrugLandscapePage() {
  const [drugs, setDrugs] = useState<DrugSummary[]>([])
  const [allDrugs, setAllDrugs] = useState<DrugSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedStatus, setSelectedStatus] = useState("all")
  const [selectedPhase, setSelectedPhase] = useState("all")
  const [compareMode, setCompareMode] = useState(false)
  const [selectedDrugs, setSelectedDrugs] = useState<Set<string>>(new Set())

  // Toggle drug selection for comparison
  const toggleDrugSelection = (drugId: string) => {
    setSelectedDrugs(prev => {
      const next = new Set(prev)
      if (next.has(drugId)) {
        next.delete(drugId)
      } else if (next.size < 4) { // Max 4 drugs for comparison
        next.add(drugId)
      }
      return next
    })
  }

  // Get selected drug objects
  const comparedDrugs = allDrugs.filter(d => selectedDrugs.has(d.id))

  useEffect(() => {
    async function loadDrugs() {
      try {
        setLoading(true)
        const data = await drugsApi.list()

        // Sort by total_score descending (highest scores first)
        const sorted = [...data].sort((a, b) => {
          const scoreA = a.total_score ?? -1
          const scoreB = b.total_score ?? -1
          return scoreB - scoreA
        })

        setAllDrugs(sorted)
      } catch (err) {
        setError("Failed to load drugs")
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    loadDrugs()
  }, [])

  // Apply filters when status or phase changes
  useEffect(() => {
    let filtered = [...allDrugs]

    // Status filter
    if (selectedStatus === "approved") {
      filtered = filtered.filter(d => d.fda_approved)
    } else if (selectedStatus === "pipeline") {
      filtered = filtered.filter(d => !d.fda_approved)
    }

    // Phase filter
    if (selectedPhase !== "all") {
      const phase = parseInt(selectedPhase)
      filtered = filtered.filter(d => d.max_phase === phase)
    }

    setDrugs(filtered)
  }, [allDrugs, selectedStatus, selectedPhase])

  // Calculate stats for header (from filtered data)
  const totalDrugs = drugs.length
  const approvedDrugs = drugs.filter(d => d.fda_approved).length
  const pipelineDrugs = drugs.filter(d => !d.fda_approved).length
  const avgScore =
    drugs.length > 0
      ? drugs.reduce((sum, d) => sum + (d.total_score || 0), 0) / drugs.filter(d => d.total_score).length
      : 0

  // Phase distribution (from filtered data)
  const phaseDistribution = drugs.reduce((acc, d) => {
    const phase = d.max_phase || 0
    acc[phase] = (acc[phase] || 0) + 1
    return acc
  }, {} as Record<number, number>)

  // Table columns - conditionally include selection column
  const baseColumns = [
    {
      key: "name",
      label: "Drug Name",
      sortable: true,
      render: (value: string, row: DrugSummary) => (
        <Link
          href={`/drug/${row.id}`}
          className="font-medium text-pd-accent hover:underline"
          onClick={(e) => {
            if (compareMode) {
              e.preventDefault()
              toggleDrugSelection(row.id)
            }
          }}
        >
          {value}
        </Link>
      ),
    },
    {
      key: "max_phase",
      label: "Phase",
      sortable: true,
      render: (value: number | null) => <PhaseBadge phase={value} />,
    },
    {
      key: "drug_type",
      label: "Type",
      sortable: true,
      render: (value: string | null) => (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-pd-border text-pd-text-secondary">
          {value || "Unknown"}
        </span>
      ),
    },
    {
      key: "scores",
      label: "Score Breakdown",
      sortable: false,
      render: (_: unknown, row: DrugSummary) => <ScoreBreakdown drug={row} />,
    },
    {
      key: "total_score",
      label: "Total Score",
      sortable: true,
      render: (value: number | null) =>
        value !== null ? <ScoreBadge score={value} size="sm" /> : <span className="text-pd-text-muted">-</span>,
    },
  ]

  // Add selection column when in compare mode
  const selectionColumn = {
    key: "select",
    label: "",
    sortable: false,
    render: (_: unknown, row: DrugSummary) => (
      <button
        onClick={(e) => {
          e.stopPropagation()
          toggleDrugSelection(row.id)
        }}
        className={cn(
          "w-5 h-5 rounded border-2 flex items-center justify-center transition-all",
          selectedDrugs.has(row.id)
            ? "bg-pd-accent border-pd-accent text-white"
            : "border-pd-border hover:border-pd-accent/50"
        )}
      >
        {selectedDrugs.has(row.id) && (
          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        )}
      </button>
    ),
  }

  const columns = compareMode ? [selectionColumn, ...baseColumns] : baseColumns

  return (
    <div className="min-h-screen bg-pd-primary">
      <div className={cn(
        "container mx-auto px-4 py-8",
        comparedDrugs.length > 0 && "pb-80"
      )}>
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-pd-text-primary mb-2">
            Drug Pipeline
          </h1>
          <p className="text-pd-text-secondary">
            Explore {allDrugs.length} epigenetic drugs ranked by TotalScore
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-8">
          <div className="pd-card p-4">
            <div className="text-pd-text-muted text-sm mb-1">Showing</div>
            <div className="text-3xl font-bold text-pd-text-primary">{totalDrugs}</div>
          </div>
          <div className="pd-card p-4">
            <div className="text-pd-text-muted text-sm mb-1">FDA Approved</div>
            <div className="text-3xl font-bold text-green-400">{approvedDrugs}</div>
          </div>
          <div className="pd-card p-4">
            <div className="text-pd-text-muted text-sm mb-1">Pipeline</div>
            <div className="text-3xl font-bold text-yellow-400">{pipelineDrugs}</div>
          </div>
          <div className="pd-card p-4">
            <div className="text-pd-text-muted text-sm mb-1">Avg Score</div>
            <div className="text-3xl font-bold text-pd-accent">
              {avgScore > 0 ? avgScore.toFixed(1) : "-"}
            </div>
          </div>
          <div className="pd-card p-4 col-span-2">
            <div className="text-pd-text-muted text-sm mb-2">Phase Distribution</div>
            <div className="flex gap-2">
              {[4, 3, 2, 1].map(phase => (
                <div key={phase} className="flex-1 text-center">
                  <div className="text-lg font-bold text-pd-text-primary">
                    {phaseDistribution[phase] || 0}
                  </div>
                  <div className="text-xs text-pd-text-muted">P{phase}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Filter Section */}
        <div className="pd-card p-4 mb-6">
          <div className="flex flex-wrap items-end justify-between gap-6">
            <div className="flex flex-wrap gap-6">
              {/* Status Filters */}
              <div>
                <div className="text-sm text-pd-text-muted mb-2">Status</div>
                <div className="flex flex-wrap gap-2">
                  {STATUS_FILTERS.map((filter) => (
                    <button
                      key={filter.key}
                      onClick={() => setSelectedStatus(filter.key)}
                      className={cn(
                        "px-3 py-1.5 rounded-lg text-sm font-medium transition-all",
                        selectedStatus === filter.key
                          ? "bg-pd-accent text-white"
                          : "bg-pd-secondary border border-pd-border text-pd-text-secondary hover:border-pd-accent/50"
                      )}
                    >
                      {filter.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Phase Filters */}
              <div>
                <div className="text-sm text-pd-text-muted mb-2">Clinical Phase</div>
                <div className="flex flex-wrap gap-2">
                  {PHASE_FILTERS.map((filter) => (
                    <button
                      key={filter.key}
                      onClick={() => setSelectedPhase(filter.key)}
                      className={cn(
                        "px-3 py-1.5 rounded-lg text-sm font-medium transition-all",
                        selectedPhase === filter.key
                          ? "bg-pd-accent text-white"
                          : "bg-pd-secondary border border-pd-border text-pd-text-secondary hover:border-pd-accent/50"
                      )}
                    >
                      {filter.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Compare Toggle */}
            <div>
              <button
                onClick={() => {
                  setCompareMode(!compareMode)
                  if (compareMode) {
                    setSelectedDrugs(new Set())
                  }
                }}
                className={cn(
                  "px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2",
                  compareMode
                    ? "bg-pd-accent text-white"
                    : "bg-pd-secondary border border-pd-border text-pd-text-secondary hover:border-pd-accent/50"
                )}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                {compareMode ? `Comparing (${selectedDrugs.size}/4)` : "Compare"}
              </button>
            </div>
          </div>
        </div>

        {/* Content */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-pd-text-muted">Loading drugs...</div>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-red-400">{error}</div>
          </div>
        ) : drugs.length === 0 ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-pd-text-muted">No drugs found matching filters</div>
          </div>
        ) : (
          <>
            {compareMode && (
              <div className="mb-4 px-4 py-3 bg-pd-accent/10 border border-pd-accent/30 rounded-lg">
                <p className="text-sm text-pd-accent">
                  Click on drugs to select them for comparison (max 4). Selected drugs will appear in the comparison panel below.
                </p>
              </div>
            )}
            <DataTable
              columns={columns}
              data={drugs}
              sortable={true}
              defaultSort={{ key: "total_score", direction: "desc" }}
              onRowClick={compareMode ? (row) => toggleDrugSelection(row.id) : (row) => (window.location.href = `/drug/${row.id}`)}
              emptyMessage="No drugs found"
            />
          </>
        )}
      </div>

      {/* Comparison Panel */}
      <ComparisonPanel
        drugs={comparedDrugs}
        onRemove={(id) => {
          setSelectedDrugs(prev => {
            const next = new Set(prev)
            next.delete(id)
            return next
          })
        }}
        onClear={() => setSelectedDrugs(new Set())}
      />
    </div>
  )
}
