"use client"

import { useState } from "react"
import Link from "next/link"
import { useAuth } from "@/lib/auth/context"
import { useFeatureAccess, FEATURES } from "@/lib/hooks/useFeatureAccess"
import { cn } from "@/lib/utils"

interface PaywallProps {
  feature: string
  children: React.ReactNode
  fallback?: React.ReactNode
  blurContent?: boolean
  showUpgrade?: boolean
}

/**
 * Paywall wrapper - shows content only if user has access to the feature.
 * Can blur content or show a custom fallback.
 */
export function Paywall({
  feature,
  children,
  fallback,
  blurContent = false,
  showUpgrade = true,
}: PaywallProps) {
  const { loading, allowed, reason, upgrade_tier } = useFeatureAccess(feature)
  const { user } = useAuth()

  if (loading) {
    return (
      <div className="animate-pulse bg-pd-secondary rounded-lg h-24" />
    )
  }

  if (allowed) {
    return <>{children}</>
  }

  // Not allowed - show paywall
  if (blurContent) {
    return (
      <div className="relative">
        <div className="blur-sm select-none pointer-events-none">
          {children}
        </div>
        <div className="absolute inset-0 flex items-center justify-center bg-pd-primary/80 rounded-lg">
          <UpgradePrompt
            reason={reason}
            upgradeTier={upgrade_tier}
            isLoggedIn={!!user}
          />
        </div>
      </div>
    )
  }

  if (fallback) {
    return <>{fallback}</>
  }

  if (showUpgrade) {
    return (
      <UpgradePrompt
        reason={reason}
        upgradeTier={upgrade_tier}
        isLoggedIn={!!user}
      />
    )
  }

  return null
}

/**
 * Upgrade prompt shown when feature is not accessible.
 */
export function UpgradePrompt({
  reason,
  upgradeTier,
  isLoggedIn,
  compact = false,
}: {
  reason?: string
  upgradeTier?: string
  isLoggedIn: boolean
  compact?: boolean
}) {
  const tierNames: Record<string, string> = {
    pro: "Analyst",
    enterprise: "Enterprise",
  }

  const tierName = tierNames[upgradeTier || "pro"] || "Pro"

  if (compact) {
    return (
      <div className="flex items-center gap-2 text-sm">
        <svg className="w-4 h-4 text-yellow-500" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
        </svg>
        <span className="text-pd-text-muted">{tierName} feature</span>
        <Link
          href="/pricing"
          className="text-pd-accent hover:underline"
        >
          Upgrade
        </Link>
      </div>
    )
  }

  return (
    <div className="pd-card p-6 text-center max-w-md mx-auto">
      <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-yellow-500/10 flex items-center justify-center">
        <svg className="w-6 h-6 text-yellow-500" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
        </svg>
      </div>
      <h3 className="text-lg font-semibold text-pd-text-primary mb-2">
        {tierName} Feature
      </h3>
      <p className="text-pd-text-muted text-sm mb-4">
        {reason || `Upgrade to ${tierName} to access this feature.`}
      </p>
      <div className="flex gap-3 justify-center">
        {!isLoggedIn ? (
          <>
            <Link
              href="/login"
              className="px-4 py-2 rounded-lg bg-pd-secondary border border-pd-border text-pd-text-secondary text-sm font-medium hover:border-pd-accent/50 transition-colors"
            >
              Sign In
            </Link>
            <Link
              href="/signup"
              className="px-4 py-2 rounded-lg bg-pd-accent text-white text-sm font-medium hover:bg-pd-accent/90 transition-colors"
            >
              Start Free Trial
            </Link>
          </>
        ) : (
          <Link
            href="/pricing"
            className="px-4 py-2 rounded-lg bg-pd-accent text-white text-sm font-medium hover:bg-pd-accent/90 transition-colors"
          >
            View Pricing
          </Link>
        )}
      </div>
    </div>
  )
}

/**
 * Blurred score display for free users.
 */
