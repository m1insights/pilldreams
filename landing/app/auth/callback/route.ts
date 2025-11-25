import { createClient } from '@/lib/supabase/server'
import { NextResponse } from 'next/server'

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url)
  const code = searchParams.get('code')
  const next = searchParams.get('next') ?? '/'

  if (code) {
    const supabase = await createClient()
    const { data, error } = await supabase.auth.exchangeCodeForSession(code)

    if (!error && data.session) {
      const forwardedHost = request.headers.get('x-forwarded-host')
      const isLocalEnv = process.env.NODE_ENV === 'development'

      if (isLocalEnv) {
        // Redirect to Streamlit app after successful login
        // Pass access_token as query parameter for Streamlit to verify
        const streamlitUrl = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:8501'
        return NextResponse.redirect(`${streamlitUrl}?access_token=${data.session.access_token}`)
      } else if (forwardedHost) {
        const appUrl = process.env.NEXT_PUBLIC_APP_URL || `https://${forwardedHost}`
        return NextResponse.redirect(`${appUrl}?access_token=${data.session.access_token}`)
      } else {
        return NextResponse.redirect(`${origin}${next}`)
      }
    }
  }

  // Error handling - redirect back to login with error
  return NextResponse.redirect(`${origin}/login?error=auth_callback_error`)
}
