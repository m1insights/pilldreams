#!/usr/bin/env python3
"""
33_fetch_pdufa.py - PDUFA Date Tracker ETL

Fetches and maintains PDUFA dates for epigenetic oncology drugs.
Sources:
  1. Seed CSV (curated list of known PDUFA dates)
  2. FDA RSS feeds (automated monitoring for approvals)
  3. Press releases (manual updates)

Usage:
    python -m backend.etl.33_fetch_pdufa --seed          # Load seed data
    python -m backend.etl.33_fetch_pdufa --check-fda     # Check FDA RSS for updates
    python -m backend.etl.33_fetch_pdufa --update-status # Update status based on PDUFA dates
    python -m backend.etl.33_fetch_pdufa --all           # Run all steps
"""

import os
import csv
import argparse
import feedparser
import requests
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Supabase setup
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY environment variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# FDA RSS feed URLs
FDA_DRUG_APPROVALS_RSS = "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/drug-approvals-and-databases/rss.xml"
FDA_NEW_DRUGS_RSS = "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/new-drugs-fda/rss.xml"

# Epigenetic drug keywords for RSS filtering
EPI_DRUG_KEYWORDS = [
    # Drug names from our database
    "tazemetostat", "vorinostat", "romidepsin", "belinostat", "panobinostat",
    "entinostat", "tucidinostat", "vorasidenib", "olutasidenib", "ivosidenib",
    "enasidenib", "revumenib", "ziftomenib", "pelabresib", "bomedemstat",
    "iadademstat", "cpi-0209", "gsk126",
    # Target class keywords
    "hdac inhibitor", "ezh2 inhibitor", "bet inhibitor", "lsd1 inhibitor",
    "dot1l inhibitor", "prmt5 inhibitor", "menin inhibitor", "idh inhibitor",
    "dnmt inhibitor", "histone deacetylase", "bromodomain",
    # Mechanism keywords
    "epigenetic", "chromatin", "histone methyltransferase"
]


