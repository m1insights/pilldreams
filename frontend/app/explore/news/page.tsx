"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { newsApi } from "@/lib/api"
import type { NewsSummary } from "@/lib/api/types"
import { cn } from "@/lib/utils"

// News category display config
const CATEGORY_CONFIG: Record<string, { label: string; color: string; icon: string }> = {
  "epi_drug": {
    label: "Drug Development",
    color: "bg-blue-900/30 text-blue-400 border-blue-800",
    icon: "💊"
  },
  "epi_editing": {
    label: "Epigenetic Editing",
    color: "bg-purple-900/30 text-purple-400 border-purple-800",
    icon: "✂️"
  },
  "epi_io": {
    label: "Immuno-Oncology",
    color: "bg-orange-900/30 text-orange-400 border-orange-800",
    icon: "🛡️"
  },
  "clinical_trial": {
    label: "Clinical Trial",
    color: "bg-green-900/30 text-green-400 border-green-800",
    icon: "🔬"
  },
  "acquisition": {
    label: "M&A / Licensing",
    color: "bg-yellow-900/30 text-yellow-400 border-yellow-800",
    icon: "🤝"
  },
  "regulatory": {
    label: "Regulatory",
    color: "bg-red-900/30 text-red-400 border-red-800",
    icon: "📋"
  },
  "research": {
    label: "Research",
    color: "bg-cyan-900/30 text-cyan-400 border-cyan-800",
    icon: "🧪"
  },
  "other": {
    label: "Other",
    color: "bg-pd-border text-pd-text-secondary border-pd-border",
    icon: "📰"
  },
}

// Impact flag display config
const IMPACT_CONFIG: Record<string, { label: string; color: string; icon: string }> = {
  "bullish": {
    label: "Bullish",
    color: "text-green-400",
    icon: "📈"
  },
  "bearish": {
    label: "Bearish",
    color: "text-red-400",
    icon: "📉"
  },
  "neutral": {
    label: "Neutral",
    color: "text-pd-text-muted",
    icon: "➡️"
  },
  "unknown": {
    label: "Unknown",
    color: "text-pd-text-muted",
    icon: "❓"
  },
}

// Source display config
const SOURCE_CONFIG: Record<string, { label: string; color: string }> = {
  "nature_drug_discovery": {
    label: "Nature Drug Discovery",
    color: "bg-red-900/20 text-red-400"
  },
  "nature_cancer": {
    label: "Nature Cancer",
    color: "bg-red-900/20 text-red-400"
  },
  "pubmed": {
    label: "PubMed",
    color: "bg-blue-900/20 text-blue-400"
  },
  "biospace": {
    label: "BioSpace",
    color: "bg-green-900/20 text-green-400"
  },
  "company_pr": {
    label: "Company PR",
    color: "bg-purple-900/20 text-purple-400"
  },
}

// Category badge
function CategoryBadge({ category }: { category: string | null }) {
  const config = CATEGORY_CONFIG[category || "other"] || CATEGORY_CONFIG["other"]

  return (
    <span className={cn(
      "inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium border",
      config.color
    )}>
      <span>{config.icon}</span>
      {config.label}
    </span>
  )
}

// Impact indicator
function ImpactIndicator({ impact }: { impact: string | null }) {
  const config = IMPACT_CONFIG[impact || "unknown"] || IMPACT_CONFIG["unknown"]

  return (
    <span className={cn("inline-flex items-center gap-1 text-sm", config.color)}>
      <span>{config.icon}</span>
      <span className="hidden sm:inline">{config.label}</span>
    </span>
  )
}

// Source badge
function SourceBadge({ source }: { source: string | null }) {
  if (!source) return null

  const config = SOURCE_CONFIG[source] || {
    label: source.replace(/_/g, " "),
    color: "bg-pd-secondary text-pd-text-muted"
  }

  return (
    <span className={cn(
      "inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium",
      config.color
    )}>
      {config.label}
    </span>
  )
}

