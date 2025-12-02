"""
ETL Script 31: Fetch Patents from USPTO PatentsView API

This script searches for epigenetic oncology patents using multiple strategies:
1. Company search - Patents assigned to known epigenetic companies
2. Target keywords - Patents mentioning epigenetic targets (HDAC, BET, EZH2, etc.)
3. Technology keywords - Patents about epigenetic editing/modification
4. Drug keywords - Patents mentioning specific epigenetic drugs

USPTO PatentsView API (New PatentSearch API):
- Base URL: https://search.patentsview.org/api/v1/
- API Key required (free, register at https://patentsview.org/apis/keyrequest)
- US patents only
- Rate limit: 45 requests/minute

Environment Variable:
    PATENTSVIEW_API_KEY - Your PatentsView API key

Usage:
    python -m backend.etl.31_fetch_patents --strategy all
    python -m backend.etl.31_fetch_patents --strategy company --dry-run
    python -m backend.etl.31_fetch_patents --strategy target --limit 50
"""

import argparse
import os
import time
import json
from datetime import datetime, timedelta
from typing import Optional
import requests

from backend.etl.supabase_client import supabase

# USPTO PatentsView API (new ElasticSearch-based API)
PATENTSVIEW_API = "https://search.patentsview.org/api/v1/patent/"

# ============ Search Configurations ============

# Known epigenetic/oncology companies (assignee search)
COMPANY_KEYWORDS = [
    # Pure-play epigenetics
    "Epizyme", "Constellation Pharmaceuticals", "Syndax", "Agios",
    "Chroma Medicine", "Tune Therapeutics", "Arbor Biotechnologies",
    "Epic Bio", "Myeloid Therapeutics", "Foghorn Therapeutics",
    "Accent Therapeutics", "Fulcrum Therapeutics", "Salarius Pharmaceuticals",
    "Prelude Therapeutics", "Imago BioSciences", "ORYZON",
    # Big pharma with epi assets
    "Bristol-Myers Squibb", "GlaxoSmithKline", "GSK", "Pfizer", "Eli Lilly",
    "Roche", "Novartis", "AbbVie", "Merck", "Johnson & Johnson",
    "Bayer", "Takeda", "AstraZeneca", "Sanofi",
    # CRISPR/gene editing
    "Intellia Therapeutics", "CRISPR Therapeutics", "Editas Medicine",
    "Beam Therapeutics", "Prime Medicine", "Verve Therapeutics",
]

# Target keywords (symbol and full names)
TARGET_KEYWORDS = [
    # HDAC family
    "HDAC", "histone deacetylase", "HDAC1", "HDAC2", "HDAC3", "HDAC6",
    # BET family
    "BET inhibitor", "BRD4", "BRD2", "BRD3", "bromodomain",
    # HMTs (methyltransferases)
    "EZH2", "EZH1", "DOT1L", "PRMT5", "PRMT1", "NSD1", "NSD2", "SETD2",
    "PRC2", "polycomb", "SET domain", "histone methyltransferase",
    # KDMs (demethylases)
    "LSD1", "KDM1A", "KDM5", "KDM4", "KDM6", "lysine demethylase",
    "Jumonji", "JmjC domain",
    # DNMTs
    "DNMT", "DNMT1", "DNMT3A", "DNMT3B", "DNA methyltransferase",
    # Other epigenetic targets
    "IDH1", "IDH2", "isocitrate dehydrogenase",
    "TET", "TET1", "TET2", "ten-eleven translocation",
    "Menin", "MLL", "MLL1", "KMT2A", "Menin-MLL",
    "SIRT", "sirtuin", "SIRT1", "SIRT2", "SIRT6",
    "CBP", "p300", "CREBBP", "EP300", "HAT inhibitor", "histone acetyltransferase",
]

