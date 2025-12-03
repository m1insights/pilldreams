"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { targetsApi } from "@/lib/api"
import type { TargetSummary } from "@/lib/api/types"
import { DataTable } from "@/components/data"
import { ScoreBadge } from "@/components/data"
import { cn } from "@/lib/utils"

// Target family filter pills
const TARGET_FAMILIES = [
  { key: "all", label: "All" },
  { key: "HDAC", label: "HDAC" },
  { key: "BET", label: "BET" },
  { key: "DNMT", label: "DNMT" },
  { key: "HMT", label: "HMT" },
  { key: "KDM", label: "KDM" },
  { key: "IDH", label: "IDH" },
  { key: "TET", label: "TET" },
  { key: "SIRT", label: "SIRT" },
]

export default function TargetLandscapePage() {
  const [targets, setTargets] = useState<TargetSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedFamily, setSelectedFamily] = useState("all")

  useEffect(() => {
    async function loadTargets() {
      try {
        setLoading(true)
        const params = selectedFamily !== "all" ? { family: selectedFamily } : undefined
        const data = await targetsApi.list(params)
        setTargets(data)
      } catch (err) {
        setError("Failed to load targets")
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    loadTargets()
  }, [selectedFamily])

  // Calculate stats for header
  const totalTargets = targets.length
  const totalAssets = targets.reduce((sum, t) => sum + (t.asset_count || 0), 0)
  const avgBioScore =
    targets.length > 0
      ? targets.reduce((sum, t) => sum + (t.avg_bio_score || 0), 0) / targets.length
      : 0

  // Table columns
  const columns = [
    {
      key: "symbol",
      label: "Target",
      sortable: true,
      render: (value: string, row: TargetSummary) => (
        <Link
          href={`/target/${row.id}`}
          className="font-medium text-pd-accent hover:underline"
        >
          {value}
        </Link>
      ),
    },
    {
      key: "name",
      label: "Full Name",
      sortable: true,
      className: "text-pd-text-secondary max-w-[200px] truncate",
    },
    {
      key: "family",
      label: "Family",
      sortable: true,
      render: (value: string) => (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-pd-border text-pd-text-secondary">
          {value}
        </span>
      ),
    },
    {
      key: "target_class",
      label: "Class",
      sortable: true,
      className: "text-pd-text-muted",
    },
    {
      key: "asset_count",
      label: "Assets",
      sortable: true,
      render: (value: number) => (
        <span className="font-mono text-pd-text-secondary">{value}</span>
      ),
    },
    {
      key: "avg_bio_score",
      label: "Avg BioScore",
      sortable: true,
      render: (value: number | null) =>
        value !== null ? <ScoreBadge score={value} size="sm" /> : <span className="text-pd-text-muted">-</span>,
    },
    {
      key: "avg_tractability_score",
      label: "Avg Tractability",
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
            Target Landscape
          </h1>
          <p className="text-pd-text-secondary">
            Explore {totalTargets} epigenetic targets across oncology
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="pd-card p-4">
            <div className="text-pd-text-muted text-sm mb-1">Total Targets</div>
            <div className="text-3xl font-bold text-pd-text-primary">{totalTargets}</div>
          </div>
          <div className="pd-card p-4">
            <div className="text-pd-text-muted text-sm mb-1">Total Pipeline Assets</div>
            <div className="text-3xl font-bold text-pd-text-primary">{totalAssets}</div>
          </div>
          <div className="pd-card p-4">
            <div className="text-pd-text-muted text-sm mb-1">Avg BioScore</div>
            <div className="text-3xl font-bold text-pd-text-primary">
              {avgBioScore > 0 ? avgBioScore.toFixed(1) : "-"}
            </div>
          </div>
        </div>

        {/* Family Filter Pills */}
        <div className="flex flex-wrap gap-2 mb-6">
          {TARGET_FAMILIES.map((fam) => (
            <button
              key={fam.key}
              onClick={() => setSelectedFamily(fam.key)}
              className={cn(
                "px-4 py-2 rounded-lg text-sm font-medium transition-all",
                selectedFamily === fam.key
                  ? "bg-pd-accent text-white"
                  : "bg-pd-card border border-pd-border text-pd-text-secondary hover:border-pd-accent/50 hover:text-pd-text-primary"
              )}
            >
              {fam.label}
            </button>
          ))}
        </div>

        {/* Content */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-pd-text-muted">Loading targets...</div>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-red-400">{error}</div>
          </div>
        ) : targets.length === 0 ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-pd-text-muted">No targets found</div>
          </div>
        ) : (
          <DataTable
            columns={columns}
            data={targets}
            sortable={true}
            defaultSort={{ key: "asset_count", direction: "desc" }}
            onRowClick={(row) => (window.location.href = `/target/${row.id}`)}
            emptyMessage="No targets found"
          />
        )}
      </div>
    </div>
  )
}
