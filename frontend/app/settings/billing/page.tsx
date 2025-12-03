"use client"

import { Suspense, useEffect, useState } from "react"
import Link from "next/link"
import { useSearchParams } from "next/navigation"
import { authApi } from "@/lib/api"
import { cn } from "@/lib/utils"

interface SubscriptionTier {
  id: string
  name: string
  description: string
  price_monthly: number
  price_yearly: number
  api_calls_limit: number
  exports_limit: number
  watchlist_limit: number
  alerts_limit: number
  feature_exports: boolean
  feature_api_access: boolean
  feature_slack_alerts: boolean
  is_popular: boolean
}

interface UsageStats {
  api_calls_used: number
  api_calls_limit: number
  api_calls_percent: number
  exports_used: number
  exports_limit: number
  exports_percent: number
  can_export: boolean
  can_api: boolean
}

// Format price from cents
function formatPrice(cents: number): string {
  if (cents === 0) return "Free"
  return `$${(cents / 100).toFixed(0)}`
}

// Usage progress bar
function UsageBar({ used, limit, label }: { used: number; limit: number; label: string }) {
  const unlimited = limit === -1
  const percent = unlimited ? 0 : Math.min((used / limit) * 100, 100)
  const isWarning = !unlimited && percent >= 80
  const isCritical = !unlimited && percent >= 95

  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span className="text-pd-text-secondary">{label}</span>
        <span className={cn(
          "font-medium",
          isCritical ? "text-red-400" : isWarning ? "text-yellow-400" : "text-pd-text-primary"
        )}>
          {used.toLocaleString()} / {unlimited ? "Unlimited" : limit.toLocaleString()}
        </span>
      </div>
      <div className="h-2 bg-pd-border rounded-full overflow-hidden">
        <div
          className={cn(
            "h-full rounded-full transition-all duration-300",
            isCritical ? "bg-red-500" : isWarning ? "bg-yellow-500" : "bg-pd-accent"
          )}
          style={{ width: unlimited ? "0%" : `${percent}%` }}
        />
      </div>
    </div>
  )
}

// Pricing card
function PricingCard({
  tier,
  currentTier,
  billingPeriod,
  onSelect,
  loading,
}: {
  tier: SubscriptionTier
  currentTier: string
  billingPeriod: "monthly" | "yearly"
  onSelect: () => void
  loading: boolean
}) {
  const price = billingPeriod === "yearly" ? tier.price_yearly : tier.price_monthly
  const isCurrentPlan = tier.id === currentTier
  const yearlyDiscount = tier.price_monthly > 0
    ? Math.round(100 - (tier.price_yearly / (tier.price_monthly * 12)) * 100)
    : 0

  return (
    <div
      className={cn(
        "pd-card p-6 relative",
        tier.is_popular && "ring-2 ring-pd-accent",
        isCurrentPlan && "ring-2 ring-green-500"
      )}
    >
      {tier.is_popular && !isCurrentPlan && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-pd-accent text-white text-xs font-medium rounded-full">
          Popular
        </div>
      )}
      {isCurrentPlan && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-green-500 text-white text-xs font-medium rounded-full">
          Current Plan
        </div>
      )}

      <div className="text-center mb-6">
        <h3 className="text-xl font-bold text-pd-text-primary mb-2">{tier.name}</h3>
        <p className="text-sm text-pd-text-muted mb-4">{tier.description}</p>
        <div className="flex items-baseline justify-center gap-1">
          <span className="text-4xl font-bold text-pd-text-primary">
            {formatPrice(price)}
          </span>
          {price > 0 && (
            <span className="text-pd-text-muted">
              /{billingPeriod === "yearly" ? "year" : "mo"}
            </span>
          )}
        </div>
        {billingPeriod === "yearly" && yearlyDiscount > 0 && (
          <div className="text-sm text-green-400 mt-1">Save {yearlyDiscount}%</div>
        )}
      </div>

      <ul className="space-y-3 mb-6">
        <li className="flex items-center gap-2 text-sm text-pd-text-secondary">
          <svg className="w-4 h-4 text-green-400 shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
          {tier.api_calls_limit === -1 ? "Unlimited" : tier.api_calls_limit.toLocaleString()} API calls/month
        </li>
        <li className="flex items-center gap-2 text-sm text-pd-text-secondary">
          <svg className="w-4 h-4 text-green-400 shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
          {tier.exports_limit === -1 ? "Unlimited" : tier.exports_limit} exports/month
        </li>
        <li className="flex items-center gap-2 text-sm text-pd-text-secondary">
          <svg className="w-4 h-4 text-green-400 shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
          {tier.watchlist_limit === -1 ? "Unlimited" : tier.watchlist_limit} watchlist items
        </li>
        {tier.feature_exports && (
          <li className="flex items-center gap-2 text-sm text-pd-text-secondary">
            <svg className="w-4 h-4 text-green-400 shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
            Excel & PowerPoint exports
          </li>
        )}
        {tier.feature_api_access && (
          <li className="flex items-center gap-2 text-sm text-pd-text-secondary">
            <svg className="w-4 h-4 text-green-400 shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
            API access
          </li>
        )}
        {tier.feature_slack_alerts && (
          <li className="flex items-center gap-2 text-sm text-pd-text-secondary">
            <svg className="w-4 h-4 text-green-400 shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
            Slack alerts
          </li>
        )}
      </ul>

      <button
        onClick={onSelect}
        disabled={isCurrentPlan || loading}
        className={cn(
          "w-full py-3 rounded-lg font-medium transition-colors",
          isCurrentPlan
            ? "bg-pd-border text-pd-text-muted cursor-not-allowed"
            : tier.is_popular
            ? "bg-pd-accent text-white hover:bg-pd-accent/90"
            : "bg-pd-secondary border border-pd-border text-pd-text-primary hover:border-pd-accent"
        )}
      >
        {loading ? "Loading..." : isCurrentPlan ? "Current Plan" : tier.price_monthly === 0 ? "Downgrade" : "Upgrade"}
      </button>
    </div>
  )
}

