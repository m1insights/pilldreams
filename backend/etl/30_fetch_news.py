"""
ETL 30: Fetch News from RSS Feeds + AI Processing

Fetches articles from:
- Nature Drug Discovery RSS
- PubMed epigenetics alerts
- BioSpace Oncology news

AI processes each article to:
- Generate summary
- Extract entities (drugs, targets, companies)
- Categorize and flag impact

Articles land in epi_news_staging for admin review in Supabase.

Usage:
    python -m backend.etl.30_fetch_news
    python -m backend.etl.30_fetch_news --source nature
    python -m backend.etl.30_fetch_news --dry-run
"""

import os
import sys
import json
import argparse
import hashlib
from datetime import datetime, timedelta
from typing import Optional
import feedparser
import requests
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

load_dotenv()

from supabase import create_client, Client
import google.generativeai as genai

# ============================================================================
# Configuration
# ============================================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# RSS Feed URLs
RSS_FEEDS = {
    "nature_drug_discovery": {
        "url": "https://www.nature.com/nrd.rss",
        "name": "Nature Reviews Drug Discovery",
    },
    "nature_cancer": {
        "url": "https://www.nature.com/natcancer.rss",
        "name": "Nature Cancer",
    },
    "pubmed_epigenetics": {
        # PubMed RSS for epigenetics + cancer search
        "url": "https://pubmed.ncbi.nlm.nih.gov/rss/search/1234567890/?limit=20&utm_campaign=pubmed-2&fc=20231101000000",  # Placeholder - needs real saved search
        "name": "PubMed Epigenetics",
        "enabled": False,  # Enable after setting up saved search
    },
    "biospace": {
        "url": "https://www.biospace.com/rss/news",
        "name": "BioSpace News",
    },
}

# Epigenetic keywords for filtering
EPI_KEYWORDS = [
    "epigenetic", "epigenetics", "hdac", "histone deacetylase",
    "ezh2", "bet inhibitor", "bromodomain", "dnmt", "methyltransferase",
    "demethylase", "chromatin", "histone", "acetylation", "methylation",
    "prmt", "dot1l", "lsd1", "kdm", "sirt", "tet2", "idh1", "idh2",
    "vorinostat", "panobinostat", "romidepsin", "belinostat", "tucidinostat",
    "tazemetostat", "enasidenib", "ivosidenib", "olutasidenib",
    "crispr epigenetic", "epigenetic editing", "gene silencing",
]

# ============================================================================
# Supabase Client
# ============================================================================

def get_supabase() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# ============================================================================
# Gemini AI Client
# ============================================================================

def get_gemini_model():
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY must be set")
    genai.configure(api_key=GEMINI_API_KEY)
    return genai.GenerativeModel("gemini-2.0-flash")

# ============================================================================
# RSS Fetching
# ============================================================================

def fetch_rss_feed(source_key: str) -> list[dict]:
    """Fetch and parse an RSS feed."""
    feed_config = RSS_FEEDS.get(source_key)
    if not feed_config:
        print(f"  Unknown source: {source_key}")
        return []

    if not feed_config.get("enabled", True):
        print(f"  Skipping disabled source: {source_key}")
        return []

    url = feed_config["url"]
    print(f"  Fetching {feed_config['name']}...")

    try:
        feed = feedparser.parse(url)

        if feed.bozo:
            print(f"  Warning: Feed parsing issue - {feed.bozo_exception}")

        articles = []
        for entry in feed.entries[:20]:  # Limit to 20 most recent
            # Generate unique ID from URL or title
            source_id = entry.get("id") or entry.get("link") or hashlib.md5(entry.title.encode()).hexdigest()

            # Parse publication date
            pub_date = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                pub_date = datetime(*entry.published_parsed[:6]).date().isoformat()
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                pub_date = datetime(*entry.updated_parsed[:6]).date().isoformat()

            # Get abstract/summary
            abstract = entry.get("summary", "")
            if hasattr(entry, "content") and entry.content:
                abstract = entry.content[0].get("value", abstract)

            # Clean HTML from abstract
            import re
            abstract = re.sub(r'<[^>]+>', '', abstract)
            abstract = abstract[:2000]  # Limit length

            # Get authors
            authors = []
            if hasattr(entry, "authors"):
                authors = [a.get("name", "") for a in entry.authors if a.get("name")]
            elif hasattr(entry, "author"):
                authors = [entry.author]

            articles.append({
                "source": source_key,
                "source_url": entry.get("link", ""),
                "source_id": source_id,
                "title": entry.get("title", "Untitled"),
                "abstract": abstract,
                "pub_date": pub_date,
                "authors": authors,
            })

        print(f"  Found {len(articles)} articles")
        return articles

    except Exception as e:
        print(f"  Error fetching {source_key}: {e}")
        return []

