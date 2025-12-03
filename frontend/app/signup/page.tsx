"use client"

import { useState } from "react"
import Link from "next/link"
import { useAuth } from "@/lib/auth/context"

export default function SignupPage() {
  const { signUp, signInWithGoogle, loading: authLoading } = useAuth()

  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [fullName, setFullName] = useState("")
  const [companyName, setCompanyName] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    // Validate passwords match
    if (password !== confirmPassword) {
      setError("Passwords do not match")
      return
    }

    // Validate password strength
    if (password.length < 8) {
      setError("Password must be at least 8 characters")
      return
    }

    setLoading(true)

    try {
      const { error: authError } = await signUp(email, password, {
        full_name: fullName || undefined,
        company_name: companyName || undefined,
      })

      if (authError) {
        setError(authError.message)
      } else {
        setSuccess(true)
      }
    } catch {
      setError("An unexpected error occurred")
    } finally {
      setLoading(false)
    }
  }

  const handleGoogleSignup = async () => {
    setError(null)
    const { error: authError } = await signInWithGoogle()
    if (authError) {
      setError(authError.message)
    }
  }

  if (authLoading) {
    return (
      <div className="min-h-screen bg-pd-primary flex items-center justify-center">
        <div className="text-pd-text-muted">Loading...</div>
      </div>
    )
  }

  if (success) {
    return (
      <div className="min-h-screen bg-pd-primary flex items-center justify-center px-4">
        <div className="w-full max-w-md">
          <div className="pd-card p-8 text-center">
            <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-green-900/30 flex items-center justify-center">
              <svg className="w-8 h-8 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-pd-text-primary mb-2">Check your email</h2>
            <p className="text-pd-text-secondary mb-6">
              We sent a confirmation link to <span className="text-pd-accent font-medium">{email}</span>
            </p>
            <p className="text-sm text-pd-text-muted mb-6">
              Click the link in the email to verify your account and get started.
            </p>
            <Link
              href="/login"
              className="inline-block px-6 py-3 rounded-lg bg-pd-accent text-white font-medium hover:bg-pd-accent/90 transition-colors"
            >
              Go to login
            </Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-pd-primary flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link href="/" className="inline-block">
            <span className="text-3xl font-bold bg-gradient-to-r from-white via-gray-300 to-gray-500 bg-clip-text text-transparent">
              Phase4
            </span>
          </Link>
          <p className="text-pd-text-secondary mt-2">Epigenetic Oncology Intelligence</p>
        </div>

        {/* Card */}
        <div className="pd-card p-8">
          <h1 className="text-2xl font-bold text-pd-text-primary mb-2">Create your account</h1>
          <p className="text-pd-text-secondary mb-6">Start your 14-day free trial. No credit card required.</p>

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-3 rounded-lg bg-red-900/30 border border-red-800 text-red-400 text-sm">
              {error}
            </div>
          )}

          {/* Google Sign Up */}
          <button
            onClick={handleGoogleSignup}
            className="w-full py-3 px-4 rounded-lg bg-pd-secondary border border-pd-border text-pd-text-primary font-medium hover:border-pd-accent/50 transition-colors flex items-center justify-center gap-3 mb-6"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path
                fill="currentColor"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="currentColor"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="currentColor"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
              />
              <path
                fill="currentColor"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
              />
            </svg>
            Continue with Google
          </button>

          {/* Divider */}
          <div className="relative mb-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-pd-border" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-pd-card text-pd-text-muted">or sign up with email</span>
            </div>
          </div>

          {/* Form */}
          <form onSubmit={handleSignup}>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="fullName" className="block text-sm font-medium text-pd-text-secondary mb-2">
                    Full name
                  </label>
                  <input
                    id="fullName"
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="w-full px-4 py-3 rounded-lg bg-pd-secondary border border-pd-border text-pd-text-primary placeholder:text-pd-text-muted focus:outline-none focus:ring-2 focus:ring-pd-accent focus:border-transparent"
                    placeholder="John Doe"
                  />
                </div>
                <div>
                  <label htmlFor="companyName" className="block text-sm font-medium text-pd-text-secondary mb-2">
                    Company
                  </label>
                  <input
                    id="companyName"
                    type="text"
                    value={companyName}
                    onChange={(e) => setCompanyName(e.target.value)}
                    className="w-full px-4 py-3 rounded-lg bg-pd-secondary border border-pd-border text-pd-text-primary placeholder:text-pd-text-muted focus:outline-none focus:ring-2 focus:ring-pd-accent focus:border-transparent"
                    placeholder="Acme Inc"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="email" className="block text-sm font-medium text-pd-text-secondary mb-2">
                  Work email
                </label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full px-4 py-3 rounded-lg bg-pd-secondary border border-pd-border text-pd-text-primary placeholder:text-pd-text-muted focus:outline-none focus:ring-2 focus:ring-pd-accent focus:border-transparent"
                  placeholder="you@company.com"
                />
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-medium text-pd-text-secondary mb-2">
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={8}
                  className="w-full px-4 py-3 rounded-lg bg-pd-secondary border border-pd-border text-pd-text-primary placeholder:text-pd-text-muted focus:outline-none focus:ring-2 focus:ring-pd-accent focus:border-transparent"
                  placeholder="••••••••"
                />
                <p className="mt-1 text-xs text-pd-text-muted">Must be at least 8 characters</p>
              </div>

              <div>
                <label htmlFor="confirmPassword" className="block text-sm font-medium text-pd-text-secondary mb-2">
                  Confirm password
                </label>
                <input
                  id="confirmPassword"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  className="w-full px-4 py-3 rounded-lg bg-pd-secondary border border-pd-border text-pd-text-primary placeholder:text-pd-text-muted focus:outline-none focus:ring-2 focus:ring-pd-accent focus:border-transparent"
                  placeholder="••••••••"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 px-4 rounded-lg bg-pd-accent text-white font-medium hover:bg-pd-accent/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Creating account...
                  </span>
                ) : (
                  "Create account"
                )}
              </button>
            </div>
          </form>

          {/* Sign In Link */}
          <p className="mt-6 text-center text-sm text-pd-text-muted">
            Already have an account?{" "}
            <Link href="/login" className="text-pd-accent hover:underline font-medium">
              Sign in
            </Link>
          </p>
        </div>

        {/* Features */}
        <div className="mt-8 grid grid-cols-3 gap-4 text-center">
          <div className="p-4">
            <div className="text-2xl mb-2">🧬</div>
            <div className="text-xs text-pd-text-muted">79 Epigenetic Targets</div>
          </div>
          <div className="p-4">
            <div className="text-2xl mb-2">💊</div>
            <div className="text-xs text-pd-text-muted">60+ Scored Drugs</div>
          </div>
          <div className="p-4">
            <div className="text-2xl mb-2">📊</div>
            <div className="text-xs text-pd-text-muted">991 Clinical Trials</div>
          </div>
        </div>

        {/* Footer */}
        <p className="mt-6 text-center text-xs text-pd-text-muted">
          By signing up, you agree to our{" "}
          <Link href="/terms" className="text-pd-accent hover:underline">Terms of Service</Link>
          {" "}and{" "}
          <Link href="/privacy" className="text-pd-accent hover:underline">Privacy Policy</Link>
        </p>
      </div>
    </div>
  )
}
