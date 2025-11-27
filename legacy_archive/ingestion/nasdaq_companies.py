"""
NASDAQ Biopharma Company List Ingestion

Uses official Nasdaq Trader symbol directory + SEC company tickers
to build an exhaustive list of biopharma companies.

Data Sources:
- https://www.nasdaqtrader.com/dynamic/symdir/nasdaqlisted.txt (official NASDAQ list)
- https://www.sec.gov/files/company_tickers.json (CIK mapping)
"""

import os
import sys
import requests
import pandas as pd
from io import StringIO
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import structlog
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from core.supabase_client import get_client

load_dotenv()
logger = structlog.get_logger()

# Official NASDAQ symbol directory
NASDAQ_URL = "https://www.nasdaqtrader.com/dynamic/symdir/nasdaqlisted.txt"
SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

# Biopharma keyword patterns (for heuristic filtering)
BIOPHARMA_KEYWORDS = [
    # Core biopharma terms
    'pharma', 'pharmaceutical', 'biopharma', 'biopharmaceutical',
    'biotech', 'biotechnology', 'biotherapeutics',

    # Bio- prefix patterns (catches Biogen, BioAge, BioVie, etc.)
    'biogen', 'bioage', 'biovie', 'biolife', 'biofrontera', 'bioharvest',
    'bioatla', 'biocardia', 'biodesix', 'bioaffinity', 'bioceres',
    'biomet', 'bionano', 'bioxcel', 'biocryst', 'biomea', 'biomarin',
    'adicet bio', 'anaptysbio', 'beta bionics', 'advanced biomed',

    # Therapeutic focus
    'therapeutics', 'therapy', 'oncology', 'immuno', 'immunology',
    'neuroscience', 'neuro', 'cardio', 'respiratory', 'metabolic',
    'dermatology', 'ophthalmology', 'hematology', 'vaccines',

    # Biology/science terms
    'biosciences', 'bioscience', 'biologic', 'biologics',
    'genomics', 'genetics', 'gene ', ' gene', 'gene-',
    'cell therapy', 'gene therapy', 'rna', 'mrna', 'dna',
    'antibody', 'antibodies', 'protein', 'peptide',

    # Drug development
    'medicines', 'drug', 'clinical', 'preclinical',

    # Common suffixes/patterns
    'thera ', ' thera', '-thera', 'medica', 'health sciences',
]

# Keywords to EXCLUDE (medical devices, services, diagnostics equipment)
EXCLUDE_KEYWORDS = [
    'medical devices', 'medical equipment', 'medical supplies',
    'surgical', 'instruments', 'imaging', 'mri', 'ct scan',
    'dental', 'ortho', 'orthopedic', 'prosthetic',
    'hospital', 'clinic ', 'healthcare services', 'health services',
    'insurance', 'hmo', 'managed care',
    'pharmacy benefit', 'pbm', 'drug distribution',
    'etf', 'fund', 'trust', 'reit',
    'spac', 'acquisition corp', 'blank check',
]

# Known major biopharma tickers that don't match keyword patterns
# These are manually curated to ensure completeness
KNOWN_BIOPHARMA_TICKERS = {
    'AMGN',   # Amgen - major biotech
    'GILD',   # Gilead Sciences - antiviral drugs
    'INCY',   # Incyte Corporation - cancer drugs
    'EXEL',   # Exelixis - cancer drugs
    'SRPT',   # Sarepta - gene therapy
    'RARE',   # Ultragenyx - rare disease
    'FOLD',   # Amicus - rare disease
    'ITCI',   # Intra-Cellular - CNS
    'CPRX',   # Catalyst - specialty pharma
    'RETA',   # Reata - rare disease
    'KRTX',   # Karuna - CNS
    'ARQT',   # Arcus - cancer
    'CYTK',   # Cytokinetics - cardiovascular
    'IMVT',   # Immunovant - autoimmune
    'PCVX',   # Vaxcyte - vaccines
    'DAWN',   # Day One - pediatric cancer
    'PRTA',   # Prothena - neurodegeneration
    'TSHA',   # Taysha - gene therapy
    'VCEL',   # Vericel - cell therapy
    'DVAX',   # Dynavax - vaccines
    'MNKD',   # MannKind - diabetes
    'PRPH',   # ProPhase Labs - diagnostics/therapeutics
    'CRVS',   # Corvus - cancer
    'CDXS',   # Codexis - protein engineering
    'VRDN',   # Viridian - thyroid
    'MRUS',   # Merus - cancer
}


