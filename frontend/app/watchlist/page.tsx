"use client"

import { useEffect, useState, useRef } from "react"
import Link from "next/link"
import { useWatchlist } from "@/lib/hooks/useWatchlist"
import { drugsApi, newsApi, companiesApi } from "@/lib/api"
import { aiApi } from "@/lib/api/client"
import type { DrugSummary, NewsSummary, CompanySummary, ChatMessage } from "@/lib/api/types"
import { ScoreBadge } from "@/components/data"
import { ExportButton } from "@/components/export-button"
import { cn } from "@/lib/utils"
import { Send, Sparkles, Loader2, X, ChevronDown, ChevronUp, Building2, Pill, Target, Newspaper, MessageCircle, TrendingUp, TrendingDown, Minus } from "lucide-react"

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
    <div className="pd-card p-3 relative group">
      <button
        onClick={(e) => {
          e.preventDefault()
          onRemove()
        }}
        className="absolute top-2 right-2 p-1 rounded bg-pd-secondary border border-pd-border text-pd-text-muted hover:text-red-400 hover:border-red-400/50 opacity-0 group-hover:opacity-100 transition-all"
        title="Remove from watchlist"
      >
        <X className="w-3 h-3" />
      </button>

      <Link href={`/drug/${drug.id}`} className="block">
        <div className="flex items-start justify-between mb-2">
          <div className="flex-1 min-w-0 mr-2">
            <h3 className="font-medium text-pd-accent hover:underline text-sm truncate">
              {drug.name}
            </h3>
            <PhaseBadge phase={drug.max_phase} />
          </div>
          {drug.total_score !== null && (
            <ScoreBadge score={drug.total_score} size="sm" />
          )}
        </div>
      </Link>
    </div>
  )
}

// Company card for watchlist
function WatchlistCompanyCard({
  company,
  onRemove,
}: {
  company: CompanySummary
  onRemove: () => void
}) {
  return (
    <div className="pd-card p-3 relative group">
      <button
        onClick={(e) => {
          e.preventDefault()
          onRemove()
        }}
        className="absolute top-2 right-2 p-1 rounded bg-pd-secondary border border-pd-border text-pd-text-muted hover:text-red-400 hover:border-red-400/50 opacity-0 group-hover:opacity-100 transition-all"
        title="Remove from watchlist"
      >
        <X className="w-3 h-3" />
      </button>

      <Link href={`/company/${company.id}`} className="block">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0 mr-2">
            <h3 className="font-medium text-pd-accent hover:underline text-sm truncate">
              {company.name}
            </h3>
            <div className="flex items-center gap-2 mt-1">
              {company.ticker && (
                <span className="text-xs text-pd-text-muted">{company.ticker}</span>
              )}
              <span className="text-xs text-pd-text-muted">
                {company.drug_count} drugs
              </span>
            </div>
          </div>
          {company.avg_drug_score !== null && (
            <ScoreBadge score={company.avg_drug_score} size="sm" />
          )}
        </div>
      </Link>
    </div>
  )
}

// Target card for watchlist
function WatchlistTargetCard({
  item,
  onRemove,
}: {
  item: { id: string; name: string; addedAt: string }
  onRemove: () => void
}) {
  return (
    <div className="pd-card p-3 relative group">
      <button
        onClick={() => onRemove()}
        className="absolute top-2 right-2 p-1 rounded bg-pd-secondary border border-pd-border text-pd-text-muted hover:text-red-400 hover:border-red-400/50 opacity-0 group-hover:opacity-100 transition-all"
        title="Remove from watchlist"
      >
        <X className="w-3 h-3" />
      </button>
      <Link href={`/target/${item.id}`} className="block">
        <h3 className="font-medium text-pd-accent hover:underline text-sm">
          {item.name}
        </h3>
        <p className="text-xs text-pd-text-muted mt-1">
          Added {new Date(item.addedAt).toLocaleDateString()}
        </p>
      </Link>
    </div>
  )
}

