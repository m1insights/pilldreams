"use client"

import { useState } from "react"
import { createClient } from "@/lib/supabase/client"
import { Button } from "@/components/ui/button"
import { GlowingEffect } from "@/components/ui/glowing-effect"
import Link from "next/link"

export default function ResetPassword() {
  const [email, setEmail] = useState("")
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState("")
  const supabase = createClient()

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setMessage("")

    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/auth/callback?next=/update-password`,
      })

      if (error) throw error

      setMessage("Check your email for a password reset link!")
    } catch (error: any) {
      setMessage(error.message || "An error occurred")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-black flex items-center justify-center px-4">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-purple-900/20 via-black to-black" />

      {/* Animated grid background */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#4f4f4f2e_1px,transparent_1px),linear-gradient(to_bottom,#4f4f4f2e_1px,transparent_1px)] bg-[size:14px_24px]" />

      <div className="relative z-10 w-full max-w-md">
        <GlowingEffect>
          <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800 rounded-lg p-8">
            {/* Logo/Header */}
            <div className="text-center mb-8">
              <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent mb-2">
                Reset Password
              </h1>
              <p className="text-gray-400">
                Enter your email to receive a reset link
              </p>
            </div>

            {/* Reset Form */}
            <form onSubmit={handleResetPassword} className="space-y-6">
              <div>
                <label
                  htmlFor="email"
                  className="block text-sm font-medium text-gray-300 mb-2"
                >
                  Email
                </label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full px-4 py-3 bg-gray-800/50 border border-gray-700 rounded-lg focus:outline-none focus:border-purple-600 text-white placeholder-gray-500"
                  placeholder="you@example.com"
                />
              </div>

              {message && (
                <div
                  className={`p-4 rounded-lg ${
                    message.includes("error") || message.includes("Error")
                      ? "bg-red-900/20 border border-red-600 text-red-400"
                      : "bg-green-900/20 border border-green-600 text-green-400"
                  }`}
                >
                  {message}
                </div>
              )}

              <Button
                type="submit"
                disabled={loading}
                className="w-full py-6 text-lg"
              >
                {loading ? "Sending reset link..." : "Send Reset Link"}
              </Button>
            </form>

            {/* Divider */}
            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-700"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-gray-900 text-gray-400">
                  Remember your password?
                </span>
              </div>
            </div>

            {/* Login link */}
            <Link href="/login">
              <Button variant="outline" className="w-full">
                Log In
              </Button>
            </Link>

            {/* Back to home */}
            <div className="mt-6 text-center">
              <Link
                href="/"
                className="text-sm text-gray-400 hover:text-purple-400 transition-colors"
              >
                ← Back to home
              </Link>
            </div>
          </div>
        </GlowingEffect>
      </div>
    </div>
  )
}
