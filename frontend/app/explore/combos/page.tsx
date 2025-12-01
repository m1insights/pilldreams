"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { combosApi } from "@/lib/api"
import type { ComboSummary, ComboLabel } from "@/lib/api/types"
import { DataTable } from "@/components/data"
import { cn } from "@/lib/utils"

// Combo label display names and colors
const COMBO_LABEL_CONFIG: Record<string, { label: string; color: string; description: string }> = {
  "epi+IO": {
    label: "Epi + IO",
    color: "bg-blue-900/30 text-blue-400 border-blue-800",
    description: "HDAC/BET inhibitors + checkpoint inhibitors (PD-1, PD-L1, CTLA-4)"
  },
  "epi+KRAS": {
    label: "Epi + KRAS",
    color: "bg-orange-900/30 text-orange-400 border-orange-800",
    description: "Epigenetic drugs + KRAS inhibitors (G12C, G12D)"
  },
  "epi+radiation": {
    label: "Epi + Radiation",
    color: "bg-purple-900/30 text-purple-400 border-purple-800",
    description: "HDAC inhibitors + radiotherapy (radiosensitization)"
  },
  "epi+Venetoclax": {
    label: "Epi + BCL-2",
    color: "bg-green-900/30 text-green-400 border-green-800",
    description: "EZH2/IDH inhibitors + Venetoclax (BCL-2 inhibitor)"
  },
  "epi+chemotherapy": {
    label: "Epi + Chemo",
    color: "bg-pink-900/30 text-pink-400 border-pink-800",
    description: "DNMTi + cytarabine and other chemotherapy agents"
  },
}

// Phase badge component
function PhaseBadge({ phase }: { phase: number | null }) {
  if (phase === null || phase === undefined) {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-800 text-gray-400 border border-gray-700">
        Unknown
      </span>
    )
  }
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

// Combo label badge
function ComboLabelBadge({ comboLabel }: { comboLabel: string }) {
  const config = COMBO_LABEL_CONFIG[comboLabel] || {
    label: comboLabel,
    color: "bg-pd-border text-pd-text-secondary"
  }

  return (
    <span className={cn(
      "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border",
      config.color
    )}>
      {config.label}
    </span>
  )
}

// NCT link component
function NCTLink({ nctId }: { nctId: string | null }) {
  if (!nctId) return <span className="text-pd-text-muted">-</span>

  return (
    <a
      href={`https://clinicaltrials.gov/study/${nctId}`}
      target="_blank"
      rel="noopener noreferrer"
      className="text-pd-accent hover:underline font-mono text-xs"
    >
      {nctId}
    </a>
  )
}

// Source badge
function SourceBadge({ source }: { source: string | null }) {
  if (!source) return <span className="text-pd-text-muted">-</span>

  const colors: Record<string, string> = {
    "ClinicalTrials": "bg-blue-900/20 text-blue-400",
    "OpenTargets": "bg-green-900/20 text-green-400",
    "PubMed": "bg-purple-900/20 text-purple-400",
    "Review": "bg-yellow-900/20 text-yellow-400",
    "CompanyPR": "bg-pink-900/20 text-pink-400",
  }

  return (
    <span className={cn(
      "inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium",
      colors[source] || "bg-pd-secondary text-pd-text-muted"
    )}>
      {source}
    </span>
  )
}

