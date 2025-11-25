# pilldreams Authentication Architecture

## Overview

**pilldreams** uses a **two-tier architecture** with separate authentication flows managed by Supabase Auth:

1. **Landing Page** (Next.js) → Authentication & Marketing at `pilldreams.com`
2. **Dashboard** (Streamlit) → Main application at `app.pilldreams.com`

---

## Authentication Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  1. User visits http://localhost:3000 (Landing Page)            │
│  2. Clicks "Get Started Free" → /signup                         │
│  3. Creates account with email + password                       │
│  4. Supabase sends confirmation email                           │
│  5. User clicks email link → /auth/callback?code=...            │
│  6. Callback exchanges code for Supabase session                │
│  7. Redirected to: http://localhost:8501?access_token=...       │
│  8. Streamlit verifies token via core/auth.py                   │
│  9. ✅ If valid → Show dashboard                                │
│  10. ❌ If invalid → Redirect back to /login                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

### Landing Page (Next.js)

**Location:** `/Users/mananshah/Dev/pilldreams/landing/`

```
landing/
├── lib/supabase/
│   ├── client.ts          # Browser Supabase client (client components)
│   └── server.ts          # Server Supabase client (server components, SSR)
├── middleware.ts          # Auth middleware (route protection, session refresh)
├── app/
│   ├── page.tsx           # Landing page (hero, features, pricing)
│   ├── login/page.tsx     # Login page (passes access_token to Streamlit)
│   ├── signup/page.tsx    # Sign up page
│   ├── reset-password/page.tsx  # Password reset
│   └── auth/callback/route.ts   # OAuth callback (exchanges code for session)
├── .env.local             # Environment variables (NOT committed to git)
└── SUPABASE_SETUP.md      # Comprehensive setup guide
```

**Key Features:**
- Aceternity-inspired glassmorphism design
- Purple/blue gradient theme
- Email/password authentication
- Email confirmation required
- Password reset flow
- Auto-redirect to Streamlit after successful auth

### Streamlit Dashboard

**Location:** `/Users/mananshah/Dev/pilldreams/app/`

```
app/
├── main.py                # Main entry point (calls require_authentication())
└── ...

core/
├── auth.py                # Authentication verification module
│   ├── require_authentication()  # Enforces auth, redirects if invalid
│   ├── get_session_from_cookies()  # Extracts session from query params
│   └── check_authentication()  # Verifies Supabase session
└── supabase_client.py     # Supabase database client
```

**Key Features:**
- Session verification on every page load
- Query parameter-based token passing
- Graceful redirect to landing page if unauthorized
- User data accessible via `require_authentication()` return value

---

## Key Files Deep Dive

### Landing Page: `lib/supabase/client.ts`

**Purpose:** Browser-side Supabase client for client components.

```typescript
import { createBrowserClient } from '@supabase/ssr'

export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  )
}
```

**Used in:** Login/Signup forms, client-side interactions.

---

### Landing Page: `lib/supabase/server.ts`

**Purpose:** Server-side Supabase client for Server Components with cookie management.

```typescript
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'

export async function createClient() {
  const cookieStore = await cookies()
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() { return cookieStore.getAll() },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options)
            )
          } catch {
            // Server Component - can be ignored with middleware
          }
        },
      },
    }
  )
}
```

**Used in:** Auth callback, middleware, server-side auth checks.

---

### Landing Page: `middleware.ts`

**Purpose:** Protects routes and refreshes sessions.

```typescript
export async function middleware(request: NextRequest) {
  const supabase = createServerClient(...)
  const { data: { user } } = await supabase.auth.getUser()

  // Redirect to login if accessing protected routes without auth
  if (!user && request.nextUrl.pathname.startsWith('/dashboard')) {
    return NextResponse.redirect('/login')
  }

  return supabaseResponse // Includes refreshed session cookies
}
```

**Protects:** Dashboard routes (if any added to landing page).

---

### Landing Page: `app/auth/callback/route.ts`

**Purpose:** Handles email confirmation and OAuth callbacks.