# Technology keywords
TECHNOLOGY_KEYWORDS = [
    # Core terms (broad catch-all)
    "epigenetic", "epigenetics", "epigenome",
    # Specific technologies
    "epigenetic editing", "epigenome editing", "epigenetic therapy",
    "chromatin modifier", "chromatin remodeling", "chromatin modifying",
    "gene silencing", "transcriptional repression", "transcriptional silencing",
    "DNA methylation inhibitor", "histone modification",
    "CRISPR epigenetic", "dCas9", "dead Cas9",
    "KRAB domain", "KRAB-dCas9", "CRISPRi", "CRISPR interference",
    "epigenetic clock", "biological age", "methylation clock",
    "histone acetylation", "histone methylation",
]

# Drug names (approved and clinical-stage)
DRUG_KEYWORDS = [
    # FDA-approved HDAC inhibitors
    "vorinostat", "romidepsin", "belinostat", "panobinostat", "tucidinostat",
    # FDA-approved IDH inhibitors
    "enasidenib", "ivosidenib", "vorasidenib",
    # FDA-approved EZH2 inhibitor
    "tazemetostat",
    # FDA-approved DNMT inhibitors
    "azacitidine", "decitabine",
    # Clinical-stage drugs
    "entinostat", "pracinostat", "mocetinostat", "abexinostat",
    "tazverik", "tibsovo", "idhifa",  # Brand names
    "pinometostat", "GSK126", "EPZ-6438", "CPI-1205",
    "INCB059872", "ORY-1001", "IMG-7289",
]

# Categories for classifying patents
PATENT_CATEGORIES = {
    "epi_editor": ["epigenetic editing", "epigenome editing", "dCas9", "CRISPR epigenetic", "CRISPRi", "KRAB domain"],
    "epi_therapy": ["HDAC inhibitor", "BET inhibitor", "EZH2 inhibitor", "DNMT inhibitor", "LSD1 inhibitor", "DOT1L inhibitor", "histone deacetylase inhibitor"],
    "epi_diagnostic": ["epigenetic biomarker", "methylation biomarker", "epigenetic clock", "biological age"],
    "epi_io": ["checkpoint inhibitor", "immunotherapy", "PD-1", "PD-L1", "CTLA-4", "immune checkpoint"],
    "epi_tool": ["chromatin", "histone modification", "DNA methylation", "gene silencing"],
}


def get_api_key() -> str:
    """Get PatentsView API key from environment."""
    api_key = os.getenv("PATENTSVIEW_API_KEY")
    if not api_key:
        raise ValueError(
            "PATENTSVIEW_API_KEY not set. "
            "Register for free at: https://patentsview.org/apis/keyrequest"
        )
    return api_key


def classify_patent(title: str, abstract: str) -> str:
    """Classify patent into a category based on title/abstract keywords."""
    text = f"{title} {abstract}".lower()

    for category, keywords in PATENT_CATEGORIES.items():
        for keyword in keywords:
            if keyword.lower() in text:
                return category

    return "epi_tool"  # Default category


def extract_target_symbols(title: str, abstract: str) -> list:
    """Extract epigenetic target symbols mentioned in patent."""
    text = f"{title} {abstract}".upper()

    # Target symbols to look for
    targets = [
        "HDAC1", "HDAC2", "HDAC3", "HDAC6", "HDAC8",
        "BRD2", "BRD3", "BRD4", "BRDT",
        "EZH1", "EZH2",
        "DOT1L", "PRMT5", "PRMT1",
        "LSD1", "KDM1A", "KDM5A", "KDM5B", "KDM4A", "KDM6A", "KDM6B",
        "DNMT1", "DNMT3A", "DNMT3B",
        "TET1", "TET2", "TET3",
        "IDH1", "IDH2",
        "NSD1", "NSD2", "SETD2",
        "SIRT1", "SIRT2", "SIRT6",
        "CBP", "EP300", "CREBBP",
        "PCSK9",  # Not classical epi but related
    ]

    found = []
    for target in targets:
        if target in text:
            found.append(target)

    return list(set(found))