export default function CombosLandscapePage() {
  const [combos, setCombos] = useState<ComboSummary[]>([])
  const [allCombos, setAllCombos] = useState<ComboSummary[]>([])
  const [labels, setLabels] = useState<ComboLabel[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedLabel, setSelectedLabel] = useState("all")
  const [selectedPhase, setSelectedPhase] = useState("all")

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true)
        const [combosData, labelsData] = await Promise.all([
          combosApi.list(),
          combosApi.getLabels()
        ])
        setAllCombos(combosData)
        setLabels(labelsData.labels || [])
      } catch (err) {
        setError("Failed to load combination therapies")
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [])

  // Apply filters
  useEffect(() => {
    let filtered = [...allCombos]

    // Label filter
    if (selectedLabel !== "all") {
      filtered = filtered.filter(c => c.combo_label === selectedLabel)
    }

    // Phase filter
    if (selectedPhase !== "all") {
      const phase = parseInt(selectedPhase)
      if (phase === 0) {
        filtered = filtered.filter(c => c.max_phase === 0 || c.max_phase === null)
      } else {
        filtered = filtered.filter(c => c.max_phase === phase)
      }
    }

    setCombos(filtered)
  }, [allCombos, selectedLabel, selectedPhase])

  // Calculate stats
  const totalCombos = combos.length
  const clinicalCombos = combos.filter(c => c.max_phase && c.max_phase >= 1).length
  const phase3Plus = combos.filter(c => c.max_phase && c.max_phase >= 3).length
  const ioCount = combos.filter(c => c.combo_label === "epi+IO").length

  // Partner class distribution
  const partnerClasses = combos.reduce((acc, c) => {
    const pc = c.partner_class || "Unknown"
    acc[pc] = (acc[pc] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  // Table columns
  const columns = [
    {
      key: "combo_label",
      label: "Combo Type",
      sortable: true,
      render: (value: string) => <ComboLabelBadge comboLabel={value} />,
    },
    {
      key: "epi_drug_name",
      label: "Epigenetic Drug",
      sortable: true,
      render: (value: string, row: ComboSummary) => (
        <Link
          href={`/drug/${row.epi_drug_id}`}
          className="font-medium text-pd-accent hover:underline"
        >
          {value}
        </Link>
      ),
    },
    {
      key: "partner_drug_name",
      label: "Partner Drug",
      sortable: true,
      render: (value: string | null) => (
        <span className="text-pd-text-primary">{value || "-"}</span>
      ),
    },
    {
      key: "partner_class",
      label: "Partner Class",
      sortable: true,
      render: (value: string | null) => (
        <span className="text-pd-text-secondary text-sm">{value || "-"}</span>
      ),
    },
    {
      key: "indication_name",
      label: "Indication",
      sortable: true,
      render: (value: string, row: ComboSummary) => (
        <Link
          href={`/indication/${row.indication_id}`}
          className="text-pd-text-secondary hover:text-pd-accent"
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
      key: "nct_id",
      label: "NCT ID",
      sortable: false,
      render: (value: string | null) => <NCTLink nctId={value} />,
    },
    {
      key: "source",
      label: "Source",
      sortable: true,
      render: (value: string | null) => <SourceBadge source={value} />,
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
            <span className="text-pd-text-secondary">Combination Therapies</span>
          </div>
          <h1 className="text-4xl font-bold text-pd-text-primary mb-2">
            Combination Therapies
          </h1>
          <p className="text-pd-text-secondary max-w-3xl">
            Epigenetic drugs paired with checkpoint inhibitors, KRAS inhibitors, radiation, and other modalities
            to enhance therapeutic efficacy and overcome resistance mechanisms.
          </p>
        </div>

        {/* Explanation Card */}
        <div className="pd-card p-6 mb-8 border-l-4 border-pd-accent">
          <h3 className="text-lg font-semibold text-pd-text-primary mb-2">Why Combinations?</h3>
          <p className="text-pd-text-secondary text-sm mb-4">
            Epigenetic drugs can <strong>prime</strong> tumors for other therapies by modulating the tumor microenvironment,
            enhancing antigen presentation, or sensitizing cells to DNA damage. Common combination strategies include:
          </p>
          <div className="grid md:grid-cols-3 gap-4 text-sm">
            <div className="bg-pd-secondary rounded-lg p-4">
              <div className="font-medium text-blue-400 mb-1">Epi + Immunotherapy</div>
              <div className="text-pd-text-muted">HDACi/BETi increase MHC expression and reduce T-cell exhaustion</div>
            </div>
            <div className="bg-pd-secondary rounded-lg p-4">
              <div className="font-medium text-orange-400 mb-1">Epi + Targeted Therapy</div>
              <div className="text-pd-text-muted">Overcome resistance to KRAS inhibitors via epigenetic reprogramming</div>
            </div>
            <div className="bg-pd-secondary rounded-lg p-4">
              <div className="font-medium text-purple-400 mb-1">Epi + Radiation</div>
              <div className="text-pd-text-muted">HDACi radiosensitize tumors by inhibiting DNA repair pathways</div>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4 mb-8">
          <div className="pd-card p-4">
            <div className="text-pd-text-muted text-sm mb-1">Total Combos</div>
            <div className="text-3xl font-bold text-pd-text-primary">{totalCombos}</div>
          </div>
          <div className="pd-card p-4">
            <div className="text-pd-text-muted text-sm mb-1">Clinical Stage</div>
            <div className="text-3xl font-bold text-green-400">{clinicalCombos}</div>
          </div>
          <div className="pd-card p-4">
            <div className="text-pd-text-muted text-sm mb-1">Phase 3+</div>
            <div className="text-3xl font-bold text-blue-400">{phase3Plus}</div>
          </div>
          <div className="pd-card p-4">
            <div className="text-pd-text-muted text-sm mb-1">Epi + IO</div>
            <div className="text-3xl font-bold text-pd-accent">{ioCount}</div>
          </div>
          <div className="pd-card p-4">
            <div className="text-pd-text-muted text-sm mb-2">Top Partner Classes</div>
            <div className="flex flex-wrap gap-1">
              {Object.entries(partnerClasses).slice(0, 3).map(([name, count]) => (
                <span key={name} className="text-xs px-2 py-1 rounded bg-pd-secondary text-pd-text-secondary">
                  {name.replace(/_/g, ' ')} ({count})
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Filter Section */}
        <div className="pd-card p-4 mb-6">
          <div className="flex flex-wrap gap-6">
            {/* Combo Label Filters */}
            <div>
              <div className="text-sm text-pd-text-muted mb-2">Combination Type</div>
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => setSelectedLabel("all")}
                  className={cn(
                    "px-3 py-1.5 rounded-lg text-sm font-medium transition-all",
                    selectedLabel === "all"
                      ? "bg-pd-accent text-white"
                      : "bg-pd-secondary border border-pd-border text-pd-text-secondary hover:border-pd-accent/50"
                  )}
                >
                  All ({allCombos.length})
                </button>
                {labels.map((l) => (
                  <button
                    key={l.label}
                    onClick={() => setSelectedLabel(l.label)}
                    className={cn(
                      "px-3 py-1.5 rounded-lg text-sm font-medium transition-all",
                      selectedLabel === l.label
                        ? "bg-pd-accent text-white"
                        : "bg-pd-secondary border border-pd-border text-pd-text-secondary hover:border-pd-accent/50"
                    )}
                  >
                    {COMBO_LABEL_CONFIG[l.label]?.label || l.label} ({l.count})
                  </button>
                ))}
              </div>
            </div>

            {/* Phase Filters */}
            <div>
              <div className="text-sm text-pd-text-muted mb-2">Phase</div>
              <div className="flex flex-wrap gap-2">
                {[
                  { key: "all", label: "All Phases" },
                  { key: "0", label: "Preclinical" },
                  { key: "1", label: "Phase 1" },
                  { key: "2", label: "Phase 2" },
                  { key: "3", label: "Phase 3" },
                ].map((filter) => (
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
            <div className="text-pd-text-muted">Loading combination therapies...</div>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div className="text-red-400 mb-4">{error}</div>
              <p className="text-pd-text-muted text-sm">
                The combos table may not be set up yet. Run the schema migration first.
              </p>
            </div>
          </div>
        ) : combos.length === 0 ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div className="text-pd-text-muted mb-4">No combination therapies found</div>
              <p className="text-pd-text-muted text-sm">
                {allCombos.length > 0
                  ? "Try adjusting your filters."
                  : "Run the seed ETL script to populate combination data."}
              </p>
            </div>
          </div>
        ) : (
          <DataTable
            columns={columns}
            data={combos}
            sortable={true}
            defaultSort={{ key: "max_phase", direction: "desc" }}
            emptyMessage="No combination therapies found"
          />
        )}
      </div>
    </div>
  )
}
