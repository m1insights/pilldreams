"use client"

import { useState, useEffect, useCallback } from "react"
import { useAuth } from "@/lib/auth/context"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export interface FeatureAccessResult {
  allowed: boolean
  reason?: string
  upgrade_tier?: string
  current_tier?: string
  limit?: number
  used?: number
}

export interface AllLimitsResult {
  tier: string
  limits: Record<string, {
    allowed: boolean
    limit: number
    used: number
  }>
}

/**
 * Hook to check if the current user can access a feature.
 * Returns loading state and access result.
 */
export function useFeatureAccess(feature: string) {
  const { session, profile } = useAuth()
  const [loading, setLoading] = useState(true)
  const [access, setAccess] = useState<FeatureAccessResult>({
    allowed: false,
    reason: "Loading...",
  })

  useEffect(() => {
    async function checkAccess() {
      // If not authenticated, use free tier logic
      if (!session?.access_token) {
        // Check against free tier features
        const freeTierFeatures = [
          "browse_targets",
          "browse_drugs_basic",
          "search",
        ]
        setAccess({
          allowed: freeTierFeatures.includes(feature),
          reason: freeTierFeatures.includes(feature)
            ? undefined
            : "Sign in to access this feature",
          upgrade_tier: "free",
          current_tier: "anonymous",
        })
        setLoading(false)
        return
      }

      try {
        const response = await fetch(
          `${API_BASE}/auth/me/can-access/${feature}`,
          {
            headers: {
              Authorization: `Bearer ${session.access_token}`,
            },
          }
        )

        if (response.ok) {
          const data = await response.json()
          setAccess(data)
        } else {
          setAccess({
            allowed: false,
            reason: "Failed to check access",
          })
        }
      } catch (error) {
        console.error("Feature access check failed:", error)
        setAccess({
          allowed: false,
          reason: "Failed to check access",
        })
      } finally {
        setLoading(false)
      }
    }

    checkAccess()
  }, [feature, session?.access_token])

  return { loading, ...access }
}

/**
 * Hook to check usage limits for a feature.
 */
export function useUsageLimit(limitName: string) {
  const { session } = useAuth()
  const [loading, setLoading] = useState(true)
  const [limit, setLimit] = useState<FeatureAccessResult>({
    allowed: false,
    reason: "Loading...",
  })

  useEffect(() => {
    async function checkLimit() {
      if (!session?.access_token) {
        setLimit({
          allowed: false,
          reason: "Sign in to use this feature",
          limit: 0,
          used: 0,
        })
        setLoading(false)
        return
      }

      try {
        const response = await fetch(
          `${API_BASE}/auth/me/check-limit/${limitName}`,
          {
            headers: {
              Authorization: `Bearer ${session.access_token}`,
            },
          }
        )

        if (response.ok) {
          const data = await response.json()
          setLimit(data)
        } else {
          setLimit({
            allowed: false,
            reason: "Failed to check limit",
          })
        }
      } catch (error) {
        console.error("Usage limit check failed:", error)
        setLimit({
          allowed: false,
          reason: "Failed to check limit",
        })
      } finally {
        setLoading(false)
      }
    }

    checkLimit()
  }, [limitName, session?.access_token])

  const refresh = useCallback(async () => {
    if (!session?.access_token) return

    setLoading(true)
    try {
      const response = await fetch(
        `${API_BASE}/auth/me/check-limit/${limitName}`,
        {
          headers: {
            Authorization: `Bearer ${session.access_token}`,
          },
        }
      )

      if (response.ok) {
        const data = await response.json()
        setLimit(data)
      }
    } catch (error) {
      console.error("Usage limit refresh failed:", error)
    } finally {
      setLoading(false)
    }
  }, [limitName, session?.access_token])

  return { loading, refresh, ...limit }
}

/**
 * Hook to get all usage limits at once.
 */
export function useAllLimits() {
  const { session } = useAuth()
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState<AllLimitsResult | null>(null)

  useEffect(() => {
    async function fetchLimits() {
      if (!session?.access_token) {
        setData(null)
        setLoading(false)
        return
      }

      try {
        const response = await fetch(`${API_BASE}/auth/me/all-limits`, {
          headers: {
            Authorization: `Bearer ${session.access_token}`,
          },
        })

        if (response.ok) {
          const result = await response.json()
          setData(result)
        }
      } catch (error) {
        console.error("All limits fetch failed:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchLimits()
  }, [session?.access_token])

  return { loading, data }
}

/**
 * Helper to determine if user is on free tier.
 */
export function useIsFreeUser() {
  const { profile, loading } = useAuth()

  if (loading) return { loading: true, isFree: true }

  const tier = profile?.subscription_tier || "free"
  return {
    loading: false,
    isFree: tier === "free",
    tier,
  }
}

/**
 * Feature names for easy reference.
 */
export const FEATURES = {
  FULL_SCORING: "full_scoring",
  PIPELINE_PHASES: "pipeline_phases",
  EXPORTS_CSV: "exports_csv",
  EXPORTS_EXCEL: "exports_excel",
  EXPORTS_PPTX: "exports_pptx",
  FULL_COMPANY_PROFILES: "full_company_profiles",
  FULL_CALENDAR: "full_calendar",
  FULL_NEWS: "full_news",
  ALERTS: "alerts",
  AI_CHAT: "ai_chat",
  API_ACCESS: "api_access",
  SSO_SAML: "sso_saml",
  PRIORITY_SUPPORT: "priority_support",
} as const

export const LIMITS = {
  WATCHLIST_ITEMS: "watchlist_items",
  EXPORTS_PER_MONTH: "exports_per_month",
  PPTX_EXPORTS_PER_MONTH: "pptx_exports_per_month",
  ALERTS_PER_MONTH: "alerts_per_month",
  AI_QUESTIONS_PER_MONTH: "ai_questions_per_month",
  API_CALLS_PER_MONTH: "api_calls_per_month",
} as const
