"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { calendarApi } from "@/lib/api"
import type { TrialSummary, CalendarStats, ConferenceSummary, DateConfidence } from "@/lib/api/types"
import { DataTable } from "@/components/data"
import { cn } from "@/lib/utils"

// Date confidence badge component with color indicators
function DateConfidenceBadge({
  confidence,
  tooltip,
  size = "sm"
}: {
  confidence: DateConfidence
  tooltip: string
  size?: "sm" | "md"
}) {
  const configs: Record<DateConfidence, { icon: string; label: string; colors: string }> = {
    confirmed: {
      icon: "checkmark",
      label: "Confirmed",
      colors: "bg-green-900/30 text-green-400 border-green-800",
    },
    estimated: {
      icon: "clock",
      label: "Estimated",
      colors: "bg-yellow-900/30 text-yellow-400 border-yellow-800",
    },
    placeholder: {
      icon: "warning",
      label: "Placeholder",
      colors: "bg-red-900/30 text-red-400 border-red-800",
    },
    unknown: {
      icon: "question",
      label: "Unknown",
      colors: "bg-gray-900/30 text-gray-400 border-gray-700",
    },
  }

  const config = configs[confidence]
  const sizeClasses = size === "sm" ? "px-1.5 py-0.5 text-[10px]" : "px-2 py-1 text-xs"

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded font-medium border",
        config.colors,
        sizeClasses
      )}
      title={tooltip}
    >
      {confidence === "confirmed" && (
        <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
        </svg>
      )}
      {confidence === "estimated" && (
        <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
        </svg>
      )}
      {confidence === "placeholder" && (
        <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
        </svg>
      )}
      {confidence === "unknown" && (
        <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
        </svg>
      )}
      {config.label}
    </span>
  )
}

// Phase badge
function PhaseBadge({ phase }: { phase: string | null }) {
  if (!phase) return <span className="text-pd-text-muted">-</span>

  // Extract phase number for coloring
  const phaseMatch = phase.match(/(\d)/)
  const phaseNum = phaseMatch ? parseInt(phaseMatch[1]) : null

  const colors: Record<number, string> = {
    4: "bg-green-900/30 text-green-400 border-green-800",
    3: "bg-blue-900/30 text-blue-400 border-blue-800",
    2: "bg-yellow-900/30 text-yellow-400 border-yellow-800",
    1: "bg-orange-900/30 text-orange-400 border-orange-800",
  }

  return (
    <span className={cn(
      "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border",
      phaseNum ? colors[phaseNum] : "bg-pd-border text-pd-text-secondary"
    )}>
      {phase}
    </span>
  )
}

// Status badge
function StatusBadge({ status }: { status: string | null }) {
  if (!status) return <span className="text-pd-text-muted">-</span>

  const colors: Record<string, string> = {
    "Recruiting": "bg-green-900/30 text-green-400 border-green-800",
    "Active, not recruiting": "bg-blue-900/30 text-blue-400 border-blue-800",
    "Completed": "bg-purple-900/30 text-purple-400 border-purple-800",
    "Not yet recruiting": "bg-yellow-900/30 text-yellow-400 border-yellow-800",
    "Terminated": "bg-red-900/30 text-red-400 border-red-800",
    "Withdrawn": "bg-red-900/30 text-red-400 border-red-800",
    "Suspended": "bg-orange-900/30 text-orange-400 border-orange-800",
  }

  return (
    <span className={cn(
      "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border whitespace-nowrap",
      colors[status] || "bg-pd-border text-pd-text-secondary border-pd-border"
    )}>
      {status}
    </span>
  )
}

// Format date for display
function formatDate(dateStr: string | null): string {
  if (!dateStr) return "-"
  const date = new Date(dateStr)
  return date.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" })
}

// Calculate days until date
function daysUntil(dateStr: string | null): number | null {
  if (!dateStr) return null
  const date = new Date(dateStr)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const diffTime = date.getTime() - today.getTime()
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24))
}

