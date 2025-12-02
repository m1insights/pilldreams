"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { patentsApi } from "@/lib/api"
import type { PatentSummary } from "@/lib/api/types"
import { DataTable } from "@/components/data"
import { cn } from "@/lib/utils"

// Patent category display config
const CATEGORY_CONFIG: Record<string, { label: string; color: string; description: string }> = {
  "epi_editor": {
    label: "Epigenetic Editor",
    color: "bg-purple-900/30 text-purple-400 border-purple-800",
    description: "CRISPR/TALE-based epigenetic editing technologies"
  },
  "epi_therapy": {
    label: "Therapeutic",
    color: "bg-blue-900/30 text-blue-400 border-blue-800",
    description: "Small molecule epigenetic drugs and combinations"
  },
  "epi_diagnostic": {
    label: "Diagnostic",
    color: "bg-green-900/30 text-green-400 border-green-800",
    description: "Epigenetic biomarkers and diagnostic methods"
  },
  "epi_io": {
    label: "Immuno-Oncology",
    color: "bg-orange-900/30 text-orange-400 border-orange-800",
    description: "Epigenetic approaches to enhance immunotherapy"
  },
  "epi_tool": {
    label: "Research Tool",
    color: "bg-cyan-900/30 text-cyan-400 border-cyan-800",
    description: "Epigenetic clocks, aging biomarkers, research methods"
  },
}

