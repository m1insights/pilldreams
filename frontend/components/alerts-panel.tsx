"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { cn } from "@/lib/utils"

interface Alert {
  id: string
  alert_type: string
  alert_title: string
  alert_body?: string
  alert_url?: string
  significance: "critical" | "high" | "medium" | "low"
  status: "pending" | "sent" | "read" | "dismissed"
  created_at: string
}

// Significance badge colors
const significanceColors = {
  critical: "bg-red-900/30 text-red-400 border-red-800",
  high: "bg-orange-900/30 text-orange-400 border-orange-800",
  medium: "bg-yellow-900/30 text-yellow-400 border-yellow-800",
  low: "bg-blue-900/30 text-blue-400 border-blue-800",
}

// Alert type icons
const alertIcons = {
  phase_change: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
    </svg>
  ),
  status_change: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
    </svg>
  ),
  pdufa: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
    </svg>
  ),
  score_change: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
  ),
  news: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
    </svg>
  ),
}

function AlertItem({
  alert,
  onRead,
  onDismiss,
}: {
  alert: Alert
  onRead: (id: string) => void
  onDismiss: (id: string) => void
}) {
  const isUnread = alert.status === "sent" || alert.status === "pending"
  const icon = alertIcons[alert.alert_type as keyof typeof alertIcons] || alertIcons.news

  return (
    <div
      className={cn(
        "p-4 border-b border-pd-border last:border-b-0 transition-colors",
        isUnread ? "bg-pd-secondary/50" : "bg-transparent"
      )}
    >
      <div className="flex items-start gap-3">
        <div className={cn("p-2 rounded-lg", significanceColors[alert.significance])}>
          {icon}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div>
              <h4 className={cn(
                "font-medium",
                isUnread ? "text-pd-text-primary" : "text-pd-text-secondary"
              )}>
                {alert.alert_title}
              </h4>
              {alert.alert_body && (
                <p className="text-sm text-pd-text-muted mt-1 line-clamp-2">
                  {alert.alert_body}
                </p>
              )}
            </div>
            <span className={cn(
              "text-xs px-2 py-0.5 rounded border shrink-0",
              significanceColors[alert.significance]
            )}>
              {alert.significance}
            </span>
          </div>
          <div className="flex items-center gap-4 mt-2">
            <span className="text-xs text-pd-text-muted">
              {new Date(alert.created_at).toLocaleDateString()}
            </span>
            {alert.alert_url && (
              <Link
                href={alert.alert_url}
                className="text-xs text-pd-accent hover:underline"
                onClick={() => isUnread && onRead(alert.id)}
              >
                View details
              </Link>
            )}
            {isUnread && (
              <button
                onClick={() => onRead(alert.id)}
                className="text-xs text-pd-text-muted hover:text-pd-text-secondary"
              >
                Mark read
              </button>
            )}
            <button
              onClick={() => onDismiss(alert.id)}
              className="text-xs text-pd-text-muted hover:text-red-400"
            >
              Dismiss
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

interface AlertsPanelProps {
  className?: string
}

export function AlertsPanel({ className }: AlertsPanelProps) {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<"all" | "unread">("all")

  // For demo, use mock data
  useEffect(() => {
    // Simulate loading
    setTimeout(() => {
      setAlerts([
        {
          id: "1",
          alert_type: "phase_change",
          alert_title: "Tazemetostat advanced to Phase 3",
          alert_body: "Ipsen announced positive Phase 2 results for epithelioid sarcoma.",
          alert_url: "/drug/tazemetostat",
          significance: "critical",
          status: "sent",
          created_at: new Date().toISOString(),
        },
        {
          id: "2",
          alert_type: "pdufa",
          alert_title: "PDUFA Date Approaching: Pelabresib",
          alert_body: "FDA decision expected in 45 days for myelofibrosis indication.",
          alert_url: "/drug/pelabresib",
          significance: "high",
          status: "sent",
          created_at: new Date(Date.now() - 86400000).toISOString(),
        },
        {
          id: "3",
          alert_type: "score_change",
          alert_title: "Score Update: Entinostat",
          alert_body: "TotalScore decreased from 72 to 67 due to trial termination.",
          alert_url: "/drug/entinostat",
          significance: "medium",
          status: "read",
          created_at: new Date(Date.now() - 172800000).toISOString(),
        },
      ])
      setLoading(false)
    }, 500)
  }, [])

  const handleRead = (id: string) => {
    setAlerts(alerts.map(a =>
      a.id === id ? { ...a, status: "read" } : a
    ))
  }

  const handleDismiss = (id: string) => {
    setAlerts(alerts.filter(a => a.id !== id))
  }

  const filteredAlerts = filter === "unread"
    ? alerts.filter(a => a.status === "sent" || a.status === "pending")
    : alerts

  const unreadCount = alerts.filter(a => a.status === "sent" || a.status === "pending").length

  if (loading) {
    return (
      <div className={cn("pd-card", className)}>
        <div className="p-4 text-center text-pd-text-muted">
          Loading alerts...
        </div>
      </div>
    )
  }

  return (
    <div className={cn("pd-card", className)}>
      <div className="flex items-center justify-between p-4 border-b border-pd-border">
        <div className="flex items-center gap-2">
          <h3 className="font-semibold text-pd-text-primary">Alerts</h3>
          {unreadCount > 0 && (
            <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-pd-accent text-white">
              {unreadCount}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setFilter("all")}
            className={cn(
              "px-3 py-1 text-xs rounded-full transition-colors",
              filter === "all"
                ? "bg-pd-accent text-white"
                : "bg-pd-border text-pd-text-muted hover:text-pd-text-secondary"
            )}
          >
            All
          </button>
          <button
            onClick={() => setFilter("unread")}
            className={cn(
              "px-3 py-1 text-xs rounded-full transition-colors",
              filter === "unread"
                ? "bg-pd-accent text-white"
                : "bg-pd-border text-pd-text-muted hover:text-pd-text-secondary"
            )}
          >
            Unread
          </button>
        </div>
      </div>

      {filteredAlerts.length === 0 ? (
        <div className="p-8 text-center">
          <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-pd-secondary flex items-center justify-center">
            <svg className="w-6 h-6 text-pd-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
          </div>
          <p className="text-pd-text-muted">
            {filter === "unread" ? "No unread alerts" : "No alerts yet"}
          </p>
          <p className="text-xs text-pd-text-muted mt-1">
            Add items to your watchlist to receive alerts
          </p>
        </div>
      ) : (
        <div className="max-h-96 overflow-y-auto">
          {filteredAlerts.map((alert) => (
            <AlertItem
              key={alert.id}
              alert={alert}
              onRead={handleRead}
              onDismiss={handleDismiss}
            />
          ))}
        </div>
      )}

      <div className="p-3 border-t border-pd-border text-center">
        <Link
          href="/settings/notifications"
          className="text-xs text-pd-text-muted hover:text-pd-accent"
        >
          Manage notification preferences
        </Link>
      </div>
    </div>
  )
}
