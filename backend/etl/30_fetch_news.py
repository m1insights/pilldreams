"""
ETL 30: Fetch News from RSS Feeds + AI Processing

Fetches articles from:
- Nature Drug Discovery RSS
- Nature Cancer RSS
- PubMed epigenetics saved search RSS
- BioSpace Oncology news

AI processes each article to:
- Generate summary
- Extract entities (drugs, targets, companies)
- Categorize and flag impact

Articles land in epi_news_staging for admin review in Supabase.

v2.0 Improvements:
- Links extracted entities to database IDs (targets, drugs, companies)
- Hardened JSON parsing with retry logic
- Dynamic keyword list from database symbols
- Structured logging for observability
- Real PubMed RSS support

Usage:
    python -m backend.etl.30_fetch_news
    python -m backend.etl.30_fetch_news --source nature_drug_discovery
    python -m backend.etl.30_fetch_news --dry-run
    python -m backend.etl.30_fetch_news --skip-ai
"""

import os
import sys
import json
import argparse
import hashlib
import re
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
        # To create your own: Go to PubMed, run search, click "Create RSS", use that URL
        "url": "https://pubmed.ncbi.nlm.nih.gov/rss/search/1JQm7l2rTxPxVb-vQmWJJ2BNw8FCGAT8G3OPFypvnlnNQPWaXi/?limit=20&utm_campaign=pubmed-2&fc=20231101000000",
        "name": "PubMed Epigenetics",
        "enabled": True,  # Enabled with real saved search
    },
    "biospace": {
        "url": "https://www.biospace.com/rss/news",
        "name": "BioSpace News",
    },
}

# Base epigenetic keywords - will be enriched with database symbols
BASE_EPI_KEYWORDS = [
    # Core terms
    "epigenetic", "epigenetics", "epigenome",
    # Mechanisms
    "hdac", "histone deacetylase", "bromodomain", "bet inhibitor",
    "dnmt", "methyltransferase", "demethylase", "chromatin",
    "histone", "acetylation", "methylation",
    # Specific targets
    "ezh2", "prmt", "prmt5", "dot1l", "lsd1", "kdm", "sirt", "tet2",
    "idh1", "idh2", "menin", "mll", "nsd2", "m6a", "ythdf",
    # Technologies
    "crispr epigenetic", "epigenetic editing", "gene silencing",
    "epigenome editing", "dcas9",
    # Drugs
    "vorinostat", "panobinostat", "romidepsin", "belinostat", "tucidinostat",
    "tazemetostat", "enasidenib", "ivosidenib", "olutasidenib", "vorasidenib",
    "azacitidine", "decitabine", "entinostat",
]

# ============================================================================
# Database Lookups for Entity Linking
# ============================================================================

# Cache for database entities
_db_targets_cache = None
_db_drugs_cache = None
_db_companies_cache = None

def load_db_targets(supabase: Client) -> dict:
    """Load target symbols from database for entity linking."""
    global _db_targets_cache
    if _db_targets_cache is not None:
        return _db_targets_cache

    try:
        result = supabase.table("epi_targets").select("id, symbol, name").execute()
        _db_targets_cache = {
            t["symbol"].upper(): t["id"] for t in result.data
        }
        # Also add full names as keys
        for t in result.data:
            if t.get("name"):
                _db_targets_cache[t["name"].upper()] = t["id"]
        return _db_targets_cache
    except Exception as e:
        print(f"  Warning: Could not load targets: {e}")
        return {}

def load_db_drugs(supabase: Client) -> dict:
    """Load drug names from database for entity linking."""
    global _db_drugs_cache
    if _db_drugs_cache is not None:
        return _db_drugs_cache

    try:
        result = supabase.table("epi_drugs").select("id, name").execute()
        _db_drugs_cache = {
            d["name"].upper(): d["id"] for d in result.data
        }
        return _db_drugs_cache
    except Exception as e:
        print(f"  Warning: Could not load drugs: {e}")
        return {}

def load_db_companies(supabase: Client) -> dict:
    """Load company names from database for entity linking."""
    global _db_companies_cache
    if _db_companies_cache is not None:
        return _db_companies_cache

    try:
        result = supabase.table("epi_companies").select("id, name, ticker").execute()
        _db_companies_cache = {}
        for c in result.data:
            _db_companies_cache[c["name"].upper()] = c["id"]
            if c.get("ticker"):
                _db_companies_cache[c["ticker"].upper()] = c["id"]
        return _db_companies_cache
    except Exception as e:
        print(f"  Warning: Could not load companies: {e}")
        return {}

def get_enriched_keywords(supabase: Client) -> list:
    """Build keyword list enriched with database symbols."""
    keywords = list(BASE_EPI_KEYWORDS)

    # Add target symbols
    targets = load_db_targets(supabase)
    for symbol in targets.keys():
        if len(symbol) >= 3:  # Skip very short symbols to avoid false positives
            keywords.append(symbol.lower())

    # Add drug names
    drugs = load_db_drugs(supabase)
    for name in drugs.keys():
        keywords.append(name.lower())

    return list(set(keywords))