def build_query_payload(keywords: list, field: str = "patent_abstract", size: int = 100, page: int = 1) -> dict:
    """Build PatentsView PatentSearch API query payload.

    Args:
        keywords: List of keywords to search
        field: Field to search in ('patent_abstract', 'patent_title', 'assignees.assignee_organization')
        size: Results per page (max 1000)
        page: Page number (1-indexed)

    Returns:
        JSON payload for POST request
    """
    # For _text_any, join keywords with space - it will match ANY of them
    # Note: The new API uses different text search operators
    # _text_any: matches if ANY keyword is found
    # _text_all: matches if ALL keywords are found
    # _text_phrase: matches exact phrase

    # Date filter - last 5 years
    five_years_ago = (datetime.now() - timedelta(days=5*365)).strftime("%Y-%m-%d")

    # Build the query with OR logic for multiple keywords
    # Each keyword gets its own _text_any clause
    or_conditions = []
    for kw in keywords:
        or_conditions.append({
            "_text_any": {field: kw}
        })

    # Combine with _or and add date filter
    query = {
        "_and": [
            {"_or": or_conditions},
            {"_gte": {"patent_date": five_years_ago}}
        ]
    }

    return {
        "q": query,
        "f": [
            "patent_id",
            "patent_title",
            "patent_abstract",
            "patent_date",
            "assignees.assignee_organization",
            "inventors.inventor_first_name",
            "inventors.inventor_last_name",
        ],
        "s": [{"patent_date": "desc"}],
        "o": {
            "size": size,
            "from": (page - 1) * size  # offset = (page-1) * size
        }
    }


