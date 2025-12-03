"""
ETL 35: Generate Weekly Change Digest

Collects pending changes and generates email digests for subscribers.
Uses Resend API for email delivery.

Automation: Runs weekly on Monday 9am ET (or per user preferences)

Usage:
    python -m backend.etl.35_generate_digest
    python -m backend.etl.35_generate_digest --dry-run
    python -m backend.etl.35_generate_digest --email user@example.com
    python -m backend.etl.35_generate_digest --preview  # Generate HTML preview
"""

import os
import sys
import json
import argparse
from datetime import datetime, date, timedelta
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: SUPABASE_URL and SUPABASE_KEY required")
    sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ============================================================
# Email Template
# ============================================================

def generate_email_html(
    changes: List[Dict],
    user_name: str,
    period_start: date,
    period_end: date
) -> str:
    """Generate HTML email content for the digest with Phase4 dark theme branding."""

    # Group changes by significance
    critical = [c for c in changes if c["significance"] == "critical"]
    high = [c for c in changes if c["significance"] == "high"]
    medium = [c for c in changes if c["significance"] == "medium"]
    low = [c for c in changes if c["significance"] == "low"]

    # Group changes by type for news/patents/pdufa sections
    news_changes = [c for c in changes if c["entity_type"] == "news"]
    patent_changes = [c for c in changes if c["entity_type"] == "patent"]
    drug_changes = [c for c in changes if c["entity_type"] == "drug"]
    trial_changes = [c for c in changes if c["entity_type"] == "trial"]
    pdufa_changes = [c for c in changes if c["entity_type"] == "pdufa"]

    # Format date range
    date_range = f"{period_start.strftime('%b %d')} - {period_end.strftime('%b %d, %Y')}"

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Phase4 Weekly Intelligence Digest</title>
    <style>
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #ffffff;
            max-width: 640px;
            margin: 0 auto;
            padding: 20px;
            background-color: #000000;
        }}
        .container {{
            background: #000000;
            padding: 32px;
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
        }}
        .logo {{
            font-size: 42px;
            font-weight: 600;
            letter-spacing: -0.02em;
            margin-bottom: 12px;
            /* Metallic gradient matching hero */
            background: radial-gradient(61.17% 178.53% at 38.83% -13.54%, #3B3B3B 0%, #888787 12.61%, #FFFFFF 50%, #888787 80%, #3B3B3B 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .subtitle {{
            color: #6b7280;
            font-size: 15px;
            letter-spacing: 0.3px;
        }}
        .greeting {{
            color: #d4d4d8;
            margin-bottom: 8px;
            font-size: 15px;
        }}
        .intro {{
            color: #a1a1aa;
            margin-bottom: 32px;
            font-size: 15px;
        }}
        .intro strong {{
            color: #ffffff;
        }}
        .stats {{
            display: flex;
            justify-content: center;
            gap: 40px;
            margin: 32px 0;
            padding: 24px;
            background: #0a0a0a;
            border-radius: 16px;
            border: 1px solid #1a1a1a;
        }}
        .stat {{
            text-align: center;
        }}
        .stat-number {{
            font-size: 32px;
            font-weight: 700;
            color: #e4e4e7;
            letter-spacing: -0.02em;
        }}
        .stat-number.critical {{
            color: #fca5a5;
        }}
        .stat-number.high {{
            color: #4ade80;
        }}
        .stat-label {{
            font-size: 11px;
            color: #71717a;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-top: 6px;
        }}
        .section {{
            margin: 32px 0;
        }}
        .section-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 16px;
        }}
        .section-icon {{
            font-size: 18px;
        }}
        .section-title {{
            font-size: 14px;
            font-weight: 600;
            color: #d4d4d8;
            flex-grow: 1;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
        }}
        .badge-critical {{
            background: rgba(252, 165, 165, 0.1);
            color: #fca5a5;
            border: 1px solid rgba(252, 165, 165, 0.2);
        }}
        .badge-high {{
            background: rgba(74, 222, 128, 0.1);
            color: #4ade80;
            border: 1px solid rgba(74, 222, 128, 0.2);
        }}
        .badge-medium {{
            background: rgba(96, 165, 250, 0.1);
            color: #60a5fa;
            border: 1px solid rgba(96, 165, 250, 0.2);
        }}
        .badge-low {{
            background: rgba(113, 113, 122, 0.1);
            color: #a1a1aa;
            border: 1px solid rgba(113, 113, 122, 0.2);
        }}
        .change-item {{
            padding: 16px 18px;
            margin: 12px 0;
            background: #0a0a0a;
            border-radius: 12px;
            border: 1px solid #1a1a1a;
            border-left: 3px solid #333333;
        }}
        .change-item.critical {{
            border-left-color: #fca5a5;
        }}
        .change-item.high {{
            border-left-color: #4ade80;
        }}
        .change-item.medium {{
            border-left-color: #60a5fa;
        }}
        .change-title {{
            font-weight: 600;
            color: #e4e4e7;
            margin-bottom: 6px;
            font-size: 14px;
        }}
        .change-detail {{
            font-size: 13px;
            color: #a1a1aa;
        }}
        .change-meta {{
            font-size: 12px;
            color: #52525b;
            margin-top: 10px;
        }}
        .change-link {{
            color: #60a5fa;
            text-decoration: none;
        }}
        .change-link:hover {{
            text-decoration: underline;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 24px;
            border-top: 1px solid #1a1a1a;
            text-align: center;
        }}
        .footer p {{
            font-size: 12px;
            color: #52525b;
            margin: 8px 0;
        }}
        .footer a {{
            color: #60a5fa;
            text-decoration: none;
        }}
        .cta-button {{
            display: inline-block;
            padding: 14px 32px;
            background: #ffffff;
            color: #000000 !important;
            text-decoration: none;
            border-radius: 9999px;
            font-weight: 600;
            margin: 24px 0;
            font-size: 14px;
        }}
        .empty-state {{
            text-align: center;
            padding: 48px 20px;
            color: #71717a;
        }}
        .divider {{
            height: 1px;
            background: linear-gradient(90deg, transparent, #333333, transparent);
            margin: 28px 0;
        }}
        .entity-tag {{
            display: inline-block;
            padding: 2px 8px;
            background: #1a1a1a;
            border-radius: 4px;
            font-size: 10px;
            color: #71717a;
            text-transform: uppercase;
            margin-right: 8px;
            letter-spacing: 0.3px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">Phase4</div>
            <div class="subtitle">Epigenetic Oncology Intelligence</div>
        </div>

        <p class="greeting">Hi {user_name or 'there'},</p>
        <p class="intro">Here's your weekly intelligence digest for <strong>{date_range}</strong>.</p>

        <div class="stats">
            <div class="stat">
                <div class="stat-number">{len(changes)}</div>
                <div class="stat-label">Total Updates</div>
            </div>
            <div class="stat">
                <div class="stat-number critical">{len(critical)}</div>
                <div class="stat-label">Critical</div>
            </div>
            <div class="stat">
                <div class="stat-number high">{len(high)}</div>
                <div class="stat-label">High Priority</div>
            </div>
        </div>
"""

    # Critical changes
    if critical:
        html += """
        <div class="section">
            <div class="section-header">
                <span class="section-icon">🚨</span>
                <span class="section-title">Critical Updates</span>
                <span class="badge badge-critical">{count}</span>
            </div>
""".format(count=len(critical))
        for c in critical:
            html += _render_change_item(c, "critical")
        html += "        </div>\n"

    # High priority changes
    if high:
        html += """
        <div class="section">
            <div class="section-header">
                <span class="section-icon">⚠️</span>
                <span class="section-title">High Priority</span>
                <span class="badge badge-high">{count}</span>
            </div>
""".format(count=len(high))
        for c in high[:10]:  # Limit to 10
            html += _render_change_item(c, "high")
        if len(high) > 10:
            html += f'            <p class="change-meta">...and {len(high) - 10} more high priority changes</p>\n'
        html += "        </div>\n"

    # Medium priority changes
    if medium:
        html += """
        <div class="section">
            <div class="section-header">
                <span class="section-icon">📢</span>
                <span class="section-title">Notable Updates</span>
                <span class="badge badge-medium">{count}</span>
            </div>
""".format(count=len(medium))
        for c in medium[:8]:  # Limit to 8
            html += _render_change_item(c, "medium")
        if len(medium) > 8:
            html += f'            <p class="change-meta">...and {len(medium) - 8} more notable changes</p>\n'
        html += "        </div>\n"

    # Low priority summary
    if low:
        html += f"""
        <div class="section">
            <div class="section-header">
                <span class="section-icon">📝</span>
                <span class="section-title">Other Updates</span>
                <span class="badge badge-low">{len(low)}</span>
            </div>
            <p class="change-meta">{len(low)} minor changes (score adjustments, metadata updates)</p>
        </div>
"""

    # No changes
    if not changes:
        html += """
        <div class="empty-state">
            <p>No significant changes detected this week.</p>
            <p>We'll notify you when there are updates to track.</p>
        </div>
"""

    # CTA and footer
    html += """
        <div class="divider"></div>

        <div style="text-align: center;">
            <a href="https://phase4.io/calendar" class="cta-button">View Full Calendar →</a>
        </div>

        <div class="footer">
            <p>You're receiving this because you subscribed to Phase4 intelligence digests.</p>
            <p>
                <a href="https://phase4.io/settings/notifications" class="change-link">Manage preferences</a> ·
                <a href="https://phase4.io/unsubscribe" class="change-link">Unsubscribe</a>
            </p>
            <p style="margin-top: 16px;">© 2025 Phase4 · Epigenetic Oncology Intelligence</p>
        </div>
    </div>
</body>
</html>
"""

    return html


def _render_change_item(change: Dict, significance: str) -> str:
    """Render a single change item as HTML."""
    title = change.get("change_summary") or change.get("entity_name", "Unknown")
    detail = ""

    if change.get("old_value") and change.get("new_value"):
        detail = f"{change.get('field_changed', 'Value')}: {change['old_value']} → {change['new_value']}"
    elif change.get("change_type") == "new_entity":
        detail = f"New {change['entity_type']} added to database"

    source_url = change.get("source_url", "")
    source_link = f'<a href="{source_url}" class="change-link">View source →</a>' if source_url else ""

    detected = change.get("detected_at", "")
    if detected:
        try:
            dt = datetime.fromisoformat(detected.replace("Z", "+00:00"))
            detected = dt.strftime("%b %d, %I:%M %p")
        except:
            pass

    # Entity type tag
    entity_type = change.get("entity_type", "").upper()
    entity_tag = f'<span class="entity-tag">{entity_type}</span>' if entity_type else ""

    return f"""
            <div class="change-item {significance}">
                <div class="change-title">{entity_tag}{title}</div>
                <div class="change-detail">{detail}</div>
                <div class="change-meta">{detected} · {change.get('source', 'etl')} {source_link}</div>
            </div>
"""


def generate_plain_text(changes: List[Dict], user_name: str, period_start: date, period_end: date) -> str:
    """Generate plain text version of the digest."""
    date_range = f"{period_start.strftime('%b %d')} - {period_end.strftime('%b %d, %Y')}"

    text = f"""
PHASE4 WEEKLY INTELLIGENCE DIGEST
Epigenetic Oncology Intelligence
{date_range}

Hi {user_name or 'there'},

Here's your weekly intelligence digest:

SUMMARY
- Total Updates: {len(changes)}
- Critical: {len([c for c in changes if c['significance'] == 'critical'])}
- High Priority: {len([c for c in changes if c['significance'] == 'high'])}
- Notable: {len([c for c in changes if c['significance'] == 'medium'])}
- Other: {len([c for c in changes if c['significance'] == 'low'])}

"""

    for sig, emoji in [("critical", "🚨"), ("high", "⚠️"), ("medium", "📢")]:
        sig_changes = [c for c in changes if c["significance"] == sig]
        if sig_changes:
            text += f"\n{emoji} {sig.upper()} UPDATES\n"
            text += "-" * 40 + "\n"
            for c in sig_changes[:10]:
                summary = c.get("change_summary") or c.get("entity_name", "Unknown")
                text += f"• {summary}\n"
                if c.get("source_url"):
                    text += f"  {c['source_url']}\n"
            if len(sig_changes) > 10:
                text += f"  ...and {len(sig_changes) - 10} more\n"

    text += f"""

View the full calendar: https://phase4.io/calendar

---
Manage preferences: https://phase4.io/settings/notifications
Unsubscribe: https://phase4.io/unsubscribe

© 2025 Phase4 · Epigenetic Oncology Intelligence
"""

    return text


# ============================================================
# Resend Email Delivery
# ============================================================

def send_email_via_resend(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: str,
    dry_run: bool = False
) -> Optional[str]:
    """Send email using Resend API."""

    if dry_run:
        print(f"   📧 DRY RUN: Would send to {to_email}")
        print(f"   Subject: {subject}")
        return "dry-run-message-id"

    if not RESEND_API_KEY:
        print("   ⚠️  RESEND_API_KEY not set - skipping email delivery")
        return None

    try:
        import requests

        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "from": "Phase4 Intelligence <digest@phase4.io>",
                "to": [to_email],
                "subject": subject,
                "html": html_content,
                "text": text_content,
                "tags": [
                    {"name": "type", "value": "digest"},
                    {"name": "frequency", "value": "weekly"}
                ]
            }
        )

        if response.status_code == 200:
            data = response.json()
            return data.get("id")
        else:
            print(f"   ❌ Resend error: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"   ❌ Email error: {e}")
        return None


# ============================================================
# Digest Generation
# ============================================================

def check_tables_exist() -> bool:
    """Check if required tables exist."""
    try:
        supabase.table("ci_change_log").select("id").limit(1).execute()
        supabase.table("ci_user_digest_prefs").select("id").limit(1).execute()
        return True
    except Exception as e:
        if "PGRST205" in str(e):
            return False
        raise


def get_pending_changes(
    min_significance: str = "low",
    entity_types: Optional[List[str]] = None,
    since: Optional[datetime] = None
) -> List[Dict]:
    """Fetch pending changes from ci_change_log."""

    # Default to last 7 days
    if since is None:
        since = datetime.now() - timedelta(days=7)

    try:
        query = supabase.table("ci_change_log")\
            .select("*")\
            .eq("digest_sent", False)\
            .gte("detected_at", since.isoformat())
    except Exception as e:
        if "PGRST205" in str(e):
            return []
        raise

    query = supabase.table("ci_change_log")\
        .select("*")\
        .eq("digest_sent", False)\
        .gte("detected_at", since.isoformat())

    # Filter by significance
    sig_levels = ["critical", "high", "medium", "low"]
    min_idx = sig_levels.index(min_significance)
    allowed_sigs = sig_levels[:min_idx + 1]
    query = query.in_("significance", allowed_sigs)

    # Filter by entity types
    if entity_types:
        query = query.in_("entity_type", entity_types)

    result = query.order("detected_at", desc=True).execute()

    return result.data or []


def get_digest_subscribers(frequency: str = "weekly") -> List[Dict]:
    """Fetch active digest subscribers."""
    try:
        result = supabase.table("ci_user_digest_prefs")\
            .select("*")\
            .eq("is_active", True)\
            .eq("digest_frequency", frequency)\
            .execute()
        return result.data or []
    except Exception as e:
        if "PGRST205" in str(e):
            return []
        raise


def mark_changes_as_sent(change_ids: List[str]) -> int:
    """Mark changes as sent in digest."""
    if not change_ids:
        return 0

    result = supabase.table("ci_change_log")\
        .update({"digest_sent": True, "digest_sent_at": datetime.now().isoformat()})\
        .in_("id", change_ids)\
        .execute()

    return len(result.data) if result.data else 0


def log_digest_sent(
    user_id: str,
    email: str,
    change_ids: List[str],
    message_id: Optional[str],
    subject: str,
    html_preview: str
) -> None:
    """Log digest to history table."""
    supabase.table("ci_digest_history").insert({
        "user_id": user_id,
        "email": email,
        "digest_type": "weekly",
        "change_count": len(change_ids),
        "change_ids": change_ids,
        "resend_message_id": message_id,
        "subject": subject,
        "html_preview": html_preview[:500],
        "delivery_status": "sent" if message_id else "failed"
    }).execute()


# ============================================================
# Main Entry Point
# ============================================================

def generate_sample_changes() -> List[Dict]:
    """Generate sample changes for preview mode when tables don't exist."""
    return [
        {"id": "1", "entity_type": "drug", "entity_name": "TAZEMETOSTAT", "change_type": "approval",
         "field_changed": "fda_approved", "old_value": "false", "new_value": "true",
         "change_summary": "TAZEMETOSTAT: FDA approval granted", "significance": "critical",
         "source": "fda", "source_url": "https://fda.gov/example", "detected_at": datetime.now().isoformat()},
        {"id": "2", "entity_type": "drug", "entity_name": "GSK126", "change_type": "phase_change",
         "field_changed": "max_phase", "old_value": "2", "new_value": "3",
         "change_summary": "GSK126: Phase 2 → Phase 3", "significance": "critical",
         "source": "ctgov", "source_url": "https://clinicaltrials.gov/study/NCT00000001", "detected_at": datetime.now().isoformat()},
        {"id": "3", "entity_type": "news", "entity_name": "EZH2 inhibitor shows synergy with anti-PD1", "change_type": "new_entity",
         "field_changed": None, "old_value": None, "new_value": "epi_io",
         "change_summary": "📰 EZH2 inhibitor shows synergy with anti-PD1 in melanoma model", "significance": "high",
         "source": "nature_cancer", "source_url": "https://nature.com/articles/example", "detected_at": datetime.now().isoformat()},
        {"id": "4", "entity_type": "patent", "entity_name": "US12345678", "change_type": "new_entity",
         "field_changed": "category", "old_value": None, "new_value": "epi_editor",
         "change_summary": "📜 CRISPR-based epigenetic silencing of oncogenes [BRD4, MYC]", "significance": "high",
         "source": "uspto", "source_url": "https://patents.google.com/patent/US12345678", "detected_at": datetime.now().isoformat()},
        {"id": "5", "entity_type": "trial", "entity_name": "NCT05432101", "change_type": "status_change",
         "field_changed": "status", "old_value": "RECRUITING", "new_value": "COMPLETED",
         "change_summary": "NCT05432101: Trial completed", "significance": "medium",
         "source": "ctgov", "source_url": "https://clinicaltrials.gov/study/NCT05432101", "detected_at": datetime.now().isoformat()},
        {"id": "6", "entity_type": "trial", "entity_name": "NCT06123456", "change_type": "date_change",
         "field_changed": "primary_completion_date", "old_value": "2025-03-01", "new_value": "2025-06-01",
         "change_summary": "NCT06123456: Primary completion delayed to June 2025", "significance": "medium",
         "source": "ctgov", "source_url": "https://clinicaltrials.gov/study/NCT06123456", "detected_at": datetime.now().isoformat()},
        {"id": "7", "entity_type": "drug", "entity_name": "VORINOSTAT", "change_type": "score_change",
         "field_changed": "total_score", "old_value": "62", "new_value": "68",
         "change_summary": "VORINOSTAT: Total score increased by 6 points", "significance": "low",
         "source": "etl", "source_url": None, "detected_at": datetime.now().isoformat()},
        {"id": "8", "entity_type": "pdufa", "entity_name": "Pelabresib (MOR)", "change_type": "new_entity",
         "field_changed": None, "old_value": None, "new_value": "2025-09-01",
         "change_summary": "📅 PDUFA Alert: Pelabresib (MOR) - Sept 1, 2025", "significance": "high",
         "source": "pdufa_tracker", "source_url": "https://morphosys.com/pipeline/pelabresib", "detected_at": datetime.now().isoformat()},
        {"id": "9", "entity_type": "pdufa", "entity_name": "Ziftomenib (KURA)", "change_type": "status_change",
         "field_changed": "status", "old_value": "pending", "new_value": "approved",
         "change_summary": "🎉 FDA APPROVED: Ziftomenib (KURA)", "significance": "critical",
         "source": "fda_rss", "source_url": "https://fda.gov/drugs/approvals", "detected_at": datetime.now().isoformat()},
    ]


def generate_digest(
    dry_run: bool = False,
    preview: bool = False,
    target_email: Optional[str] = None
) -> Dict[str, Any]:
    """Generate and send weekly digest to subscribers."""

    print("=" * 60)
    print("CI Platform: Weekly Digest Generator")
    print(f"Time: {datetime.now().isoformat()}")
    print(f"Mode: {'DRY RUN' if dry_run else 'PREVIEW' if preview else 'LIVE'}")
    print("=" * 60)

    # Check if tables exist
    tables_exist = check_tables_exist()
    if not tables_exist:
        print("\n⚠️  Required tables not found!")
        print("   Run migration: core/migration_ci_change_detection.sql")
        if preview:
            print("   Using sample data for preview...")
        else:
            return {"subscribers": 0, "emails_sent": 0, "emails_failed": 0, "total_changes": 0}

    # Get date range
    period_end = date.today()
    period_start = period_end - timedelta(days=7)

    # Get subscribers
    if target_email:
        subscribers = [{"id": None, "email": target_email, "name": "Test User", "min_significance": "low", "entity_types": None}]
    elif preview:
        subscribers = [{"id": None, "email": "preview@example.com", "name": "Preview User", "min_significance": "low", "entity_types": None}]
    else:
        subscribers = get_digest_subscribers("weekly")

    print(f"\n👥 Found {len(subscribers)} active subscribers")

    # In preview mode, always use sample data for demonstration
    use_sample_data = preview

    results = {
        "subscribers": len(subscribers),
        "emails_sent": 0,
        "emails_failed": 0,
        "total_changes": 0
    }

    for sub in subscribers:
        email = sub["email"]
        name = sub.get("name", "")
        min_sig = sub.get("min_significance", "low")
        entity_types = sub.get("entity_types")

        print(f"\n📬 Processing: {email}")

        # Get changes for this subscriber
        if use_sample_data:
            changes = generate_sample_changes()
        else:
            changes = get_pending_changes(
                min_significance=min_sig,
                entity_types=entity_types,
                since=datetime.combine(period_start, datetime.min.time())
            )

        print(f"   Found {len(changes)} changes (min_sig: {min_sig})")
        results["total_changes"] += len(changes)

        if not changes:
            print("   ⏭️  No changes - skipping")
            continue

        # Generate email content
        html = generate_email_html(changes, name, period_start, period_end)
        text = generate_plain_text(changes, name, period_start, period_end)

        # Count by significance
        critical_count = len([c for c in changes if c["significance"] == "critical"])
        high_count = len([c for c in changes if c["significance"] == "high"])

        # Generate subject line
        if critical_count > 0:
            subject = f"🚨 {critical_count} Critical Updates in Epigenetic Oncology"
        elif high_count > 0:
            subject = f"⚠️ {high_count} High Priority Updates This Week"
        else:
            subject = f"📊 Your Weekly Epigenetic Oncology Digest ({len(changes)} updates)"

        # Preview mode - just output HTML
        if preview:
            preview_path = f"/tmp/pilldreams_digest_preview_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            with open(preview_path, "w") as f:
                f.write(html)
            print(f"   📄 Preview saved to: {preview_path}")
            continue

        # Send email
        message_id = send_email_via_resend(email, subject, html, text, dry_run)

        if message_id:
            results["emails_sent"] += 1
            change_ids = [c["id"] for c in changes]

            if not dry_run:
                # Mark changes as sent
                mark_changes_as_sent(change_ids)

                # Log to history
                log_digest_sent(
                    user_id=sub.get("id"),
                    email=email,
                    change_ids=change_ids,
                    message_id=message_id,
                    subject=subject,
                    html_preview=html
                )

            print(f"   ✅ Sent ({len(changes)} changes)")
        else:
            results["emails_failed"] += 1
            print(f"   ❌ Failed to send")

    # Summary
    print("\n" + "=" * 60)
    print("DIGEST SUMMARY")
    print("=" * 60)
    print(f"Subscribers: {results['subscribers']}")
    print(f"Emails Sent: {results['emails_sent']}")
    print(f"Emails Failed: {results['emails_failed']}")
    print(f"Total Changes: {results['total_changes']}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Generate and send weekly digest")
    parser.add_argument("--dry-run", action="store_true", help="Preview without sending emails")
    parser.add_argument("--preview", action="store_true", help="Generate HTML preview file")
    parser.add_argument("--email", type=str, help="Send to specific email only")
    args = parser.parse_args()

    generate_digest(
        dry_run=args.dry_run,
        preview=args.preview,
        target_email=args.email
    )


if __name__ == "__main__":
    main()
