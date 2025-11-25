"use client"

import { motion } from "framer-motion"
import { Button } from "./ui/button"
import { GlowingEffect } from "./ui/glowing-effect"
import Link from "next/link"

const tiers = [
  {
    name: "Free",
    price: "$0",
    period: "forever",
    description: "Perfect for exploring the platform",
    features: [
      "Access to 1,000 drugs",
      "Basic drug intelligence",
      "Trial progress tracking",
      "Safety signal alerts",
      "Community support",
    ],
    cta: "Get Started Free",
    featured: false,
  },
  {
    name: "Professional",
    price: "$49",
    period: "per month",
    description: "For serious biotech investors",
    features: [
      "Access to all 26,000+ drugs",
      "Full drug intelligence suite",
      "Real-time FDA data updates",
      "AI-powered approval predictions",
      "Advanced filtering & search",
      "Export data & reports",
      "Priority email support",
      "API access (coming soon)",
    ],
    cta: "Start Free Trial",
    featured: true,
  },
  {
    name: "Enterprise",
    price: "Custom",
    period: "contact us",
    description: "For teams and institutions",
    features: [
      "Everything in Professional",
      "Unlimited team members",
      "Custom data integrations",
      "Dedicated account manager",
      "SLA & priority support",
      "White-label options",
      "Custom training sessions",
      "Volume discounts",
    ],
    cta: "Contact Sales",
    featured: false,
  },
]

export function Pricing() {
  return (
    <div id="pricing" className="relative py-24 bg-black">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-black via-blue-900/10 to-black" />

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            <span className="bg-gradient-to-r from-white via-purple-200 to-blue-200 bg-clip-text text-transparent">
              Simple, transparent pricing
            </span>
          </h2>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto">
            Choose the plan that fits your investment strategy. All plans include our core intelligence features.
          </p>
        </motion.div>

        {/* Pricing cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {tiers.map((tier, index) => (
            <motion.div
              key={tier.name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              viewport={{ once: true }}
              className={`${tier.featured ? "md:-mt-4" : ""} h-full`}
            >
              <GlowingEffect
                glowClassName={
                  tier.featured
                    ? "bg-gradient-to-r from-purple-600 to-blue-600 opacity-30 group-hover:opacity-50"
                    : "bg-gradient-to-r from-purple-600 to-blue-600 opacity-10 group-hover:opacity-20"
                }
              >
                <div
                  className={`relative h-full bg-gray-900/50 backdrop-blur-sm border rounded-lg p-8 ${tier.featured
                      ? "border-purple-600 md:py-12"
                      : "border-gray-800 hover:border-gray-700"
                    } transition-all duration-300`}
                >
                  {/* Featured badge */}
                  {tier.featured && (
                    <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                      <div className="px-4 py-1 bg-gradient-to-r from-purple-600 to-blue-600 rounded-full text-sm font-medium text-white">
                        Most Popular
                      </div>
                    </div>
                  )}

                  {/* Tier name */}
                  <h3 className="text-2xl font-bold text-white mb-2">
                    {tier.name}
                  </h3>

                  {/* Description */}
                  <p className="text-gray-400 mb-6">{tier.description}</p>

                  {/* Price */}
                  <div className="mb-6">
                    <div className="flex items-baseline gap-2">
                      <span className="text-5xl font-bold text-white">
                        {tier.price}
                      </span>
                      <span className="text-gray-400">/{tier.period}</span>
                    </div>
                  </div>

                  {/* CTA button */}
                  <Link href="/signup" className="block mb-8">
                    <Button
                      variant={tier.featured ? "default" : "outline"}
                      className="w-full"
                    >
                      {tier.cta}
                    </Button>
                  </Link>

                  {/* Features list */}
                  <ul className="space-y-4">
                    {tier.features.map((feature) => (
                      <li key={feature} className="flex items-start gap-3">
                        <svg
                          className="w-5 h-5 text-purple-400 mt-0.5 flex-shrink-0"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M5 13l4 4L19 7"
                          />
                        </svg>
                        <span className="text-gray-300">{feature}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </GlowingEffect>
            </motion.div>
          ))}
        </div>

        {/* FAQ link */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          viewport={{ once: true }}
          className="text-center mt-12"
        >
          <p className="text-gray-400">
            Have questions?{" "}
            <a
              href="#faq"
              className="text-purple-400 hover:text-purple-300 transition-colors"
            >
              Check our FAQ
            </a>{" "}
            or{" "}
            <a
              href="mailto:support@pilldreams.com"
              className="text-purple-400 hover:text-purple-300 transition-colors"
            >
              contact us
            </a>
          </p>
        </motion.div>
      </div>
    </div>
  )
}
