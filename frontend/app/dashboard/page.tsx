"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useAuth } from "@/lib/auth/context"
import { useWatchlist } from "@/lib/hooks/useWatchlist"
import { calendarApi, drugsApi, newsApi, statsApi, watchlistApi } from "@/lib/api"
import type { DrugSummary, TrialSummary, NewsSummary, PlatformStats, WatchlistAlert } from "@/lib/api/types"
import { ScoreBadge } from "@/components/data"
import { cn } from "@/lib/utils"

// Stat card component
function StatCard({
  label,
  value,
  icon,
  trend,
  href,
}: {
  label: string
  value: string | number
  icon: React.ReactNode
  trend?: { value: number; positive: boolean }
  href?: string
}) {
  const content = (
    <div className={cn(
      "pd-card p-5 transition-all",
      href && "hover:border-pd-accent/50 cursor-pointer"
    )}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-pd-text-muted mb-1">{label}</p>
          <p className="text-3xl font-bold text-pd-text-primary">{value}</p>
          {trend && (
            <p className={cn(
              "text-xs mt-1 flex items-center gap-1",
              trend.positive ? "text-green-400" : "text-red-400"
            )}>
              <svg className={cn("w-3 h-3", !trend.positive && "rotate-180")} fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
              </svg>
              {trend.value > 0 ? "+" : ""}{trend.value} this month
            </p>
          )}
        </div>
        <div className="p-3 rounded-lg bg-pd-secondary text-pd-accent">
          {icon}
        </div>
      </div>
    </div>
  )

  if (href) {
    return <Link href={href}>{content}</Link>
  }
  return content
}

// Mini watchlist card
function WatchlistMiniCard({ drug }: { drug: DrugSummary }) {
  return (
    <Link
      href={`/drug/${drug.id}`}
      className="flex items-center justify-between p-3 rounded-lg bg-pd-secondary/50 hover:bg-pd-secondary transition-colors"
    >
      <div>
        <p className="font-medium text-pd-text-primary text-sm">{drug.name}</p>
        <p className="text-xs text-pd-text-muted">
          Phase {drug.max_phase || "-"} {drug.fda_approved && "| Approved"}
        </p>
      </div>
      {drug.total_score !== null && (
        <ScoreBadge score={drug.total_score} size="sm" />
      )}
    </Link>
  )
}

// Upcoming trial card
function UpcomingTrialCard({ trial }: { trial: TrialSummary }) {
  const daysUntil = trial.primary_completion_date
    ? Math.ceil((new Date(trial.primary_completion_date).getTime() - Date.now()) / (1000 * 60 * 60 * 24))
    : null

  return (
    <Link
      href={`/calendar?nct=${trial.nct_id}`}
      className="p-3 rounded-lg bg-pd-secondary/50 hover:bg-pd-secondary transition-colors block"
    >
      <div className="flex items-start justify-between mb-2">
        <p className="font-medium text-pd-text-primary text-sm line-clamp-1">
          {trial.drug_name || trial.nct_id}
        </p>
        {daysUntil !== null && daysUntil > 0 && (
          <span className={cn(
            "text-xs px-2 py-0.5 rounded",
            daysUntil <= 30 ? "bg-orange-900/30 text-orange-400" : "bg-blue-900/30 text-blue-400"
          )}>
            {daysUntil}d
          </span>
        )}
      </div>
      <p className="text-xs text-pd-text-muted line-clamp-1">{trial.indication_name}</p>
      <p className="text-xs text-pd-text-muted mt-1">
        {trial.phase} | {trial.lead_sponsor}
      </p>
    </Link>
  )
}

// Alert card
function AlertCard({ alert }: { alert: WatchlistAlert }) {
  const significanceColors: Record<string, string> = {
    critical: "border-l-red-500 bg-red-900/10",
    high: "border-l-orange-500 bg-orange-900/10",
    medium: "border-l-yellow-500 bg-yellow-900/10",
    low: "border-l-blue-500 bg-blue-900/10",
  }

  return (
    <div className={cn(
      "p-3 rounded-lg border-l-4",
      significanceColors[alert.significance] || "border-l-pd-border bg-pd-secondary/50"
    )}>
      <p className="font-medium text-pd-text-primary text-sm">{alert.alert_title}</p>
      {alert.alert_body && (
        <p className="text-xs text-pd-text-muted mt-1 line-clamp-2">{alert.alert_body}</p>
      )}
      <p className="text-xs text-pd-text-muted mt-2">
        {new Date(alert.created_at).toLocaleDateString()}
      </p>
    </div>
  )
}

