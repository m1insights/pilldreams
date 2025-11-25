# pilldreams Landing Page

Next.js landing page with Supabase authentication for the pilldreams drug intelligence platform.

## Architecture

This is a **two-tier architecture**:
- **Landing Page** (Next.js) → Authentication & Marketing at `pilldreams.com`
- **Dashboard** (Streamlit) → Main application at `localhost:8501` or `app.pilldreams.com`

**Flow:** User visits landing page → Signs up/logs in → Redirected to Streamlit dashboard

## Tech Stack

- **Framework:** Next.js 15 (App Router)
- **Styling:** Tailwind CSS + custom components
- **Animation:** Framer Motion
- **Auth:** Supabase Auth (SSR-based)
- **Database:** Supabase (PostgreSQL)

## Setup Instructions

### 1. Install Dependencies

```bash
cd landing
npm install
```

### 2. Set Up Supabase

1. Go to [supabase.com/dashboard](https://supabase.com/dashboard)
2. Click "New Project"
3. Fill in project details:
   - **Name:** `pilldreams`
   - **Database Password:** (save this securely)
   - **Region:** (closest to your users)
4. Wait for project to be created (~2 minutes)
5. Go to **Settings** → **API**
6. Copy:
   - **Project URL** (looks like `https://xxxxx.supabase.co`)
   - **anon public** key (starts with `eyJ...`)

### 3. Configure Environment Variables

Create `.env.local` in the `landing/` directory:

```bash
cp .env.example .env.local
```

Edit `.env.local` and add your Supabase credentials:

```env
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJxxxxxxxxxxxxxxxxx

# App URLs
NEXT_PUBLIC_APP_URL=http://localhost:8501
NEXT_PUBLIC_SITE_URL=http://localhost:3000
```

### 4. Configure Supabase Auth Settings

1. In Supabase Dashboard, go to **Authentication** → **URL Configuration**
2. Add the following URLs:

**Site URL:**
```
http://localhost:3000
```

**Redirect URLs:**
```
http://localhost:3000/auth/callback
http://localhost:8501
```

3. Go to **Authentication** → **Email Templates**
4. Customize email templates if desired (optional)

### 5. Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### 6. Test the Flow

1. Visit `http://localhost:3000`
2. Click "Get Started Free"
3. Sign up with an email and password
4. Check your email for confirmation link
5. Click confirmation link
6. You should be redirected to the Streamlit app at `http://localhost:8501`

**Note:** Make sure the Streamlit app is running on port 8501:

```bash
cd /Users/mananshah/Dev/pilldreams
streamlit run app/main.py --server.port=8501
```

## Project Structure

```
landing/
├── app/                      # Next.js App Router
│   ├── page.tsx             # Main landing page
│   ├── login/               # Login page
│   ├── signup/              # Signup page
│   ├── reset-password/      # Password reset page
│   └── auth/
│       └── callback/        # Auth callback handler
├── components/              # React components
│   ├── hero.tsx            # Hero section
│   ├── features.tsx        # Features section
│   ├── pricing.tsx         # Pricing section
│   └── ui/                 # UI components
│       ├── button.tsx
│       └── glowing-effect.tsx
├── lib/                     # Utility functions
│   ├── utils.ts            # Class name utilities
│   └── supabase/           # Supabase clients
│       ├── client.ts       # Browser client
│       └── server.ts       # Server client
├── middleware.ts            # Auth middleware
└── .env.local              # Environment variables (not committed)
```

## Key Features

### Landing Page
- Animated hero section with scroll effects
- Feature cards highlighting drug intelligence capabilities
- Three-tier pricing (Free, Professional, Enterprise)
- Smooth scroll-to-section navigation
- Mobile responsive

### Authentication
- Email/password sign up with email confirmation
- Login with error handling
- Password reset flow
- Session management via Supabase cookies
- Protected routes via middleware
- Auto-redirect to Streamlit app after login

### Design System
- Aceternity-inspired glassmorphism UI
- Purple/blue gradient theme
- Glowing effects on interactive elements
- Framer Motion scroll animations
- Responsive grid layouts

## Authentication Flow

```
1. User visits landing page (/)
2. Clicks "Get Started Free"
3. Redirected to /signup
4. Enters email + password
5. Supabase sends confirmation email
6. User clicks email link → /auth/callback
7. Session created, redirected to Streamlit app (localhost:8501)
```

## Deployment

### Production URLs

Update `.env.local` for production:

```env
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJxxxxxxxxxxxxxxxxx
NEXT_PUBLIC_APP_URL=https://app.pilldreams.com
NEXT_PUBLIC_SITE_URL=https://pilldreams.com
```

### Supabase Production Settings

In Supabase Dashboard, update **Authentication** → **URL Configuration**:

**Site URL:**
```
https://pilldreams.com
```

**Redirect URLs:**
```
https://pilldreams.com/auth/callback
https://app.pilldreams.com
```

### Deploy to Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Set environment variables in Vercel dashboard
# Settings → Environment Variables
```

## Development

### Adding New Components

```bash
# Create a new component
touch components/new-component.tsx
```

```tsx
// components/new-component.tsx
"use client"

import { motion } from "framer-motion"

export function NewComponent() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      whileInView={{ opacity: 1 }}
      viewport={{ once: true }}
    >
      {/* Your content */}
    </motion.div>
  )
}
```

### Modifying Pricing Tiers

Edit `components/pricing.tsx`:

```tsx
const tiers = [
  {
    name: "Free",
    price: "$0",
    period: "forever",
    features: ["Feature 1", "Feature 2"],
    // ...
  },
  // Add or modify tiers
]
```

### Customizing Colors

Edit `tailwind.config.ts` for global color changes, or update gradient classes in components:

```tsx
// Purple/blue gradient
className="bg-gradient-to-r from-purple-600 to-blue-600"

// Purple/pink gradient
className="bg-gradient-to-r from-purple-600 to-pink-600"
```

## Troubleshooting

### Issue: "Error: Invalid API key"
- **Solution:** Check that `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` are set correctly in `.env.local`
- Restart dev server after changing environment variables

### Issue: "Email not confirmed"
- **Solution:** Check spam folder for confirmation email
- Or disable email confirmation in Supabase → Authentication → Email Auth → "Confirm email" (not recommended for production)

### Issue: "Redirect URL not allowed"
- **Solution:** Add the redirect URL to Supabase → Authentication → URL Configuration → Redirect URLs

### Issue: Middleware not protecting routes
- **Solution:** Check that `middleware.ts` is in the root of the `app/` directory
- Verify the `matcher` config in `middleware.ts` includes the routes you want to protect

### Issue: Session not persisting
- **Solution:** Ensure cookies are enabled in browser
- Check that Supabase is configured for SSR (using `@supabase/ssr` package)

## Next Steps

1. ✅ Landing page created
2. ✅ Authentication implemented
3. ⏳ **Add Supabase auth to Streamlit app** (see `/Users/mananshah/Dev/pilldreams/CLAUDE.md` for integration guide)
4. ⏳ Deploy landing page to Vercel
5. ⏳ Deploy Streamlit app to Streamlit Cloud or other platform
6. ⏳ Set up custom domain
7. ⏳ Configure email templates in Supabase

## Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [Supabase Auth Guide](https://supabase.com/docs/guides/auth)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Framer Motion](https://www.framer.com/motion/)