// Filter options
const PHASE_FILTERS = [
  { key: "all", label: "All Phases" },
  { key: "PHASE3", label: "Phase 3" },
  { key: "PHASE2", label: "Phase 2" },
  { key: "PHASE1", label: "Phase 1" },
]

const CONFIDENCE_FILTERS = [
  { key: "all", label: "All Dates" },
  { key: "confirmed", label: "Confirmed Only" },
  { key: "hide_placeholders", label: "Hide Placeholders" },
]

const TIME_FILTERS = [
  { key: "upcoming", label: "Upcoming" },
  { key: "30", label: "30 Days" },
  { key: "90", label: "90 Days" },
  { key: "180", label: "6 Months" },
  { key: "all", label: "All Time" },
]

// Conference Card
function ConferenceCard({ conference }: { conference: ConferenceSummary }) {
  const daysAway = daysUntil(conference.start_date)
  const isPast = daysAway !== null && daysAway < 0
  const isUpcoming = daysAway !== null && daysAway >= 0 && daysAway <= 30

  return (
    <div className={cn(
      "pd-card p-4",
      isPast && "opacity-50",
      isUpcoming && "ring-1 ring-pd-accent/30"
    )}>
      <div className="flex justify-between items-start mb-2">
        <div>
          <h4 className="font-semibold text-pd-text-primary">{conference.short_name || conference.name}</h4>
          <p className="text-xs text-pd-text-muted">{conference.name}</p>
        </div>
        {isUpcoming && (
          <span className="text-xs px-2 py-0.5 bg-pd-accent/20 text-pd-accent rounded">
            {daysAway === 0 ? "Today" : `${daysAway}d`}
          </span>
        )}
      </div>
      <div className="text-sm text-pd-text-secondary">
        <div>{formatDate(conference.start_date)}</div>
        <div className="text-xs text-pd-text-muted">{conference.location}</div>
      </div>
      {conference.epigenetics_track && (
        <span className="inline-block mt-2 text-[10px] px-1.5 py-0.5 bg-purple-900/30 text-purple-400 border border-purple-800 rounded">
          Epigenetics Track
        </span>
      )}
    </div>
  )
}

