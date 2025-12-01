"use client"

import { useEffect, useState, useRef } from "react"
import { useParams } from "next/navigation"
import Link from "next/link"
import { companiesApi } from "@/lib/api"
import { ScoreBadge, WatchButton } from "@/components/data"
import { cn } from "@/lib/utils"

interface CompanyDetailData {
  company: {
    id: string
    name: string
    ticker: string | null
    exchange: string | null
    market_cap: number | null
    sector: string | null
    industry: string | null
    description: string | null
    website: string | null
    headquarters: string | null
    founded_year: number | null
    employee_count: number | null
    epi_focus_score: number | null
    is_pure_play_epi: boolean
  }
  drugs: Array<{
    drug: {
      id: string
      name: string
      chembl_id: string | null
      drug_type: string | null
      fda_approved: boolean
    }
    role: string | null
    is_primary: boolean
    score: {
      bio_score: number | null
      chem_score: number | null
      tractability_score: number | null
      total_score: number | null
    } | null
  }>
  editing_assets: Array<{
    asset: {
      id: string
      name: string
      sponsor: string | null
      target_gene_symbol: string | null
      dbd_type: string | null
      phase: number
      status: string
    }
    role: string | null
    is_primary: boolean
    score: {
      target_bio_score: number | null
      editing_modality_score: number | null
      durability_score: number | null
      total_editing_score: number | null
    } | null
  }>
}

// TradingView Widget Component
function TradingViewWidget({ ticker }: { ticker: string }) {
  const container = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const containerEl = container.current
    if (!containerEl || !ticker) return

    // Clear previous widget
    containerEl.innerHTML = ""

    const script = document.createElement("script")
    script.src = "https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js"
    script.type = "text/javascript"
    script.async = true
    script.innerHTML = JSON.stringify({
      width: "100%",
      height: "600",
      symbol: ticker,
      interval: "D",
      timezone: "Etc/UTC",
      theme: "dark",
      style: "1",
      locale: "en",
      enable_publishing: false,
      backgroundColor: "rgba(0, 0, 0, 0)",
      gridColor: "rgba(255, 255, 255, 0.06)",
      hide_top_toolbar: false,
      hide_legend: false,
      save_image: false,
      calendar: false,
      support_host: "https://www.tradingview.com",
    })

    containerEl.appendChild(script)

    return () => {
      containerEl.innerHTML = ""
    }
  }, [ticker])

  return (
    <div className="tradingview-widget-container h-[600px]" ref={container}>
      <div className="tradingview-widget-container__widget h-full" />
    </div>
  )
}

// Market Cap Display
function formatMarketCap(cap: number | null, ticker: string | null) {
  if (cap) {
    if (cap >= 1e12) return `$${(cap / 1e12).toFixed(1)}T`
    if (cap >= 1e9) return `$${(cap / 1e9).toFixed(1)}B`
    if (cap >= 1e6) return `$${(cap / 1e6).toFixed(0)}M`
    return `$${cap.toLocaleString()}`
  }
  // No market cap data
  if (ticker) return "N/A"  // Has ticker but no cap = data fetch failed
  return "Private"  // No ticker = private company
}

// Phase badge
function PhaseBadge({ phase }: { phase: number }) {
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

// External link
function ExternalLink({ href, label, icon }: { href: string; label: string; icon: string }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm bg-pd-secondary border border-pd-border text-pd-accent hover:bg-pd-accent/10 transition-colors"
    >
      <span>{icon}</span>
      <span>{label}</span>
      <svg className="w-3 h-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
      </svg>
    </a>
  )
}

