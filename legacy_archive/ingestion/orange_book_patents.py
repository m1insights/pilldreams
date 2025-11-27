"""
FDA Orange Book Patent Data Ingestion

Fetches patent and exclusivity data from FDA Orange Book.

Orange Book provides:
- Patent numbers and expiration dates
- Patent types (substance, product, use)
- Exclusivity periods (NCE, ODE, etc.)

API: https://www.accessdata.fda.gov/scripts/cder/ob/index.cfm
Note: Orange Book data can be downloaded as bulk files or accessed via their search interface.

For MVP: We'll create a framework ready for real data, with sample data for testing.
"""

import structlog
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.supabase_client import get_client
from datetime import datetime, timedelta
import random

logger = structlog.get_logger()


def fetch_patents_for_drug(drug_name: str) -> list:
    """
    Fetch patent data from Orange Book for a specific drug.

    Args:
        drug_name: Generic or brand name of drug

    Returns:
        List of patent dictionaries

    TODO: Implement real API call to Orange Book
    For now, returns sample data structure
    """
    # PLACEHOLDER: In production, this would call Orange Book API
    # Example: https://www.accessdata.fda.gov/scripts/cder/ob/search_product.cfm

    logger.info("Fetching patents for drug", drug_name=drug_name)

    # Sample patent data structure
    sample_patents = [
        {
            'patent_number': f'US{random.randint(7000000, 9999999)}',
            'patent_expire_date': (datetime.now() + timedelta(days=random.randint(365, 3650))).date().isoformat(),
            'drug_substance_flag': True,
            'drug_product_flag': False,
            'use_code': None,
            'use_description': 'Drug substance patent'
        },
        {
            'patent_number': f'US{random.randint(7000000, 9999999)}',
            'patent_expire_date': (datetime.now() + timedelta(days=random.randint(365, 2920))).date().isoformat(),
            'drug_substance_flag': False,
            'drug_product_flag': True,
            'use_code': 'U-1',
            'use_description': 'Formulation patent'
        }
    ]

    return sample_patents


def fetch_exclusivity_for_drug(drug_name: str) -> list:
    """
    Fetch exclusivity data from Orange Book.

    Args:
        drug_name: Generic or brand name of drug

    Returns:
        List of exclusivity dictionaries
    """
    logger.info("Fetching exclusivity for drug", drug_name=drug_name)

    # Sample exclusivity data
    exclusivity_codes = ['NCE', 'ODE', 'PED', 'NGE']
    sample_exclusivity = []

    if random.random() > 0.5:  # 50% chance of having exclusivity
        sample_exclusivity.append({
            'exclusivity_code': random.choice(exclusivity_codes),
            'exclusivity_date': (datetime.now() + timedelta(days=random.randint(1095, 2555))).date().isoformat()
        })

    return sample_exclusivity