// Entity tags
function EntityTags({ entities }: { entities: NewsSummary["ai_extracted_entities"] }) {
  if (!entities) return null

  const { drugs = [], targets = [], companies = [] } = entities

  if (drugs.length === 0 && targets.length === 0 && companies.length === 0) {
    return null
  }

  return (
    <div className="flex flex-wrap gap-1 mt-2">
      {drugs.slice(0, 2).map((drug) => (
        <span
          key={drug}
          className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-blue-900/20 text-blue-400"
        >
          {drug}
        </span>
      ))}
      {targets.slice(0, 2).map((target) => (
        <span
          key={target}
          className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-purple-900/20 text-purple-400"
        >
          {target}
        </span>
      ))}
      {companies.slice(0, 1).map((company) => (
        <span
          key={company}
          className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-green-900/20 text-green-400"
        >
          {company}
        </span>
      ))}
    </div>
  )
}

// Date formatter
function formatDate(dateStr: string | null) {
  if (!dateStr) return ""
  try {
    const date = new Date(dateStr)
    const now = new Date()
    const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24))

    if (diffDays === 0) return "Today"
    if (diffDays === 1) return "Yesterday"
    if (diffDays < 7) return `${diffDays} days ago`
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`

    return date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
  } catch {
    return dateStr
  }
}

// News card component
function NewsCard({ news }: { news: NewsSummary }) {
  return (
    <div className="pd-card p-4 hover:border-pd-accent/50 transition-all">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          {/* Header with source and date */}
          <div className="flex items-center gap-2 mb-2">
            <SourceBadge source={news.source} />
            <span className="text-pd-text-muted text-xs">
              {formatDate(news.pub_date)}
            </span>
            <ImpactIndicator impact={news.ai_impact_flag} />
          </div>

          {/* Title */}
          <a
            href={news.source_url || "#"}
            target="_blank"
            rel="noopener noreferrer"
            className="block group"
          >
            <h3 className="text-pd-text-primary font-medium group-hover:text-pd-accent transition-colors line-clamp-2">
              {news.title}
            </h3>
          </a>

          {/* AI Summary */}
          {news.ai_summary && (
            <p className="text-pd-text-secondary text-sm mt-2 line-clamp-2">
              {news.ai_summary}
            </p>
          )}

          {/* Entity tags */}
          <EntityTags entities={news.ai_extracted_entities} />
        </div>

        {/* Category badge */}
        <div className="flex-shrink-0">
          <CategoryBadge category={news.ai_category} />
        </div>
      </div>

      {/* Read more link */}
      {news.source_url && (
        <div className="mt-3 pt-3 border-t border-pd-border">
          <a
            href={news.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-pd-accent hover:underline inline-flex items-center gap-1"
          >
            Read Full Article
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </a>
        </div>
      )}
    </div>
  )
}

export default function NewsPage() {
  const [news, setNews] = useState<NewsSummary[]>([])
  const [allNews, setAllNews] = useState<NewsSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedCategory, setSelectedCategory] = useState("all")
  const [selectedImpact, setSelectedImpact] = useState("all")

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true)
        // News API returns only approved items (status = 'approved' from epi_news table)
        const newsData = await newsApi.list({ limit: 100 })
        setAllNews(newsData)
      } catch (err) {
        setError("Failed to load news")
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [])

  // Apply filters
  useEffect(() => {
    let filtered = [...allNews]

    if (selectedCategory !== "all") {
      filtered = filtered.filter(n => n.ai_category === selectedCategory)
    }

    if (selectedImpact !== "all") {
      filtered = filtered.filter(n => n.ai_impact_flag === selectedImpact)
    }

    setNews(filtered)
  }, [allNews, selectedCategory, selectedImpact])

  // Calculate stats
  const categories = allNews.reduce((acc, n) => {
    const cat = n.ai_category || "other"
    acc[cat] = (acc[cat] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const bullishCount = allNews.filter(n => n.ai_impact_flag === "bullish").length
  const bearishCount = allNews.filter(n => n.ai_impact_flag === "bearish").length

  return (
    <div className="min-h-screen bg-pd-primary">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-2 text-pd-text-muted text-sm mb-2">
            <Link href="/" className="hover:text-pd-accent">Home</Link>
            <span>/</span>
            <span className="text-pd-text-secondary">Intelligence Feed</span>
          </div>
          <h1 className="text-4xl font-bold text-pd-text-primary mb-2">
            Intelligence Feed
          </h1>
          <p className="text-pd-text-secondary max-w-3xl">
            AI-curated news and research from Nature, PubMed, and industry sources.
            Each article is analyzed for relevance to epigenetic oncology and tagged with
            impact signals.
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="pd-card p-4">
            <div className="text-pd-text-muted text-sm mb-1">Total Articles</div>
            <div className="text-3xl font-bold text-pd-text-primary">{allNews.length}</div>
          </div>
          <div className="pd-card p-4">
            <div className="text-pd-text-muted text-sm mb-1">Bullish Signals</div>
            <div className="text-3xl font-bold text-green-400">{bullishCount}</div>
          </div>
          <div className="pd-card p-4">
            <div className="text-pd-text-muted text-sm mb-1">Bearish Signals</div>
            <div className="text-3xl font-bold text-red-400">{bearishCount}</div>
          </div>
          <div className="pd-card p-4">
            <div className="text-pd-text-muted text-sm mb-1">Categories</div>
            <div className="text-3xl font-bold text-pd-accent">{Object.keys(categories).length}</div>
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
                  All
                </button>
                {Object.entries(categories).map(([cat, count]) => (
                  <button
                    key={cat}
                    onClick={() => setSelectedCategory(cat)}
                    className={cn(
                      "px-3 py-1.5 rounded-lg text-sm font-medium transition-all",
                      selectedCategory === cat
                        ? "bg-pd-accent text-white"
                        : "bg-pd-secondary border border-pd-border text-pd-text-secondary hover:border-pd-accent/50"
                    )}
                  >
                    {CATEGORY_CONFIG[cat]?.label || cat} ({count})
                  </button>
                ))}
              </div>
            </div>

            {/* Impact Filters */}
            <div>
              <div className="text-sm text-pd-text-muted mb-2">Impact Signal</div>
              <div className="flex flex-wrap gap-2">
                {["all", "bullish", "bearish", "neutral"].map((impact) => (
                  <button
                    key={impact}
                    onClick={() => setSelectedImpact(impact)}
                    className={cn(
                      "px-3 py-1.5 rounded-lg text-sm font-medium transition-all",
                      selectedImpact === impact
                        ? "bg-pd-accent text-white"
                        : "bg-pd-secondary border border-pd-border text-pd-text-secondary hover:border-pd-accent/50"
                    )}
                  >
                    {impact === "all" ? "All" : IMPACT_CONFIG[impact]?.label || impact}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Content */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-pd-text-muted">Loading intelligence feed...</div>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div className="text-red-400 mb-4">{error}</div>
              <p className="text-pd-text-muted text-sm">
                The news tables may not be set up yet. Run the schema migration first.
              </p>
            </div>
          </div>
        ) : news.length === 0 ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div className="text-6xl mb-4">📰</div>
              <div className="text-pd-text-primary text-xl font-medium mb-2">No News Yet</div>
              <p className="text-pd-text-muted text-sm max-w-md mx-auto">
                {allNews.length > 0
                  ? "Try adjusting your filters to see more articles."
                  : "Our intelligence feed is being curated. Check back soon for AI-analyzed news and research from Nature, PubMed, and industry sources."}
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {news.map((item) => (
              <NewsCard key={item.id} news={item} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
