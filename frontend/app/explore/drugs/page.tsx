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

export default function DrugLandscapePage() {
  const [drugs, setDrugs] = useState<DrugSummary[]>([])
  const [allDrugs, setAllDrugs] = useState<DrugSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedStatus, setSelectedStatus] = useState("all")
  const [selectedPhase, setSelectedPhase] = useState("all")

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

  // Table columns
  const columns = [
    {
      key: "name",
      label: "Drug Name",
      sortable: true,
      render: (value: string, row: DrugSummary) => (
        <Link
          href={`/drug/${row.id}`}
          className="font-medium text-pd-accent hover:underline"
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

  return (
    <div className="min-h-screen bg-pd-primary">
      <div className="container mx-auto px-4 py-8">
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
          <DataTable
            columns={columns}
            data={drugs}
            sortable={true}
            defaultSort={{ key: "total_score", direction: "desc" }}
            onRowClick={(row) => (window.location.href = `/drug/${row.id}`)}
            emptyMessage="No drugs found"
          />
        )}
      </div>
    </div>
  )
}
