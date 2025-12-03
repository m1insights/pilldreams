"use client"

import React from "react"
import { useRouter } from "next/navigation"
import { IconCheck, IconX } from "@tabler/icons-react"
import { cn } from "@/lib/utils"
import { Button } from "./button"
import { IconGift } from "@/icons/gift"
import { useEffect, useState } from "react"
import { useAuth } from "@/lib/auth/context"

function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(false)

  useEffect(() => {
    const mediaQuery = window.matchMedia(query)
    setMatches(mediaQuery.matches)

    const listener = (e: MediaQueryListEvent) => {
      setMatches(e.matches)
    }

    mediaQuery.addEventListener("change", listener)
    return () => mediaQuery.removeEventListener("change", listener)
  }, [query])

  return matches
}

export enum planType {
  free = "free",
  pro = "pro",
  enterprise = "enterprise",
}

export type Plan = {
  id: string
  name: string
  shortDescription: string
  badge?: string
  price: number
  originalPrice?: number
  period: string
  features: {
    text: string
    included: boolean
    highlight?: boolean
  }[]
  buttonText: string
  subText?: string | React.ReactNode
  onClick: () => void
}

export function PricingPlans() {
  const router = useRouter()
  const { user, profile } = useAuth()

  const currentTier = profile?.subscription_tier || "free"

  const plans: Array<Plan> = [
    {
      id: planType.free,
      name: "Explorer",
      shortDescription: "Browse & Discover",
      badge: "",
      price: 0,
      period: "forever",
      features: [
        { text: "Browse all 79 epigenetic targets", included: true },
        { text: "View approved drug profiles", included: true },
        { text: "Basic search functionality", included: true },
        { text: "5 watchlist items", included: true },
        { text: "30-day calendar view", included: true },
        { text: "Full scoring (Bio/Chem/Tract)", included: false },
        { text: "Pipeline phase data", included: false },
        { text: "Export data (CSV/Excel)", included: false },
        { text: "AI-powered insights", included: false },
      ],
      buttonText: currentTier === "free" ? "Current Plan" : "Downgrade",
      subText: "No credit card required",
      onClick: () => {
        if (!user) {
          router.push("/signup")
        }
      },
    },
    {
      id: planType.pro,
      name: "Analyst",
      shortDescription: "Full Intelligence",
      badge: "MOST POPULAR",
      price: 49,
      originalPrice: 99,
      period: "/month",
      features: [
        { text: "Everything in Explorer", included: true },
        { text: "Full scoring (Bio/Chem/Tract)", included: true, highlight: true },
        { text: "Pipeline phase tracking", included: true, highlight: true },
        { text: "50 watchlist items", included: true },
        { text: "25 exports/month (CSV/Excel)", included: true, highlight: true },
        { text: "5 PowerPoint decks/month", included: true, highlight: true },
        { text: "50 AI questions/month", included: true, highlight: true },
        { text: "Full calendar & PDUFA dates", included: true },
        { text: "10 custom alerts/month", included: true },
        { text: "API access", included: false },
      ],
      buttonText: currentTier === "pro" ? "Current Plan" : "Get Full Access",
      subText: (
        <div className="flex gap-1 justify-center items-center">
          <IconGift />
          50% off for early adopters
        </div>
      ),
      onClick: () => {
        if (!user) {
          router.push("/signup?plan=pro")
        } else {
          router.push("/settings?upgrade=pro")
        }
      },
    },
    {
      id: planType.enterprise,
      name: "Enterprise",
      shortDescription: "Team Access",
      price: 499,
      period: "/month",
      features: [
        { text: "Everything in Analyst", included: true },
        { text: "Unlimited watchlist & exports", included: true, highlight: true },
        { text: "Unlimited AI questions", included: true, highlight: true },
        { text: "Unlimited custom alerts", included: true },
        { text: "API access (10,000 calls/mo)", included: true, highlight: true },
        { text: "SSO/SAML integration", included: true, highlight: true },
        { text: "Priority support", included: true },
        { text: "Custom report requests", included: true },
        { text: "Up to 10 team seats", included: true },
      ],
      buttonText: currentTier === "enterprise" ? "Current Plan" : "Contact Sales",
      subText: "Billed annually, up to 10 seats",
      onClick: () => {
        window.location.href = "mailto:sales@phase4.ai?subject=Enterprise%20Inquiry"
      },
    },
  ]

  return plans
}