def get_seed_file_path() -> str:
    """Get the path to the seed CSV file."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, "seed_pdufa_dates.csv")


def check_pdufa_table_exists() -> bool:
    """Check if ci_pdufa_dates table exists."""
    try:
        supabase.table("ci_pdufa_dates").select("id").limit(1).execute()
        return True
    except Exception as e:
        if "PGRST205" in str(e) or "could not find" in str(e).lower():
            return False
        raise


def load_seed_data(dry_run: bool = False) -> Tuple[int, int, int]:
    """
    Load PDUFA dates from seed CSV file.

    Returns:
        Tuple of (inserted, updated, skipped) counts
    """
    seed_file = get_seed_file_path()

    if not os.path.exists(seed_file):
        print(f"Seed file not found: {seed_file}")
        return 0, 0, 0

    # Check if table exists
    if not check_pdufa_table_exists():
        print("   ⚠️  ci_pdufa_dates table not found!")
        print("   Run migration: cat core/migration_ci_pdufa.sql | pbcopy")
        print("   Then paste in Supabase Dashboard > SQL Editor")
        if dry_run:
            print("\n   Showing seed data preview:")
            with open(seed_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    print(f"   [DRY RUN] Would insert: {row['drug_name']} ({row['company_ticker']}) - PDUFA: {row['pdufa_date']}")
            return 0, 0, 0
        return 0, 0, 0

    inserted = 0
    updated = 0
    skipped = 0

    with open(seed_file, 'r') as f:
        reader = csv.DictReader(f)

        for row in reader:
            drug_name = row['drug_name'].strip()
            indication = row['indication'].strip()
            pdufa_date = row['pdufa_date'].strip()

            # Check if record exists
            existing = supabase.table("ci_pdufa_dates").select("id, status").eq(
                "drug_name", drug_name
            ).eq(
                "indication", indication
            ).eq(
                "pdufa_date", pdufa_date
            ).execute()

            record = {
                "drug_name": drug_name,
                "company_name": row['company_name'].strip(),
                "company_ticker": row['company_ticker'].strip() if row['company_ticker'] else None,
                "application_type": row['application_type'].strip(),
                "indication": indication,
                "pdufa_date": pdufa_date,
                "pdufa_date_type": row['pdufa_date_type'].strip() if row['pdufa_date_type'] else 'standard',
                "status": row['status'].strip() if row['status'] else 'pending',
                "outcome_date": row['outcome_date'].strip() if row['outcome_date'] else None,
                "outcome_notes": row['outcome_notes'].strip() if row['outcome_notes'] else None,
                "source": row['source'].strip() if row['source'] else 'manual',
                "source_url": row['source_url'].strip() if row['source_url'] else None,
            }

            if dry_run:
                if existing.data:
                    print(f"  [DRY RUN] Would update: {drug_name} ({indication})")
                    updated += 1
                else:
                    print(f"  [DRY RUN] Would insert: {drug_name} ({indication}) - PDUFA: {pdufa_date}")
                    inserted += 1
                continue

            if existing.data:
                # Update existing record
                supabase.table("ci_pdufa_dates").update(record).eq(
                    "id", existing.data[0]['id']
                ).execute()
                print(f"  Updated: {drug_name} ({indication})")
                updated += 1
            else:
                # Insert new record
                supabase.table("ci_pdufa_dates").insert(record).execute()
                print(f"  Inserted: {drug_name} ({indication}) - PDUFA: {pdufa_date}")
                inserted += 1

    return inserted, updated, skipped


def check_fda_rss(dry_run: bool = False) -> List[Dict]:
    """
    Check FDA RSS feeds for new drug approvals related to epigenetics.

    Returns:
        List of matching RSS entries
    """
    matching_entries = []

    for feed_url in [FDA_DRUG_APPROVALS_RSS, FDA_NEW_DRUGS_RSS]:
        try:
            print(f"  Fetching: {feed_url}")
            feed = feedparser.parse(feed_url)

            if feed.bozo:
                print(f"    Warning: Feed parsing error - {feed.bozo_exception}")
                continue

            for entry in feed.entries:
                title = entry.get('title', '').lower()
                summary = entry.get('summary', '').lower()
                content = title + " " + summary

                # Check if entry matches any epigenetic drug keywords
                for keyword in EPI_DRUG_KEYWORDS:
                    if keyword.lower() in content:
                        matching_entries.append({
                            "title": entry.get('title'),
                            "link": entry.get('link'),
                            "published": entry.get('published'),
                            "summary": entry.get('summary', '')[:500],
                            "matched_keyword": keyword,
                            "feed_source": feed_url
                        })
                        print(f"    Found match: {entry.get('title')[:80]}...")
                        break

        except Exception as e:
            print(f"    Error fetching feed: {e}")
            continue

    return matching_entries


def update_pdufa_from_rss(entries: List[Dict], dry_run: bool = False) -> int:
    """
    Update PDUFA records based on FDA RSS entries.

    Returns:
        Number of records updated
    """
    updated = 0

    for entry in entries:
        title = entry['title'].lower()

        # Try to find matching pending PDUFA record
        pending = supabase.table("ci_pdufa_dates").select("*").eq(
            "status", "pending"
        ).execute()

        for record in pending.data:
            drug_name = record['drug_name'].lower()

            if drug_name in title and "approv" in title:
                if dry_run:
                    print(f"  [DRY RUN] Would mark as approved: {record['drug_name']}")
                    updated += 1
                    continue

                # Update status to approved
                update_data = {
                    "status": "approved",
                    "outcome_date": datetime.now().date().isoformat(),
                    "outcome_notes": f"FDA approved - {entry['title'][:200]}",
                    "source_url": entry.get('link')
                }

                supabase.table("ci_pdufa_dates").update(update_data).eq(
                    "id", record['id']
                ).execute()

                # Log history
                supabase.table("ci_pdufa_history").insert({
                    "pdufa_id": record['id'],
                    "change_type": "status_updated",
                    "old_value": "pending",
                    "new_value": "approved",
                    "source": "fda_rss",
                    "source_url": entry.get('link'),
                    "notes": entry['title']
                }).execute()

                print(f"  Marked as approved: {record['drug_name']}")
                updated += 1
                break

    return updated


def update_status_by_date(dry_run: bool = False) -> int:
    """
    Update status for PDUFA dates that have passed without recorded outcome.

    Returns:
        Number of records flagged for review
    """
    flagged = 0
    today = date.today()

    # Find pending records with PDUFA date in the past
    pending = supabase.table("ci_pdufa_dates").select("*").eq(
        "status", "pending"
    ).lt(
        "pdufa_date", today.isoformat()
    ).execute()

    for record in pending.data:
        pdufa_date = datetime.strptime(record['pdufa_date'], '%Y-%m-%d').date()
        days_overdue = (today - pdufa_date).days

        if days_overdue > 7:  # Give 7 day buffer for news to reach RSS
            if dry_run:
                print(f"  [DRY RUN] Would flag for review: {record['drug_name']} (PDUFA: {record['pdufa_date']}, {days_overdue} days ago)")
                flagged += 1
                continue

            # Flag as needing manual review
            print(f"  Needs review: {record['drug_name']} - PDUFA was {record['pdufa_date']} ({days_overdue} days ago)")
            flagged += 1

    return flagged


def get_upcoming_pdufa_dates(days: int = 90) -> List[Dict]:
    """
    Get PDUFA dates in the next N days.

    Returns:
        List of upcoming PDUFA records
    """
    today = date.today()
    end_date = today + timedelta(days=days)

    result = supabase.table("ci_pdufa_dates").select("*").eq(
        "status", "pending"
    ).gte(
        "pdufa_date", today.isoformat()
    ).lte(
        "pdufa_date", end_date.isoformat()
    ).order(
        "pdufa_date"
    ).execute()

    return result.data


def print_pdufa_calendar(days: int = 180):
    """Print a formatted PDUFA calendar."""
    upcoming = get_upcoming_pdufa_dates(days)

    print(f"\n{'='*60}")
    print(f"PDUFA Calendar - Next {days} Days")
    print(f"{'='*60}")

    if not upcoming:
        print("No pending PDUFA dates in this period.")
        return

    for record in upcoming:
        pdufa_date = record['pdufa_date']
        days_until = (datetime.strptime(pdufa_date, '%Y-%m-%d').date() - date.today()).days

        urgency = ""
        if days_until <= 7:
            urgency = " [IMMINENT]"
        elif days_until <= 30:
            urgency = " [SOON]"

        print(f"\n{record['drug_name']} ({record['company_ticker'] or 'N/A'}){urgency}")
        print(f"  PDUFA Date: {pdufa_date} ({days_until} days)")
        print(f"  Indication: {record['indication']}")
        print(f"  Type: {record['application_type']} ({record['pdufa_date_type']})")
        print(f"  Company: {record['company_name']}")

    print(f"\n{'='*60}")


def link_to_epi_drugs(dry_run: bool = False) -> int:
    """
    Link PDUFA records to existing epi_drugs table entries.

    Returns:
        Number of records linked
    """
    linked = 0

    # Get PDUFA records without drug_id
    pdufa_records = supabase.table("ci_pdufa_dates").select("id, drug_name").is_(
        "drug_id", "null"
    ).execute()

    # Get all epi_drugs for matching
    drugs = supabase.table("epi_drugs").select("id, name").execute()
    drug_map = {d['name'].lower(): d['id'] for d in drugs.data}

    for record in pdufa_records.data:
        drug_name_lower = record['drug_name'].lower()

        if drug_name_lower in drug_map:
            drug_id = drug_map[drug_name_lower]

            if dry_run:
                print(f"  [DRY RUN] Would link: {record['drug_name']} -> {drug_id}")
                linked += 1
                continue

            supabase.table("ci_pdufa_dates").update({
                "drug_id": drug_id
            }).eq("id", record['id']).execute()

            print(f"  Linked: {record['drug_name']} -> {drug_id}")
            linked += 1

    return linked


def main():
    parser = argparse.ArgumentParser(description="PDUFA Date Tracker ETL")
    parser.add_argument("--seed", action="store_true", help="Load seed data from CSV")
    parser.add_argument("--check-fda", action="store_true", help="Check FDA RSS feeds")
    parser.add_argument("--update-status", action="store_true", help="Update status based on dates")
    parser.add_argument("--link-drugs", action="store_true", help="Link to epi_drugs table")
    parser.add_argument("--calendar", action="store_true", help="Print PDUFA calendar")
    parser.add_argument("--all", action="store_true", help="Run all steps")
    parser.add_argument("--dry-run", action="store_true", help="Preview without making changes")
    parser.add_argument("--days", type=int, default=180, help="Days to show in calendar (default: 180)")
    args = parser.parse_args()

    # If no action specified, show help
    if not any([args.seed, args.check_fda, args.update_status, args.link_drugs, args.calendar, args.all]):
        parser.print_help()
        return

    dry_run_label = " [DRY RUN]" if args.dry_run else ""

    if args.seed or args.all:
        print(f"\n{'='*60}")
        print(f"Step 1: Loading Seed Data{dry_run_label}")
        print(f"{'='*60}")
        inserted, updated, skipped = load_seed_data(dry_run=args.dry_run)
        print(f"\nSeed data: {inserted} inserted, {updated} updated, {skipped} skipped")

    if args.link_drugs or args.all:
        print(f"\n{'='*60}")
        print(f"Step 2: Linking to epi_drugs{dry_run_label}")
        print(f"{'='*60}")
        linked = link_to_epi_drugs(dry_run=args.dry_run)
        print(f"\nLinked: {linked} records")

    if args.check_fda or args.all:
        print(f"\n{'='*60}")
        print(f"Step 3: Checking FDA RSS Feeds{dry_run_label}")
        print(f"{'='*60}")
        entries = check_fda_rss(dry_run=args.dry_run)
        if entries:
            updated = update_pdufa_from_rss(entries, dry_run=args.dry_run)
            print(f"\nFDA RSS: {len(entries)} matches found, {updated} records updated")
        else:
            print("\nNo matching entries found in FDA RSS feeds")

    if args.update_status or args.all:
        print(f"\n{'='*60}")
        print(f"Step 4: Updating Status by Date{dry_run_label}")
        print(f"{'='*60}")
        flagged = update_status_by_date(dry_run=args.dry_run)
        print(f"\nStatus check: {flagged} records flagged for review")

    if args.calendar or args.all:
        print_pdufa_calendar(args.days)

    print("\nPDUFA ETL complete!")


if __name__ == "__main__":
    main()