// Compact news card
function CompactNewsCard({ news }: { news: NewsSummary }) {
  const impactIcon = news.ai_impact_flag === "bullish"
    ? <TrendingUp className="w-3 h-3 text-green-400" />
    : news.ai_impact_flag === "bearish"
    ? <TrendingDown className="w-3 h-3 text-red-400" />
    : <Minus className="w-3 h-3 text-pd-text-muted" />

  return (
    <a
      href={news.source_url || "#"}
      target="_blank"
      rel="noopener noreferrer"
      className="block p-3 border-b border-pd-border last:border-b-0 hover:bg-pd-hover transition-colors"
    >
      <div className="flex items-start gap-2">
        {impactIcon}
        <div className="flex-1 min-w-0">
          <h4 className="text-sm text-pd-text-primary line-clamp-2 hover:text-pd-accent">
            {news.title}
          </h4>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-xs text-pd-text-muted">
              {news.source || "News"}
            </span>
            <span className="text-xs text-pd-text-muted">•</span>
            <span className="text-xs text-pd-text-muted">
              {news.pub_date ? new Date(news.pub_date).toLocaleDateString() : ""}
            </span>
          </div>
        </div>
      </div>
    </a>
  )
}

// AI Chat Sidebar (always visible)
function ChatSidebar() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isExpanded, setIsExpanded] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: ChatMessage = { role: "user", content: input.trim() }
    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setError(null)
    setIsLoading(true)

    try {
      const response = await aiApi.chat({
        question: input.trim(),
        conversation_history: messages,
      })

      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: response.answer,
      }
      setMessages((prev) => [...prev, assistantMessage])
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to get response")
    } finally {
      setIsLoading(false)
    }
  }

  const suggestedQuestions = [
    "What is Vorinostat?",
    "Compare HDAC vs BET inhibitors",
    "Top approved epigenetic drugs",
  ]

  return (
    <div className="pd-card flex flex-col h-full">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center justify-between p-4 border-b border-pd-border hover:bg-pd-hover transition-colors"
      >
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-blue-400" />
          <h3 className="font-semibold text-pd-text-primary">Ask AI</h3>
        </div>
        {isExpanded ? (
          <ChevronDown className="w-4 h-4 text-pd-text-muted" />
        ) : (
          <ChevronUp className="w-4 h-4 text-pd-text-muted" />
        )}
      </button>

      {isExpanded && (
        <>
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3 min-h-[200px] max-h-[400px]">
            {messages.length === 0 ? (
              <div className="text-center py-4">
                <p className="text-sm text-pd-text-muted mb-3">
                  Ask about drugs, targets, or scores
                </p>
                <div className="space-y-2">
                  {suggestedQuestions.map((q, i) => (
                    <button
                      key={i}
                      onClick={() => setInput(q)}
                      className="w-full text-left px-3 py-2 rounded-lg bg-pd-secondary hover:bg-pd-hover text-xs text-pd-text-secondary hover:text-pd-text-primary border border-pd-border hover:border-pd-accent/30 transition-colors"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <>
                {messages.map((msg, i) => (
                  <div
                    key={i}
                    className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={cn(
                        "max-w-[90%] rounded-lg px-3 py-2 text-sm",
                        msg.role === "user"
                          ? "bg-blue-600 text-white"
                          : "bg-pd-secondary text-pd-text-primary border border-pd-border"
                      )}
                    >
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    </div>
                  </div>
                ))}

                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-pd-secondary border border-pd-border rounded-lg px-3 py-2">
                      <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />
                    </div>
                  </div>
                )}

                {error && (
                  <div className="text-center">
                    <span className="text-xs text-red-400">{error}</span>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          {/* Input */}
          <form onSubmit={handleSubmit} className="p-3 border-t border-pd-border">
            <div className="flex gap-2">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask a question..."
                className="flex-1 bg-pd-secondary border border-pd-border rounded-lg px-3 py-2 text-sm text-pd-text-primary placeholder-pd-text-muted focus:outline-none focus:border-blue-500/50"
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={!input.trim() || isLoading}
                className="px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-pd-border disabled:cursor-not-allowed rounded-lg text-white transition-colors"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </form>
        </>
      )}
    </div>
  )
}

// Empty state
function EmptyWatchlist() {
  return (
    <div className="pd-card p-8 text-center">
      <div className="w-14 h-14 mx-auto mb-4 rounded-full bg-pd-secondary flex items-center justify-center">
        <Target className="w-7 h-7 text-pd-text-muted" />
      </div>
      <h3 className="text-lg font-medium text-pd-text-primary mb-2">
        Your watchlist is empty
      </h3>
      <p className="text-pd-text-muted mb-6 max-w-sm mx-auto text-sm">
        Start tracking drugs, targets, and companies by clicking the Watch button on any page.
      </p>
      <div className="flex gap-3 justify-center flex-wrap">
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
        <Link
          href="/explore/companies"
          className="px-4 py-2 rounded-lg bg-pd-secondary border border-pd-border text-pd-text-secondary text-sm font-medium hover:border-pd-accent/50 transition-colors"
        >
          Explore Companies
        </Link>
      </div>
    </div>
  )
}

// Tab type
type TabType = "all" | "drugs" | "targets" | "companies"

export default function DashboardPage() {
  const { items, isLoaded, removeItem, clearAll, drugCount, targetCount, companyCount } = useWatchlist()
  const [drugsData, setDrugsData] = useState<Record<string, DrugSummary>>({})
  const [companiesData, setCompaniesData] = useState<Record<string, CompanySummary>>({})
  const [news, setNews] = useState<NewsSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<TabType>("all")

  // Fetch all data
  useEffect(() => {
    async function loadData() {
      if (!isLoaded) return

      try {
        setLoading(true)

        // Fetch drugs and companies in parallel
        const [allDrugs, allCompanies, newsData] = await Promise.all([
          drugsApi.list().catch(() => []),
          companiesApi.list().catch(() => []),
          newsApi.list({ limit: 10 }).catch(() => []),
        ])

        // Map drugs by ID
        const drugMap: Record<string, DrugSummary> = {}
        allDrugs.forEach((drug) => {
          drugMap[drug.id] = drug
        })
        setDrugsData(drugMap)

        // Map companies by ID
        const companyMap: Record<string, CompanySummary> = {}
        allCompanies.forEach((company) => {
          companyMap[company.id] = company
        })
        setCompaniesData(companyMap)

        setNews(newsData)
      } catch (err) {
        console.error("Failed to load data:", err)
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [isLoaded])

  // Filter items by type
  const watchedDrugs = items
    .filter((i) => i.type === "drug")
    .map((item) => ({
      item,
      data: drugsData[item.id],
    }))
    .sort((a, b) => {
      const scoreA = a.data?.total_score ?? -1
      const scoreB = b.data?.total_score ?? -1
      return scoreB - scoreA
    })

  const watchedCompanies = items
    .filter((i) => i.type === "company")
    .map((item) => ({
      item,
      data: companiesData[item.id],
    }))

  const watchedTargets = items.filter((i) => i.type === "target")

  // Get visible items based on tab
  const getVisibleItems = () => {
    switch (activeTab) {
      case "drugs":
        return { drugs: watchedDrugs, targets: [], companies: [] }
      case "targets":
        return { drugs: [], targets: watchedTargets, companies: [] }
      case "companies":
        return { drugs: [], targets: [], companies: watchedCompanies }
      default:
        return { drugs: watchedDrugs, targets: watchedTargets, companies: watchedCompanies }
    }
  }

  const visibleItems = getVisibleItems()

  if (!isLoaded) {
    return (
      <div className="min-h-screen bg-pd-primary flex items-center justify-center">
        <div className="text-pd-text-muted">Loading dashboard...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-pd-primary">
      <div className="container mx-auto px-4 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-pd-text-primary">
              Dashboard
            </h1>
            <span className="text-sm text-pd-text-muted">
              {items.length} tracked
            </span>
          </div>
          {items.length > 0 && (
            <div className="flex items-center gap-2">
              <ExportButton entityType="watchlist" className="text-xs" />
              <button
                onClick={clearAll}
                className="px-3 py-1.5 rounded-lg text-sm bg-pd-secondary border border-pd-border text-pd-text-muted hover:text-red-400 hover:border-red-400/50 transition-colors"
              >
                Clear
              </button>
            </div>
          )}
        </div>

        {/* Two-column layout: Left (News + Watchlist stacked) | Right (AI Chat) */}
        <div className="grid lg:grid-cols-3 gap-4">
          {/* Left Column - News on top, Watchlist below */}
          <div className="lg:col-span-2 space-y-4">
            {/* News Feed */}
            <div className="pd-card">
              <div className="flex items-center justify-between px-4 py-3 border-b border-pd-border">
                <div className="flex items-center gap-2">
                  <Newspaper className="w-4 h-4 text-pd-text-muted" />
                  <h3 className="font-semibold text-pd-text-primary">
                    News
                  </h3>
                </div>
                <Link
                  href="/explore/news"
                  className="text-xs text-pd-accent hover:underline"
                >
                  View All
                </Link>
              </div>
              <div className="p-3">
                {news.length === 0 ? (
                  <div className="py-8 text-center">
                    <p className="text-sm text-pd-text-muted">No news available</p>
                  </div>
                ) : (
                  <div className="space-y-1 max-h-[200px] overflow-y-auto">
                    {news.slice(0, 8).map((item) => (
                      <CompactNewsCard key={item.id} news={item} />
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Watchlist - below news */}
            <div className="pd-card">
              <div className="flex items-center justify-between px-4 py-3 border-b border-pd-border">
                <h3 className="font-semibold text-pd-text-primary">
                  Watchlist
                </h3>
                <div className="flex items-center gap-3 text-xs text-pd-text-muted">
                  <span className="flex items-center gap-1">
                    <Pill className="w-3 h-3 text-pd-accent" /> {drugCount}
                  </span>
                  <span className="flex items-center gap-1">
                    <Target className="w-3 h-3 text-blue-400" /> {targetCount}
                  </span>
                  <span className="flex items-center gap-1">
                    <Building2 className="w-3 h-3 text-green-400" /> {companyCount}
                  </span>
                </div>
              </div>

              {/* Tabs */}
              <div className="flex border-b border-pd-border">
                {[
                  { key: "all", label: "All" },
                  { key: "companies", label: "Companies" },
                  { key: "drugs", label: "Drugs" },
                  { key: "targets", label: "Targets" },
                ].map((tab) => (
                  <button
                    key={tab.key}
                    onClick={() => setActiveTab(tab.key as TabType)}
                    className={cn(
                      "flex-1 px-3 py-2 text-xs font-medium transition-colors",
                      activeTab === tab.key
                        ? "text-pd-accent border-b border-pd-accent bg-pd-accent/5"
                        : "text-pd-text-muted hover:text-pd-text-secondary"
                    )}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              {/* Content */}
              {items.length === 0 ? (
                <EmptyWatchlist />
              ) : loading ? (
                <div className="p-8 text-center text-pd-text-muted">
                  Loading...
                </div>
              ) : (
                <div className="p-3 max-h-[400px] overflow-y-auto">
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                    {/* Companies */}
                    {visibleItems.companies.map(({ item, data }) =>
                      data ? (
                        <WatchlistCompanyCard
                          key={item.id}
                          company={data}
                          onRemove={() => removeItem(item.id, "company")}
                        />
                      ) : (
                        <div key={item.id} className="pd-card p-3 text-pd-text-muted text-xs">
                          {item.name}
                        </div>
                      )
                    )}
                    {/* Drugs */}
                    {visibleItems.drugs.map(({ item, data }) =>
                      data ? (
                        <WatchlistDrugCard
                          key={item.id}
                          drug={data}
                          onRemove={() => removeItem(item.id, "drug")}
                        />
                      ) : (
                        <div key={item.id} className="pd-card p-3 text-pd-text-muted text-xs">
                          {item.name}
                        </div>
                      )
                    )}
                    {/* Targets */}
                    {visibleItems.targets.map((item) => (
                      <WatchlistTargetCard
                        key={item.id}
                        item={item}
                        onRemove={() => removeItem(item.id, "target")}
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right Column - AI Chat (sticky) */}
          <div className="lg:col-span-1">
            <div className="lg:sticky lg:top-20">
              <ChatSidebar />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