export default function CompanyDetailPage() {
  const params = useParams()
  const [data, setData] = useState<CompanyDetailData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<"chart" | "drugs" | "editing">("chart")

  useEffect(() => {
    async function load() {
      try {
        setLoading(true)
        const res = await companiesApi.get(String(params.id))
        setData(res)
      } catch {
        setError("Failed to load company details")
      } finally {
        setLoading(false)
      }
    }
    if (params.id) load()
  }, [params.id])

  if (loading) {
    return (
      <div className="min-h-screen bg-pd-primary flex items-center justify-center">
        <div className="text-pd-text-muted">Loading company details...</div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-pd-primary flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-400 mb-4">{error || "Company not found"}</div>
          <Link href="/explore/companies" className="text-pd-accent hover:underline">
            Back to Companies
          </Link>
        </div>
      </div>
    )
  }

  const { company, drugs, editing_assets } = data
  const totalAssets = drugs.length + editing_assets.length

  // Calculate avg score
  const drugScores = drugs
    .filter(d => d.score?.total_score)
    .map(d => d.score!.total_score!)
  const avgDrugScore = drugScores.length > 0
    ? drugScores.reduce((a, b) => a + b, 0) / drugScores.length
    : null

  return (
    <div className="min-h-screen bg-pd-primary">
      <div className="container mx-auto px-4 py-8">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-pd-text-muted text-sm mb-4">
          <Link href="/explore/companies" className="hover:text-pd-accent">
            Companies
          </Link>
          <span>/</span>
          <span className="text-pd-text-secondary">{company.name}</span>
        </div>

        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4 mb-8">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-4xl font-bold text-pd-text-primary">{company.name}</h1>
              {company.ticker && (
                <span className="font-mono text-lg text-pd-text-secondary">
                  ({company.ticker})
                </span>
              )}
              {company.is_pure_play_epi && (
                <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm bg-purple-900/30 text-purple-400 border border-purple-800">
                  <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
                  Pure Play Epi
                </span>
              )}
            </div>
            <p className="text-pd-text-secondary">
              {company.industry || company.sector || "Biotechnology"}
            </p>
            {company.description && (
              <p className="text-pd-text-muted mt-2 max-w-2xl">{company.description}</p>
            )}
          </div>

          {/* Actions */}
          <div className="flex items-center gap-4">
            <WatchButton id={company.id} type="company" name={company.name} />
            {company.epi_focus_score && (
              <div className="flex flex-col items-center">
                <div className="text-3xl font-bold text-pd-accent">
                  {company.epi_focus_score.toFixed(0)}%
                </div>
                <span className="text-pd-text-muted text-xs">Epi Focus</span>
              </div>
            )}
          </div>
        </div>

        {/* External Links */}
        <div className="pd-card p-4 mb-6">
          <h3 className="text-sm font-medium text-pd-text-muted mb-3">External Resources</h3>
          <div className="flex flex-wrap gap-2">
            {company.website && (
              <ExternalLink href={company.website} label="Website" icon="🌐" />
            )}
            {company.ticker && (
              <>
                <ExternalLink
                  href={`https://finance.yahoo.com/quote/${company.ticker}`}
                  label="Yahoo Finance"
                  icon="📈"
                />
                <ExternalLink
                  href={`https://www.google.com/finance/quote/${company.ticker}:${company.exchange || "NASDAQ"}`}
                  label="Google Finance"
                  icon="📊"
                />
                <ExternalLink
                  href={`https://clinicaltrials.gov/search?sponsor=${encodeURIComponent(company.name)}`}
                  label="ClinicalTrials.gov"
                  icon="🏥"
                />
              </>
            )}
            <ExternalLink
              href={`https://pubmed.ncbi.nlm.nih.gov/?term=${encodeURIComponent(company.name)}`}
              label="PubMed"
              icon="📚"
            />
          </div>
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
          <div className="pd-card p-4">
            <div className="text-pd-text-muted text-sm mb-1">Market Cap</div>
            <div className="text-2xl font-bold text-pd-text-primary">
              {formatMarketCap(company.market_cap, company.ticker)}
            </div>
          </div>
          <div className="pd-card p-4">
            <div className="text-pd-text-muted text-sm mb-1">Total Assets</div>
            <div className="text-2xl font-bold text-pd-text-primary">{totalAssets}</div>
          </div>
          <div className="pd-card p-4">
            <div className="text-pd-text-muted text-sm mb-1">Drugs</div>
            <div className="text-2xl font-bold text-blue-400">{drugs.length}</div>
          </div>
          <div className="pd-card p-4">
            <div className="text-pd-text-muted text-sm mb-1">Editing Programs</div>
            <div className="text-2xl font-bold text-purple-400">{editing_assets.length}</div>
          </div>
          <div className="pd-card p-4">
            <div className="text-pd-text-muted text-sm mb-1">Avg Drug Score</div>
            <div className="text-2xl font-bold text-pd-accent">
              {avgDrugScore ? avgDrugScore.toFixed(1) : "-"}
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setActiveTab("chart")}
            className={cn(
              "px-4 py-2 rounded-lg text-sm font-medium transition-all",
              activeTab === "chart"
                ? "bg-pd-accent text-white"
                : "bg-pd-secondary border border-pd-border text-pd-text-secondary hover:border-pd-accent/50"
            )}
          >
            Stock Chart
          </button>
          <button
            onClick={() => setActiveTab("drugs")}
            className={cn(
              "px-4 py-2 rounded-lg text-sm font-medium transition-all",
              activeTab === "drugs"
                ? "bg-pd-accent text-white"
                : "bg-pd-secondary border border-pd-border text-pd-text-secondary hover:border-pd-accent/50"
            )}
          >
            Drug Pipeline ({drugs.length})
          </button>
          <button
            onClick={() => setActiveTab("editing")}
            className={cn(
              "px-4 py-2 rounded-lg text-sm font-medium transition-all",
              activeTab === "editing"
                ? "bg-pd-accent text-white"
                : "bg-pd-secondary border border-pd-border text-pd-text-secondary hover:border-pd-accent/50"
            )}
          >
            Editing Assets ({editing_assets.length})
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === "chart" && (
          <div className="pd-card p-6">
            <h3 className="text-lg font-semibold text-pd-text-primary mb-4">
              Stock Performance
            </h3>
            {company.ticker ? (
              <TradingViewWidget ticker={company.ticker} />
            ) : (
              <div className="h-[400px] flex items-center justify-center text-pd-text-muted">
                <div className="text-center">
                  <div className="text-6xl mb-4">🔒</div>
                  <p className="text-lg font-medium">Private Company</p>
                  <p className="text-sm mt-2">Stock data is not available for private companies.</p>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === "drugs" && (
          <div className="pd-card p-6">
            <h3 className="text-lg font-semibold text-pd-text-primary mb-4">
              Drug Pipeline
            </h3>
            {drugs.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-pd-border">
                      <th className="text-left py-3 px-4 text-pd-text-muted font-medium">Drug</th>
                      <th className="text-left py-3 px-4 text-pd-text-muted font-medium">Type</th>
                      <th className="text-center py-3 px-4 text-pd-text-muted font-medium">Role</th>
                      <th className="text-center py-3 px-4 text-pd-text-muted font-medium">Status</th>
                      <th className="text-center py-3 px-4 text-pd-text-muted font-medium">Bio</th>
                      <th className="text-center py-3 px-4 text-pd-text-muted font-medium">Chem</th>
                      <th className="text-center py-3 px-4 text-pd-text-muted font-medium">Tract</th>
                      <th className="text-center py-3 px-4 text-pd-text-muted font-medium">Total Score</th>
                    </tr>
                  </thead>
                  <tbody>
                    {drugs.map((d) => (
                      <tr key={d.drug.id} className="border-b border-pd-border/50 hover:bg-pd-secondary/50">
                        <td className="py-3 px-4">
                          <Link
                            href={`/drug/${d.drug.id}`}
                            className="font-medium text-pd-accent hover:underline"
                          >
                            {d.drug.name}
                          </Link>
                        </td>
                        <td className="py-3 px-4 text-pd-text-secondary">
                          {d.drug.drug_type || "-"}
                        </td>
                        <td className="text-center py-3 px-4">
                          <span className="text-xs px-2 py-0.5 rounded bg-pd-secondary text-pd-text-secondary">
                            {d.role || "Unknown"}
                          </span>
                        </td>
                        <td className="text-center py-3 px-4">
                          {d.drug.fda_approved ? (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-900/30 text-green-400 border border-green-800">
                              Approved
                            </span>
                          ) : (
                            <span className="text-pd-text-muted">-</span>
                          )}
                        </td>
                        <td className="text-center py-3 px-4 text-pd-text-secondary">
                          {d.score?.bio_score?.toFixed(1) ?? "-"}
                        </td>
                        <td className="text-center py-3 px-4 text-pd-text-secondary">
                          {d.score?.chem_score?.toFixed(1) ?? "-"}
                        </td>
                        <td className="text-center py-3 px-4 text-pd-text-secondary">
                          {d.score?.tractability_score?.toFixed(1) ?? "-"}
                        </td>
                        <td className="text-center py-3 px-4">
                          {d.score?.total_score ? (
                            <ScoreBadge score={d.score.total_score} size="sm" />
                          ) : (
                            <span className="text-pd-text-muted">-</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-pd-text-muted text-center py-8">
                No drugs in pipeline. This company may focus on epigenetic editing platforms.
              </p>
            )}
          </div>
        )}

        {activeTab === "editing" && (
          <div className="pd-card p-6">
            <h3 className="text-lg font-semibold text-pd-text-primary mb-4">
              Epigenetic Editing Assets
            </h3>
            {editing_assets.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-pd-border">
                      <th className="text-left py-3 px-4 text-pd-text-muted font-medium">Program</th>
                      <th className="text-left py-3 px-4 text-pd-text-muted font-medium">Target Gene</th>
                      <th className="text-center py-3 px-4 text-pd-text-muted font-medium">DBD</th>
                      <th className="text-center py-3 px-4 text-pd-text-muted font-medium">Phase</th>
                      <th className="text-center py-3 px-4 text-pd-text-muted font-medium">Bio</th>
                      <th className="text-center py-3 px-4 text-pd-text-muted font-medium">Modality</th>
                      <th className="text-center py-3 px-4 text-pd-text-muted font-medium">Durability</th>
                      <th className="text-center py-3 px-4 text-pd-text-muted font-medium">Total Score</th>
                    </tr>
                  </thead>
                  <tbody>
                    {editing_assets.map((e) => (
                      <tr key={e.asset.id} className="border-b border-pd-border/50 hover:bg-pd-secondary/50">
                        <td className="py-3 px-4">
                          <Link
                            href={`/editing/${e.asset.id}`}
                            className="font-medium text-pd-accent hover:underline"
                          >
                            {e.asset.name}
                          </Link>
                        </td>
                        <td className="py-3 px-4">
                          <span className="font-mono text-pd-text-primary">
                            {e.asset.target_gene_symbol || "-"}
                          </span>
                        </td>
                        <td className="text-center py-3 px-4">
                          <span className="text-xs px-2 py-0.5 rounded bg-pd-secondary text-pd-text-secondary">
                            {e.asset.dbd_type || "-"}
                          </span>
                        </td>
                        <td className="text-center py-3 px-4">
                          <PhaseBadge phase={e.asset.phase} />
                        </td>
                        <td className="text-center py-3 px-4 text-pd-text-secondary">
                          {e.score?.target_bio_score?.toFixed(1) ?? "-"}
                        </td>
                        <td className="text-center py-3 px-4 text-pd-text-secondary">
                          {e.score?.editing_modality_score?.toFixed(1) ?? "-"}
                        </td>
                        <td className="text-center py-3 px-4 text-pd-text-secondary">
                          {e.score?.durability_score?.toFixed(1) ?? "-"}
                        </td>
                        <td className="text-center py-3 px-4">
                          {e.score?.total_editing_score ? (
                            <ScoreBadge score={e.score.total_editing_score} size="sm" />
                          ) : (
                            <span className="text-pd-text-muted">-</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-pd-text-muted text-center py-8">
                No editing programs. This company may focus on traditional drug development.
              </p>
            )}
          </div>
        )}

        {/* Company Info Footer */}
        <div className="pd-card p-6 mt-6">
          <h3 className="text-lg font-semibold text-pd-text-primary mb-4">Company Info</h3>
          <div className="grid md:grid-cols-3 gap-4">
            {company.headquarters && (
              <div>
                <div className="text-pd-text-muted text-sm mb-1">Headquarters</div>
                <div className="text-pd-text-primary">{company.headquarters}</div>
              </div>
            )}
            {company.founded_year && (
              <div>
                <div className="text-pd-text-muted text-sm mb-1">Founded</div>
                <div className="text-pd-text-primary">{company.founded_year}</div>
              </div>
            )}
            {company.employee_count && (
              <div>
                <div className="text-pd-text-muted text-sm mb-1">Employees</div>
                <div className="text-pd-text-primary">{company.employee_count.toLocaleString()}</div>
              </div>
            )}
            {company.exchange && (
              <div>
                <div className="text-pd-text-muted text-sm mb-1">Exchange</div>
                <div className="text-pd-text-primary">{company.exchange}</div>
              </div>
            )}
            {company.sector && (
              <div>
                <div className="text-pd-text-muted text-sm mb-1">Sector</div>
                <div className="text-pd-text-primary">{company.sector}</div>
              </div>
            )}
            {company.industry && (
              <div>
                <div className="text-pd-text-muted text-sm mb-1">Industry</div>
                <div className="text-pd-text-primary">{company.industry}</div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
