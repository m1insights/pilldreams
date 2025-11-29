"use client"

import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import Link from "next/link"
import { editingAssetsApi } from "@/lib/api"
import { ScoreBadge } from "@/components/data"
import { cn } from "@/lib/utils"

interface EditingAssetData {
  asset: {
    id: string
    name: string
    sponsor: string | null
    modality: string
    delivery_type: string | null
    dbd_type: string | null
    effector_type: string | null
    effector_domains: string[] | null
    target_gene_symbol: string | null
    target_locus_description: string | null
    primary_indication: string | null
    phase: number
    status: string
    mechanism_summary: string | null
    description: string | null
    source_url: string | null
  }
  scores: {
    target_bio_score: number | null
    editing_modality_score: number | null
    durability_score: number | null
    total_editing_score: number | null
    score_rationale: string | null
  } | null
  target_genes: Array<{
    target_gene_id: string
    is_primary_target: boolean
    mechanism_at_target: string | null
    epi_editing_target_genes: {
      id: string
      symbol: string
      full_name: string | null
      gene_category: string | null
    } | null
  }>
}

type Tab = "overview" | "mechanism" | "target"

// Score Ring component for visual display
function ScoreRing({ score, label, color }: { score: number | null; label: string; color: string }) {
  const pct = score ? Math.min(100, score) : 0
  const circumference = 2 * Math.PI * 40
  const offset = circumference - (pct / 100) * circumference

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-24 h-24">
        <svg className="w-24 h-24 transform -rotate-90">
          <circle
            cx="48"
            cy="48"
            r="40"
            stroke="currentColor"
            strokeWidth="8"
            fill="none"
            className="text-pd-border"
          />
          <circle
            cx="48"
            cy="48"
            r="40"
            stroke="currentColor"
            strokeWidth="8"
            fill="none"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            className={color}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-xl font-bold text-pd-text-primary">
            {score?.toFixed(0) ?? "-"}
          </span>
        </div>
      </div>
      <span className="text-sm text-pd-text-muted mt-2">{label}</span>
    </div>
  )
}

// External link component
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

// DBD Type badge
function DBDBadge({ dbd }: { dbd: string | null }) {
  if (!dbd) return <span className="text-pd-text-muted">Unknown</span>

  const info: Record<string, { label: string; desc: string; color: string }> = {
    "CRISPR_dCas9": {
      label: "CRISPR dCas9",
      desc: "Catalytically dead Cas9 - most versatile, requires PAM sequence",
      color: "bg-indigo-900/30 text-indigo-400 border-indigo-800"
    },
    "ZF": {
      label: "Zinc Finger",
      desc: "Engineered zinc finger proteins - no PAM requirement, compact",
      color: "bg-cyan-900/30 text-cyan-400 border-cyan-800"
    },
    "TALE": {
      label: "TALE",
      desc: "Transcription Activator-Like Effector - highly specific, larger size",
      color: "bg-amber-900/30 text-amber-400 border-amber-800"
    },
    "Base_Editor": {
      label: "Base Editor",
      desc: "Chemical base conversion - permanent DNA change",
      color: "bg-pink-900/30 text-pink-400 border-pink-800"
    },
  }

  const data = info[dbd] || { label: dbd, desc: "", color: "bg-pd-border text-pd-text-secondary" }

  return (
    <div>
      <span className={cn(
        "inline-flex items-center px-3 py-1 rounded-lg text-sm font-medium border",
        data.color
      )}>
        {data.label}
      </span>
      {data.desc && (
        <p className="text-xs text-pd-text-muted mt-1">{data.desc}</p>
      )}
    </div>
  )
}

// Phase badge
function PhaseBadge({ phase, status }: { phase: number; status: string }) {
  if (phase === 0) {
    return (
      <span className="inline-flex items-center px-3 py-1 rounded-lg text-sm font-medium bg-gray-800 text-gray-400 border border-gray-700">
        Preclinical ({status})
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
      "inline-flex items-center px-3 py-1 rounded-lg text-sm font-medium border",
      colors[phase] || "bg-pd-border text-pd-text-secondary"
    )}>
      Phase {phase} ({status})
    </span>
  )
}

