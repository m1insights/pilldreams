-- CI Platform: Watchlist, Auth, and Payments Schema
-- Weeks 4-6 Implementation
-- Created: 2025-12-02

-- ============================================
-- WEEK 4: WATCHLIST + ALERTS
-- ============================================

-- User watchlist items (drugs, targets, companies, trials)
CREATE TABLE IF NOT EXISTS ci_watchlist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,  -- References auth.users

    -- Entity being watched
    entity_type TEXT NOT NULL CHECK (entity_type IN ('drug', 'target', 'company', 'trial', 'indication')),
    entity_id UUID NOT NULL,
    entity_name TEXT NOT NULL,  -- Denormalized for quick display

    -- Watch preferences
    alert_on_phase_change BOOLEAN DEFAULT true,
    alert_on_status_change BOOLEAN DEFAULT true,
    alert_on_score_change BOOLEAN DEFAULT true,
    alert_on_news BOOLEAN DEFAULT true,
    alert_on_patent BOOLEAN DEFAULT false,
    alert_on_pdufa BOOLEAN DEFAULT true,

    -- Alert delivery
    alert_email BOOLEAN DEFAULT true,
    alert_slack BOOLEAN DEFAULT false,
    alert_in_app BOOLEAN DEFAULT true,

    -- Metadata
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Prevent duplicate watches
    UNIQUE(user_id, entity_type, entity_id)
);

-- User alert queue (pending alerts to be sent)
CREATE TABLE IF NOT EXISTS ci_alert_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    watchlist_id UUID REFERENCES ci_watchlist(id) ON DELETE CASCADE,
    change_log_id UUID REFERENCES ci_change_log(id),

    -- Alert content
    alert_type TEXT NOT NULL,  -- 'phase_change', 'status_change', 'pdufa', etc.
    alert_title TEXT NOT NULL,
    alert_body TEXT,
    alert_url TEXT,  -- Deep link to entity
    significance TEXT NOT NULL CHECK (significance IN ('critical', 'high', 'medium', 'low')),

    -- Delivery status
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'read', 'dismissed')),
    email_sent_at TIMESTAMPTZ,
    slack_sent_at TIMESTAMPTZ,
    read_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- User notification preferences (global settings)
CREATE TABLE IF NOT EXISTS ci_notification_prefs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE,

    -- Global email settings
    email_enabled BOOLEAN DEFAULT true,
    email_frequency TEXT DEFAULT 'realtime' CHECK (email_frequency IN ('realtime', 'daily', 'weekly')),
    email_min_significance TEXT DEFAULT 'high' CHECK (email_min_significance IN ('critical', 'high', 'medium', 'low')),

    -- Slack integration
    slack_enabled BOOLEAN DEFAULT false,
    slack_webhook_url TEXT,
    slack_min_significance TEXT DEFAULT 'critical',

    -- In-app notifications
    in_app_enabled BOOLEAN DEFAULT true,

    -- Quiet hours
    quiet_hours_enabled BOOLEAN DEFAULT false,
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    timezone TEXT DEFAULT 'America/New_York',

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- WEEK 6: AUTH + PAYMENTS (STRIPE)
-- ============================================

-- User profiles (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS ci_user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Profile info
    email TEXT NOT NULL,
    full_name TEXT,
    company_name TEXT,
    job_title TEXT,

    -- Subscription info
    subscription_tier TEXT DEFAULT 'free' CHECK (subscription_tier IN ('free', 'pro', 'enterprise')),
    subscription_status TEXT DEFAULT 'active' CHECK (subscription_status IN ('active', 'past_due', 'canceled', 'trialing')),

    -- Stripe integration
    stripe_customer_id TEXT UNIQUE,
    stripe_subscription_id TEXT,
    stripe_price_id TEXT,

    -- Trial info
    trial_ends_at TIMESTAMPTZ,
    trial_used BOOLEAN DEFAULT false,

    -- Usage limits
    api_calls_this_month INTEGER DEFAULT 0,
    api_calls_limit INTEGER DEFAULT 100,  -- Free tier limit
    exports_this_month INTEGER DEFAULT 0,
    exports_limit INTEGER DEFAULT 5,  -- Free tier limit

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ
);