```typescript
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const code = searchParams.get('code')

  if (code) {
    const supabase = await createClient()
    const { data, error } = await supabase.auth.exchangeCodeForSession(code)

    if (!error && data.session) {
      const streamlitUrl = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:8501'
      // Pass access_token to Streamlit via query parameter
      return NextResponse.redirect(`${streamlitUrl}?access_token=${data.session.access_token}`)
    }
  }

  return NextResponse.redirect(`/login?error=auth_callback_error`)
}
```

**Critical:** This file passes the `access_token` to Streamlit.

---

### Landing Page: `app/login/page.tsx`

**Purpose:** Login form that redirects to Streamlit after successful auth.

```typescript
const handleLogin = async (e: React.FormEvent) => {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  })

  if (data.user && data.session) {
    const appUrl = process.env.NEXT_PUBLIC_APP_URL || "http://localhost:8501"
    // Pass access_token to Streamlit
    window.location.href = `${appUrl}?access_token=${data.session.access_token}`
  }
}
```

**Flow:** User enters credentials → Supabase validates → Redirect to Streamlit with token.

---

### Streamlit: `core/auth.py`

**Purpose:** Verifies Supabase sessions in the Streamlit app.

```python
from supabase import create_client, Client
import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
LANDING_PAGE_URL = os.getenv("NEXT_PUBLIC_SITE_URL", "http://localhost:3000")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

def get_session_from_cookies():
    """Extract access_token from query parameters."""
    query_params = st.query_params
    access_token = query_params.get("access_token", None)

    if access_token:
        try:
            user = supabase.auth.get_user(access_token)
            if user:
                return {
                    "access_token": access_token,
                    "user": user.user
                }
        except Exception as e:
            st.error(f"Token verification failed: {e}")
            return None

    return None

def check_authentication():
    """Check if user is authenticated."""
    session = get_session_from_cookies()
    if session:
        return session["user"]
    return None

def require_authentication():
    """Enforce authentication for the Streamlit app."""
    user = check_authentication()

    if not user:
        # Show redirect message
        st.markdown(f"""
        <div style="text-align: center;">
            <h1>💊 pilldreams</h1>
            <p>Authentication Required</p>
            <a href="{LANDING_PAGE_URL}/login">Go to Login →</a>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    return user
```

**Usage in `app/main.py`:**

```python
from core.auth import require_authentication

# At the top of main.py, before any UI rendering:
user = require_authentication()

# Now `user` contains authenticated user data
# If user is not authenticated, execution stops and redirect message is shown
```

---

## Environment Variables

### Landing Page: `.env.local`

**Location:** `/Users/mananshah/Dev/pilldreams/landing/.env.local`

```env
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://fhwvmhgqxqtflbctogtq.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# App URLs (local development)
NEXT_PUBLIC_APP_URL=http://localhost:8501
NEXT_PUBLIC_SITE_URL=http://localhost:3000
```

**Note:** `.env.local` is in `.gitignore` and NOT committed to version control.

---

### Streamlit App: `.env`

**Location:** `/Users/mananshah/Dev/pilldreams/.env`

```env
# Supabase Auth (for Streamlit app auth integration)
NEXT_PUBLIC_SUPABASE_URL=https://fhwvmhgqxqtflbctogtq.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
NEXT_PUBLIC_SITE_URL=http://localhost:3000
NEXT_PUBLIC_APP_URL=http://localhost:8501
```

---

## Supabase Dashboard Configuration

### URL Configuration

1. Go to **Supabase Dashboard** → **Authentication** → **URL Configuration**

2. **Site URL** (development):
   ```
   http://localhost:3000
   ```

3. **Redirect URLs** (development):
   ```
   http://localhost:3000/auth/callback
   http://localhost:8501
   ```

### Production Configuration

**Site URL:**
```
https://pilldreams.com
```

**Redirect URLs:**
```
https://pilldreams.com/auth/callback
https://app.pilldreams.com
```

---

## Security Considerations

### Token Passing

- **Access tokens** are passed via URL query parameters (`?access_token=...`)
- Tokens are **short-lived** and **single-use**
- Supabase handles token refresh and expiration automatically
- No passwords or secrets stored in Streamlit app