export default function EditingAssetPage() {
  const params = useParams()
  const [data, setData] = useState<EditingAssetData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<Tab>("overview")

  useEffect(() => {
    async function load() {
      try {
        setLoading(true)
        const res = await editingAssetsApi.get(String(params.id))
        setData(res)
      } catch {
        setError("Failed to load editing asset details")
      } finally {
        setLoading(false)
      }
    }
    if (params.id) load()
  }, [params.id])

  if (loading) {
    return (
      <div className="min-h-screen bg-pd-primary flex items-center justify-center">
        <div className="text-pd-text-muted">Loading editing program...</div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-pd-primary flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-400 mb-4">{error || "Program not found"}</div>
          <Link href="/explore/editing" className="text-pd-accent hover:underline">
            Back to Editing Programs
          </Link>
        </div>
      </div>
    )
  }

  const { asset, scores, target_genes } = data

  const tabs: { key: Tab; label: string }[] = [
    { key: "overview", label: "Overview" },
    { key: "mechanism", label: "Mechanism" },
    { key: "target", label: "Target Gene" },
  ]

  return (
    <div className="min-h-screen bg-pd-primary">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-2 text-pd-text-muted text-sm mb-2">
            <Link href="/explore/editing" className="hover:text-pd-accent">
              Editing Programs
            </Link>
            <span>/</span>
            <span className="text-pd-text-secondary">{asset.name}</span>
          </div>
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-4xl font-bold text-pd-text-primary mb-1">
                {asset.name}
              </h1>
              <p className="text-lg text-pd-text-secondary">
                {asset.sponsor || "Unknown Sponsor"} • Epigenetic Editor
              </p>
            </div>
            <div className="flex items-center gap-4">
              <PhaseBadge phase={asset.phase} status={asset.status} />
              {scores?.total_editing_score && (
                <ScoreBadge score={scores.total_editing_score} size="lg" />
              )}
            </div>
          </div>
        </div>

        {/* Score Rings */}
        {scores && (
          <div className="pd-card p-6 mb-6">
            <h3 className="text-lg font-semibold text-pd-text-primary mb-4">EditingScore Breakdown</h3>
            <div className="flex justify-around items-center">
              <ScoreRing
                score={scores.target_bio_score}
                label="Target Biology (50%)"
                color="text-blue-500"
              />
              <ScoreRing
                score={scores.editing_modality_score}
                label="Modality (30%)"
                color="text-purple-500"
              />
              <ScoreRing
                score={scores.durability_score}
                label="Durability (20%)"
                color="text-green-500"
              />
              <div className="flex flex-col items-center">
                <div className="w-24 h-24 rounded-full bg-pd-accent/20 border-4 border-pd-accent flex items-center justify-center">
                  <span className="text-2xl font-bold text-pd-accent">
                    {scores.total_editing_score?.toFixed(0) ?? "-"}
                  </span>
                </div>
                <span className="text-sm text-pd-text-muted mt-2">Total Score</span>
              </div>
            </div>
            {scores.score_rationale && (
              <p className="text-sm text-pd-text-muted mt-4 text-center italic">
                {scores.score_rationale}
              </p>
            )}
          </div>
        )}

        {/* External Resources */}
        <div className="pd-card p-4 mb-6">
          <h3 className="text-sm font-medium text-pd-text-muted mb-3">External Resources</h3>
          <div className="flex flex-wrap gap-2">
            {asset.target_gene_symbol && (
              <>
                <ExternalLink
                  href={`https://pubmed.ncbi.nlm.nih.gov/?term=${encodeURIComponent(asset.target_gene_symbol + " epigenetic editing")}`}
                  label="PubMed"
                  icon="📚"
                />
                <ExternalLink
                  href={`https://www.genecards.org/cgi-bin/carddisp.pl?gene=${asset.target_gene_symbol}`}
                  label="GeneCards"
                  icon="🗂️"
                />
              </>
            )}
            {asset.sponsor && (
              <ExternalLink
                href={`https://www.google.com/search?q=${encodeURIComponent(asset.sponsor + " " + asset.name)}`}
                label={`${asset.sponsor} News`}
                icon="🔍"
              />
            )}
            {asset.source_url && (
              <ExternalLink
                href={asset.source_url}
                label="Source"
                icon="🔗"
              />
            )}
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-6 border-b border-pd-border">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={cn(
                "px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px",
                activeTab === tab.key
                  ? "border-pd-accent text-pd-text-primary"
                  : "border-transparent text-pd-text-muted hover:text-pd-text-secondary"
              )}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {activeTab === "overview" && (
          <div className="grid md:grid-cols-2 gap-6">
            {/* Platform Details */}
            <div className="pd-card p-6">
              <h3 className="text-lg font-semibold text-pd-text-primary mb-4">
                Platform Details
              </h3>
              <dl className="space-y-4">
                <div>
                  <dt className="text-sm text-pd-text-muted mb-1">DNA Binding Domain</dt>
                  <dd><DBDBadge dbd={asset.dbd_type} /></dd>
                </div>
                <div>
                  <dt className="text-sm text-pd-text-muted mb-1">Delivery Type</dt>
                  <dd className="text-pd-text-primary">
                    {asset.delivery_type || "Unknown"}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm text-pd-text-muted mb-1">Effector Type</dt>
                  <dd className="text-pd-text-primary capitalize">
                    {asset.effector_type?.replace(/_/g, " ") || "Unknown"}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm text-pd-text-muted mb-1">Effector Domains</dt>
                  <dd className="flex flex-wrap gap-2">
                    {asset.effector_domains?.map((d, i) => (
                      <span key={i} className="px-2 py-1 rounded bg-pd-secondary border border-pd-border text-sm">
                        {d}
                      </span>
                    )) || <span className="text-pd-text-muted">-</span>}
                  </dd>
                </div>
              </dl>
            </div>

            {/* Clinical Info */}
            <div className="pd-card p-6">
              <h3 className="text-lg font-semibold text-pd-text-primary mb-4">
                Clinical Information
              </h3>
              <dl className="space-y-4">
                <div>
                  <dt className="text-sm text-pd-text-muted mb-1">Primary Indication</dt>
                  <dd className="text-pd-text-primary">
                    {asset.primary_indication || "Not specified"}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm text-pd-text-muted mb-1">Development Stage</dt>
                  <dd>
                    <PhaseBadge phase={asset.phase} status={asset.status} />
                  </dd>
                </div>
                <div>
                  <dt className="text-sm text-pd-text-muted mb-1">Sponsor</dt>
                  <dd className="text-pd-text-primary">
                    {asset.sponsor || "Unknown"}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm text-pd-text-muted mb-1">Target Gene</dt>
                  <dd className="font-mono text-pd-accent">
                    {asset.target_gene_symbol || "-"}
                  </dd>
                </div>
              </dl>
            </div>
          </div>
        )}

        {activeTab === "mechanism" && (
          <div className="pd-card p-6">
            <h3 className="text-lg font-semibold text-pd-text-primary mb-4">
              Mechanism of Action
            </h3>
            {asset.mechanism_summary ? (
              <div className="prose prose-invert max-w-none">
                <p className="text-pd-text-secondary leading-relaxed">
                  {asset.mechanism_summary}
                </p>
              </div>
            ) : (
              <p className="text-pd-text-muted">No mechanism information available.</p>
            )}

            <div className="mt-6 pt-6 border-t border-pd-border">
              <h4 className="font-medium text-pd-text-primary mb-3">Target Locus</h4>
              <p className="text-pd-text-secondary">
                {asset.target_locus_description || "Not specified"}
              </p>
            </div>

            {asset.description && (
              <div className="mt-6 pt-6 border-t border-pd-border">
                <h4 className="font-medium text-pd-text-primary mb-3">Additional Details</h4>
                <p className="text-pd-text-secondary">
                  {asset.description}
                </p>
              </div>
            )}
          </div>
        )}

        {activeTab === "target" && (
          <div className="pd-card p-6">
            <h3 className="text-lg font-semibold text-pd-text-primary mb-4">
              Target Gene: {asset.target_gene_symbol || "Unknown"}
            </h3>
            {target_genes.length > 0 ? (
              <div className="space-y-4">
                {target_genes.map((tg, i) => (
                  <div key={i} className="bg-pd-secondary rounded-lg p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <span className="font-mono text-lg text-pd-accent">
                          {tg.epi_editing_target_genes?.symbol || "Unknown"}
                        </span>
                        {tg.is_primary_target && (
                          <span className="ml-2 px-2 py-0.5 text-xs rounded bg-pd-accent/20 text-pd-accent">
                            Primary Target
                          </span>
                        )}
                      </div>
                      <span className="text-sm text-pd-text-muted capitalize">
                        {tg.epi_editing_target_genes?.gene_category?.replace(/_/g, " ") || "Other"}
                      </span>
                    </div>
                    {tg.epi_editing_target_genes?.full_name && (
                      <p className="text-pd-text-secondary text-sm mb-2">
                        {tg.epi_editing_target_genes.full_name}
                      </p>
                    )}
                    {tg.mechanism_at_target && (
                      <p className="text-pd-text-muted text-sm">
                        <strong>Mechanism:</strong> {tg.mechanism_at_target}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-pd-text-muted">
                No linked target genes found. The target gene symbol is: <strong>{asset.target_gene_symbol}</strong>
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