-- Subscription tiers configuration
CREATE TABLE IF NOT EXISTS ci_subscription_tiers (
    id TEXT PRIMARY KEY,  -- 'free', 'pro', 'enterprise'
    name TEXT NOT NULL,
    description TEXT,

    -- Pricing
    price_monthly INTEGER,  -- In cents (e.g., 4900 = $49)
    price_yearly INTEGER,   -- In cents (e.g., 39900 = $399/year)
    stripe_price_id_monthly TEXT,
    stripe_price_id_yearly TEXT,

    -- Limits
    api_calls_limit INTEGER,
    exports_limit INTEGER,
    watchlist_limit INTEGER,
    alerts_limit INTEGER,

    -- Features
    feature_exports BOOLEAN DEFAULT false,
    feature_api_access BOOLEAN DEFAULT false,
    feature_slack_alerts BOOLEAN DEFAULT false,
    feature_priority_support BOOLEAN DEFAULT false,
    feature_custom_reports BOOLEAN DEFAULT false,

    -- Display
    is_popular BOOLEAN DEFAULT false,
    display_order INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert default subscription tiers
INSERT INTO ci_subscription_tiers (id, name, description, price_monthly, price_yearly, api_calls_limit, exports_limit, watchlist_limit, alerts_limit, feature_exports, feature_api_access, feature_slack_alerts, display_order) VALUES
    ('free', 'Free', 'Basic access to epigenetic oncology intelligence', 0, 0, 100, 5, 10, 50, false, false, false, 1),
    ('pro', 'Pro', 'Full access for individual researchers and analysts', 4900, 39900, 1000, 50, 100, 500, true, true, true, 2),
    ('enterprise', 'Enterprise', 'Unlimited access for teams with priority support', 19900, 159900, -1, -1, -1, -1, true, true, true, 3)
ON CONFLICT (id) DO UPDATE SET
    price_monthly = EXCLUDED.price_monthly,
    price_yearly = EXCLUDED.price_yearly;

-- Stripe webhook events log
CREATE TABLE IF NOT EXISTS ci_stripe_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stripe_event_id TEXT NOT NULL UNIQUE,
    event_type TEXT NOT NULL,

    -- Event data
    customer_id TEXT,
    subscription_id TEXT,
    invoice_id TEXT,
    amount INTEGER,
    currency TEXT,

    -- Processing
    processed BOOLEAN DEFAULT false,
    processed_at TIMESTAMPTZ,
    error_message TEXT,

    -- Raw data
    raw_payload JSONB,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Payment history
CREATE TABLE IF NOT EXISTS ci_payment_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES ci_user_profiles(id),

    -- Stripe references
    stripe_invoice_id TEXT,
    stripe_payment_intent_id TEXT,
    stripe_subscription_id TEXT,

    -- Payment details
    amount INTEGER NOT NULL,  -- In cents
    currency TEXT DEFAULT 'usd',
    status TEXT NOT NULL CHECK (status IN ('succeeded', 'pending', 'failed', 'refunded')),

    -- Invoice details
    description TEXT,
    period_start TIMESTAMPTZ,
    period_end TIMESTAMPTZ,

    -- Receipt
    receipt_url TEXT,
    invoice_pdf_url TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- INDEXES
-- ============================================

CREATE INDEX IF NOT EXISTS idx_watchlist_user ON ci_watchlist(user_id);
CREATE INDEX IF NOT EXISTS idx_watchlist_entity ON ci_watchlist(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_alert_queue_user ON ci_alert_queue(user_id, status);
CREATE INDEX IF NOT EXISTS idx_alert_queue_pending ON ci_alert_queue(status) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_user_profiles_stripe ON ci_user_profiles(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_stripe_events_type ON ci_stripe_events(event_type, processed);
CREATE INDEX IF NOT EXISTS idx_payment_history_user ON ci_payment_history(user_id);

-- ============================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================

-- Enable RLS on all tables
ALTER TABLE ci_watchlist ENABLE ROW LEVEL SECURITY;
ALTER TABLE ci_alert_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE ci_notification_prefs ENABLE ROW LEVEL SECURITY;
ALTER TABLE ci_user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE ci_payment_history ENABLE ROW LEVEL SECURITY;

-- Watchlist: Users can only see/modify their own
CREATE POLICY watchlist_user_policy ON ci_watchlist
    FOR ALL USING (auth.uid() = user_id);

-- Alert queue: Users can only see their own alerts
CREATE POLICY alert_queue_user_policy ON ci_alert_queue
    FOR ALL USING (auth.uid() = user_id);

-- Notification prefs: Users can only see/modify their own
CREATE POLICY notification_prefs_user_policy ON ci_notification_prefs
    FOR ALL USING (auth.uid() = user_id);

-- User profiles: Users can only see/modify their own
CREATE POLICY user_profiles_policy ON ci_user_profiles
    FOR ALL USING (auth.uid() = id);

-- Payment history: Users can only see their own
CREATE POLICY payment_history_user_policy ON ci_payment_history
    FOR ALL USING (auth.uid() = user_id);

-- Subscription tiers: Everyone can read (public pricing)
ALTER TABLE ci_subscription_tiers ENABLE ROW LEVEL SECURITY;
CREATE POLICY subscription_tiers_read ON ci_subscription_tiers
    FOR SELECT USING (true);

-- ============================================
-- FUNCTIONS
-- ============================================

-- Function to create user profile on signup
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO ci_user_profiles (id, email, full_name, trial_ends_at)
    VALUES (
        NEW.id,
        NEW.email,
        NEW.raw_user_meta_data->>'full_name',
        NOW() + INTERVAL '14 days'
    );

    INSERT INTO ci_notification_prefs (user_id)
    VALUES (NEW.id);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger on auth.users insert
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- Function to check feature access
CREATE OR REPLACE FUNCTION check_feature_access(
    p_user_id UUID,
    p_feature TEXT
) RETURNS BOOLEAN AS $$
DECLARE
    v_tier TEXT;
    v_has_access BOOLEAN;
BEGIN
    -- Get user's tier
    SELECT subscription_tier INTO v_tier
    FROM ci_user_profiles
    WHERE id = p_user_id;

    IF v_tier IS NULL THEN
        RETURN false;
    END IF;

    -- Check feature access based on tier
    EXECUTE format('SELECT feature_%s FROM ci_subscription_tiers WHERE id = $1', p_feature)
    INTO v_has_access
    USING v_tier;

    RETURN COALESCE(v_has_access, false);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to increment usage counter
CREATE OR REPLACE FUNCTION increment_usage(
    p_user_id UUID,
    p_counter TEXT
) RETURNS BOOLEAN AS $$
DECLARE
    v_current INTEGER;
    v_limit INTEGER;
BEGIN
    -- Get current usage and limit
    EXECUTE format('SELECT %s_this_month, %s_limit FROM ci_user_profiles WHERE id = $1', p_counter, p_counter)
    INTO v_current, v_limit
    USING p_user_id;

    -- Check if limit reached (-1 means unlimited)
    IF v_limit != -1 AND v_current >= v_limit THEN
        RETURN false;
    END IF;

    -- Increment counter
    EXECUTE format('UPDATE ci_user_profiles SET %s_this_month = %s_this_month + 1 WHERE id = $1', p_counter, p_counter)
    USING p_user_id;

    RETURN true;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Reset monthly usage counters (run via cron on 1st of month)
CREATE OR REPLACE FUNCTION reset_monthly_usage()
RETURNS void AS $$
BEGIN
    UPDATE ci_user_profiles
    SET api_calls_this_month = 0,
        exports_this_month = 0,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- COMMENTS
-- ============================================

COMMENT ON TABLE ci_watchlist IS 'User watchlist for tracking specific entities';
COMMENT ON TABLE ci_alert_queue IS 'Queue of pending alerts to be delivered';
COMMENT ON TABLE ci_user_profiles IS 'Extended user profiles with subscription info';
COMMENT ON TABLE ci_subscription_tiers IS 'Subscription tier definitions and limits';
COMMENT ON TABLE ci_stripe_events IS 'Stripe webhook event log for debugging';
COMMENT ON TABLE ci_payment_history IS 'User payment history and receipts';