def is_epigenetics_relevant(article: dict) -> bool:
    """Check if article is relevant to epigenetics/oncology."""
    text = f"{article['title']} {article['abstract']}".lower()
    return any(keyword in text for keyword in EPI_KEYWORDS)

# ============================================================================
# AI Processing
# ============================================================================

def process_with_ai(article: dict, model) -> dict:
    """Use Gemini to analyze article and extract entities."""

    prompt = f"""Analyze this scientific article about drug discovery/oncology.

TITLE: {article['title']}

ABSTRACT: {article['abstract'][:1500]}

Respond with a JSON object containing:
{{
    "summary": "2-3 sentence summary focusing on key findings and implications for drug development",
    "category": "one of: epi_drug, epi_editing, epi_io, clinical_trial, acquisition, regulatory, research, other",
    "impact_flag": "one of: bullish (positive for drug development), bearish (negative/failure), neutral (informational)",
    "confidence": 0.0-1.0 confidence in your analysis,
    "drugs": ["list of drug names mentioned"],
    "targets": ["list of protein/gene targets mentioned (e.g., EZH2, HDAC1, BRD4)"],
    "companies": ["list of pharma/biotech companies mentioned"],
    "key_finding": "one sentence on the most important takeaway"
}}

Focus on epigenetic drugs, targets, and mechanisms. Be specific about drug names and targets.
Respond ONLY with the JSON object, no other text."""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()

        # Clean up response - remove markdown code blocks if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()

        result = json.loads(text)
        return {
            "ai_summary": result.get("summary", ""),
            "ai_category": result.get("category", "other"),
            "ai_impact_flag": result.get("impact_flag", "neutral"),
            "ai_confidence": result.get("confidence", 0.5),
            "ai_extracted_entities": {
                "drugs": result.get("drugs", []),
                "targets": result.get("targets", []),
                "companies": result.get("companies", []),
                "key_finding": result.get("key_finding", ""),
            },
        }
    except Exception as e:
        print(f"    AI processing error: {e}")
        return {
            "ai_summary": None,
            "ai_category": "other",
            "ai_impact_flag": "unknown",
            "ai_confidence": 0.0,
            "ai_extracted_entities": {},
        }

# ============================================================================
# Database Operations
# ============================================================================

def article_exists(supabase: Client, source: str, source_id: str) -> bool:
    """Check if article already exists in staging table."""
    try:
        result = supabase.table("epi_news_staging")\
            .select("id")\
            .eq("source", source)\
            .eq("source_id", source_id)\
            .execute()
        return len(result.data) > 0
    except:
        return False

def insert_article(supabase: Client, article: dict) -> bool:
    """Insert article into staging table."""
    try:
        supabase.table("epi_news_staging").insert(article).execute()
        return True
    except Exception as e:
        print(f"    Insert error: {e}")
        return False

# ============================================================================
# Main Pipeline
# ============================================================================

