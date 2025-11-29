"use client"

import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import Link from "next/link"
import { targetsApi } from "@/lib/api"
import { ScoreBadge, DataTable, WatchButton } from "@/components/data"
import { cn } from "@/lib/utils"

interface TargetData {
  target: {
    id: number
    symbol: string
    full_name: string | null
    family: string
    target_class: string
    ot_target_id: string | null
    uniprot_id: string | null
    ensembl_id: string | null
  }
  drugs: Array<{
    drug_id: number
    mechanism_of_action: string | null
    is_primary_target: boolean
    epi_drugs: {
      id: number
      name: string
      chembl_id: string | null
      drug_type: string | null
      fda_approved: boolean
    }
  }>
  signatures: Array<{
    signature_id: number
    role: string | null
    epi_signatures: {
      id: number
      name: string
      description: string | null
    }
  }>
}

type Tab = "overview" | "drugs" | "signatures"

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

export default function TargetPage() {
  const params = useParams()
  const [data, setData] = useState<TargetData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<Tab>("overview")

  useEffect(() => {
    async function load() {
      try {
        setLoading(true)
        const res = await targetsApi.get(String(params.id))
        setData(res)
      } catch {
        setError("Failed to load target details")
      } finally {
        setLoading(false)
      }
    }
    if (params.id) load()
  }, [params.id])

  if (loading) {
    return (
      <div className="min-h-screen bg-pd-primary flex items-center justify-center">
        <div className="text-pd-text-muted">Loading target...</div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-pd-primary flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-400 mb-4">{error || "Target not found"}</div>
          <Link href="/explore/targets" className="text-pd-accent hover:underline">
            Back to Target Landscape
          </Link>
        </div>
      </div>
    )
  }

  const { target, drugs, signatures } = data

  const tabs: { key: Tab; label: string; count?: number }[] = [
    { key: "overview", label: "Overview" },
    { key: "drugs", label: "Drugs", count: drugs.length },
    { key: "signatures", label: "Signatures", count: signatures.length },
  ]

  // Drug table columns
  const drugColumns = [
    {
      key: "epi_drugs.name",
      label: "Drug Name",
      sortable: true,
      render: (_: unknown, row: typeof drugs[0]) => (
        <Link
          href={`/drug/${row.drug_id}`}
          className="font-medium text-pd-accent hover:underline"
        >
          {row.epi_drugs.name}
        </Link>
      ),
    },
    {
      key: "mechanism_of_action",
      label: "Mechanism",
      sortable: true,
      className: "text-pd-text-secondary",
    },
    {
      key: "epi_drugs.drug_type",
      label: "Type",
      sortable: true,
      render: (_: unknown, row: typeof drugs[0]) => (
        <span className="text-pd-text-muted">{row.epi_drugs.drug_type || "-"}</span>
      ),
    },
    {
      key: "is_primary_target",
      label: "Primary",
      render: (_: unknown, row: typeof drugs[0]) =>
        row.is_primary_target ? (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-pd-accent/20 text-pd-accent">
            Primary
          </span>
        ) : (
          <span className="text-pd-text-muted">-</span>
        ),
    },
    {
      key: "epi_drugs.fda_approved",
      label: "Status",
      render: (_: unknown, row: typeof drugs[0]) =>
        row.epi_drugs.fda_approved ? (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-pd-score-high/20 text-pd-score-high">
            Approved
          </span>
        ) : (
          <span className="text-pd-text-muted">Pipeline</span>
        ),
    },
  ]

  return (
    <div className="min-h-screen bg-pd-primary">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-2 text-pd-text-muted text-sm mb-2">
            <Link href="/explore/targets" className="hover:text-pd-accent">
              Targets
            </Link>
            <span>/</span>
            <span className="text-pd-text-secondary">{target.symbol}</span>
          </div>
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-4xl font-bold text-pd-text-primary mb-1">
                {target.symbol}
              </h1>
              <p className="text-lg text-pd-text-secondary">
                {target.full_name || "Epigenetic Target"}
              </p>
            </div>
            <div className="flex items-center gap-4">
              <WatchButton id={String(target.id)} type="target" name={target.symbol} />
              <div className="flex gap-2">
                <span className="inline-flex items-center px-3 py-1 rounded-lg text-sm bg-pd-card border border-pd-border text-pd-text-secondary">
                  {target.family}
                </span>
                <span className="inline-flex items-center px-3 py-1 rounded-lg text-sm bg-pd-card border border-pd-border text-pd-text-muted">
                  {target.target_class}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* External Resources */}
        <div className="pd-card p-4 mb-6">
          <h3 className="text-sm font-medium text-pd-text-muted mb-3">External Resources</h3>
          <div className="flex flex-wrap gap-2">
            {target.uniprot_id && (
              <ExternalLink
                href={`https://www.uniprot.org/uniprotkb/${target.uniprot_id}`}
                label="UniProt"
                icon="🧬"
              />
            )}
            {target.ot_target_id && (
              <ExternalLink
                href={`https://platform.opentargets.org/target/${target.ot_target_id}`}
                label="Open Targets"
                icon="🎯"
              />
            )}
            {target.ensembl_id && (
              <>
                <ExternalLink
                  href={`https://ensembl.org/Homo_sapiens/Gene/Summary?g=${target.ensembl_id}`}
                  label="Ensembl"
                  icon="🧪"
                />
                <ExternalLink
                  href={`https://alphafold.ebi.ac.uk/entry/${target.uniprot_id || target.ensembl_id}`}
                  label="AlphaFold"
                  icon="🔬"
                />
              </>
            )}
            <ExternalLink
              href={`https://pubmed.ncbi.nlm.nih.gov/?term=${encodeURIComponent(target.symbol)}`}
              label="PubMed"
              icon="📚"
            />
            <ExternalLink
              href={`https://www.genecards.org/cgi-bin/carddisp.pl?gene=${target.symbol}`}
              label="GeneCards"
              icon="🗂️"
            />
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
              {tab.count !== undefined && (
                <span className="ml-1.5 text-xs text-pd-text-muted">({tab.count})</span>
              )}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {activeTab === "overview" && (
          <div className="grid md:grid-cols-2 gap-6">
            {/* Target Details Card */}
            <div className="pd-card p-6">
              <h3 className="text-lg font-semibold text-pd-text-primary mb-4">
                Target Details
              </h3>
              <dl className="space-y-3">
                <div className="flex justify-between">
                  <dt className="text-pd-text-muted">Symbol</dt>
                  <dd className="text-pd-text-primary font-medium">{target.symbol}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-pd-text-muted">Family</dt>
                  <dd className="text-pd-text-primary">{target.family}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-pd-text-muted">Class</dt>
                  <dd className="text-pd-text-primary">{target.target_class}</dd>
                </div>
                {target.uniprot_id && (
                  <div className="flex justify-between">
                    <dt className="text-pd-text-muted">UniProt</dt>
                    <dd>
                      <a
                        href={`https://www.uniprot.org/uniprotkb/${target.uniprot_id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-pd-accent hover:underline"
                      >
                        {target.uniprot_id}
                      </a>
                    </dd>
                  </div>
                )}
                {target.ensembl_id && (
                  <div className="flex justify-between">
                    <dt className="text-pd-text-muted">Ensembl</dt>
                    <dd>
                      <a
                        href={`https://ensembl.org/Homo_sapiens/Gene/Summary?g=${target.ensembl_id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-pd-accent hover:underline"
                      >
                        {target.ensembl_id}
                      </a>
                    </dd>
                  </div>
                )}
                {target.ot_target_id && (
                  <div className="flex justify-between">
                    <dt className="text-pd-text-muted">Open Targets</dt>
                    <dd>
                      <a
                        href={`https://platform.opentargets.org/target/${target.ot_target_id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-pd-accent hover:underline"
                      >
                        View
                      </a>
                    </dd>
                  </div>
                )}
              </dl>
            </div>

            {/* Stats Card */}
            <div className="pd-card p-6">
              <h3 className="text-lg font-semibold text-pd-text-primary mb-4">
                Pipeline Summary
              </h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-4 bg-pd-secondary rounded-lg">
                  <div className="text-3xl font-bold text-pd-text-primary">{drugs.length}</div>
                  <div className="text-sm text-pd-text-muted">Total Drugs</div>
                </div>
                <div className="text-center p-4 bg-pd-secondary rounded-lg">
                  <div className="text-3xl font-bold text-pd-text-primary">
                    {drugs.filter((d) => d.epi_drugs.fda_approved).length}
                  </div>
                  <div className="text-sm text-pd-text-muted">Approved</div>
                </div>
                <div className="text-center p-4 bg-pd-secondary rounded-lg">
                  <div className="text-3xl font-bold text-pd-text-primary">
                    {drugs.filter((d) => d.is_primary_target).length}
                  </div>
                  <div className="text-sm text-pd-text-muted">Primary Target</div>
                </div>
                <div className="text-center p-4 bg-pd-secondary rounded-lg">
                  <div className="text-3xl font-bold text-pd-text-primary">
                    {signatures.length}
                  </div>
                  <div className="text-sm text-pd-text-muted">Signatures</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "drugs" && (
          <div>
            {drugs.length === 0 ? (
              <div className="text-center py-12 text-pd-text-muted">
                No drugs found targeting {target.symbol}
              </div>
            ) : (
              <DataTable
                columns={drugColumns}
                data={drugs}
                sortable={true}
                onRowClick={(row) => (window.location.href = `/drug/${row.drug_id}`)}
              />
            )}
          </div>
        )}

        {activeTab === "signatures" && (
          <div>
            {signatures.length === 0 ? (
              <div className="text-center py-12 text-pd-text-muted">
                No signatures associated with {target.symbol}
              </div>
            ) : (
              <div className="grid gap-4">
                {signatures.map((sig) => (
                  <div key={sig.signature_id} className="pd-card p-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="font-medium text-pd-text-primary">
                          {sig.epi_signatures.name}
                        </h4>
                        {sig.epi_signatures.description && (
                          <p className="text-sm text-pd-text-secondary mt-1">
                            {sig.epi_signatures.description}
                          </p>
                        )}
                      </div>
                      {sig.role && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-pd-border text-pd-text-secondary">
                          {sig.role}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