def link_entities_to_db(entities: dict, supabase: Client) -> dict:
    """Link extracted entity names to database IDs."""
    targets = load_db_targets(supabase)
    drugs = load_db_drugs(supabase)
    companies = load_db_companies(supabase)

    linked = {
        "drugs": entities.get("drugs", []),
        "targets": entities.get("targets", []),
        "companies": entities.get("companies", []),
        "key_finding": entities.get("key_finding", ""),
        # New: linked IDs
        "linked_target_ids": [],
        "linked_drug_ids": [],
        "linked_company_ids": [],
    }

    # Link targets
    for target_name in entities.get("targets", []):
        target_upper = target_name.upper()
        if target_upper in targets:
            linked["linked_target_ids"].append(targets[target_upper])

    # Link drugs
    for drug_name in entities.get("drugs", []):
        drug_upper = drug_name.upper()
        if drug_upper in drugs:
            linked["linked_drug_ids"].append(drugs[drug_upper])

    # Link companies
    for company_name in entities.get("companies", []):
        company_upper = company_name.upper()
        if company_upper in companies:
            linked["linked_company_ids"].append(companies[company_upper])

    return linked

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

def is_epigenetics_relevant(article: dict, keywords: list) -> bool:
    """Check if article is relevant to epigenetics/oncology."""
    text = f"{article['title']} {article['abstract']}".lower()
    return any(keyword in text for keyword in keywords)

# ============================================================================
# AI Processing with Hardened JSON Parsing
# ============================================================================

def parse_ai_json(text: str) -> Optional[dict]:
    """Parse JSON from AI response with multiple fallback strategies."""
    # Strategy 1: Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Remove markdown code blocks
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Remove first and last lines (```json and ```)
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

    # Strategy 3: Find JSON object in text
    match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return None

def process_with_ai(article: dict, model, retry_on_fail: bool = True) -> dict:
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

        result = parse_ai_json(text)

        if result is None:
            if retry_on_fail:
                # Retry with stricter prompt
                print(f"    JSON parse failed, retrying with strict prompt...")
                retry_prompt = f"""Return ONLY valid JSON for this article. No markdown, no commentary.

TITLE: {article['title']}

{{
    "summary": "brief summary",
    "category": "epi_drug or clinical_trial or research or other",
    "impact_flag": "bullish or bearish or neutral",
    "confidence": 0.8,
    "drugs": [],
    "targets": [],
    "companies": [],
    "key_finding": "main finding"
}}"""
                retry_response = model.generate_content(retry_prompt)
                result = parse_ai_json(retry_response.text.strip())

            if result is None:
                print(f"    AI JSON parse failed after retry. Raw text: {text[:200]}...")
                return _empty_ai_result()

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
        return _empty_ai_result()

def _empty_ai_result() -> dict:
    """Return empty AI result structure."""
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

def log_etl_run(supabase: Client, stats: dict, source_keys: list) -> None:
    """Log ETL run to etl_refresh_log table for observability."""
    try:
        record = {
            "entity_type": "news",
            "api_source": ",".join(source_keys),
            "records_found": stats["fetched"],
            "records_inserted": stats["inserted"],
            "records_skipped": stats["skipped_duplicate"] + stats["skipped_irrelevant"],
            "status": "success" if stats["inserted"] > 0 or stats["fetched"] == 0 else "no_new_records",
            "details": json.dumps(stats),
        }
        supabase.table("etl_refresh_log").insert(record).execute()
    except Exception as e:
        # Don't fail the pipeline if logging fails
        print(f"  Warning: Could not log ETL run: {e}")

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
    print("NEWS FETCHER - ETL 30 (v2.0)")
    print("="*60)

    # Initialize clients
    if not dry_run:
        supabase = get_supabase()
        # Load enriched keywords from database
        keywords = get_enriched_keywords(supabase)
        print(f"Loaded {len(keywords)} keywords (incl. {len(load_db_targets(supabase))} targets, {len(load_db_drugs(supabase))} drugs)")
    else:
        supabase = None
        keywords = BASE_EPI_KEYWORDS

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
        "ai_parse_failures": 0,
        "entities_linked": 0,
    }

    # Process each source
    for source_key in feed_keys:
        print(f"\n--- {source_key} ---")

        articles = fetch_rss_feed(source_key)
        stats["fetched"] += len(articles)

        for article in articles:
            print(f"\n  Processing: {article['title'][:60]}...")

            # Filter for relevance
            if filter_relevant and not is_epigenetics_relevant(article, keywords):
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

                if ai_result.get("ai_confidence", 0) == 0:
                    stats["ai_parse_failures"] += 1

                print(f"    Category: {ai_result['ai_category']}, Impact: {ai_result['ai_impact_flag']}")

                # Link entities to database IDs
                if not dry_run and ai_result.get("ai_extracted_entities"):
                    linked = link_entities_to_db(ai_result["ai_extracted_entities"], supabase)
                    article["ai_extracted_entities"] = linked
                    total_linked = len(linked.get("linked_target_ids", [])) + len(linked.get("linked_drug_ids", [])) + len(linked.get("linked_company_ids", []))
                    if total_linked > 0:
                        stats["entities_linked"] += total_linked
                        print(f"    Linked {total_linked} entities to database")

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

    # Log ETL run
    if not dry_run:
        log_etl_run(supabase, stats, feed_keys)

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"  Fetched:            {stats['fetched']}")
    print(f"  Relevant:           {stats['relevant']}")
    print(f"  Skipped irrelevant: {stats['skipped_irrelevant']}")
    print(f"  Skipped duplicate:  {stats['skipped_duplicate']}")
    print(f"  New articles:       {stats['new']}")
    print(f"  Inserted:           {stats['inserted']}")
    print(f"  AI parse failures:  {stats['ai_parse_failures']}")
    print(f"  Entities linked:    {stats['entities_linked']}")
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
