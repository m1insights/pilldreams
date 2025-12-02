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
    """Generate HTML email content for the digest."""

    # Group changes by significance
    critical = [c for c in changes if c["significance"] == "critical"]
    high = [c for c in changes if c["significance"] == "high"]
    medium = [c for c in changes if c["significance"] == "medium"]
    low = [c for c in changes if c["significance"] == "low"]

    # Format date range
    date_range = f"{period_start.strftime('%b %d')} - {period_end.strftime('%b %d, %Y')}"

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pilldreams Weekly Digest</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #1a1a2e;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .container {{
            background: #ffffff;
            border-radius: 12px;
            padding: 32px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        .header {{
            text-align: center;
            margin-bottom: 32px;
            padding-bottom: 24px;
            border-bottom: 1px solid #e9ecef;
        }}
        .logo {{
            font-size: 28px;
            font-weight: 700;
            color: #0a0a0a;
            margin-bottom: 8px;
        }}
        .logo span {{
            color: #3b82f6;
        }}
        .subtitle {{
            color: #6c757d;
            font-size: 14px;
        }}
        .stats {{
            display: flex;
            justify-content: center;
            gap: 24px;
            margin: 24px 0;
            padding: 16px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        .stat {{
            text-align: center;
        }}
        .stat-number {{
            font-size: 24px;
            font-weight: 700;
            color: #0a0a0a;
        }}
        .stat-label {{
            font-size: 12px;
            color: #6c757d;
            text-transform: uppercase;
        }}
        .section {{
            margin: 24px 0;
        }}
        .section-title {{
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }}
        .badge-critical {{
            background: #fee2e2;
            color: #dc2626;
        }}
        .badge-high {{
            background: #fef3c7;
            color: #d97706;
        }}
        .badge-medium {{
            background: #dbeafe;
            color: #2563eb;
        }}
        .badge-low {{
            background: #f3f4f6;
            color: #6b7280;
        }}
        .change-item {{
            padding: 12px 16px;
            border-left: 3px solid #e9ecef;
            margin: 8px 0;
            background: #fafafa;
            border-radius: 0 8px 8px 0;
        }}
        .change-item.critical {{
            border-left-color: #dc2626;
            background: #fef2f2;
        }}
        .change-item.high {{
            border-left-color: #d97706;
            background: #fffbeb;
        }}
        .change-item.medium {{
            border-left-color: #2563eb;
            background: #eff6ff;
        }}
        .change-title {{
            font-weight: 600;
            color: #0a0a0a;
            margin-bottom: 4px;
        }}
        .change-detail {{
            font-size: 14px;
            color: #4b5563;
        }}
        .change-meta {{
            font-size: 12px;
            color: #9ca3af;
            margin-top: 4px;
        }}
        .change-link {{
            color: #3b82f6;
            text-decoration: none;
        }}
        .change-link:hover {{
            text-decoration: underline;
        }}
        .footer {{
            margin-top: 32px;
            padding-top: 24px;
            border-top: 1px solid #e9ecef;
            text-align: center;
            font-size: 12px;
            color: #9ca3af;
        }}
        .cta-button {{
            display: inline-block;
            padding: 12px 24px;
            background: #0a0a0a;
            color: #ffffff !important;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            margin: 16px 0;
        }}
        .empty-state {{
            text-align: center;
            padding: 32px;
            color: #6c757d;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">pill<span>dreams</span></div>
            <div class="subtitle">Epigenetic Oncology Intelligence</div>
        </div>

        <p>Hi {user_name or 'there'},</p>
        <p>Here's your weekly digest of changes in the epigenetic oncology landscape for <strong>{date_range}</strong>.</p>

        <div class="stats">
            <div class="stat">
                <div class="stat-number">{len(changes)}</div>
                <div class="stat-label">Total Changes</div>
            </div>
            <div class="stat">
                <div class="stat-number">{len(critical)}</div>
                <div class="stat-label">Critical</div>
            </div>
            <div class="stat">
                <div class="stat-number">{len(high)}</div>
                <div class="stat-label">High Priority</div>
            </div>
        </div>
"""

    # Critical changes
    if critical:
        html += """
        <div class="section">
            <div class="section-title">
                <span>🚨</span>
                <span>Critical Updates</span>
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
            <div class="section-title">
                <span>⚠️</span>
                <span>High Priority</span>
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
            <div class="section-title">
                <span>📢</span>
                <span>Notable Updates</span>
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
            <div class="section-title">
                <span>📝</span>
                <span>Other Updates</span>
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
        <div style="text-align: center;">
            <a href="https://pilldreams.io/calendar" class="cta-button">View Full Calendar →</a>
        </div>

        <div class="footer">
            <p>You're receiving this because you subscribed to Pilldreams digests.</p>
            <p>
                <a href="https://pilldreams.io/settings/notifications" class="change-link">Manage preferences</a> ·
                <a href="https://pilldreams.io/unsubscribe" class="change-link">Unsubscribe</a>
            </p>
            <p style="margin-top: 16px;">© 2024 Pilldreams · Epigenetic Oncology Intelligence</p>
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
        detail = f"New {change['entity_type']} added to the database"

    source_url = change.get("source_url", "")
    source_link = f'<a href="{source_url}" class="change-link">View source →</a>' if source_url else ""

    detected = change.get("detected_at", "")
    if detected:
        try:
            dt = datetime.fromisoformat(detected.replace("Z", "+00:00"))
            detected = dt.strftime("%b %d, %I:%M %p")
        except:
            pass

    return f"""
            <div class="change-item {significance}">
                <div class="change-title">{title}</div>
                <div class="change-detail">{detail}</div>
                <div class="change-meta">{detected} · {change.get('source', 'etl')} {source_link}</div>
            </div>
"""


def generate_plain_text(changes: List[Dict], user_name: str, period_start: date, period_end: date) -> str:
    """Generate plain text version of the digest."""
    date_range = f"{period_start.strftime('%b %d')} - {period_end.strftime('%b %d, %Y')}"

    text = f"""
PILLDREAMS WEEKLY DIGEST
Epigenetic Oncology Intelligence
{date_range}

Hi {user_name or 'there'},

Here's your weekly summary of changes:

SUMMARY
- Total Changes: {len(changes)}
- Critical: {len([c for c in changes if c['significance'] == 'critical'])}
- High Priority: {len([c for c in changes if c['significance'] == 'high'])}
- Medium: {len([c for c in changes if c['significance'] == 'medium'])}
- Low: {len([c for c in changes if c['significance'] == 'low'])}

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

View the full calendar: https://pilldreams.io/calendar

---
Manage preferences: https://pilldreams.io/settings/notifications
Unsubscribe: https://pilldreams.io/unsubscribe

© 2024 Pilldreams · Epigenetic Oncology Intelligence
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
                "from": "Pilldreams <digest@pilldreams.io>",
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
        {"id": "3", "entity_type": "trial", "entity_name": "NCT05432101", "change_type": "status_change",
         "field_changed": "status", "old_value": "RECRUITING", "new_value": "COMPLETED",
         "change_summary": "NCT05432101: Trial completed", "significance": "high",
         "source": "ctgov", "source_url": "https://clinicaltrials.gov/study/NCT05432101", "detected_at": datetime.now().isoformat()},
        {"id": "4", "entity_type": "trial", "entity_name": "NCT06123456", "change_type": "date_change",
         "field_changed": "primary_completion_date", "old_value": "2025-03-01", "new_value": "2025-06-01",
         "change_summary": "NCT06123456: Primary completion delayed to June 2025", "significance": "medium",
         "source": "ctgov", "source_url": "https://clinicaltrials.gov/study/NCT06123456", "detected_at": datetime.now().isoformat()},
        {"id": "5", "entity_type": "drug", "entity_name": "VORINOSTAT", "change_type": "score_change",
         "field_changed": "total_score", "old_value": "62", "new_value": "68",
         "change_summary": "VORINOSTAT: Total score increased by 6 points", "significance": "low",
         "source": "etl", "source_url": None, "detected_at": datetime.now().isoformat()},
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

    # Use sample data in preview mode if tables don't exist
    use_sample_data = preview and not tables_exist

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