def fetch_nasdaq_listed() -> pd.DataFrame:
    """
    Fetch official NASDAQ listed securities from Nasdaq Trader.

    Returns:
        DataFrame with Symbol, Security Name, Market Category, etc.
    """
    logger.info("Fetching NASDAQ listed securities...")

    response = requests.get(NASDAQ_URL, timeout=30)
    response.raise_for_status()

    # Drop footer line (starts with 'File Creation Time')
    lines = [ln for ln in response.text.splitlines()
             if not ln.startswith('File Creation Time')]
    txt = "\n".join(lines)

    df = pd.read_csv(StringIO(txt), sep="|")

    # Filter out test issues
    df = df[df["Test Issue"] == "N"]

    # Filter out ETFs
    df = df[df["ETF"] == "N"]

    logger.info(f"Fetched {len(df)} NASDAQ securities (excluding ETFs)")
    return df


def fetch_sec_tickers() -> Dict[str, dict]:
    """
    Fetch SEC company tickers with CIK mapping.

    Returns:
        Dict mapping ticker -> {cik_str, ticker, title}
    """
    logger.info("Fetching SEC company tickers...")

    headers = {
        "User-Agent": "pilldreams/1.0 (drug intelligence platform; contact@pilldreams.com)"
    }

    response = requests.get(SEC_TICKERS_URL, headers=headers, timeout=30)
    response.raise_for_status()

    data = response.json()

    # Convert from numeric keys to ticker-keyed dict
    ticker_map = {}
    for item in data.values():
        ticker_map[item['ticker']] = {
            'cik': str(item['cik_str']),
            'title': item['title']
        }

    logger.info(f"Fetched {len(ticker_map)} SEC tickers with CIK")
    return ticker_map


def is_biopharma_company(name: str, ticker: str = "") -> Tuple[bool, str]:
    """
    Heuristic check if company name indicates biopharma.

    Args:
        name: Company/security name
        ticker: Stock ticker symbol

    Returns:
        Tuple of (is_biopharma, reason)
    """
    import re

    name_lower = name.lower()

    # First check if ticker is in known biopharma allowlist
    if ticker and isinstance(ticker, str) and ticker.upper() in KNOWN_BIOPHARMA_TICKERS:
        return True, "Known biopharma (allowlist)"

    # Check exclusions
    for exclude in EXCLUDE_KEYWORDS:
        if exclude in name_lower:
            return False, f"Excluded: contains '{exclude}'"

    # Check for "Bio" prefix pattern (BioGen, BioAge, BioVie, etc.)
    # But not just "Bio" alone - needs to be followed by capital or lowercase letter
    if re.search(r'\bbio[a-z]', name_lower):
        return True, "Matched: 'Bio-' prefix"

    # Check for "Nano" prefix (Nanobiotix, etc.)
    if re.search(r'\bnano[a-z]', name_lower):
        return True, "Matched: 'Nano-' prefix"

    # Check company names ending with "bio" (AnaptysBio, Adicet Bio)
    if re.search(r'bio\b', name_lower) or re.search(r'bio,', name_lower):
        return True, "Matched: '-bio' suffix"

    # Check for "pharming" (edge case - Pharming Group)
    if 'pharming' in name_lower:
        return True, "Matched: 'pharming'"

    # Then check for biopharma keywords
    for keyword in BIOPHARMA_KEYWORDS:
        if keyword in name_lower:
            return True, f"Matched: '{keyword}'"

    return False, "No biopharma keywords found"


def build_biopharma_list() -> pd.DataFrame:
    """
    Build comprehensive list of NASDAQ biopharma companies.

    Returns:
        DataFrame with biopharma companies
    """
    # Fetch data
    nasdaq_df = fetch_nasdaq_listed()
    sec_tickers = fetch_sec_tickers()

    # Filter for biopharma
    biopharma_companies = []
    excluded_companies = []

    for _, row in nasdaq_df.iterrows():
        symbol = row['Symbol']
        name = row['Security Name']

        is_biopharma, reason = is_biopharma_company(name, ticker=symbol)

        # Get SEC data if available
        sec_data = sec_tickers.get(symbol, {})

        company = {
            'ticker': symbol,
            'name': name,
            'market_category': row.get('Market Category', ''),
            'financial_status': row.get('Financial Status', ''),
            'cik': sec_data.get('cik', ''),
            'sec_name': sec_data.get('title', ''),
            'is_biopharma': is_biopharma,
            'classification_reason': reason
        }

        if is_biopharma:
            biopharma_companies.append(company)
        else:
            excluded_companies.append(company)

    logger.info(f"Identified {len(biopharma_companies)} biopharma companies")
    logger.info(f"Excluded {len(excluded_companies)} non-biopharma companies")

    return pd.DataFrame(biopharma_companies), pd.DataFrame(excluded_companies)


