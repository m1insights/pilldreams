"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { companiesApi } from "@/lib/api"
import type { CompanySummary } from "@/lib/api/types"
import { DataTable, ScoreBadge } from "@/components/data"
import { cn } from "@/lib/utils"

// Focus filter pills
const FOCUS_FILTERS = [
  { key: "all", label: "All Companies" },
  { key: "pure_play", label: "Pure Play Epi" },
  { key: "public", label: "Publicly Traded" },
]

// Epi Focus Badge
function EpiFocusBadge({ score, isPurePlay }: { score: number | null; isPurePlay: boolean }) {
  if (isPurePlay) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-purple-900/30 text-purple-400 border border-purple-800">
        <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
        Pure Play
      </span>
    )
  }

  if (!score) {
    return <span className="text-pd-text-muted">-</span>
  }

  const getColor = (s: number) => {
    if (s >= 80) return "bg-green-900/30 text-green-400 border-green-800"
    if (s >= 50) return "bg-blue-900/30 text-blue-400 border-blue-800"
    if (s >= 25) return "bg-yellow-900/30 text-yellow-400 border-yellow-800"
    return "bg-gray-800 text-gray-400 border-gray-700"
  }

  return (
    <span className={cn(
      "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border",
      getColor(score)
    )}>
      {score.toFixed(0)}% Focus
    </span>
  )
}

// Market Cap Display
function MarketCapDisplay({ cap, ticker }: { cap: number | null; ticker: string | null }) {
  const formatCap = (c: number) => {
    if (c >= 1e12) return `$${(c / 1e12).toFixed(1)}T`
    if (c >= 1e9) return `$${(c / 1e9).toFixed(1)}B`
    if (c >= 1e6) return `$${(c / 1e6).toFixed(0)}M`
    return `$${c.toLocaleString()}`
  }

  if (cap) {
    return <span className="font-mono text-pd-text-secondary">{formatCap(cap)}</span>
  }

  // No market cap data
  if (ticker) {
    // Has ticker but no market cap - likely data fetch failed
    return <span className="text-pd-text-muted italic">N/A</span>
  }

  // No ticker = private company
  return <span className="text-pd-text-muted italic">Private</span>
}

// Pipeline Count Badge
function PipelineBadge({ drugCount, editingCount }: { drugCount: number; editingCount: number }) {
  const total = drugCount + editingCount

  return (
    <div className="flex items-center gap-2">
      <span className="text-pd-text-primary font-medium">{total}</span>
      <span className="text-pd-text-muted text-xs">
        ({drugCount} drugs, {editingCount} editing)
      </span>
    </div>
  )
}

// Ticker Display
function TickerDisplay({ ticker, exchange }: { ticker: string | null; exchange: string | null }) {
  if (!ticker) {
    return <span className="text-pd-text-muted italic">Private</span>
  }

  return (
    <div className="flex items-center gap-1">
      <span className="font-mono font-medium text-pd-text-primary">{ticker}</span>
      {exchange && (
        <span className="text-xs text-pd-text-muted">({exchange})</span>
      )}
    </div>
  )
}