def run_news_fetch(
    sources: Optional[list[str]] = None,
    dry_run: bool = False,
    skip_ai: bool = False,
    filter_relevant: bool = True,
):
    """Main news fetching pipeline."""

    print("\n" + "="*60)
    print("NEWS FETCHER - ETL 30")
    print("="*60)

    # Initialize clients
    if not dry_run:
        supabase = get_supabase()
    else:
        supabase = None

    if not skip_ai:
        model = get_gemini_model()
    else:
        model = None

    # Determine which sources to fetch
    if sources:
        feed_keys = [s for s in sources if s in RSS_FEEDS]
    else:
        feed_keys = [k for k, v in RSS_FEEDS.items() if v.get("enabled", True)]

    print(f"\nSources: {feed_keys}")
    print(f"Dry run: {dry_run}")
    print(f"AI processing: {not skip_ai}")
    print(f"Filter relevant: {filter_relevant}")

    # Stats
    stats = {
        "fetched": 0,
        "relevant": 0,
        "new": 0,
        "inserted": 0,
        "skipped_duplicate": 0,
        "skipped_irrelevant": 0,
    }

    # Process each source
    for source_key in feed_keys:
        print(f"\n--- {source_key} ---")

        articles = fetch_rss_feed(source_key)
        stats["fetched"] += len(articles)

        for article in articles:
            print(f"\n  Processing: {article['title'][:60]}...")

            # Filter for relevance
            if filter_relevant and not is_epigenetics_relevant(article):
                print(f"    Skipping (not epigenetics-related)")
                stats["skipped_irrelevant"] += 1
                continue

            stats["relevant"] += 1

            # Check for duplicates
            if not dry_run and article_exists(supabase, article["source"], article["source_id"]):
                print(f"    Skipping (already exists)")
                stats["skipped_duplicate"] += 1
                continue

            stats["new"] += 1

            # AI processing
            if model:
                print(f"    Running AI analysis...")
                ai_result = process_with_ai(article, model)
                article.update(ai_result)
                print(f"    Category: {ai_result['ai_category']}, Impact: {ai_result['ai_impact_flag']}")

            # Insert into database
            if not dry_run:
                # Prepare record
                record = {
                    "source": article["source"],
                    "source_url": article["source_url"],
                    "source_id": article["source_id"],
                    "title": article["title"],
                    "abstract": article.get("abstract"),
                    "pub_date": article.get("pub_date"),
                    "authors": article.get("authors", []),
                    "ai_summary": article.get("ai_summary"),
                    "ai_category": article.get("ai_category", "other"),
                    "ai_impact_flag": article.get("ai_impact_flag", "unknown"),
                    "ai_extracted_entities": article.get("ai_extracted_entities", {}),
                    "ai_confidence": article.get("ai_confidence", 0.0),
                    "status": "pending",
                }

                if insert_article(supabase, record):
                    print(f"    Inserted into staging")
                    stats["inserted"] += 1
            else:
                print(f"    [DRY RUN] Would insert")
                stats["inserted"] += 1

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"  Fetched:           {stats['fetched']}")
    print(f"  Relevant:          {stats['relevant']}")
    print(f"  Skipped irrelevant: {stats['skipped_irrelevant']}")
    print(f"  Skipped duplicate:  {stats['skipped_duplicate']}")
    print(f"  New articles:       {stats['new']}")
    print(f"  Inserted:           {stats['inserted']}")
    print("\nNext step: Review pending articles in Supabase Table Editor")
    print("  Table: epi_news_staging")
    print("  Filter: status = 'pending'")
    print("  Action: Change status to 'approved' or 'rejected'")

    return stats


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch news from RSS feeds")
    parser.add_argument("--source", type=str, help="Specific source to fetch (e.g., 'nature_drug_discovery')")
    parser.add_argument("--dry-run", action="store_true", help="Don't insert into database")
    parser.add_argument("--skip-ai", action="store_true", help="Skip AI processing")
    parser.add_argument("--no-filter", action="store_true", help="Don't filter for epigenetics relevance")

    args = parser.parse_args()

    sources = [args.source] if args.source else None

    run_news_fetch(
        sources=sources,
        dry_run=args.dry_run,
        skip_ai=args.skip_ai,
        filter_relevant=not args.no_filter,
    )