export default function TrialCalendarPage() {
  const [trials, setTrials] = useState<TrialSummary[]>([])
  const [stats, setStats] = useState<CalendarStats | null>(null)
  const [conferences, setConferences] = useState<ConferenceSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Filters
  const [selectedPhase, setSelectedPhase] = useState("all")
  const [selectedConfidence, setSelectedConfidence] = useState("all")
  const [selectedTime, setSelectedTime] = useState("upcoming")

  // Load data
  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true)
        const [statsData, conferencesData] = await Promise.all([
          calendarApi.getStats(),
          calendarApi.getConferences(2025),
        ])
        setStats(statsData)
        setConferences(conferencesData)
      } catch (err) {
        setError("Failed to load calendar data")
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])

  // Load trials based on filters
  useEffect(() => {
    async function loadTrials() {
      try {
        const params: Parameters<typeof calendarApi.getTrials>[0] = {}

        // Phase filter
        if (selectedPhase !== "all") {
          params.phase = selectedPhase
        }

        // Confidence filter
        if (selectedConfidence === "confirmed") {
          params.date_confidence = "confirmed"
        } else if (selectedConfidence === "hide_placeholders") {
          params.exclude_placeholders = true
        }

        // Time filter - use upcoming endpoint for time-based queries
        if (selectedTime === "upcoming") {
          const data = await calendarApi.getUpcomingTrials({
            days: 365,
            phase_min: selectedPhase !== "all" ? parseInt(selectedPhase.replace("PHASE", "")) : undefined,
            exclude_placeholders: selectedConfidence === "hide_placeholders",
          })
          setTrials(data)
        } else if (selectedTime !== "all") {
          const days = parseInt(selectedTime)
          const data = await calendarApi.getUpcomingTrials({
            days,
            phase_min: selectedPhase !== "all" ? parseInt(selectedPhase.replace("PHASE", "")) : undefined,
            exclude_placeholders: selectedConfidence === "hide_placeholders",
          })
          setTrials(data)
        } else {
          params.limit = 200
          const data = await calendarApi.getTrials(params)
          // Sort by date
          data.sort((a, b) => {
            const dateA = a.primary_completion_date ? new Date(a.primary_completion_date).getTime() : Infinity
            const dateB = b.primary_completion_date ? new Date(b.primary_completion_date).getTime() : Infinity
            return dateA - dateB
          })
          setTrials(data)
        }
      } catch (err) {
        console.error("Failed to load trials:", err)
      }
    }
    loadTrials()
  }, [selectedPhase, selectedConfidence, selectedTime])

  // Table columns
  const columns = [
    {
      key: "primary_completion_date",
      label: "Readout Date",
      sortable: true,
      render: (value: string | null, row: TrialSummary) => {
        const days = daysUntil(value)
        return (
          <div className="flex flex-col gap-1">
            <span className="font-medium text-pd-text-primary">{formatDate(value)}</span>
            <div className="flex items-center gap-2">
              <DateConfidenceBadge
                confidence={row.date_confidence}
                tooltip={row.date_confidence_tooltip}
              />
              {days !== null && days >= 0 && days <= 90 && (
                <span className="text-xs text-pd-text-muted">
                  {days === 0 ? "Today" : `${days}d`}
                </span>
              )}
            </div>
          </div>
        )
      },
    },
    {
      key: "drug_name",
      label: "Drug",
      sortable: true,
      render: (value: string | null, row: TrialSummary) => (
        <div>
          {row.drug_id ? (
            <Link
              href={`/drug/${row.drug_id}`}
              className="font-medium text-pd-accent hover:underline"
            >
              {value || "Unknown"}
            </Link>
          ) : (
            <span className="font-medium text-pd-text-primary">{value || "Unknown"}</span>
          )}
        </div>
      ),
    },
    {
      key: "phase",
      label: "Phase",
      sortable: true,
      render: (value: string | null) => <PhaseBadge phase={value} />,
    },
    {
      key: "status",
      label: "Status",
      sortable: true,
      render: (value: string | null) => <StatusBadge status={value} />,
    },
    {
      key: "lead_sponsor",
      label: "Sponsor",
      sortable: true,
      render: (value: string | null) => (
        <span className="text-pd-text-secondary text-sm truncate max-w-[200px] block" title={value || ""}>
          {value || "-"}
        </span>
      ),
    },
    {
      key: "nct_id",
      label: "NCT ID",
      sortable: false,
      render: (value: string) => (
        <a
          href={`https://clinicaltrials.gov/study/${value}`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-pd-accent hover:underline text-sm"
        >
          {value}
        </a>
      ),
    },
  ]

  if (loading) {
    return (
      <div className="min-h-screen bg-pd-primary flex items-center justify-center">
        <div className="text-pd-text-muted">Loading calendar...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-pd-primary flex items-center justify-center">
        <div className="text-red-400">{error}</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-pd-primary">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-pd-text-primary mb-2">
            Trial Readout Calendar
          </h1>
          <p className="text-pd-text-secondary">
            Track clinical trial readouts for epigenetic oncology drugs
          </p>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-8">
            <div className="pd-card p-4">
              <div className="text-pd-text-muted text-sm mb-1">Total Trials</div>
              <div className="text-3xl font-bold text-pd-text-primary">{stats.total_trials}</div>
            </div>
            <div className="pd-card p-4">
              <div className="text-pd-text-muted text-sm mb-1">Next 30 Days</div>
              <div className="text-3xl font-bold text-green-400">{stats.upcoming_30_days}</div>
            </div>
            <div className="pd-card p-4">
              <div className="text-pd-text-muted text-sm mb-1">Next 90 Days</div>
              <div className="text-3xl font-bold text-yellow-400">{stats.upcoming_90_days}</div>
            </div>
            <div className="pd-card p-4">
              <div className="text-pd-text-muted text-sm mb-1">Confirmed Dates</div>
              <div className="text-3xl font-bold text-pd-accent">
                {stats.by_date_confidence?.confirmed || 0}
              </div>
            </div>
            <div className="pd-card p-4 col-span-2">
              <div className="text-pd-text-muted text-sm mb-2">Date Confidence</div>
              <div className="flex gap-3">
                <div className="flex items-center gap-1.5">
                  <div className="w-2 h-2 rounded-full bg-green-400"></div>
                  <span className="text-xs text-pd-text-secondary">
                    {stats.by_date_confidence?.confirmed || 0} confirmed
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  <div className="w-2 h-2 rounded-full bg-yellow-400"></div>
                  <span className="text-xs text-pd-text-secondary">
                    {stats.by_date_confidence?.estimated || 0} estimated
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  <div className="w-2 h-2 rounded-full bg-red-400"></div>
                  <span className="text-xs text-pd-text-secondary">
                    {stats.by_date_confidence?.placeholder || 0} placeholder
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Conferences Section */}
        {conferences.length > 0 && (
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-pd-text-primary mb-4">
              2025 Oncology Conferences
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
              {conferences.map((conf) => (
                <ConferenceCard key={conf.id} conference={conf} />
              ))}
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="pd-card p-4 mb-6">
          <div className="flex flex-wrap items-end gap-6">
            {/* Time Filters */}
            <div>
              <div className="text-sm text-pd-text-muted mb-2">Timeframe</div>
              <div className="flex flex-wrap gap-2">
                {TIME_FILTERS.map((filter) => (
                  <button
                    key={filter.key}
                    onClick={() => setSelectedTime(filter.key)}
                    className={cn(
                      "px-3 py-1.5 rounded-lg text-sm font-medium transition-all",
                      selectedTime === filter.key
                        ? "bg-pd-accent text-white"
                        : "bg-pd-secondary border border-pd-border text-pd-text-secondary hover:border-pd-accent/50"
                    )}
                  >
                    {filter.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Phase Filters */}
            <div>
              <div className="text-sm text-pd-text-muted mb-2">Phase</div>
              <div className="flex flex-wrap gap-2">
                {PHASE_FILTERS.map((filter) => (
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

            {/* Confidence Filters */}
            <div>
              <div className="text-sm text-pd-text-muted mb-2">Date Quality</div>
              <div className="flex flex-wrap gap-2">
                {CONFIDENCE_FILTERS.map((filter) => (
                  <button
                    key={filter.key}
                    onClick={() => setSelectedConfidence(filter.key)}
                    className={cn(
                      "px-3 py-1.5 rounded-lg text-sm font-medium transition-all",
                      selectedConfidence === filter.key
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

        {/* Legend */}
        <div className="mb-4 px-4 py-3 bg-pd-secondary border border-pd-border rounded-lg">
          <div className="flex flex-wrap items-center gap-4 text-sm">
            <span className="text-pd-text-muted">Date confidence:</span>
            <div className="flex items-center gap-1">
              <DateConfidenceBadge confidence="confirmed" tooltip="ACTUAL completion date reported" />
              <span className="text-pd-text-muted ml-1">= verified by sponsor</span>
            </div>
            <div className="flex items-center gap-1">
              <DateConfidenceBadge confidence="estimated" tooltip="Anticipated completion date" />
              <span className="text-pd-text-muted ml-1">= sponsor estimate</span>
            </div>
            <div className="flex items-center gap-1">
              <DateConfidenceBadge confidence="placeholder" tooltip="Dec 31/Jan 1 dates are often placeholders" />
              <span className="text-pd-text-muted ml-1">= likely placeholder (Dec 31/Jan 1)</span>
            </div>
          </div>
        </div>

        {/* Trials Table */}
        {trials.length === 0 ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-pd-text-muted">No trials found matching filters</div>
          </div>
        ) : (
          <div>
            <div className="mb-4 text-sm text-pd-text-muted">
              Showing {trials.length} trial{trials.length !== 1 ? "s" : ""}
            </div>
            <DataTable
              columns={columns}
              data={trials}
              sortable={true}
              defaultSort={{ key: "primary_completion_date", direction: "asc" }}
              emptyMessage="No trials found"
            />
          </div>
        )}
      </div>
    </div>
  )
}
