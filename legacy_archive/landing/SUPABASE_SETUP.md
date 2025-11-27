# Supabase Setup Guide for pilldreams

Complete step-by-step guide to set up Supabase authentication for the pilldreams landing page.

---

## Step 1: Create Supabase Project

1. Go to [supabase.com/dashboard](https://supabase.com/dashboard)
2. Click **"New Project"** button
3. Fill in the project details:
   - **Organization:** Select or create one
   - **Name:** `pilldreams`
   - **Database Password:** Create a strong password (save this securely - you'll need it later)
   - **Region:** Choose closest to your users (e.g., `us-east-1` for US East Coast)
   - **Pricing Plan:** Free (or Pro if you need more resources)

4. Click **"Create new project"**
5. Wait 2-3 minutes for project to be provisioned

---

## Step 2: Get API Credentials

1. Once project is ready, go to **Settings** (gear icon in sidebar)
2. Click **API** in the settings menu
3. You'll see two important values:

### Project URL
```
https://xxxxxxxxxxxxx.supabase.co
```
Copy this entire URL.

### API Keys
Under "Project API keys", find the **anon public** key:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```
Copy this entire key (it's very long, starts with `eyJ`).

**Note:** Do NOT copy the `service_role` key - that's a secret key for server use only.

---

## Step 3: Configure Environment Variables

1. Navigate to the landing page directory:
   ```bash
   cd /Users/mananshah/Dev/pilldreams/landing
   ```

2. Copy the example environment file:
   ```bash
   cp .env.example .env.local
   ```

3. Open `.env.local` in your editor:
   ```bash
   open .env.local
   # or
   code .env.local
   ```

4. Replace the placeholder values with your actual credentials:
   ```env
   # Supabase Configuration
   NEXT_PUBLIC_SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

   # App URLs (keep these as-is for local development)
   NEXT_PUBLIC_APP_URL=http://localhost:8501
   NEXT_PUBLIC_SITE_URL=http://localhost:3000
   ```

5. Save the file

**Security Note:** `.env.local` is in `.gitignore` and will NOT be committed to git.

---

## Step 4: Configure Supabase Authentication

### 4.1 Set Site URL

1. In Supabase Dashboard, go to **Authentication** → **URL Configuration**
2. Find **Site URL** field
3. For local development, enter:
   ```
   http://localhost:3000
   ```
4. For production, you'll change this to:
   ```
   https://pilldreams.com
   ```

### 4.2 Add Redirect URLs

1. Still in **Authentication** → **URL Configuration**
2. Find **Redirect URLs** section
3. Click **"Add URL"** and add these URLs (one at a time):

   **For local development:**
   ```
   http://localhost:3000/auth/callback
   http://localhost:8501
   ```

   **For production (add these later):**
   ```
   https://pilldreams.com/auth/callback
   https://app.pilldreams.com
   ```

4. Click **Save**

### 4.3 Email Auth Settings (Optional Customization)

1. Go to **Authentication** → **Providers**
2. Click on **Email** provider
3. Settings you can customize:
   - **Confirm email:** Toggle ON (recommended for production)
   - **Secure email change:** Toggle ON (recommended)
   - **Secure password change:** Toggle ON (recommended)

4. Click **Save**

### 4.4 Customize Email Templates (Optional)

1. Go to **Authentication** → **Email Templates**
2. You can customize these templates:
   - **Confirm signup** - Email sent to new users
   - **Magic Link** - Passwordless login (if you enable it)
   - **Change Email Address** - Email confirmation for email changes
   - **Reset Password** - Password reset email

Example customization for **Confirm signup**:
```html
<h2>Welcome to pilldreams!</h2>
<p>Click the link below to confirm your email address:</p>
<p><a href="{{ .ConfirmationURL }}">Confirm Email</a></p>
<p>Or copy and paste this URL: {{ .ConfirmationURL }}</p>
```

---

## Step 5: Install Dependencies & Run

1. Install npm packages:
   ```bash
   cd /Users/mananshah/Dev/pilldreams/landing
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

3. Open [http://localhost:3000](http://localhost:3000)

---

## Step 6: Test Authentication Flow

### Test Signup

1. Visit `http://localhost:3000`
2. Click **"Get Started Free"**
3. Enter your email and password (min 6 characters)
4. Click **"Sign Up"**
5. You should see: "Check your email to confirm your account!"
6. Check your email inbox (and spam folder)
7. Click the confirmation link in the email
8. You should be redirected to `http://localhost:8501` (the Streamlit app)

**Note:** Make sure Streamlit is running on port 8501:
```bash
cd /Users/mananshah/Dev/pilldreams
streamlit run app/main.py --server.port=8501
```

### Test Login

1. Visit `http://localhost:3000/login`
2. Enter your confirmed email and password
3. Click **"Log In"**
4. You should be redirected to the Streamlit app

### Test Password Reset

1. Visit `http://localhost:3000/reset-password`
2. Enter your email
3. Click **"Send Reset Link"**
4. Check your email for the reset link
5. Click the link and follow the flow

---

## Step 7: Verify Everything Works

### Check Supabase Dashboard

1. Go to **Authentication** → **Users**
2. You should see your test user listed
3. Check the user's:
   - **Email** (should match what you signed up with)
   - **Email Confirmed At** (should have a timestamp)
   - **Last Sign In** (should show recent login)

### Check Browser Console

1. Open browser DevTools (F12 or Cmd+Option+I)
2. Go to **Application** → **Cookies** → `http://localhost:3000`
3. You should see Supabase auth cookies:
   - `sb-<project-id>-auth-token`
   - `sb-<project-id>-auth-token-code-verifier`

---

## Troubleshooting

### Issue: "Invalid API key"

**Symptoms:** Error message when trying to sign up/login

**Solutions:**
1. Double-check your `.env.local` file has correct values
2. Make sure you copied the **anon public** key (NOT service_role)
3. Restart the dev server after changing `.env.local`:
   ```bash
   # Kill the server (Ctrl+C)
   npm run dev
   ```

### Issue: "Email not confirmed"

**Symptoms:** Can't log in after signing up

**Solutions:**
1. Check spam/junk folder for confirmation email
2. In Supabase Dashboard → Authentication → Users, manually confirm the email:
   - Click on the user
   - Toggle **Email Confirmed** to ON
3. For testing, disable email confirmation:
   - Go to **Authentication** → **Providers** → **Email**
   - Toggle **Confirm email** to OFF
   - Click **Save**

### Issue: "Redirect URL not allowed"

**Symptoms:** Error after clicking email confirmation link

**Solutions:**
1. Check **Authentication** → **URL Configuration** → **Redirect URLs**
2. Make sure you added:
   - `http://localhost:3000/auth/callback`
   - `http://localhost:8501`
3. Click **Save** after adding URLs

### Issue: Confirmation email not received

**Solutions:**
1. Check spam/junk folder
2. In Supabase Dashboard → **Authentication** → **Users**, click **"Send recovery email"**
3. Verify email provider settings (some providers block Supabase emails)
4. For development, use a Gmail or similar mainstream email provider

### Issue: Session not persisting

**Symptoms:** User gets logged out immediately after login

**Solutions:**
1. Check browser cookies are enabled
2. Clear browser cache and cookies
3. Verify middleware is configured correctly in `middleware.ts`
4. Check browser console for errors

---

## Production Deployment

### Update Environment Variables

When deploying to production (e.g., Vercel):

1. In Vercel Dashboard → **Settings** → **Environment Variables**
2. Add these variables:
   ```
   NEXT_PUBLIC_SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   NEXT_PUBLIC_APP_URL=https://app.pilldreams.com
   NEXT_PUBLIC_SITE_URL=https://pilldreams.com
   ```

### Update Supabase Settings

1. Go to **Authentication** → **URL Configuration**
2. Update **Site URL**:
   ```
   https://pilldreams.com
   ```
3. Add production **Redirect URLs**:
   ```
   https://pilldreams.com/auth/callback
   https://app.pilldreams.com
   ```
4. Click **Save**

---

## Additional Security Settings (Recommended for Production)

### Enable Email Rate Limiting

1. Go to **Authentication** → **Rate Limits**
2. Set limits to prevent abuse:
   - **Sign ups:** 10 per hour per IP
   - **Password recovery:** 5 per hour per email
   - **Email/SMS OTPs:** 10 per hour per email/phone

### Enable CAPTCHA (Optional)

1. Go to **Authentication** → **Settings**
2. Enable **CAPTCHA** protection
3. Add your CAPTCHA provider credentials (hCaptcha or reCAPTCHA)

### Monitor Auth Events

1. Go to **Authentication** → **Logs**
2. Monitor for:
   - Failed login attempts
   - Suspicious IP addresses
   - Unusual signup patterns

---

## Useful Supabase SQL Queries

Access via **SQL Editor** in Supabase Dashboard:

### View all users
```sql
SELECT id, email, created_at, last_sign_in_at, email_confirmed_at
FROM auth.users
ORDER BY created_at DESC;
```

### Count confirmed vs unconfirmed users
```sql
SELECT
  COUNT(*) FILTER (WHERE email_confirmed_at IS NOT NULL) as confirmed,
  COUNT(*) FILTER (WHERE email_confirmed_at IS NULL) as unconfirmed
FROM auth.users;
```

### Delete test users
```sql
-- WARNING: Use with caution!
DELETE FROM auth.users WHERE email LIKE '%test%';
```

---

## Support Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase Auth Guide](https://supabase.com/docs/guides/auth)
- [Next.js + Supabase Guide](https://supabase.com/docs/guides/getting-started/quickstarts/nextjs)
- [Supabase Discord Community](https://discord.supabase.com)

---

## Quick Reference

### Environment Variables
```env
NEXT_PUBLIC_SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
NEXT_PUBLIC_APP_URL=http://localhost:8501
NEXT_PUBLIC_SITE_URL=http://localhost:3000
```

### Redirect URLs (Local)
```
http://localhost:3000/auth/callback
http://localhost:8501
```

### Redirect URLs (Production)
```
https://pilldreams.com/auth/callback
https://app.pilldreams.com
```

### Site URL
- **Local:** `http://localhost:3000`
- **Production:** `https://pilldreams.com`