// Category badge component
function CategoryBadge({ category }: { category: string | null }) {
  const config = CATEGORY_CONFIG[category || ""] || {
    label: category || "Other",
    color: "bg-pd-border text-pd-text-secondary border-pd-border"
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

// Target badges component
function TargetBadges({ targets }: { targets: string[] | null }) {
  if (!targets || targets.length === 0) {
    return <span className="text-pd-text-muted">-</span>
  }

  return (
    <div className="flex flex-wrap gap-1">
      {targets.slice(0, 3).map((target) => (
        <Link
          key={target}
          href={`/explore/targets?search=${target}`}
          className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-pd-secondary text-pd-accent hover:bg-pd-accent/20 transition-colors"
        >
          {target}
        </Link>
      ))}
      {targets.length > 3 && (
        <span className="px-1.5 py-0.5 rounded text-[10px] text-pd-text-muted">
          +{targets.length - 3} more
        </span>
      )}
    </div>
  )
}

// Patent number link component
function PatentLink({ patentNumber }: { patentNumber: string }) {
  // Determine link based on patent type
  let url = "#"
  if (patentNumber.startsWith("US")) {
    url = `https://patents.google.com/patent/${patentNumber}`
  } else if (patentNumber.startsWith("WO")) {
    url = `https://patents.google.com/patent/${patentNumber}`
  } else if (patentNumber.startsWith("EP")) {
    url = `https://patents.google.com/patent/${patentNumber}`
  }

  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="font-mono text-xs text-pd-accent hover:underline"
    >
      {patentNumber}
    </a>
  )
}

// Date formatter
function formatDate(dateStr: string | null) {
  if (!dateStr) return "-"
  try {
    const date = new Date(dateStr)
    return date.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" })
  } catch {
    return dateStr
  }
}

export default function PatentsPage() {
  const [patents, setPatents] = useState<PatentSummary[]>([])
  const [allPatents, setAllPatents] = useState<PatentSummary[]>([])
  const [categories, setCategories] = useState<{ category: string; count: number }[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedCategory, setSelectedCategory] = useState("all")

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true)
        const [patentsData, categoriesData] = await Promise.all([
          patentsApi.list(),
          patentsApi.getCategories()
        ])
        setAllPatents(patentsData)
        setCategories(categoriesData)
      } catch (err) {
        setError("Failed to load patents")
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [])

  // Apply filters
  useEffect(() => {
    let filtered = [...allPatents]

    if (selectedCategory !== "all") {
      filtered = filtered.filter(p => p.category === selectedCategory)
    }

    setPatents(filtered)
  }, [allPatents, selectedCategory])

  // Calculate stats
  const totalPatents = patents.length
  const editorPatents = patents.filter(p => p.category === "epi_editor").length
  const therapyPatents = patents.filter(p => p.category === "epi_therapy").length
  const uniqueAssignees = new Set(patents.map(p => p.assignee).filter(Boolean)).size

  // Recent patents (last 12 months)
  const oneYearAgo = new Date()
  oneYearAgo.setFullYear(oneYearAgo.getFullYear() - 1)
  const recentPatents = patents.filter(p => {
    if (!p.pub_date) return false
    return new Date(p.pub_date) >= oneYearAgo
  }).length

  // Table columns
  const columns = [
    {
      key: "patent_number",
      label: "Patent #",
      sortable: true,
      render: (value: string) => <PatentLink patentNumber={value} />,
    },
    {
      key: "title",
      label: "Title",
      sortable: true,
      render: (value: string) => (
        <span className="text-pd-text-primary line-clamp-2" title={value}>
          {value}
        </span>
      ),
    },
    {
      key: "assignee",
      label: "Assignee",
      sortable: true,
      render: (value: string | null) => (
        <span className="text-pd-text-secondary font-medium">
          {value || "-"}
        </span>
      ),
    },
    {
      key: "category",
      label: "Category",
      sortable: true,
      render: (value: string | null) => <CategoryBadge category={value} />,
    },
    {
      key: "related_target_symbols",
      label: "Targets",
      sortable: false,
      render: (value: string[] | null) => <TargetBadges targets={value} />,
    },
    {
      key: "pub_date",
      label: "Published",
      sortable: true,
      render: (value: string | null) => (
        <span className="text-pd-text-muted text-sm">
          {formatDate(value)}
        </span>
      ),
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
            <span className="text-pd-text-secondary">Patents</span>
          </div>
          <h1 className="text-4xl font-bold text-pd-text-primary mb-2">
            Epigenetic Patents
          </h1>
          <p className="text-pd-text-secondary max-w-3xl">
            Patent filings covering epigenetic therapies, CRISPR-based editors, diagnostics,
            and immuno-oncology combinations. Track IP landscape and competitive positioning.
          </p>
        </div>

        {/* Explanation Card */}
        <div className="pd-card p-6 mb-8 border-l-4 border-pd-accent">
          <h3 className="text-lg font-semibold text-pd-text-primary mb-2">Patent Categories</h3>
          <div className="grid md:grid-cols-3 lg:grid-cols-5 gap-4 text-sm">
            {Object.entries(CATEGORY_CONFIG).map(([key, config]) => (
              <div key={key} className="bg-pd-secondary rounded-lg p-3">
                <div className={cn("font-medium mb-1", config.color.split(" ")[1])}>
                  {config.label}
                </div>
                <div className="text-pd-text-muted text-xs">{config.description}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
          <div className="pd-card p-4">
            <div className="text-pd-text-muted text-sm mb-1">Total Patents</div>
            <div className="text-3xl font-bold text-pd-text-primary">{totalPatents}</div>
          </div>
          <div className="pd-card p-4">
            <div className="text-pd-text-muted text-sm mb-1">Epi Editors</div>
            <div className="text-3xl font-bold text-purple-400">{editorPatents}</div>
          </div>
          <div className="pd-card p-4">
            <div className="text-pd-text-muted text-sm mb-1">Therapeutics</div>
            <div className="text-3xl font-bold text-blue-400">{therapyPatents}</div>
          </div>
          <div className="pd-card p-4">
            <div className="text-pd-text-muted text-sm mb-1">Assignees</div>
            <div className="text-3xl font-bold text-green-400">{uniqueAssignees}</div>
          </div>
          <div className="pd-card p-4">
            <div className="text-pd-text-muted text-sm mb-1">Last 12 Months</div>
            <div className="text-3xl font-bold text-pd-accent">{recentPatents}</div>
          </div>
        </div>

        {/* Filter Section */}
        <div className="pd-card p-4 mb-6">
          <div className="flex flex-wrap gap-6">
            {/* Category Filters */}
            <div>
              <div className="text-sm text-pd-text-muted mb-2">Category</div>
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => setSelectedCategory("all")}
                  className={cn(
                    "px-3 py-1.5 rounded-lg text-sm font-medium transition-all",
                    selectedCategory === "all"
                      ? "bg-pd-accent text-white"
                      : "bg-pd-secondary border border-pd-border text-pd-text-secondary hover:border-pd-accent/50"
                  )}
                >
                  All ({allPatents.length})
                </button>
                {categories.map((cat) => (
                  <button
                    key={cat.category}
                    onClick={() => setSelectedCategory(cat.category)}
                    className={cn(
                      "px-3 py-1.5 rounded-lg text-sm font-medium transition-all",
                      selectedCategory === cat.category
                        ? "bg-pd-accent text-white"
                        : "bg-pd-secondary border border-pd-border text-pd-text-secondary hover:border-pd-accent/50"
                    )}
                  >
                    {CATEGORY_CONFIG[cat.category]?.label || cat.category} ({cat.count})
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Content */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-pd-text-muted">Loading patents...</div>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div className="text-red-400 mb-4">{error}</div>
              <p className="text-pd-text-muted text-sm">
                The patents table may not be set up yet. Run the ETL script first.
              </p>
            </div>
          </div>
        ) : patents.length === 0 ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div className="text-pd-text-muted mb-4">No patents found</div>
              <p className="text-pd-text-muted text-sm">
                {allPatents.length > 0
                  ? "Try adjusting your filters."
                  : "Run the seed ETL script to populate patent data."}
              </p>
            </div>
          </div>
        ) : (
          <DataTable
            columns={columns}
            data={patents}
            sortable={true}
            defaultSort={{ key: "pub_date", direction: "desc" }}
            emptyMessage="No patents found"
          />
        )}
      </div>
    </div>
  )
}