def save_to_database(biopharma_df: pd.DataFrame) -> int:
    """
    Save biopharma companies to Supabase company table.

    Args:
        biopharma_df: DataFrame with biopharma companies

    Returns:
        Number of companies inserted/updated
    """
    db = get_client()

    inserted = 0
    for _, row in biopharma_df.iterrows():
        try:
            # Clean up security name for company name
            # Remove trailing ", Inc." or similar
            clean_name = row['name']
            if ' - ' in clean_name:
                clean_name = clean_name.split(' - ')[0].strip()

            # Upsert company (matches new schema_company.sql)
            db.client.table('company').upsert({
                'ticker': row['ticker'],
                'name': clean_name,
                'exchange': 'NASDAQ',
                'market_category': row['market_category'],
                'financial_status': row['financial_status'],
                'cik': row['cik'] if row['cik'] else None,
                'is_nbi_member': False,  # Will be updated separately for NBI members
                'updated_at': datetime.now().isoformat()
            }, on_conflict='ticker').execute()

            inserted += 1

            if inserted % 100 == 0:
                logger.info(f"Progress: {inserted}/{len(biopharma_df)} companies inserted")

        except Exception as e:
            logger.error(f"Failed to insert {row['ticker']}: {e}")

    logger.info(f"Saved {inserted} biopharma companies to database")
    return inserted


def analyze_coverage():
    """
    Analyze the biopharma coverage and print statistics.
    """
    biopharma_df, excluded_df = build_biopharma_list()

    print("\n" + "="*80)
    print("NASDAQ BIOPHARMA COMPANY ANALYSIS")
    print("="*80)

    print(f"\nTotal NASDAQ securities analyzed: {len(biopharma_df) + len(excluded_df)}")
    print(f"Identified as Biopharma: {len(biopharma_df)}")
    print(f"Excluded (non-biopharma): {len(excluded_df)}")

    # Market category breakdown
    print("\n--- Biopharma by Market Category ---")
    print(biopharma_df['market_category'].value_counts())

    # Top keywords matched
    print("\n--- Top Classification Reasons ---")
    print(biopharma_df['classification_reason'].value_counts().head(15))

    # Sample companies
    print("\n--- Sample Biopharma Companies (first 30) ---")
    for i, (_, row) in enumerate(biopharma_df.head(30).iterrows()):
        print(f"{i+1:3}. {row['ticker']:8} | {row['name'][:55]}")

    # Show some borderline excluded companies
    print("\n--- Sample EXCLUDED Companies (review these) ---")
    # Look for companies with 'bio' in name that got excluded
    borderline = excluded_df[excluded_df['name'].str.lower().str.contains('bio|pharm|therap', regex=True)]
    for i, (_, row) in enumerate(borderline.head(20).iterrows()):
        print(f"{i+1:3}. {row['ticker']:8} | {row['name'][:50]} | {row['classification_reason']}")

    return biopharma_df, excluded_df


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch NASDAQ biopharma companies")
    parser.add_argument("--analyze", action="store_true", help="Analyze coverage without saving")
    parser.add_argument("--save", action="store_true", help="Save to database")
    parser.add_argument("--export", type=str, help="Export to CSV file")

    args = parser.parse_args()

    if args.analyze:
        biopharma_df, excluded_df = analyze_coverage()

    elif args.save:
        biopharma_df, _ = build_biopharma_list()
        save_to_database(biopharma_df)

    elif args.export:
        biopharma_df, excluded_df = build_biopharma_list()
        biopharma_df.to_csv(args.export, index=False)
        print(f"Exported {len(biopharma_df)} companies to {args.export}")

    else:
        # Default: just analyze
        analyze_coverage()