def fetch_patents(api_key: str, keywords: list, field: str, per_page: int = 100, max_pages: int = 5) -> list:
    """Fetch patents from PatentsView PatentSearch API.

    Args:
        api_key: PatentsView API key
        keywords: List of keywords to search
        field: Field to search in
        per_page: Results per page (max 1000)
        max_pages: Maximum pages to fetch

    Returns:
        List of patent dicts
    """
    all_patents = []
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json"
    }

    for page in range(1, max_pages + 1):
        payload = build_query_payload(keywords, field, size=per_page, page=page)

        try:
            response = requests.post(
                PATENTSVIEW_API,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            patents = data.get("patents", [])
            if not patents:
                break

            all_patents.extend(patents)
            total_count = data.get("total_patent_count", 0)
            print(f"  Page {page}: fetched {len(patents)} patents (total: {total_count})")

            # Check if we've got all results
            if len(all_patents) >= total_count:
                break

            # Rate limit: 45 requests/minute = ~1.3 sec between requests
            time.sleep(1.5)

        except requests.RequestException as e:
            print(f"  Error fetching page {page}: {e}")
            # Try to get error details
            try:
                error_detail = response.json() if response else None
                if error_detail:
                    print(f"  Error details: {error_detail}")
            except:
                pass
            break

    return all_patents


def process_patent(patent: dict) -> dict:
    """Process a raw patent from PatentsView into our schema."""
    patent_id = patent.get("patent_id", "")
    title = patent.get("patent_title", "")
    abstract = patent.get("patent_abstract", "") or ""
    pub_date = patent.get("patent_date")

    # Get first assignee
    assignees = patent.get("assignees", []) or []
    assignee = assignees[0].get("assignee_organization") if assignees else None

    # Get first inventor
    inventors = patent.get("inventors", []) or []
    first_inventor = None
    if inventors:
        inv = inventors[0]
        first_name = inv.get("inventor_first_name", "")
        last_name = inv.get("inventor_last_name", "")
        first_inventor = f"{first_name} {last_name}".strip() or None

    # Classify and extract targets
    category = classify_patent(title, abstract)
    target_symbols = extract_target_symbols(title, abstract)

    # Format patent number
    patent_number = f"US{patent_id}" if patent_id and not patent_id.startswith("US") else patent_id

    return {
        "patent_number": patent_number,
        "title": title,
        "abstract_snippet": abstract[:500] if abstract else None,
        "assignee": assignee,
        "first_inventor": first_inventor,
        "pub_date": pub_date,
        "category": category,
        "related_target_symbols": target_symbols if target_symbols else None,
        "source_url": f"https://patents.google.com/patent/{patent_number}",
    }


def upsert_patent(patent: dict, dry_run: bool = False) -> bool:
    """Upsert a patent to the database.

    Returns True if inserted/updated, False if skipped.
    """
    if dry_run:
        targets = patent.get('related_target_symbols', []) or []
        target_str = f" [{', '.join(targets)}]" if targets else ""
        print(f"  [DRY RUN] {patent['patent_number']}: {patent['title'][:50]}...{target_str}")
        return True

    try:
        # Check if exists
        existing = supabase.table("epi_patents").select("id").eq(
            "patent_number", patent["patent_number"]
        ).execute()

        if existing.data:
            # Update
            supabase.table("epi_patents").update(patent).eq(
                "patent_number", patent["patent_number"]
            ).execute()
            return True
        else:
            # Insert
            supabase.table("epi_patents").insert(patent).execute()
            return True

    except Exception as e:
        print(f"  Error upserting {patent['patent_number']}: {e}")
        return False


def run_strategy(api_key: str, strategy: str, keywords: list, field: str,
                dry_run: bool = False, limit: Optional[int] = None) -> int:
    """Run a single search strategy.

    Returns count of patents found.
    """
    print(f"\n{'='*60}")
    print(f"Strategy: {strategy}")
    print(f"Keywords: {len(keywords)} terms")
    print(f"Field: {field}")
    print(f"{'='*60}")

    # Fetch patents
    patents = fetch_patents(
        api_key,
        keywords,
        field,
        per_page=100,
        max_pages=5 if not limit else (limit // 100 + 1)
    )

    if limit:
        patents = patents[:limit]

    print(f"\nFound {len(patents)} patents")

    # Process and upsert
    upserted = 0
    for patent in patents:
        processed = process_patent(patent)
        if upsert_patent(processed, dry_run=dry_run):
            upserted += 1

    print(f"Upserted {upserted} patents")
    return len(patents)


def main():
    parser = argparse.ArgumentParser(description="Fetch epigenetic patents from USPTO PatentsView")
    parser.add_argument("--strategy", choices=["all", "company", "target", "technology", "drug"],
                       default="all", help="Search strategy to use")
    parser.add_argument("--dry-run", action="store_true", help="Don't write to database")
    parser.add_argument("--limit", type=int, help="Limit results per strategy")
    args = parser.parse_args()

    print("USPTO PatentsView Patent Fetcher (New PatentSearch API)")
    print(f"Strategy: {args.strategy}")
    print(f"Dry run: {args.dry_run}")

    # Get API key
    try:
        api_key = get_api_key()
        print("API key: configured ✓")
    except ValueError as e:
        print(f"\nError: {e}")
        print("\nTo get a free API key:")
        print("1. Go to https://patentsview.org/apis/keyrequest")
        print("2. Fill out the request form")
        print("3. Add to your .env: PATENTSVIEW_API_KEY=your_key_here")
        return

    total_found = 0

    strategies = {
        "company": (COMPANY_KEYWORDS, "assignees.assignee_organization"),
        "target": (TARGET_KEYWORDS, "patent_abstract"),
        "technology": (TECHNOLOGY_KEYWORDS, "patent_abstract"),
        "drug": (DRUG_KEYWORDS, "patent_abstract"),
    }

    if args.strategy == "all":
        for name, (keywords, field) in strategies.items():
            count = run_strategy(api_key, name, keywords, field, dry_run=args.dry_run, limit=args.limit)
            total_found += count
            time.sleep(2)  # Pause between strategies
    else:
        keywords, field = strategies[args.strategy]
        total_found = run_strategy(api_key, keywords, field, dry_run=args.dry_run, limit=args.limit)

    print(f"\n{'='*60}")
    print(f"TOTAL: Found {total_found} patents")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