// News card
function NewsCard({ news }: { news: NewsSummary }) {
  const impactColors: Record<string, string> = {
    bullish: "text-green-400",
    bearish: "text-red-400",
    neutral: "text-pd-text-muted",
  }

  return (
    <Link
      href={news.source_url || "#"}
      target="_blank"
      rel="noopener noreferrer"
      className="p-3 rounded-lg bg-pd-secondary/50 hover:bg-pd-secondary transition-colors block"
    >
      <div className="flex items-start gap-2 mb-2">
        {news.ai_impact_flag && (
          <span className={cn("text-xs", impactColors[news.ai_impact_flag] || "text-pd-text-muted")}>
            {news.ai_impact_flag === "bullish" ? "+" : news.ai_impact_flag === "bearish" ? "-" : "~"}
          </span>
        )}
        <p className="font-medium text-pd-text-primary text-sm line-clamp-2 flex-1">{news.title}</p>
      </div>
      <p className="text-xs text-pd-text-muted">
        {news.source} | {news.pub_date ? new Date(news.pub_date).toLocaleDateString() : "Recent"}
      </p>
    </Link>
  )
}

// Empty state for sections
function EmptySection({ message, cta, href }: { message: string; cta: string; href: string }) {
  return (
    <div className="text-center py-8">
      <p className="text-pd-text-muted text-sm mb-3">{message}</p>
      <Link
        href={href}
        className="text-pd-accent text-sm hover:underline"
      >
        {cta} →
      </Link>
    </div>
  )
}