export function BlurredScore({
  score,
  label,
  feature = FEATURES.FULL_SCORING,
}: {
  score: number | null
  label: string
  feature?: string
}) {
  const { loading, allowed } = useFeatureAccess(feature)
  const { user } = useAuth()

  if (loading) {
    return (
      <div className="text-center">
        <div className="text-xs text-pd-text-muted mb-1">{label}</div>
        <div className="animate-pulse bg-pd-secondary rounded h-6 w-8 mx-auto" />
      </div>
    )
  }

  if (allowed && score !== null) {
    return (
      <div className="text-center">
        <div className="text-xs text-pd-text-muted mb-1">{label}</div>
        <div className="text-sm font-medium text-pd-text-primary">
          {score.toFixed(0)}
        </div>
      </div>
    )
  }

  // Show blurred/locked score
  return (
    <div className="text-center group relative">
      <div className="text-xs text-pd-text-muted mb-1">{label}</div>
      <div className="text-sm font-medium text-pd-text-muted blur-[4px] select-none">
        {score !== null ? score.toFixed(0) : "??"}
      </div>
      <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
        <Link
          href={user ? "/pricing" : "/login"}
          className="text-xs text-pd-accent hover:underline"
        >
          {user ? "Upgrade" : "Sign in"}
        </Link>
      </div>
    </div>
  )
}

/**
 * Locked indicator badge.
 */
export function LockedBadge({
  tier = "pro",
  size = "sm",
}: {
  tier?: "pro" | "enterprise"
  size?: "sm" | "md"
}) {
  const tierNames = {
    pro: "Pro",
    enterprise: "Enterprise",
  }

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full bg-yellow-500/10 text-yellow-500 border border-yellow-500/20",
        size === "sm" ? "px-2 py-0.5 text-xs" : "px-3 py-1 text-sm"
      )}
    >
      <svg
        className={size === "sm" ? "w-3 h-3" : "w-4 h-4"}
        fill="currentColor"
        viewBox="0 0 20 20"
      >
        <path
          fillRule="evenodd"
          d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z"
          clipRule="evenodd"
        />
      </svg>
      {tierNames[tier]}
    </span>
  )
}

/**
 * Usage limit indicator with progress bar.
 */
export function UsageLimitIndicator({
  label,
  used,
  limit,
  showUpgrade = true,
}: {
  label: string
  used: number
  limit: number
  showUpgrade?: boolean
}) {
  const isUnlimited = limit === -1
  const percentage = isUnlimited ? 0 : Math.min((used / limit) * 100, 100)
  const isNearLimit = percentage >= 80
  const isAtLimit = used >= limit && !isUnlimited

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm">
        <span className="text-pd-text-muted">{label}</span>
        <span className={cn(
          "font-medium",
          isAtLimit ? "text-red-400" : isNearLimit ? "text-yellow-400" : "text-pd-text-primary"
        )}>
          {isUnlimited ? "Unlimited" : `${used} / ${limit}`}
        </span>
      </div>
      {!isUnlimited && (
        <div className="h-2 bg-pd-secondary rounded-full overflow-hidden">
          <div
            className={cn(
              "h-full rounded-full transition-all",
              isAtLimit ? "bg-red-500" : isNearLimit ? "bg-yellow-500" : "bg-pd-accent"
            )}
            style={{ width: `${percentage}%` }}
          />
        </div>
      )}
      {isAtLimit && showUpgrade && (
        <div className="flex items-center justify-between text-xs">
          <span className="text-red-400">Limit reached</span>
          <Link href="/pricing" className="text-pd-accent hover:underline">
            Upgrade for more
          </Link>
        </div>
      )}
    </div>
  )
}

/**
 * Feature comparison modal for upgrade prompts.
 */
