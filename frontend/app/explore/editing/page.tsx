"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { editingAssetsApi } from "@/lib/api"
import type { EditingAssetSummary } from "@/lib/api/types"
import { DataTable, ScoreBadge } from "@/components/data"
import { cn } from "@/lib/utils"

// Status filter pills
const STATUS_FILTERS = [
  { key: "all", label: "All" },
  { key: "clinical", label: "Clinical" },
  { key: "preclinical", label: "Preclinical" },
]

// DBD Type filter pills
const DBD_FILTERS = [
  { key: "all", label: "All DBDs" },
  { key: "CRISPR_dCas9", label: "dCas9" },
  { key: "ZF", label: "Zinc Finger" },
  { key: "TALE", label: "TALE" },
]

// Effector Type filter pills
const EFFECTOR_FILTERS = [
  { key: "all", label: "All Effectors" },
  { key: "combo", label: "Combo" },
  { key: "writer", label: "Writer" },
  { key: "indirect_repressor", label: "Repressor" },
  { key: "eraser", label: "Eraser" },
]

// Mini Score Bar component for inline visualization
function ScoreBar({ label, value, color }: { label: string; value: number | null; color: string }) {
  const width = value ? Math.min(100, value) : 0
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-16 text-pd-text-muted">{label}</span>
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

// Score Breakdown for editing assets
function EditingScoreBreakdown({ asset }: { asset: EditingAssetSummary }) {
  return (
    <div className="space-y-1.5 min-w-[200px]">
      <ScoreBar label="Bio" value={asset.target_bio_score} color="bg-blue-500" />
      <ScoreBar label="Modality" value={asset.modality_score} color="bg-purple-500" />
      <ScoreBar label="Durability" value={asset.durability_score} color="bg-green-500" />
    </div>
  )
}

// Phase badge component
// eslint-disable-next-line @typescript-eslint/no-unused-vars
function PhaseBadge({ phase, status }: { phase: number; status: string }) {
  if (phase === 0) {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-800 text-gray-400 border border-gray-700">
        Preclinical
      </span>
    )
  }

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

// DBD Type badge
function DBDBadge({ dbd }: { dbd: string | null }) {
  if (!dbd) return <span className="text-pd-text-muted">-</span>

  const colors: Record<string, string> = {
    "CRISPR_dCas9": "bg-indigo-900/30 text-indigo-400 border-indigo-800",
    "ZF": "bg-cyan-900/30 text-cyan-400 border-cyan-800",
    "TALE": "bg-amber-900/30 text-amber-400 border-amber-800",
    "Base_Editor": "bg-pink-900/30 text-pink-400 border-pink-800",
  }

  const labels: Record<string, string> = {
    "CRISPR_dCas9": "dCas9",
    "ZF": "ZF",
    "TALE": "TALE",
    "Base_Editor": "Base Editor",
  }

  return (
    <span className={cn(
      "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border",
      colors[dbd] || "bg-pd-border text-pd-text-secondary"
    )}>
      {labels[dbd] || dbd}
    </span>
  )
}

// Effector domains display
function EffectorDomains({ domains }: { domains: string[] | null }) {
  if (!domains || domains.length === 0) return <span className="text-pd-text-muted">-</span>

  return (
    <div className="flex flex-wrap gap-1">
      {domains.slice(0, 3).map((domain, i) => (
        <span
          key={i}
          className="inline-flex items-center px-1.5 py-0.5 rounded text-xs bg-pd-secondary border border-pd-border text-pd-text-secondary"
        >
          {domain}
        </span>
      ))}
      {domains.length > 3 && (
        <span className="text-xs text-pd-text-muted">+{domains.length - 3}</span>
      )}
    </div>
  )
}

export default function EditingLandscapePage() {
  const [assets, setAssets] = useState<EditingAssetSummary[]>([])
  const [allAssets, setAllAssets] = useState<EditingAssetSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedStatus, setSelectedStatus] = useState("all")
  const [selectedDBD, setSelectedDBD] = useState("all")
  const [selectedEffector, setSelectedEffector] = useState("all")

  useEffect(() => {
    async function loadAssets() {
      try {
        setLoading(true)
        const data = await editingAssetsApi.list()
        setAllAssets(data)
      } catch (err) {
        setError("Failed to load editing assets")
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    loadAssets()
  }, [])

  // Apply filters
  useEffect(() => {
    let filtered = [...allAssets]

    // Status filter
    if (selectedStatus === "clinical") {
      filtered = filtered.filter(a => a.phase >= 1)
    } else if (selectedStatus === "preclinical") {
      filtered = filtered.filter(a => a.phase === 0)
    }

    // DBD filter
    if (selectedDBD !== "all") {
      filtered = filtered.filter(a => a.dbd_type === selectedDBD)
    }

    // Effector filter
    if (selectedEffector !== "all") {
      filtered = filtered.filter(a => a.effector_type === selectedEffector)
    }

    setAssets(filtered)
  }, [allAssets, selectedStatus, selectedDBD, selectedEffector])

  // Calculate stats
  const totalAssets = assets.length
  const clinicalAssets = assets.filter(a => a.phase >= 1).length
  const preclinicalAssets = assets.filter(a => a.phase === 0).length
  const avgScore =
    assets.length > 0
      ? assets.reduce((sum, a) => sum + (a.total_editing_score || 0), 0) / assets.filter(a => a.total_editing_score).length
      : 0

  // Sponsor distribution
  const sponsors = assets.reduce((acc, a) => {
    const sponsor = a.sponsor || "Unknown"
    acc[sponsor] = (acc[sponsor] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  // Table columns
  const columns = [
    {
      key: "name",
      label: "Program Name",
      sortable: true,
      render: (value: string, row: EditingAssetSummary) => (
        <Link
          href={`/editing/${row.id}`}
          className="font-medium text-pd-accent hover:underline"
        >
          {value}
        </Link>
      ),
    },
    {
      key: "sponsor",
      label: "Sponsor",
      sortable: true,
      render: (value: string | null) => (
        <span className="text-pd-text-secondary">{value || "-"}</span>
      ),
    },
    {
      key: "target_gene_symbol",
      label: "Target Gene",
      sortable: true,
      render: (value: string | null) => (
        <span className="font-mono text-pd-text-primary">{value || "-"}</span>
      ),
    },
    {
      key: "dbd_type",
      label: "DBD",
      sortable: true,
      render: (value: string | null) => <DBDBadge dbd={value} />,
    },
    {
      key: "effector_domains",
      label: "Effector Domains",
      sortable: false,
      render: (value: string[] | null) => <EffectorDomains domains={value} />,
    },
    {
      key: "phase",
      label: "Phase",
      sortable: true,
      render: (value: number, row: EditingAssetSummary) => (
        <PhaseBadge phase={value} status={row.status} />
      ),
    },
    {
      key: "scores",
      label: "Score Breakdown",
      sortable: false,
      render: (_: unknown, row: EditingAssetSummary) => <EditingScoreBreakdown asset={row} />,
    },
    {
      key: "total_editing_score",
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
          <div className="flex items-center gap-2 text-pd-text-muted text-sm mb-2">
            <Link href="/" className="hover:text-pd-accent">Home</Link>
            <span>/</span>
            <span className="text-pd-text-secondary">Epigenetic Editing</span>
          </div>
          <h1 className="text-4xl font-bold text-pd-text-primary mb-2">
            Epigenetic Editing Programs
          </h1>
          <p className="text-pd-text-secondary max-w-3xl">
            Next-generation therapeutics using locus-targeted epigenetic modifiers (CRISPR-dCas9, Zinc Fingers, TALEs)
            to precisely control gene expression through durable epigenetic marks.
          </p>
        </div>

        {/* Explanation Card */}
        <div className="pd-card p-6 mb-8 border-l-4 border-pd-accent">
          <h3 className="text-lg font-semibold text-pd-text-primary mb-2">What is Epigenetic Editing?</h3>
          <p className="text-pd-text-secondary text-sm mb-4">
            Unlike traditional gene editing (cutting DNA), epigenetic editors modify the chemical marks on DNA
            and histones to silence or activate genes <strong>without altering the DNA sequence</strong>. This enables:
          </p>
          <div className="grid md:grid-cols-3 gap-4 text-sm">
            <div className="bg-pd-secondary rounded-lg p-4">
              <div className="font-medium text-pd-text-primary mb-1">Reversibility</div>
              <div className="text-pd-text-muted">Effects can be temporary or permanent depending on effector choice</div>
            </div>
            <div className="bg-pd-secondary rounded-lg p-4">
              <div className="font-medium text-pd-text-primary mb-1">Precision</div>
              <div className="text-pd-text-muted">Target specific loci without DNA double-strand breaks</div>
            </div>
            <div className="bg-pd-secondary rounded-lg p-4">
              <div className="font-medium text-pd-text-primary mb-1">Durability</div>
              <div className="text-pd-text-muted">Combo effectors (KRAB+DNMT) create stable, heritable silencing</div>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-8">
          <div className="pd-card p-4">
            <div className="text-pd-text-muted text-sm mb-1">Total Programs</div>
            <div className="text-3xl font-bold text-pd-text-primary">{totalAssets}</div>
          </div>
          <div className="pd-card p-4">
            <div className="text-pd-text-muted text-sm mb-1">Clinical</div>
            <div className="text-3xl font-bold text-green-400">{clinicalAssets}</div>
          </div>
          <div className="pd-card p-4">
            <div className="text-pd-text-muted text-sm mb-1">Preclinical</div>
            <div className="text-3xl font-bold text-yellow-400">{preclinicalAssets}</div>
          </div>
          <div className="pd-card p-4">
            <div className="text-pd-text-muted text-sm mb-1">Avg Score</div>
            <div className="text-3xl font-bold text-pd-accent">
              {avgScore > 0 ? avgScore.toFixed(1) : "-"}
            </div>
          </div>
          <div className="pd-card p-4 col-span-2">
            <div className="text-pd-text-muted text-sm mb-2">Active Sponsors</div>
            <div className="flex flex-wrap gap-1">
              {Object.entries(sponsors).slice(0, 4).map(([name, count]) => (
                <span key={name} className="text-xs px-2 py-1 rounded bg-pd-secondary text-pd-text-secondary">
                  {name} ({count})
                </span>
              ))}
              {Object.keys(sponsors).length > 4 && (
                <span className="text-xs text-pd-text-muted">+{Object.keys(sponsors).length - 4} more</span>
              )}
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

            {/* DBD Filters */}
            <div>
              <div className="text-sm text-pd-text-muted mb-2">DNA Binding Domain</div>
              <div className="flex flex-wrap gap-2">
                {DBD_FILTERS.map((filter) => (
                  <button
                    key={filter.key}
                    onClick={() => setSelectedDBD(filter.key)}
                    className={cn(
                      "px-3 py-1.5 rounded-lg text-sm font-medium transition-all",
                      selectedDBD === filter.key
                        ? "bg-pd-accent text-white"
                        : "bg-pd-secondary border border-pd-border text-pd-text-secondary hover:border-pd-accent/50"
                    )}
                  >
                    {filter.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Effector Filters */}
            <div>
              <div className="text-sm text-pd-text-muted mb-2">Effector Type</div>
              <div className="flex flex-wrap gap-2">
                {EFFECTOR_FILTERS.map((filter) => (
                  <button
                    key={filter.key}
                    onClick={() => setSelectedEffector(filter.key)}
                    className={cn(
                      "px-3 py-1.5 rounded-lg text-sm font-medium transition-all",
                      selectedEffector === filter.key
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
            <div className="text-pd-text-muted">Loading editing programs...</div>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div className="text-red-400 mb-4">{error}</div>
              <p className="text-pd-text-muted text-sm">
                The editing assets table may not be set up yet. Run the schema migration first.
              </p>
            </div>
          </div>
        ) : assets.length === 0 ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div className="text-pd-text-muted mb-4">No editing programs found</div>
              <p className="text-pd-text-muted text-sm">
                {allAssets.length > 0
                  ? "Try adjusting your filters."
                  : "Run the seed ETL script to populate editing assets."}
              </p>
            </div>
          </div>
        ) : (
          <DataTable
            columns={columns}
            data={assets}
            sortable={true}
            defaultSort={{ key: "total_editing_score", direction: "desc" }}
            onRowClick={(row) => (window.location.href = `/editing/${row.id}`)}
            emptyMessage="No editing programs found"
          />
        )}
      </div>
    </div>
  )
}