### Session Verification

- Streamlit verifies the token on **every page load** via `require_authentication()`
- Invalid/expired tokens trigger redirect to landing page login
- Unauthorized users **cannot access the dashboard**

### Environment Variables

- **Sensitive keys** (Supabase URL, Anon Key) stored in `.env` files
- `.env.local` is in `.gitignore` (Next.js)
- `.env` should NOT be committed (Streamlit) - add to `.gitignore`

### HTTPS in Production

- **Always use HTTPS** in production for:
  - Landing page (`https://pilldreams.com`)
  - Streamlit app (`https://app.pilldreams.com`)
  - Supabase API (`https://fhwvmhgqxqtflbctogtq.supabase.co`)

---

## Testing the Auth Flow

### Local Development Setup

1. **Start Landing Page:**
   ```bash
   cd /Users/mananshah/Dev/pilldreams/landing
   npm run dev
   ```
   Runs on: `http://localhost:3000`

2. **Start Streamlit App:**
   ```bash
   cd /Users/mananshah/Dev/pilldreams
   streamlit run app/main.py --server.port=8501
   ```
   Runs on: `http://localhost:8501`

### Test Scenarios

#### ✅ Successful Auth Flow

1. Visit `http://localhost:3000`
2. Click "Get Started Free"
3. Enter email + password (min 6 characters)
4. Check email for confirmation link
5. Click link → Redirected to `http://localhost:8501?access_token=...`
6. Dashboard loads successfully

#### ❌ Unauthorized Access

1. Visit `http://localhost:8501` **directly** (without logging in)
2. Should see authentication required message
3. Click "Go to Login" → Redirected to `http://localhost:3000/login`

#### 🔄 Login Flow

1. Visit `http://localhost:3000/login`
2. Enter confirmed email + password
3. Click "Log In"
4. Redirected to `http://localhost:8501?access_token=...`
5. Dashboard loads successfully

#### 🔑 Password Reset Flow

1. Visit `http://localhost:3000/reset-password`
2. Enter email
3. Click "Send Reset Link"
4. Check email for reset link
5. Click link → Set new password
6. Log in with new password

---

## Production Deployment

### Landing Page (Vercel)

1. **Set Environment Variables:**

   In Vercel Dashboard → **Settings** → **Environment Variables**:
   ```
   NEXT_PUBLIC_SUPABASE_URL=https://fhwvmhgqxqtflbctogtq.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
   NEXT_PUBLIC_APP_URL=https://app.pilldreams.com
   NEXT_PUBLIC_SITE_URL=https://pilldreams.com
   ```

2. **Deploy:**
   ```bash
   cd landing
   vercel
   ```

### Streamlit App (Streamlit Cloud / Render)

1. **Set Environment Variables:**

   In deployment platform's environment settings:
   ```
   NEXT_PUBLIC_SUPABASE_URL=https://fhwvmhgqxqtflbctogtq.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
   NEXT_PUBLIC_SITE_URL=https://pilldreams.com
   NEXT_PUBLIC_APP_URL=https://app.pilldreams.com
   ```

2. **Deploy:**
   - **Streamlit Cloud:** Connect GitHub repo, select `app/main.py`
   - **Render:** Create Web Service, set start command: `streamlit run app/main.py`

### Update Supabase Configuration

1. Go to **Supabase Dashboard** → **Authentication** → **URL Configuration**

2. **Site URL:**
   ```
   https://pilldreams.com
   ```

3. **Redirect URLs:**
   ```
   https://pilldreams.com/auth/callback
   https://app.pilldreams.com
   ```

4. Click **Save**

---

## Troubleshooting

### Issue: "Invalid API key"

**Symptoms:** Error message when trying to sign up/login.

**Solutions:**
1. Double-check `.env.local` and `.env` have correct Supabase credentials
2. Ensure you copied the **anon public** key (NOT service_role key)
3. Restart dev servers after changing environment variables:
   ```bash
   # Landing page
   cd landing && npm run dev

   # Streamlit app
   cd .. && streamlit run app/main.py --server.port=8501
   ```