export function FeatureComparisonModal({
  isOpen,
  onClose,
  highlightFeature,
}: {
  isOpen: boolean
  onClose: () => void
  highlightFeature?: string
}) {
  if (!isOpen) return null

  const features = [
    { name: "Browse targets & drugs", free: true, pro: true, enterprise: true },
    { name: "Full scoring (Bio/Chem/Tract)", free: false, pro: true, enterprise: true, key: "full_scoring" },
    { name: "Pipeline phase data", free: false, pro: true, enterprise: true, key: "pipeline_phases" },
    { name: "Watchlist items", free: "5", pro: "50", enterprise: "Unlimited" },
    { name: "Exports (CSV/Excel)", free: false, pro: "25/mo", enterprise: "Unlimited", key: "exports" },
    { name: "PowerPoint decks", free: false, pro: "5/mo", enterprise: "Unlimited", key: "exports_pptx" },
    { name: "AI questions", free: false, pro: "50/mo", enterprise: "Unlimited", key: "ai_chat" },
    { name: "Custom alerts", free: false, pro: "10/mo", enterprise: "Unlimited", key: "alerts" },
    { name: "API access", free: false, pro: false, enterprise: true, key: "api_access" },
    { name: "SSO/SAML", free: false, pro: false, enterprise: true, key: "sso_saml" },
    { name: "Priority support", free: false, pro: false, enterprise: true, key: "priority_support" },
  ]

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/80" onClick={onClose} />
      <div className="relative bg-pd-primary border border-pd-border rounded-xl max-w-3xl w-full max-h-[80vh] overflow-auto">
        <div className="sticky top-0 bg-pd-primary border-b border-pd-border p-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-pd-text-primary">Compare Plans</h2>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-pd-secondary transition-colors"
          >
            <svg className="w-5 h-5 text-pd-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-4">
          <table className="w-full">
            <thead>
              <tr className="border-b border-pd-border">
                <th className="text-left py-3 px-4 text-pd-text-muted font-medium">Feature</th>
                <th className="text-center py-3 px-4 text-pd-text-muted font-medium">Explorer<br/><span className="text-xs">Free</span></th>
                <th className="text-center py-3 px-4 text-pd-accent font-medium">Analyst<br/><span className="text-xs">$49/mo</span></th>
                <th className="text-center py-3 px-4 text-pd-text-muted font-medium">Enterprise<br/><span className="text-xs">$499/mo</span></th>
              </tr>
            </thead>
            <tbody>
              {features.map((feature, idx) => (
                <tr
                  key={idx}
                  className={cn(
                    "border-b border-pd-border/50",
                    feature.key === highlightFeature && "bg-pd-accent/10"
                  )}
                >
                  <td className="py-3 px-4 text-pd-text-primary text-sm">{feature.name}</td>
                  <td className="text-center py-3 px-4">
                    {renderFeatureValue(feature.free)}
                  </td>
                  <td className="text-center py-3 px-4">
                    {renderFeatureValue(feature.pro)}
                  </td>
                  <td className="text-center py-3 px-4">
                    {renderFeatureValue(feature.enterprise)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="mt-6 flex justify-center gap-4">
            <Link
              href="/pricing"
              className="px-6 py-3 rounded-lg bg-pd-accent text-white font-medium hover:bg-pd-accent/90 transition-colors"
              onClick={onClose}
            >
              View Full Pricing
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

function renderFeatureValue(value: boolean | string) {
  if (value === true) {
    return (
      <svg className="w-5 h-5 text-green-500 mx-auto" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
      </svg>
    )
  }
  if (value === false) {
    return (
      <svg className="w-5 h-5 text-pd-text-muted mx-auto" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
      </svg>
    )
  }
  return <span className="text-sm text-pd-text-primary">{value}</span>
}

/**
 * Simple inline upgrade link.
 */
export function UpgradeLink({
  children,
  className,
}: {
  children?: React.ReactNode
  className?: string
}) {
  return (
    <Link
      href="/pricing"
      className={cn(
        "inline-flex items-center gap-1 text-pd-accent hover:underline",
        className
      )}
    >
      {children || (
        <>
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
          </svg>
          Upgrade
        </>
      )}
    </Link>
  )
}
