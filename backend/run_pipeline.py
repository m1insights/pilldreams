import sys
import os
import asyncio

# Add current directory to path so we can import main
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import run_full_etl, run_enrichment, run_pipeline_etl

def main():
    print("🚀 Starting Disease-Anchored Drug Intelligence Pipeline")
    
    print("\n[1/3] Fetching known drugs (Gold Set) from Open Targets...")
    try:
        run_full_etl()
        print("✅ Open Targets fetch complete.")
    except Exception as e:
        print(f"❌ Error in Open Targets fetch: {e}")
        return

    print("\n[2/3] Fetching Pipeline Assets (Phase 1-2) and Scoring...")
    try:
        run_pipeline_etl()
        print("✅ Pipeline Assets fetch complete.")
    except Exception as e:
        print(f"❌ Error in Pipeline Assets fetch: {e}")
        return

    print("\n[3/3] Enriching drugs with PubMed and OpenFDA data...")
    try:
        run_enrichment()
        print("✅ Enrichment complete.")
    except Exception as e:
        print(f"❌ Error in Enrichment: {e}")
        return

    print("\n✨ Pipeline finished successfully!")

if __name__ == "__main__":
    main()