// Mobile Card Component
const MobileCard = ({ plan, isCurrentPlan }: { plan: Plan; isCurrentPlan: boolean }) => {
  return (
    <div className="mb-4 last:mb-0">
      <div className={cn(
        "bg-neutral-900 rounded-xl p-4",
        isCurrentPlan && "ring-2 ring-pd-accent"
      )}>
        {plan.badge && (
          <div className="text-center mb-3">
            <span className="text-xs px-3 py-1 rounded-full bg-pd-accent/20 text-pd-accent">
              {plan.badge}
            </span>
          </div>
        )}
        <div className="flex justify-between items-start mb-4">
          <div>
            <h3 className="text-white font-semibold">{plan.name}</h3>
            <p className="text-sm text-neutral-400">{plan.shortDescription}</p>
          </div>
          <div className="text-right">
            {plan.originalPrice && (
              <div className="text-xs text-neutral-500 line-through">
                ${plan.originalPrice}
              </div>
            )}
            <div className="text-xl font-bold text-white">${plan.price}</div>
            <div className="text-xs text-neutral-400">{plan.period}</div>
          </div>
        </div>

        <div className="space-y-2 mb-4">
          {plan.features.map((feature, idx) => (
            <div key={idx} className="flex items-center gap-2">
              {feature.included ? (
                <IconCheck className={cn(
                  "h-4 w-4",
                  feature.highlight ? "text-pd-accent" : "text-neutral-400"
                )} />
              ) : (
                <IconX className="h-4 w-4 text-neutral-600" />
              )}
              <span
                className={cn(
                  "text-xs",
                  feature.included
                    ? feature.highlight
                      ? "text-white"
                      : "text-neutral-300"
                    : "text-neutral-500"
                )}
              >
                {feature.text}
              </span>
            </div>
          ))}
        </div>

        <Button
          onClick={plan.onClick}
          disabled={isCurrentPlan}
          className={cn(
            "w-full py-2 text-sm rounded-lg",
            isCurrentPlan
              ? "bg-pd-secondary text-pd-text-muted cursor-not-allowed"
              : plan.id === planType.free
                ? "bg-gradient-to-b from-neutral-700 to-neutral-800"
                : "!bg-[linear-gradient(180deg,#B6B6B6_0%,#313131_100%)]"
          )}
        >
          {plan.buttonText}
        </Button>

        {plan.subText && !isCurrentPlan && (
          <div className="text-xs text-neutral-500 text-center mt-2">
            {plan.subText}
          </div>
        )}
      </div>
    </div>
  )
}

