"use client"

import { useState } from "react"
import Link from "next/link"
import { cn } from "@/lib/utils"
import { useAuth } from "@/lib/auth/context"
import { useFeatureAccess, useUsageLimit, FEATURES, LIMITS } from "@/lib/hooks/useFeatureAccess"
import { LockedBadge } from "@/components/paywall"

interface ExportButtonProps {
  entityType: "drugs" | "targets" | "trials" | "scores" | "watchlist"
  entityIds?: string[] // For batch export
  drugId?: string // For deal memo export
  targetId?: string // For target landscape export
  indicationId?: string // For indication landscape export
  companyId?: string // For company portfolio export
  className?: string
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export function ExportButton({
  entityType,
  entityIds,
  drugId,
  targetId,
  indicationId,
  companyId,
  className,
}: ExportButtonProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [loading, setLoading] = useState<string | null>(null)
  const { session, user, profile } = useAuth()

  // Check feature access
  const csvAccess = useFeatureAccess(FEATURES.EXPORTS_CSV)
  const pptxAccess = useFeatureAccess(FEATURES.EXPORTS_PPTX)
  const exportLimit = useUsageLimit(LIMITS.EXPORTS_PER_MONTH)
  const pptxLimit = useUsageLimit(LIMITS.PPTX_EXPORTS_PER_MONTH)

  const isFreeUser = !profile || profile.subscription_tier === "free"

  const handleExport = async (format: "excel" | "csv" | "pptx") => {
    setLoading(format)

    // Check authentication
    if (!session?.access_token) {
      alert("Please sign in to export data. Exports require a Pro or Enterprise subscription.")
      setLoading(null)
      setIsOpen(false)
      return
    }

    // Check feature access for free users
    if (format === "pptx" && !pptxAccess.allowed) {
      alert(pptxAccess.reason || "PowerPoint exports require a Pro subscription.")
      setLoading(null)
      setIsOpen(false)
      return
    }

    if ((format === "excel" || format === "csv") && !csvAccess.allowed) {
      alert(csvAccess.reason || "Exports require a Pro subscription.")
      setLoading(null)
      setIsOpen(false)
      return
    }

    // Check usage limits
    if (format === "pptx" && !pptxLimit.allowed) {
      alert(pptxLimit.reason || "You've reached your monthly PowerPoint export limit.")
      setLoading(null)
      setIsOpen(false)
      return
    }

    if ((format === "excel" || format === "csv") && !exportLimit.allowed) {
      alert(exportLimit.reason || "You've reached your monthly export limit.")
      setLoading(null)
      setIsOpen(false)
      return
    }

    try {
      let endpoint: string
      let body: Record<string, unknown>

      if (format === "pptx") {
        // PowerPoint landscape export
        endpoint = `${API_BASE}/exports/landscape`

        if (drugId) {
          // Single drug deal memo
          body = {
            export_type: "pipeline",
            drug_ids: [drugId],
            include_scores: true,
            template: "executive",
          }
        } else if (targetId) {
          // Target landscape
          body = {
            export_type: "target",
            target_id: targetId,
            include_scores: true,
            template: "executive",
          }
        } else if (indicationId) {
          // Indication landscape
          body = {
            export_type: "indication",
            indication_id: indicationId,
            include_scores: true,
            template: "executive",
          }
        } else if (companyId) {
          // Company portfolio
          body = {
            export_type: "company",
            company_id: companyId,
            include_scores: true,
            template: "executive",
          }
        } else if (entityIds && entityIds.length > 0) {
          // Custom pipeline comparison
          body = {
            export_type: "pipeline",
            drug_ids: entityIds,
            include_scores: true,
            template: "comparison",
          }
        } else {
          alert("Please select items to export as PowerPoint")
          setLoading(null)
          setIsOpen(false)
          return
        }
      } else {
        // Excel/CSV export
        endpoint = `${API_BASE}/exports/${format === "excel" ? "excel" : "csv"}`
        body = {
          entity_type: entityType,
          entity_ids: entityIds || null,
          include_scores: true,
        }
      }

      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${session.access_token}`,
        },
        body: JSON.stringify(body),
      })

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: "Export failed" }))
        if (response.status === 401) {
          alert("Please sign in to export data.")
        } else if (response.status === 403) {
          alert(error.detail || "Export limit reached. Upgrade your plan for more exports.")
        } else {
          alert(error.detail || "Export failed. Please try again.")
        }
        return
      }

      // Download the file
      const blob = await response.blob()
      const contentDisposition = response.headers.get("Content-Disposition")
      const filenameMatch = contentDisposition?.match(/filename=(.+)/)
      const filename = filenameMatch?.[1] || `phase4_export.${format === "pptx" ? "pptx" : format === "excel" ? "xlsx" : "csv"}`

      const url = window.URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      a.remove()

    } catch (err) {
      console.error("Export failed:", err)
      alert("Export failed. Please check your connection and try again.")
    } finally {
      setLoading(null)
      setIsOpen(false)
    }
  }

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "flex items-center gap-2 px-4 py-2 rounded-lg bg-pd-secondary border border-pd-border text-pd-text-secondary text-sm font-medium hover:border-pd-accent transition-colors",
          className
        )}
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
        Export
        <svg className={cn("w-4 h-4 transition-transform", isOpen && "rotate-180")} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
          <div className="absolute right-0 top-full mt-2 w-48 rounded-lg bg-pd-secondary border border-pd-border shadow-lg z-50">
            <div className="p-2 space-y-1">
              <button
                onClick={() => handleExport("excel")}
                disabled={loading !== null}
                className="w-full flex items-center gap-3 px-3 py-2 rounded-md text-left text-sm text-pd-text-secondary hover:bg-pd-border hover:text-pd-text-primary transition-colors"
              >
                <svg className="w-5 h-5 text-green-500" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20M12.9,14.5L15.8,19H14L12,15.6L10,19H8.2L11.1,14.5L8.2,10H10L12,13.4L14,10H15.8L12.9,14.5Z" />
                </svg>
                {loading === "excel" ? "Exporting..." : "Excel (.xlsx)"}
              </button>
              <button
                onClick={() => handleExport("csv")}
                disabled={loading !== null}
                className="w-full flex items-center gap-3 px-3 py-2 rounded-md text-left text-sm text-pd-text-secondary hover:bg-pd-border hover:text-pd-text-primary transition-colors"
              >
                <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                {loading === "csv" ? "Exporting..." : "CSV (.csv)"}
              </button>
              {/* PPTX - available for drugs, targets, indications, companies */}
              {(drugId || targetId || indicationId || companyId || (entityIds && entityIds.length > 0)) && (
                <button
                  onClick={() => handleExport("pptx")}
                  disabled={loading !== null}
                  className="w-full flex items-center gap-3 px-3 py-2 rounded-md text-left text-sm text-pd-text-secondary hover:bg-pd-border hover:text-pd-text-primary transition-colors"
                >
                  <svg className="w-5 h-5 text-orange-500" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M6,2H14L20,8V20A2,2 0 0,1 18,22H6A2,2 0 0,1 4,20V4A2,2 0 0,1 6,2M13,3.5V9H18.5L13,3.5M8,11V13H9C9.55,13 10,13.45 10,14V15C10,15.55 9.55,16 9,16H8V18H6V11H8M12,18H10V11H12A2,2 0 0,1 14,13V16A2,2 0 0,1 12,18M12,13V16H12V13M18,11V18H16V14H15V18H13V11H18Z" />
                  </svg>
                  {loading === "pptx" ? "Generating..." : "Landscape Deck (.pptx)"}
                </button>
              )}
            </div>
            <div className="border-t border-pd-border px-3 py-2">
              {isFreeUser ? (
                <div className="flex items-center justify-between">
                  <p className="text-xs text-pd-text-muted">
                    Exports require Pro plan
                  </p>
                  <Link href="/pricing" className="text-xs text-pd-accent hover:underline">
                    Upgrade
                  </Link>
                </div>
              ) : (
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-pd-text-muted">CSV/Excel</span>
                    <span className="text-pd-text-secondary">
                      {exportLimit.limit === -1
                        ? "Unlimited"
                        : `${exportLimit.used || 0}/${exportLimit.limit || 0}`}
                    </span>
                  </div>
                  {(drugId || targetId || indicationId || companyId || entityIds?.length) && (
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-pd-text-muted">PowerPoint</span>
                      <span className="text-pd-text-secondary">
                        {pptxLimit.limit === -1
                          ? "Unlimited"
                          : `${pptxLimit.used || 0}/${pptxLimit.limit || 0}`}
                      </span>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