export default function CompaniesLandscapePage() {
  const [companies, setCompanies] = useState<CompanySummary[]>([])
  const [allCompanies, setAllCompanies] = useState<CompanySummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedFilter, setSelectedFilter] = useState("all")

  useEffect(() => {
    async function loadCompanies() {
      try {
        setLoading(true)
        const data = await companiesApi.list()
        setAllCompanies(data)
      } catch (err) {
        setError("Failed to load companies")
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    loadCompanies()
  }, [])

  // Apply filters
  useEffect(() => {
    let filtered = [...allCompanies]

    if (selectedFilter === "pure_play") {
      filtered = filtered.filter(c => c.is_pure_play_epi)
    } else if (selectedFilter === "public") {
      filtered = filtered.filter(c => c.ticker !== null)
    }

    setCompanies(filtered)
  }, [allCompanies, selectedFilter])

  // Calculate stats
  const totalCompanies = companies.length
  const purePlayCount = companies.filter(c => c.is_pure_play_epi).length
  const publicCount = companies.filter(c => c.ticker !== null).length
  const totalAssets = companies.reduce((sum, c) => sum + c.drug_count + c.editing_asset_count, 0)
  const avgFocus = companies.length > 0
    ? companies.reduce((sum, c) => sum + (c.epi_focus_score || 0), 0) / companies.filter(c => c.epi_focus_score).length
    : 0

  // Table columns
  const columns = [
    {
      key: "name",
      label: "Company",
      sortable: true,
      render: (value: string, row: CompanySummary) => (
        <Link
          href={`/company/${row.id}`}
          className="font-medium text-pd-accent hover:underline"
        >
          {value}
        </Link>
      ),
    },
    {
      key: "ticker",
      label: "Ticker",
      sortable: true,
      render: (value: string | null, row: CompanySummary) => (
        <TickerDisplay ticker={value} exchange={row.exchange} />
      ),
    },
    {
      key: "epi_focus_score",
      label: "Epi Focus",
      sortable: true,
      render: (value: number | null, row: CompanySummary) => (
        <EpiFocusBadge score={value} isPurePlay={row.is_pure_play_epi} />
      ),
    },
    {
      key: "drug_count",
      label: "Pipeline",
      sortable: true,
      render: (_: number, row: CompanySummary) => (
        <PipelineBadge drugCount={row.drug_count} editingCount={row.editing_asset_count} />
      ),
    },
    {
      key: "market_cap",
      label: "Market Cap",
      sortable: true,
      render: (value: number | null, row: CompanySummary) => <MarketCapDisplay cap={value} ticker={row.ticker} />,
    },
    {
      key: "avg_drug_score",
      label: "Avg Drug Score",
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
            <span className="text-pd-text-secondary">Companies</span>
          </div>
          <h1 className="text-4xl font-bold text-pd-text-primary mb-2">
            Epigenetics Companies
          </h1>
          <p className="text-pd-text-secondary max-w-3xl">
            Explore pharmaceutical and biotech companies developing epigenetic therapies,
            from pure-play pioneers to large pharma with epigenetic portfolios.
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
          <div className="pd-card p-4">
            <div className="text-pd-text-muted text-sm mb-1">Total Companies</div>
            <div className="text-3xl font-bold text-pd-text-primary">{totalCompanies}</div>
          </div>
          <div className="pd-card p-4">
            <div className="text-pd-text-muted text-sm mb-1">Pure Play Epi</div>
            <div className="text-3xl font-bold text-purple-400">{purePlayCount}</div>
          </div>
          <div className="pd-card p-4">
            <div className="text-pd-text-muted text-sm mb-1">Publicly Traded</div>
            <div className="text-3xl font-bold text-blue-400">{publicCount}</div>
          </div>
          <div className="pd-card p-4">
            <div className="text-pd-text-muted text-sm mb-1">Total Assets</div>
            <div className="text-3xl font-bold text-green-400">{totalAssets}</div>
          </div>
          <div className="pd-card p-4">
            <div className="text-pd-text-muted text-sm mb-1">Avg Epi Focus</div>
            <div className="text-3xl font-bold text-pd-accent">
              {avgFocus > 0 ? `${avgFocus.toFixed(0)}%` : "-"}
            </div>
          </div>
        </div>

        {/* Filter Section */}
        <div className="pd-card p-4 mb-6">
          <div className="flex flex-wrap gap-6">
            <div>
              <div className="text-sm text-pd-text-muted mb-2">Filter</div>
              <div className="flex flex-wrap gap-2">
                {FOCUS_FILTERS.map((filter) => (
                  <button
                    key={filter.key}
                    onClick={() => setSelectedFilter(filter.key)}
                    className={cn(
                      "px-3 py-1.5 rounded-lg text-sm font-medium transition-all",
                      selectedFilter === filter.key
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
            <div className="text-pd-text-muted">Loading companies...</div>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div className="text-red-400 mb-4">{error}</div>
              <p className="text-pd-text-muted text-sm">
                The companies table may not be set up yet. Run the schema migration and seed script first.
              </p>
            </div>
          </div>
        ) : companies.length === 0 ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div className="text-pd-text-muted mb-4">No companies found</div>
              <p className="text-pd-text-muted text-sm">
                {allCompanies.length > 0
                  ? "Try adjusting your filters."
                  : "Run the company seed ETL script to populate companies."}
              </p>
            </div>
          </div>
        ) : (
          <DataTable
            columns={columns}
            data={companies}
            sortable={true}
            defaultSort={{ key: "epi_focus_score", direction: "desc" }}
            onRowClick={(row) => (window.location.href = `/company/${row.id}`)}
            emptyMessage="No companies found"
          />
        )}
      </div>
    </div>
  )
}