def ingest_patents_for_drug(drug_id: str, drug_name: str) -> dict:
    """
    Ingest patent and exclusivity data for a single drug.

    Args:
        drug_id: UUID of the drug in database
        drug_name: Name of the drug

    Returns:
        Dictionary with ingestion results
    """
    client = get_client()

    # Fetch data from Orange Book
    patents = fetch_patents_for_drug(drug_name)
    exclusivities = fetch_exclusivity_for_drug(drug_name)

    patents_inserted = 0
    exclusivities_inserted = 0

    # Insert patents
    for patent in patents:
        try:
            client.client.table('patent').insert({
                'drug_id': drug_id,
                **patent
            }).execute()
            patents_inserted += 1
        except Exception as e:
            logger.error("Failed to insert patent", drug_id=drug_id, error=str(e))

    # Insert exclusivities
    for exclusivity in exclusivities:
        try:
            client.client.table('exclusivity').insert({
                'drug_id': drug_id,
                **exclusivity
            }).execute()
            exclusivities_inserted += 1
        except Exception as e:
            logger.error("Failed to insert exclusivity", drug_id=drug_id, error=str(e))

    # Calculate aggregate metrics
    if patents:
        substance_patents = len([p for p in patents if p['drug_substance_flag']])
        formulation_patents = len([p for p in patents if p['drug_product_flag']])
        use_patents = len([p for p in patents if p.get('use_code')])

        expiry_dates = [p['patent_expire_date'] for p in patents]
        earliest_expiry = min(expiry_dates) if expiry_dates else None
        latest_expiry = max(expiry_dates) if expiry_dates else None

        # Calculate patent cliff risk
        if earliest_expiry:
            days_to_cliff = (datetime.fromisoformat(earliest_expiry) - datetime.now()).days
            if days_to_cliff < 730:  # < 2 years
                patent_cliff_risk = 'High'
            elif days_to_cliff < 1825:  # < 5 years
                patent_cliff_risk = 'Medium'
            else:
                patent_cliff_risk = 'Low'
        else:
            patent_cliff_risk = 'Unknown'

        # Upsert to patentaggregate table
        try:
            client.client.table('patentaggregate').upsert({
                'drug_id': drug_id,
                'total_patents': len(patents),
                'substance_patents': substance_patents,
                'formulation_patents': formulation_patents,
                'use_patents': use_patents,
                'earliest_expiry_date': earliest_expiry,
                'latest_expiry_date': latest_expiry,
                'has_exclusivity': len(exclusivities) > 0,
                'exclusivity_expiry_date': exclusivities[0]['exclusivity_date'] if exclusivities else None,
                'patent_cliff_risk': patent_cliff_risk,
                'updated_at': datetime.now().isoformat()
            }).execute()
        except Exception as e:
            logger.error("Failed to update patentaggregate", drug_id=drug_id, error=str(e))

    logger.info("Patent ingestion complete",
                drug_id=drug_id,
                patents=patents_inserted,
                exclusivities=exclusivities_inserted)

    return {
        'drug_id': drug_id,
        'drug_name': drug_name,
        'patents_inserted': patents_inserted,
        'exclusivities_inserted': exclusivities_inserted
    }


def ingest_all_approved_drugs():
    """
    Ingest patent data for all approved drugs in database.

    Note: This assumes `is_approved` flag is set correctly.
    """
    client = get_client()

    # Get all approved drugs
    drugs = client.client.table('drug').select('id, name').eq('is_approved', True).execute()

    if not drugs.data:
        logger.warning("No approved drugs found")
        return

    total_drugs = len(drugs.data)
    logger.info(f"Starting patent ingestion for {total_drugs} approved drugs")

    results = []
    for i, drug in enumerate(drugs.data, 1):
        logger.info(f"Processing drug {i}/{total_drugs}", drug_name=drug['name'])
        result = ingest_patents_for_drug(drug['id'], drug['name'])
        results.append(result)

    # Summary
    total_patents = sum(r['patents_inserted'] for r in results)
    total_exclusivities = sum(r['exclusivities_inserted'] for r in results)

    logger.info("Patent ingestion completed",
                total_drugs=total_drugs,
                total_patents=total_patents,
                total_exclusivities=total_exclusivities)

    print(f"\n{'='*80}")
    print(f"PATENT INGESTION SUMMARY")
    print(f"{'='*80}")
    print(f"Drugs processed: {total_drugs}")
    print(f"Patents added: {total_patents}")
    print(f"Exclusivities added: {total_exclusivities}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Ingest patent data from FDA Orange Book')
    parser.add_argument('--drug-name', type=str, help='Specific drug name to process')
    parser.add_argument('--all-approved', action='store_true', help='Process all approved drugs')
    parser.add_argument('--test', action='store_true', help='Test mode with single drug')

    args = parser.parse_args()

    if args.test:
        # Test with first drug in database
        client = get_client()
        drug = client.client.table('drug').select('id, name').limit(1).execute()

        if drug.data:
            result = ingest_patents_for_drug(drug.data[0]['id'], drug.data[0]['name'])
            print(f"\n✅ Test complete: {result}")
        else:
            print("No drugs found in database")

    elif args.drug_name:
        # Process specific drug
        client = get_client()
        drug = client.client.table('drug').select('id, name').ilike('name', f'%{args.drug_name}%').limit(1).execute()

        if drug.data:
            result = ingest_patents_for_drug(drug.data[0]['id'], drug.data[0]['name'])
            print(f"\n✅ Complete: {result}")
        else:
            print(f"Drug '{args.drug_name}' not found")

    elif args.all_approved:
        ingest_all_approved_drugs()

    else:
        parser.print_help()