---

### Issue: "Email not confirmed"

**Symptoms:** Can't log in after signing up.

**Solutions:**
1. Check spam/junk folder for confirmation email
2. In Supabase Dashboard → **Authentication** → **Users**:
   - Click on the user
   - Toggle **Email Confirmed** to ON
3. For testing, disable email confirmation:
   - Go to **Authentication** → **Providers** → **Email**
   - Toggle **Confirm email** to OFF

---

### Issue: "Redirect URL not allowed"

**Symptoms:** Error after clicking email confirmation link.

**Solutions:**
1. Check **Supabase Dashboard** → **Authentication** → **URL Configuration** → **Redirect URLs**
2. Ensure these URLs are added:
   - `http://localhost:3000/auth/callback`
   - `http://localhost:8501`
3. Click **Save**

---

### Issue: Streamlit shows "Authentication Required" even after logging in

**Symptoms:** Token verification fails, shows redirect message.

**Solutions:**
1. Check Streamlit console for errors (token verification failed)
2. Verify `.env` has correct `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`
3. Check browser URL has `?access_token=...` query parameter
4. Try logging in again (token may have expired)

---

### Issue: "Module not found: supabase"

**Symptoms:** Import error in Streamlit app.

**Solutions:**
1. Install Supabase Python SDK:
   ```bash
   cd /Users/mananshah/Dev/pilldreams
   source venv/bin/activate
   pip install supabase
   ```
2. Verify `supabase>=2.0.0` is in `requirements.txt`

---

## Setup Checklist

### Initial Setup

- [ ] Create Supabase project at [supabase.com/dashboard](https://supabase.com/dashboard)
- [ ] Copy Project URL and anon public key
- [ ] Create `landing/.env.local` with Supabase credentials
- [ ] Update `/Users/mananshah/Dev/pilldreams/.env` with Supabase auth variables
- [ ] Configure Supabase Site URL and Redirect URLs
- [ ] Install dependencies: `cd landing && npm install`
- [ ] Install Python dependencies: `cd .. && pip install supabase`

### Testing

- [ ] Start landing page: `cd landing && npm run dev`
- [ ] Start Streamlit: `cd .. && streamlit run app/main.py --server.port=8501`
- [ ] Test signup flow (email confirmation)
- [ ] Test login flow
- [ ] Test unauthorized access (direct Streamlit visit)
- [ ] Test password reset flow

### Production Deployment

- [ ] Update environment variables in Vercel (landing page)
- [ ] Update environment variables in Streamlit Cloud/Render
- [ ] Update Supabase Site URL to production domain
- [ ] Update Supabase Redirect URLs to production domains
- [ ] Test production auth flow end-to-end
- [ ] Verify HTTPS is enforced on all endpoints

---

## Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase Auth Guide](https://supabase.com/docs/guides/auth)
- [Next.js + Supabase Quickstart](https://supabase.com/docs/guides/getting-started/quickstarts/nextjs)
- [Streamlit Authentication Patterns](https://docs.streamlit.io/knowledge-base/deploy/authentication-without-sso)
- [pilldreams Supabase Setup Guide](/landing/SUPABASE_SETUP.md)

---

## Quick Reference

### Run Commands

**Landing Page:**
```bash
cd /Users/mananshah/Dev/pilldreams/landing
npm run dev
```

**Streamlit App:**
```bash
cd /Users/mananshah/Dev/pilldreams
source venv/bin/activate
streamlit run app/main.py --server.port=8501
```

### URLs (Development)

- **Landing Page:** http://localhost:3000
- **Streamlit App:** http://localhost:8501
- **Login:** http://localhost:3000/login
- **Signup:** http://localhost:3000/signup
- **Password Reset:** http://localhost:3000/reset-password

### Environment Variables Template

```env
NEXT_PUBLIC_SUPABASE_URL=https://fhwvmhgqxqtflbctogtq.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
NEXT_PUBLIC_SITE_URL=http://localhost:3000
NEXT_PUBLIC_APP_URL=http://localhost:8501
```