// Desktop Card Component
const DesktopCard = ({ plan, isCurrentPlan }: { plan: Plan; isCurrentPlan: boolean }) => {
  return (
    <div
      className={cn(
        "rounded-3xl bg-neutral-900 p-8 ring-1 ring-neutral-700 relative",
        plan.badge && "ring-1 ring-neutral-700",
        isCurrentPlan && "ring-2 ring-pd-accent"
      )}
    >
      {isCurrentPlan && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2">
          <span className="text-xs px-3 py-1 rounded-full bg-pd-accent text-white">
            Current Plan
          </span>
        </div>
      )}
      {plan.badge && !isCurrentPlan && (
        <div className="text-center -mt-12 mb-6">
          <span className="text-white text-sm px-4 py-1 rounded-[128px] bg-gradient-to-b from-[#393939] via-[#141414] to-[#303030] shadow-[0px_2px_6.4px_0px_rgba(0,0,0,0.60)]">
            {plan.badge}
          </span>
        </div>
      )}
      <div className="flex flex-col h-full">
        <div className="mb-8">
          <div className="inline-flex items-center font-bold justify-center p-2 rounded-[10px] border border-[rgba(62,62,64,0.77)] bg-[rgba(255,255,255,0)]">
            <h3 className="text-sm text-white">{plan.name}</h3>
          </div>
          <div>
            <p className="text-md text-neutral-400 my-4">
              {plan.shortDescription}
            </p>
          </div>
          <div className="mt-4">
            {plan.originalPrice && (
              <span className="text-neutral-500 line-through mr-2">
                ${plan.originalPrice}
              </span>
            )}
            <span className="text-5xl font-bold text-white">${plan.price}</span>
            <span className="text-neutral-400 ml-2">{plan.period}</span>
          </div>
        </div>

        <div className="space-y-4 mb-8 flex-1">
          {plan.features.map((feature, idx) => (
            <div key={idx} className="flex items-center gap-3">
              {feature.included ? (
                <IconCheck className={cn(
                  "h-5 w-5",
                  feature.highlight ? "text-pd-accent" : "text-neutral-400"
                )} />
              ) : (
                <IconX className="h-5 w-5 text-neutral-600" />
              )}
              <span
                className={cn(
                  "text-sm",
                  feature.included
                    ? feature.highlight
                      ? "text-white font-medium"
                      : "text-neutral-300"
                    : "text-neutral-500"
                )}
              >
                {feature.text}
              </span>
            </div>
          ))}
        </div>

        <div className="mt-auto">
          <Button
            onClick={plan.onClick}
            disabled={isCurrentPlan}
            className={cn(
              "w-full py-3 rounded-xl",
              isCurrentPlan
                ? "bg-pd-secondary text-pd-text-muted cursor-not-allowed"
                : plan.id === planType.free
                  ? "bg-gradient-to-b from-neutral-700 to-neutral-800 hover:from-neutral-600 hover:to-neutral-700"
                  : "!bg-[linear-gradient(180deg,#B6B6B6_0%,#313131_100%)] hover:shadow-[0_4px_12px_0px_rgba(0,0,0,0.4)]"
            )}
          >
            {plan.buttonText}
          </Button>
          {plan.subText && !isCurrentPlan && (
            <div className="text-sm text-neutral-500 text-center mt-4">
              {plan.subText}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export function PricingList() {
  const isMobile = useMediaQuery("(max-width: 768px)")
  const plans = PricingPlans()
  const { profile } = useAuth()
  const currentTier = profile?.subscription_tier || "free"

  if (isMobile) {
    return (
      <div className="w-full px-4 py-4">
        <div className="max-w-md mx-auto">
          {plans.map((plan) => (
            <MobileCard
              plan={plan}
              key={plan.id}
              isCurrentPlan={plan.id === currentTier}
            />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="w-full px-4 py-8">
      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-8">
        {plans.map((plan) => (
          <DesktopCard
            plan={plan}
            key={plan.id}
            isCurrentPlan={plan.id === currentTier}
          />
        ))}
      </div>
    </div>
  )
}

// Feature comparison table
export function FeatureComparisonTable() {
  const features = [
    { category: "Data Access", items: [
      { name: "Browse epigenetic targets", free: true, pro: true, enterprise: true },
      { name: "Approved drug profiles", free: true, pro: true, enterprise: true },
      { name: "Search functionality", free: true, pro: true, enterprise: true },
      { name: "Full scoring (Bio/Chem/Tract)", free: false, pro: true, enterprise: true },
      { name: "Pipeline phase data", free: false, pro: true, enterprise: true },
      { name: "Company profiles", free: "Basic", pro: "Full", enterprise: "Full" },
    ]},
    { category: "Tracking & Alerts", items: [
      { name: "Watchlist items", free: "5", pro: "50", enterprise: "Unlimited" },
      { name: "Custom alerts", free: false, pro: "10/mo", enterprise: "Unlimited" },
      { name: "Calendar view", free: "30 days", pro: "Full year", enterprise: "Full year" },
      { name: "PDUFA date tracking", free: false, pro: true, enterprise: true },
    ]},
    { category: "Exports & Analysis", items: [
      { name: "CSV exports", free: false, pro: "25/mo", enterprise: "Unlimited" },
      { name: "Excel exports", free: false, pro: "25/mo", enterprise: "Unlimited" },
      { name: "PowerPoint decks", free: false, pro: "5/mo", enterprise: "Unlimited" },
      { name: "AI questions", free: false, pro: "50/mo", enterprise: "Unlimited" },
    ]},
    { category: "Enterprise", items: [
      { name: "API access", free: false, pro: false, enterprise: "10,000/mo" },
      { name: "SSO/SAML", free: false, pro: false, enterprise: true },
      { name: "Priority support", free: false, pro: false, enterprise: true },
      { name: "Custom reports", free: false, pro: false, enterprise: true },
      { name: "Team seats", free: "1", pro: "1", enterprise: "Up to 10" },
    ]},
  ]

  return (
    <div className="w-full max-w-5xl mx-auto px-4 py-8">
      <h3 className="text-2xl font-bold text-center text-pd-text-primary mb-8">
        Full Feature Comparison
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-pd-border">
              <th className="text-left py-4 px-4 text-pd-text-muted font-medium">Feature</th>
              <th className="text-center py-4 px-4 text-pd-text-muted font-medium w-28">Explorer</th>
              <th className="text-center py-4 px-4 text-pd-accent font-medium w-28">Analyst</th>
              <th className="text-center py-4 px-4 text-pd-text-muted font-medium w-28">Enterprise</th>
            </tr>
          </thead>
          <tbody>
            {features.map((category, catIdx) => (
              <React.Fragment key={catIdx}>
                <tr className="bg-pd-secondary/30">
                  <td colSpan={4} className="py-3 px-4 font-semibold text-pd-text-primary text-sm">
                    {category.category}
                  </td>
                </tr>
                {category.items.map((item, itemIdx) => (
                  <tr key={itemIdx} className="border-b border-pd-border/50">
                    <td className="py-3 px-4 text-pd-text-secondary text-sm">{item.name}</td>
                    <td className="text-center py-3 px-4">
                      {renderValue(item.free)}
                    </td>
                    <td className="text-center py-3 px-4">
                      {renderValue(item.pro)}
                    </td>
                    <td className="text-center py-3 px-4">
                      {renderValue(item.enterprise)}
                    </td>
                  </tr>
                ))}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function renderValue(value: boolean | string) {
  if (value === true) {
    return <IconCheck className="w-5 h-5 text-green-500 mx-auto" />
  }
  if (value === false) {
    return <IconX className="w-5 h-5 text-neutral-600 mx-auto" />
  }
  return <span className="text-sm text-pd-text-primary">{value}</span>
}

export function Pricing() {
  const isMobile = useMediaQuery("(max-width: 768px)")

  return (
    <div
      id="pricing"
      className="relative isolate w-full overflow-hidden px-4 py-16 md:py-40 pt-10 md:pt-60 lg:px-4 min-h-[900px] md:min-h-[1100px]"
    >
      {!isMobile && (
        <div className="absolute inset-0 pointer-events-none">
          <BackgroundShape />
        </div>
      )}
      <div
        className={cn(
          "z-20",
          isMobile ? "flex flex-col mt-0 relative" : "absolute inset-0 mt-80"
        )}
      >
        <div
          className={cn(
            "relative z-50 mx-auto mb-4",
            isMobile ? "w-full" : "max-w-4xl text-center"
          )}
        >
          <h2
            className={cn(
              "inline-block text-3xl md:text-6xl bg-[radial-gradient(61.17%_178.53%_at_38.83%_-13.54%,#3B3B3B_0%,#888787_12.61%,#FFFFFF_50%,#888787_80%,#3B3B3B_100%)] ",
              "bg-clip-text text-transparent"
            )}
          >
            Choose Your Plan
          </h2>
        </div>
        <p
          className={cn(
            "text-sm text-neutral-400 mt-4 px-4",
            isMobile ? "w-full" : "max-w-lg text-center mx-auto"
          )}
        >
          Access mechanism-aware intelligence on epigenetic cancer programs.
          Choose the plan that fits your research and investment needs.
        </p>
        <div className="mx-auto mt-12 md:mt-20">
          <PricingList />
        </div>
      </div>
      {!isMobile && (
        <div
          className="absolute inset-0 rounded-[20px]"
          style={{
            background:
              "linear-gradient(179.87deg, rgba(0, 0, 0, 0) 0.11%, rgba(0, 0, 0, 0.8) 69.48%, #000000 92.79%)",
          }}
        />
      )}
    </div>
  )
}

function BackgroundShape() {
  const isMobile = useMediaQuery("(max-width: 768px)")
  const size = isMobile ? 600 : 1100
  const innerSize = isMobile ? 400 : 820

  return (
    <div className="absolute inset-0 overflow-hidden">
      <div
        className="absolute left-1/2 top-[55%] -translate-x-1/2 -translate-y-1/2 rounded-full border border-[rgba(255,255,255,0.1)]"
        style={{
          width: size,
          height: size,
          clipPath: "circle(50% at 50% 50%)",
          background: `
            radial-gradient(
              circle at center,
              rgba(40, 40, 40, 0.8) 0%,
              rgba(20, 20, 20, 0.6) 30%,
              rgba(0, 0, 0, 0.4) 70%
            )
          `,
        }}
      >
        <div
          className="absolute inset-0 opacity-10"
          style={{
            backgroundImage: `
              linear-gradient(rgba(255, 255, 255, 0.3) 1px, transparent 1px),
              linear-gradient(90deg, rgba(255, 255, 255, 0.3) 1px, transparent 1px)
            `,
            backgroundSize: isMobile ? "20px 40px" : "60px 120px",
          }}
        />
      </div>
      <div
        className="absolute bg-black z-2 left-1/2 top-[55%]
          -translate-x-1/2 -translate-y-1/2 rounded-full
          border border-[rgba(255,255,255,0.1)]
          shadow-[0_0_200px_80px_rgba(255,255,255,0.1)]"
        style={{
          width: innerSize,
          height: innerSize,
        }}
      />
    </div>
  )
}