function BillingPageContent() {
  const searchParams = useSearchParams()
  const [tiers, setTiers] = useState<SubscriptionTier[]>([])
  const [usage, setUsage] = useState<UsageStats | null>(null)
  const [currentTier, setCurrentTier] = useState<string>("free")
  const [billingPeriod, setBillingPeriod] = useState<"monthly" | "yearly">("monthly")
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  // Check for success/cancel params from Stripe redirect
  useEffect(() => {
    if (searchParams.get("success") === "true") {
      setSuccessMessage("Subscription updated successfully!")
      setTimeout(() => setSuccessMessage(null), 5000)
    }
    if (searchParams.get("canceled") === "true") {
      setSuccessMessage("Checkout was canceled.")
      setTimeout(() => setSuccessMessage(null), 5000)
    }
  }, [searchParams])

  // Load tiers and usage
  useEffect(() => {
    async function loadData() {
      try {
        const [tiersData, usageData] = await Promise.all([
          authApi.getTiers(),
          // For demo, we'll show mock usage since auth isn't set up
          Promise.resolve({
            api_calls_used: 47,
            api_calls_limit: 100,
            api_calls_percent: 47,
            exports_used: 2,
            exports_limit: 5,
            exports_percent: 40,
            can_export: true,
            can_api: true,
          }),
        ])
        setTiers(tiersData)
        setUsage(usageData)
        // Set current tier from user profile when auth is configured
        // For now, default to 'free' tier for demo
        setCurrentTier("free")
      } catch (err) {
        console.error("Failed to load billing data:", err)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])

  const handleSelectPlan = async (tierId: string) => {
    if (tierId === currentTier) return

    setActionLoading(true)
    try {
      // In production, this would create a Stripe checkout session
      // For now, show a message about setting up Stripe
      alert(`To upgrade to ${tierId}, configure your Stripe keys in .env and set up products in Stripe Dashboard.`)
    } catch (err) {
      console.error("Failed to create checkout session:", err)
    } finally {
      setActionLoading(false)
    }
  }

  const handleManageSubscription = async () => {
    setActionLoading(true)
    try {
      // In production, this would create a Stripe portal session
      alert("To manage your subscription, configure your Stripe keys in .env")
    } catch (err) {
      console.error("Failed to create portal session:", err)
    } finally {
      setActionLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-pd-primary flex items-center justify-center">
        <div className="text-pd-text-muted">Loading billing information...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-pd-primary">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Success message */}
        {successMessage && (
          <div className="mb-6 p-4 rounded-lg bg-green-900/30 border border-green-800 text-green-400">
            {successMessage}
          </div>
        )}

        {/* Header */}
        <div className="mb-8">
          <nav className="text-sm text-pd-text-muted mb-4">
            <Link href="/" className="hover:text-pd-accent">Home</Link>
            <span className="mx-2">/</span>
            <span className="text-pd-text-primary">Billing</span>
          </nav>
          <h1 className="text-4xl font-bold text-pd-text-primary mb-2">
            Billing & Subscription
          </h1>
          <p className="text-pd-text-secondary">
            Manage your subscription and track your usage
          </p>
        </div>

        {/* Current Usage */}
        {usage && (
          <div className="pd-card p-6 mb-8">
            <h2 className="text-lg font-semibold text-pd-text-primary mb-4">Current Usage</h2>
            <div className="grid md:grid-cols-2 gap-6">
              <UsageBar used={usage.api_calls_used} limit={usage.api_calls_limit} label="API Calls" />
              <UsageBar used={usage.exports_used} limit={usage.exports_limit} label="Exports" />
            </div>
            <p className="text-xs text-pd-text-muted mt-4">
              Usage resets on the 1st of each month
            </p>
          </div>
        )}

        {/* Current Plan */}
        <div className="pd-card p-6 mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-pd-text-primary mb-1">Current Plan</h2>
              <p className="text-pd-text-secondary">
                You are on the <span className="text-pd-accent font-medium capitalize">{currentTier}</span> plan
              </p>
            </div>
            <button
              onClick={handleManageSubscription}
              disabled={actionLoading || currentTier === "free"}
              className={cn(
                "px-4 py-2 rounded-lg text-sm font-medium transition-colors",
                currentTier === "free"
                  ? "bg-pd-border text-pd-text-muted cursor-not-allowed"
                  : "bg-pd-secondary border border-pd-border text-pd-text-primary hover:border-pd-accent"
              )}
            >
              Manage Subscription
            </button>
          </div>
        </div>

        {/* Billing Period Toggle */}
        <div className="flex justify-center mb-8">
          <div className="inline-flex rounded-lg bg-pd-secondary p-1">
            <button
              onClick={() => setBillingPeriod("monthly")}
              className={cn(
                "px-4 py-2 rounded-md text-sm font-medium transition-colors",
                billingPeriod === "monthly"
                  ? "bg-pd-primary text-pd-text-primary"
                  : "text-pd-text-muted hover:text-pd-text-secondary"
              )}
            >
              Monthly
            </button>
            <button
              onClick={() => setBillingPeriod("yearly")}
              className={cn(
                "px-4 py-2 rounded-md text-sm font-medium transition-colors",
                billingPeriod === "yearly"
                  ? "bg-pd-primary text-pd-text-primary"
                  : "text-pd-text-muted hover:text-pd-text-secondary"
              )}
            >
              Yearly <span className="text-green-400 ml-1">Save 20%</span>
            </button>
          </div>
        </div>

        {/* Pricing Cards */}
        <div className="grid md:grid-cols-3 gap-6 mb-12">
          {tiers.map((tier) => (
            <PricingCard
              key={tier.id}
              tier={tier}
              currentTier={currentTier}
              billingPeriod={billingPeriod}
              onSelect={() => handleSelectPlan(tier.id)}
              loading={actionLoading}
            />
          ))}
        </div>

        {/* FAQ */}
        <div className="pd-card p-6">
          <h2 className="text-lg font-semibold text-pd-text-primary mb-4">Frequently Asked Questions</h2>
          <div className="space-y-4">
            <div>
              <h3 className="font-medium text-pd-text-primary mb-1">Can I change plans at any time?</h3>
              <p className="text-sm text-pd-text-muted">
                Yes, you can upgrade or downgrade your plan at any time. Changes take effect immediately.
              </p>
            </div>
            <div>
              <h3 className="font-medium text-pd-text-primary mb-1">What happens when I hit my usage limit?</h3>
              <p className="text-sm text-pd-text-muted">
                You&apos;ll receive a notification when you reach 80% of your limit. Once you hit 100%, you&apos;ll need to upgrade or wait until the next billing cycle.
              </p>
            </div>
            <div>
              <h3 className="font-medium text-pd-text-primary mb-1">Do you offer refunds?</h3>
              <p className="text-sm text-pd-text-muted">
                We offer a 14-day money-back guarantee for first-time subscribers. Contact support for assistance.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// Wrap in Suspense to handle useSearchParams during SSG
export default function BillingPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-pd-primary flex items-center justify-center">
        <div className="text-pd-text-muted">Loading billing information...</div>
      </div>
    }>
      <BillingPageContent />
    </Suspense>
  )
}
