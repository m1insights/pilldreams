"""
14b_fix_company_status.py

Updates company status for acquired/delisted/bankrupt companies
and fixes European ticker formats.

Run: python -m backend.etl.14b_fix_company_status

Prerequisites:
- Run migration_company_status.sql in Supabase first
"""

from backend.etl.supabase_client import supabase

# Company updates based on research (2025-12-01)
COMPANY_UPDATES = [
    {
        "ticker": "OMGA",
        "updates": {
            "status": "bankrupt",
            "status_notes": "Filed Chapter 11 bankruptcy Feb 2025. Flagship seized $14.7M cash. Attempting asset sale.",
            "market_cap": 7_900_000,  # $7.9M last traded
        }
    },
    {
        "ticker": "SPPI",
        "updates": {
            "status": "acquired",
            "acquirer": "Assertio Holdings (ASRT)",
            "acquisition_date": "2023-07-31",
            "status_notes": "Acquired for $1.34/share (all-stock + CVR). SPPI shareholders received 0.1783 ASRT shares per share.",
            "market_cap": None,  # Delisted
        }
    },
    {
        "ticker": "MOR",
        "updates": {
            "status": "acquired",
            "acquirer": "Novartis AG (NVS)",
            "acquisition_date": "2024-05-23",
            "status_notes": "Acquired for EUR 68/share (EUR 2.7B total). Novartis wanted pelabresib (myelofibrosis drug). Delisted from NASDAQ Q3 2024.",
            "market_cap": None,  # Delisted
        }
    },
    {
        "ticker": "VERV",
        "updates": {
            "status": "acquired",
            "acquirer": "Eli Lilly (LLY)",
            "acquisition_date": "2025-07-25",
            "status_notes": "Acquired for $10.50/share cash + CVR up to $3.00/share ($1.3B total). Gene editing for cardiovascular disease.",
            "market_cap": None,  # Delisted
        }
    },
    {
        # Ipsen - European stock, needs correct ticker format
        "ticker": "IPN",
        "updates": {
            "status": "active",
            "ticker": "IPN.PA",  # Paris exchange format for yfinance
            "exchange": "Euronext Paris",
            "market_cap": 11_000_000_000,  # ~$11B USD
        }
    },
    {
        # Oryzon - Spanish stock, needs correct ticker format
        "ticker": "ORY",
        "updates": {
            "status": "active",
            "ticker": "ORY.MC",  # Madrid exchange format for yfinance
            "exchange": "BME (Madrid)",
            "market_cap": 290_000_000,  # ~$290M USD (EUR 244M)
        }
    },
]


def main():
    print("=" * 60)
    print("14b_fix_company_status.py")
    print("Updating Company Status and Ticker Formats")
    print("=" * 60)

    updated = 0
    errors = 0

    for company_update in COMPANY_UPDATES:
        old_ticker = company_update["ticker"]
        updates = company_update["updates"]

        print(f"\nProcessing: {old_ticker}")

        try:
            # Find the company by old ticker
            result = supabase.table("epi_companies").select("id, name, ticker").eq("ticker", old_ticker).execute()

            if not result.data:
                print(f"  ERROR: Company with ticker {old_ticker} not found")
                errors += 1
                continue

            company = result.data[0]
            company_id = company["id"]
            company_name = company["name"]

            print(f"  Found: {company_name}")

            # Apply updates
            supabase.table("epi_companies").update(updates).eq("id", company_id).execute()

            # Print what was updated
            for key, value in updates.items():
                if value is not None:
                    print(f"    {key}: {value}")
                else:
                    print(f"    {key}: (cleared)")

            updated += 1

        except Exception as e:
            print(f"  ERROR: {e}")
            errors += 1

    print("\n" + "=" * 60)
    print(f"DONE: {updated} companies updated")
    print(f"      {errors} errors")
    print("=" * 60)

    # Print summary
    print("\nSummary of changes:")
    print("  - OMGA: Marked as bankrupt (Chapter 11)")
    print("  - SPPI: Marked as acquired by Assertio (July 2023)")
    print("  - MOR: Marked as acquired by Novartis (May 2024)")
    print("  - VERV: Marked as acquired by Eli Lilly (July 2025)")
    print("  - IPN: Ticker changed to IPN.PA (Paris), market cap $11B")
    print("  - ORY: Ticker changed to ORY.MC (Madrid), market cap $290M")


if __name__ == "__main__":
    main()
