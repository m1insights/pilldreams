"use client"

import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import Link from "next/link"
import { drugsApi } from "@/lib/api"
import { ScoreBadge, WatchButton } from "@/components/data"
import { cn } from "@/lib/utils"

interface DrugDetailData {
  drug: {
    id: string
    name: string
    chembl_id: string | null
    drug_type: string | null
    fda_approved: boolean
    first_approval_date: string | null
    source: string | null
  }
  targets: Array<{
    target_id: string
    mechanism_of_action: string | null
    is_primary_target: boolean
    epi_targets: {
      id: string
      symbol: string
      full_name: string | null
      family: string
      uniprot_id: string | null
      ot_target_id: string | null
    }
  }>
  indications: Array<{
    indication_id: string
    max_phase: number | null
    epi_indications: {
      id: string
      name: string
      efo_id: string | null
    }
  }>
  scores: Array<{
    id: string
    indication_id: string
    bio_score: number | null
    chem_score: number | null
    tractability_score: number | null
    total_score: number | null
    epi_indications: {
      name: string
    }
  }>
  chemistry: {
    chem_score: number | null
    p_act_median: number | null
    p_act_best: number | null
    p_off_best: number | null
    delta_p: number | null
    n_activities_primary: number | null
    n_activities_total: number | null
  } | null
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

// Score bar component for visualizing individual scores
function ScoreBar({ label, value, color, description }: { label: string; value: number | null; color: string; description?: string }) {
  const width = value ? Math.min(100, value) : 0
  return (
    <div className="space-y-1">
      <div className="flex justify-between items-center text-sm">
        <span className="text-pd-text-secondary">{label}</span>
        <span className="font-medium text-pd-text-primary">{value?.toFixed(1) ?? "-"}</span>
      </div>
      <div className="h-3 bg-pd-border rounded-full overflow-hidden">
        <div
          className={cn("h-full rounded-full transition-all", color)}
          style={{ width: `${width}%` }}
        />
      </div>
      {description && <p className="text-xs text-pd-text-muted">{description}</p>}
    </div>
  )
}

// Phase badge
function PhaseBadge({ phase }: { phase: number | null }) {
  if (!phase) return <span className="text-pd-text-muted">-</span>
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

export default function DrugDetailPage() {
  const params = useParams()
  const [data, setData] = useState<DrugDetailData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
      try {
        setLoading(true)
        const res = await drugsApi.get(String(params.id))
        setData(res)
      } catch {
        setError("Failed to load drug details")
      } finally {
        setLoading(false)
      }
    }
    if (params.id) load()
  }, [params.id])

  if (loading) {
    return (
      <div className="min-h-screen bg-pd-primary flex items-center justify-center">
        <div className="text-pd-text-muted">Loading drug details...</div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-pd-primary flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-400 mb-4">{error || "Drug not found"}</div>
          <Link href="/explore/drugs" className="text-pd-accent hover:underline">
            Back to Drug Pipeline
          </Link>
        </div>
      </div>
    )
  }

  const { drug, targets, scores, chemistry, indications } = data

  // Find best score
  const bestScore = scores.reduce((best, s) => {
    if (!s.total_score) return best
    if (!best || s.total_score > best.total_score!) return s
    return best
  }, null as typeof scores[0] | null)

  // Get max phase from indications
  const maxPhase = indications.reduce((max, ind) => {
    return ind.max_phase && ind.max_phase > (max || 0) ? ind.max_phase : max
  }, null as number | null)

  return (
    <div className="min-h-screen bg-pd-primary">
      <div className="container mx-auto px-4 py-8">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-pd-text-muted text-sm mb-4">
          <Link href="/explore/drugs" className="hover:text-pd-accent">
            Drugs
          </Link>
          <span>/</span>
          <span className="text-pd-text-secondary">{drug.name}</span>
        </div>

        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4 mb-8">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-4xl font-bold text-pd-text-primary">{drug.name}</h1>
              {drug.fda_approved && (
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-pd-score-high/20 text-pd-score-high border border-pd-score-high/30">
                  FDA Approved
                </span>
              )}
              {maxPhase && <PhaseBadge phase={maxPhase} />}
            </div>
            <p className="text-pd-text-secondary">{drug.drug_type || "Small molecule"}</p>
            {drug.chembl_id && (
              <p className="text-pd-text-muted text-sm mt-1">ChEMBL: {drug.chembl_id}</p>
            )}
          </div>

          {/* Actions */}
          <div className="flex items-center gap-4">
            <WatchButton id={drug.id} type="drug" name={drug.name} />
            {/* Total Score Badge */}
            {bestScore?.total_score && (
              <div className="flex flex-col items-center">
                <ScoreBadge score={bestScore.total_score} size="lg" />
                <span className="text-pd-text-muted text-xs mt-1">TotalScore</span>
              </div>
            )}
          </div>
        </div>

        {/* External Links */}
        <div className="pd-card p-4 mb-6">
          <h3 className="text-sm font-medium text-pd-text-muted mb-3">External Resources</h3>
          <div className="flex flex-wrap gap-2">
            {drug.chembl_id && (
              <>
                <ExternalLink
                  href={`https://www.ebi.ac.uk/chembl/compound_report_card/${drug.chembl_id}/`}
                  label="ChEMBL"
                  icon="🧪"
                />
                <ExternalLink
                  href={`https://pubmed.ncbi.nlm.nih.gov/?term=${encodeURIComponent(drug.name)}`}
                  label="PubMed"
                  icon="📚"
                />
                <ExternalLink
                  href={`https://platform.opentargets.org/drug/${drug.chembl_id}`}
                  label="Open Targets"
                  icon="🎯"
                />
                <ExternalLink
                  href={`https://go.drugbank.com/unearth/q?utf8=%E2%9C%93&searcher=drugs&query=${encodeURIComponent(drug.name)}`}
                  label="DrugBank"
                  icon="💊"
                />
                <ExternalLink
                  href={`https://clinicaltrials.gov/search?term=${encodeURIComponent(drug.name)}`}
                  label="ClinicalTrials.gov"
                  icon="🏥"
                />
              </>
            )}
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-6 mb-8">
          {/* Score Breakdown Card */}
          <div className="pd-card p-6">
            <h3 className="text-lg font-semibold text-pd-text-primary mb-4">Score Breakdown</h3>
            {bestScore ? (
              <div className="space-y-4">
                <ScoreBar
                  label="Biological Rationale"
                  value={bestScore.bio_score}
                  color="bg-blue-500"
                  description="Target-disease association strength"
                />
                <ScoreBar
                  label="Chemistry Quality"
                  value={bestScore.chem_score}
                  color="bg-purple-500"
                  description="Potency, selectivity & data richness"
                />
                <ScoreBar
                  label="Tractability"
                  value={bestScore.tractability_score}
                  color="bg-green-500"
                  description="Target druggability assessment"
                />
                <div className="pt-4 border-t border-pd-border">
                  <div className="flex justify-between items-center">
                    <span className="text-pd-text-primary font-medium">Total Score</span>
                    <span className="text-2xl font-bold text-pd-accent">
                      {bestScore.total_score?.toFixed(1)}
                    </span>
                  </div>
                  <p className="text-xs text-pd-text-muted mt-1">
                    50% Bio + 30% Chem + 20% Tract
                  </p>
                </div>
              </div>
            ) : (
              <p className="text-pd-text-muted">No score data available</p>
            )}
          </div>

          {/* Chemistry Metrics Card */}
          <div className="pd-card p-6">
            <h3 className="text-lg font-semibold text-pd-text-primary mb-4">Chemistry Metrics</h3>
            {chemistry ? (
              <div className="space-y-3">
                <div className="flex justify-between items-center py-2 border-b border-pd-border">
                  <span className="text-pd-text-secondary">Best Potency (pAct)</span>
                  <span className="font-mono text-pd-text-primary">{chemistry.p_act_best?.toFixed(2) ?? "-"}</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-pd-border">
                  <span className="text-pd-text-secondary">Median Potency</span>
                  <span className="font-mono text-pd-text-primary">{chemistry.p_act_median?.toFixed(2) ?? "-"}</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-pd-border">
                  <span className="text-pd-text-secondary">Selectivity (ΔpAct)</span>
                  <span className="font-mono text-pd-text-primary">{chemistry.delta_p?.toFixed(2) ?? "-"}</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-pd-border">
                  <span className="text-pd-text-secondary">Primary Activities</span>
                  <span className="font-mono text-pd-text-primary">{chemistry.n_activities_primary ?? "-"}</span>
                </div>
                <div className="flex justify-between items-center py-2">
                  <span className="text-pd-text-secondary">Total Activities</span>
                  <span className="font-mono text-pd-text-primary">{chemistry.n_activities_total ?? "-"}</span>
                </div>
              </div>
            ) : (
              <p className="text-pd-text-muted">No chemistry data available</p>
            )}
          </div>

          {/* Targets Card */}
          <div className="pd-card p-6">
            <h3 className="text-lg font-semibold text-pd-text-primary mb-4">
              Targets <span className="text-pd-text-muted font-normal">({targets.length})</span>
            </h3>
            {targets.length > 0 ? (
              <div className="space-y-3">
                {targets.map((t) => (
                  <div key={t.target_id} className="p-3 bg-pd-secondary rounded-lg">
                    <div className="flex items-start justify-between">
                      <div>
                        <Link
                          href={`/target/${t.target_id}`}
                          className="font-medium text-pd-accent hover:underline"
                        >
                          {t.epi_targets.symbol}
                        </Link>
                        <p className="text-xs text-pd-text-muted mt-0.5">
                          {t.epi_targets.family}
                        </p>
                      </div>
                      {t.is_primary_target && (
                        <span className="text-xs px-2 py-0.5 rounded bg-pd-accent/20 text-pd-accent">
                          Primary
                        </span>
                      )}
                    </div>
                    {t.mechanism_of_action && (
                      <p className="text-sm text-pd-text-secondary mt-2">
                        {t.mechanism_of_action}
                      </p>
                    )}
                    {/* Target external links */}
                    <div className="flex gap-2 mt-2">
                      {t.epi_targets.uniprot_id && (
                        <a
                          href={`https://www.uniprot.org/uniprotkb/${t.epi_targets.uniprot_id}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-pd-accent hover:underline"
                        >
                          UniProt
                        </a>
                      )}
                      {t.epi_targets.ot_target_id && (
                        <a
                          href={`https://platform.opentargets.org/target/${t.epi_targets.ot_target_id}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-pd-accent hover:underline"
                        >
                          Open Targets
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-pd-text-muted">No targets found</p>
            )}
          </div>
        </div>

        {/* Indications & Scores Table */}
        <div className="pd-card p-6">
          <h3 className="text-lg font-semibold text-pd-text-primary mb-4">
            Indications & Scores <span className="text-pd-text-muted font-normal">({scores.length})</span>
          </h3>
          {scores.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-pd-border">
                    <th className="text-left py-3 px-4 text-pd-text-muted font-medium">Indication</th>
                    <th className="text-center py-3 px-4 text-pd-text-muted font-medium">Bio Score</th>
                    <th className="text-center py-3 px-4 text-pd-text-muted font-medium">Chem Score</th>
                    <th className="text-center py-3 px-4 text-pd-text-muted font-medium">Tractability</th>
                    <th className="text-center py-3 px-4 text-pd-text-muted font-medium">Total Score</th>
                  </tr>
                </thead>
                <tbody>
                  {scores.map((s) => (
                    <tr key={s.id} className="border-b border-pd-border/50 hover:bg-pd-secondary/50">
                      <td className="py-3 px-4">
                        <Link
                          href={`/indication/${s.indication_id}`}
                          className="text-pd-accent hover:underline"
                        >
                          {s.epi_indications.name}
                        </Link>
                      </td>
                      <td className="text-center py-3 px-4 text-pd-text-secondary">
                        {s.bio_score?.toFixed(1) ?? "-"}
                      </td>
                      <td className="text-center py-3 px-4 text-pd-text-secondary">
                        {s.chem_score?.toFixed(1) ?? "-"}
                      </td>
                      <td className="text-center py-3 px-4 text-pd-text-secondary">
                        {s.tractability_score?.toFixed(1) ?? "-"}
                      </td>
                      <td className="text-center py-3 px-4">
                        {s.total_score ? (
                          <ScoreBadge score={s.total_score} size="sm" />
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
            <p className="text-pd-text-muted">No indication data available</p>
          )}
        </div>

        {/* Deal History & Literature Section */}
        <div className="grid lg:grid-cols-2 gap-6 mt-6">
          {/* Deal History Card */}
          <div className="pd-card p-6">
            <h3 className="text-lg font-semibold text-pd-text-primary mb-4 flex items-center gap-2">
              <svg className="w-5 h-5 text-pd-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
              Deal History
            </h3>
            <div className="space-y-3">
              <div className="text-center py-8">
                <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-pd-secondary flex items-center justify-center">
                  <svg className="w-6 h-6 text-pd-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <p className="text-pd-text-muted text-sm">
                  Deal history and licensing information coming soon.
                </p>
                <p className="text-pd-text-muted text-xs mt-1">
                  Track acquisitions, partnerships, and licensing agreements.
                </p>
              </div>
            </div>
          </div>

          {/* Literature Citations Card */}
          <div className="pd-card p-6">
            <h3 className="text-lg font-semibold text-pd-text-primary mb-4 flex items-center gap-2">
              <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
              Literature & Citations
            </h3>
            <div className="space-y-3">
              <p className="text-pd-text-secondary text-sm">
                Explore scientific literature and clinical publications for {drug.name}.
              </p>
              <div className="flex flex-wrap gap-2">
                <a
                  href={`https://pubmed.ncbi.nlm.nih.gov/?term=${encodeURIComponent(drug.name)}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm bg-pd-secondary border border-pd-border text-pd-accent hover:bg-pd-accent/10 transition-colors"
                >
                  <span>Search PubMed</span>
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </a>
                <a
                  href={`https://scholar.google.com/scholar?q=${encodeURIComponent(drug.name)}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm bg-pd-secondary border border-pd-border text-pd-accent hover:bg-pd-accent/10 transition-colors"
                >
                  <span>Google Scholar</span>
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </a>
                {drug.chembl_id && (
                  <a
                    href={`https://www.ebi.ac.uk/chembl/compound_report_card/${drug.chembl_id}/#Bibliography`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm bg-pd-secondary border border-pd-border text-pd-accent hover:bg-pd-accent/10 transition-colors"
                  >
                    <span>ChEMBL References</span>
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                  </a>
                )}
              </div>
              <div className="mt-4 pt-4 border-t border-pd-border">
                <p className="text-xs text-pd-text-muted">
                  Citation counts and impact metrics will be added in a future update.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
