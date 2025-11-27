"use client"

import { useState } from "react"
import { createClient } from "@/lib/supabase/client"
import { Button } from "@/components/ui/button"
import { GlowingEffect } from "@/components/ui/glowing-effect"
import Link from "next/link"
import { useRouter } from "next/navigation"

export default function SignUp() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState("")
  const router = useRouter()
  const supabase = createClient()

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setMessage("")

    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          emailRedirectTo: `${window.location.origin}/auth/callback`,
        },
      })

      if (error) throw error

      if (data.user) {
        setMessage("Check your email to confirm your account!")
      }
    } catch (error: any) {
      setMessage(error.message || "An error occurred during signup")
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
                Create Account
              </h1>
              <p className="text-gray-400">
                Start analyzing drug intelligence today
              </p>
            </div>

            {/* Signup Form */}
            <form onSubmit={handleSignUp} className="space-y-6">
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

              <div>
                <label
                  htmlFor="password"
                  className="block text-sm font-medium text-gray-300 mb-2"
                >
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={6}
                  className="w-full px-4 py-3 bg-gray-800/50 border border-gray-700 rounded-lg focus:outline-none focus:border-purple-600 text-white placeholder-gray-500"
                  placeholder="At least 6 characters"
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
                {loading ? "Creating account..." : "Sign Up"}
              </Button>
            </form>

            {/* Divider */}
            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-700"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-gray-900 text-gray-400">
                  Already have an account?
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
