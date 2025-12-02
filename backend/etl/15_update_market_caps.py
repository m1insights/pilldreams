"""
14_update_market_caps.py

Fetches market cap data from Yahoo Finance for all companies with tickers.

Run: python -m backend.etl.14_update_market_caps
"""

import time
from backend.etl.supabase_client import supabase

try:
    import yfinance as yf
except ImportError:
    print("Installing yfinance...")
    import subprocess
    subprocess.check_call(["pip", "install", "yfinance"])
    import yfinance as yf


def format_market_cap(value: int | None) -> str:
    """Format market cap for display."""
    if not value:
        return "N/A"
    if value >= 1_000_000_000_000:
        return f"${value / 1_000_000_000_000:.1f}T"
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.1f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    return f"${value:,}"


def get_market_cap(ticker: str) -> int | None:
    """Fetch market cap from Yahoo Finance."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        market_cap = info.get("marketCap")
        if market_cap and isinstance(market_cap, (int, float)):
            return int(market_cap)
        return None
    except Exception as e:
        print(f"    Error fetching {ticker}: {e}")
        return None


def main():
    print("=" * 60)
    print("14_update_market_caps.py")
    print("Fetching Market Cap Data from Yahoo Finance")
    print("=" * 60)

    # Get all companies with tickers
    result = supabase.table("epi_companies").select("id, name, ticker, exchange, market_cap").execute()
    companies = result.data

    # Filter to companies with tickers (public companies)
    public_companies = [c for c in companies if c.get("ticker")]
    print(f"\nFound {len(public_companies)} public companies with tickers.\n")

    updated = 0
    skipped = 0
    errors = 0

    for company in public_companies:
        name = company["name"]
        ticker = company["ticker"]
        current_cap = company.get("market_cap")

        print(f"Processing: {name} ({ticker})")

        if current_cap:
            print(f"  Already has market cap: {format_market_cap(current_cap)}")
            skipped += 1
            continue

        market_cap = get_market_cap(ticker)

        if market_cap:
            try:
                supabase.table("epi_companies").update({
                    "market_cap": market_cap
                }).eq("id", company["id"]).execute()
                print(f"  Updated: {format_market_cap(market_cap)}")
                updated += 1
            except Exception as e:
                print(f"  Error updating: {e}")
                errors += 1
        else:
            print(f"  Could not fetch market cap")
            errors += 1

        # Rate limit
        time.sleep(0.5)

    print("\n" + "=" * 60)
    print(f"DONE: {updated} companies updated")
    print(f"      {skipped} companies skipped (already had data)")
    print(f"      {errors} errors")
    print("=" * 60)


if __name__ == "__main__":
    main()