export default function DashboardPage() {
  const router = useRouter()
  const { user, profile, loading: authLoading } = useAuth()
  const { items: watchlistItems, isLoaded: watchlistLoaded, drugCount, targetCount } = useWatchlist()

  // Data states
  const [stats, setStats] = useState<PlatformStats | null>(null)
  const [watchedDrugs, setWatchedDrugs] = useState<DrugSummary[]>([])
  const [upcomingTrials, setUpcomingTrials] = useState<TrialSummary[]>([])
  const [alerts, setAlerts] = useState<WatchlistAlert[]>([])
  const [news, setNews] = useState<NewsSummary[]>([])
  const [loading, setLoading] = useState(true)

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login?redirect=/dashboard")
    }
  }, [user, authLoading, router])

  // Fetch dashboard data
  useEffect(() => {
    async function fetchData() {
      try {
        // Fetch platform stats
        const statsData = await statsApi.get()
        setStats(statsData)

        // Fetch upcoming trials (next 90 days)
        const trialsData = await calendarApi.getUpcomingTrials({
          days: 90,
          phase_min: 2,
          exclude_placeholders: true,
        })
        setUpcomingTrials(trialsData.slice(0, 5))

        // Fetch recent news
        const newsData = await newsApi.list({ limit: 5 })
        setNews(newsData)

        // Fetch watched drug data
        if (watchlistLoaded && watchlistItems.length > 0) {
          const drugIds = watchlistItems
            .filter((i) => i.type === "drug")
            .map((i) => i.id)

          if (drugIds.length > 0) {
            const allDrugs = await drugsApi.list()
            const watched = allDrugs.filter((d) => drugIds.includes(d.id))
            setWatchedDrugs(watched.slice(0, 4))
          }
        }

        // Fetch alerts if authenticated
        if (user) {
          try {
            const session = await fetch("/api/auth/session")
            const sessionData = await session.json()
            if (sessionData?.access_token) {
              const alertsData = await watchlistApi.getAlerts(sessionData.access_token, "pending", 5)
              setAlerts(alertsData)
            }
          } catch {
            // Alerts fetch failed - not critical
          }
        }
      } catch (error) {
        console.error("Failed to fetch dashboard data:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [watchlistItems, watchlistLoaded, user])

  // Show loading state
  if (authLoading || loading) {
    return (
      <div className="min-h-screen bg-pd-primary flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-pd-accent border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-pd-text-muted">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  // Don't render if not authenticated
  if (!user) {
    return null
  }

  const displayName = profile?.full_name || user.email?.split("@")[0] || "there"

  return (
    <div className="min-h-screen bg-pd-primary">
      <div className="container mx-auto px-4 py-8">
        {/* Welcome Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-pd-text-primary mb-2">
            Welcome back, {displayName}
          </h1>
          <p className="text-pd-text-secondary">
            Your epigenetics intelligence overview
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <StatCard
            label="Watched Items"
            value={drugCount + targetCount}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            }
            href="/watchlist"
          />
          <StatCard
            label="Pipeline Drugs"
            value={stats?.total_drugs || "-"}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
              </svg>
            }
            href="/explore/drugs"
          />
          <StatCard
            label="Targets"
            value={stats?.total_targets || "-"}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            }
            href="/explore/targets"
          />
          <StatCard
            label="Approved Drugs"
            value={stats?.approved_drugs || "-"}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
          />
        </div>

        {/* Main Grid */}
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Left Column - Watchlist + Alerts */}
          <div className="lg:col-span-2 space-y-6">
            {/* Watchlist Quick View */}
            <div className="pd-card p-5">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-pd-text-primary flex items-center gap-2">
                  <svg className="w-5 h-5 text-pd-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                  Your Watchlist
                </h2>
                <Link href="/watchlist" className="text-sm text-pd-accent hover:underline">
                  View all →
                </Link>
              </div>
              {watchedDrugs.length > 0 ? (
                <div className="space-y-2">
                  {watchedDrugs.map((drug) => (
                    <WatchlistMiniCard key={drug.id} drug={drug} />
                  ))}
                </div>
              ) : (
                <EmptySection
                  message="Start tracking drugs to see them here"
                  cta="Explore drugs"
                  href="/explore/drugs"
                />
              )}
            </div>

            {/* Recent Alerts */}
            <div className="pd-card p-5">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-pd-text-primary flex items-center gap-2">
                  <svg className="w-5 h-5 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                  </svg>
                  Recent Alerts
                </h2>
                <Link href="/watchlist" className="text-sm text-pd-accent hover:underline">
                  Manage alerts →
                </Link>
              </div>
              {alerts.length > 0 ? (
                <div className="space-y-3">
                  {alerts.map((alert) => (
                    <AlertCard key={alert.id} alert={alert} />
                  ))}
                </div>
              ) : (
                <EmptySection
                  message="No pending alerts. Watch assets to receive notifications."
                  cta="Set up alerts"
                  href="/watchlist"
                />
              )}
            </div>
          </div>

          {/* Right Column - Upcoming + News */}
          <div className="space-y-6">
            {/* Upcoming Catalysts */}
            <div className="pd-card p-5">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-pd-text-primary flex items-center gap-2">
                  <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  Upcoming Catalysts
                </h2>
                <Link href="/calendar" className="text-sm text-pd-accent hover:underline">
                  Full calendar →
                </Link>
              </div>
              {upcomingTrials.length > 0 ? (
                <div className="space-y-3">
                  {upcomingTrials.map((trial) => (
                    <UpcomingTrialCard key={trial.id} trial={trial} />
                  ))}
                </div>
              ) : (
                <EmptySection
                  message="No upcoming catalysts in the next 90 days"
                  cta="View calendar"
                  href="/calendar"
                />
              )}
            </div>

            {/* Latest News */}
            <div className="pd-card p-5">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-pd-text-primary flex items-center gap-2">
                  <svg className="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
                  </svg>
                  Latest News
                </h2>
                <Link href="/explore/news" className="text-sm text-pd-accent hover:underline">
                  All news →
                </Link>
              </div>
              {news.length > 0 ? (
                <div className="space-y-3">
                  {news.map((item) => (
                    <NewsCard key={item.id} news={item} />
                  ))}
                </div>
              ) : (
                <EmptySection
                  message="No recent news available"
                  cta="Browse news"
                  href="/explore/news"
                />
              )}
            </div>

            {/* Quick Links */}
            <div className="pd-card p-5">
              <h2 className="text-lg font-semibold text-pd-text-primary mb-4">Quick Actions</h2>
              <div className="space-y-2">
                <Link
                  href="/explore/targets"
                  className="flex items-center gap-3 p-3 rounded-lg bg-pd-secondary/50 hover:bg-pd-secondary transition-colors"
                >
                  <span className="text-xl">🎯</span>
                  <span className="text-sm text-pd-text-primary">Explore Targets</span>
                </Link>
                <Link
                  href="/explore/drugs"
                  className="flex items-center gap-3 p-3 rounded-lg bg-pd-secondary/50 hover:bg-pd-secondary transition-colors"
                >
                  <span className="text-xl">💊</span>
                  <span className="text-sm text-pd-text-primary">Browse Pipeline</span>
                </Link>
                <Link
                  href="/explore/companies"
                  className="flex items-center gap-3 p-3 rounded-lg bg-pd-secondary/50 hover:bg-pd-secondary transition-colors"
                >
                  <span className="text-xl">🏢</span>
                  <span className="text-sm text-pd-text-primary">Company Profiles</span>
                </Link>
                <Link
                  href="/settings"
                  className="flex items-center gap-3 p-3 rounded-lg bg-pd-secondary/50 hover:bg-pd-secondary transition-colors"
                >
                  <span className="text-xl">⚙️</span>
                  <span className="text-sm text-pd-text-primary">Account Settings</span>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
