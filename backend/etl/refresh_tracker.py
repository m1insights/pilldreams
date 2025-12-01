"""
Refresh Tracker: Utility to track when entities were last refreshed from external APIs.

Usage:
    from backend.etl.refresh_tracker import log_refresh, get_stale_entities

    # Log a refresh
    log_refresh('target', target_id, 'open_targets', records_found=15)

    # Find entities that haven't been refreshed in 30 days
    stale = get_stale_entities('target', 'open_targets', days=30)
"""
import sys
import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional

sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

from backend.etl.supabase_client import supabase


def log_refresh(
    entity_type: str,
    entity_id: str,
    api_source: str,
    records_found: int = 0,
    status: str = 'success',
    error_message: Optional[str] = None
) -> None:
    """
    Log a refresh event and update the entity's last_refresh timestamp.

    Args:
        entity_type: 'target', 'drug', or 'indication'
        entity_id: UUID of the entity
        api_source: 'open_targets', 'chembl', 'clinicaltrials'
        records_found: Number of records returned
        status: 'success', 'error', 'no_data'
        error_message: Error details if status is 'error'
    """
    # Insert into refresh log
    try:
        supabase.table('etl_refresh_log').insert({
            'entity_type': entity_type,
            'entity_id': entity_id,
            'api_source': api_source,
            'records_found': records_found,
            'status': status,
            'error_message': error_message
        }).execute()
    except Exception as e:
        # Table may not exist yet - that's OK
        print(f"  Note: Could not log to etl_refresh_log: {e}")

    # Update entity's last refresh timestamp
    table_name = f'epi_{entity_type}s'
    column_name = f'last_{api_source.replace("open_targets", "ot")}_refresh'

    try:
        supabase.table(table_name).update({
            column_name: datetime.now(timezone.utc).isoformat()
        }).eq('id', entity_id).execute()
    except Exception as e:
        # Column may not exist yet - that's OK
        pass


def get_stale_entities(
    entity_type: str,
    api_source: str,
    days: int = 30
) -> List[dict]:
    """
    Find entities that haven't been refreshed in the specified number of days.

    Args:
        entity_type: 'target', 'drug', or 'indication'
        api_source: 'open_targets' or 'chembl'
        days: Number of days after which an entity is considered stale

    Returns:
        List of stale entities with their IDs and last refresh dates
    """
    table_name = f'epi_{entity_type}s'
    column_name = f'last_{api_source.replace("open_targets", "ot")}_refresh'
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    try:
        # Targets have 'symbol', drugs/indications have 'name'
        name_col = 'symbol' if entity_type == 'target' else 'name'

        # Find entities where refresh is NULL or older than cutoff
        result = supabase.table(table_name).select(f'id, {name_col}, {column_name}').or_(
            f'{column_name}.is.null,{column_name}.lt.{cutoff}'
        ).execute()
        return result.data
    except Exception as e:
        print(f"  Error checking stale {entity_type}s: {e}")
        return []


def get_refresh_stats() -> dict:
    """Get summary statistics on data freshness."""
    stats = {}

    for entity_type in ['target', 'drug', 'indication']:
        table_name = f'epi_{entity_type}s'
        try:
            # Indications don't have ChEMBL refresh
            if entity_type == 'indication':
                result = supabase.table(table_name).select('id, last_ot_refresh').execute()
            else:
                result = supabase.table(table_name).select('id, last_ot_refresh, last_chembl_refresh').execute()

            entities = result.data
            total = len(entities)
            ot_refreshed = sum(1 for e in entities if e.get('last_ot_refresh'))
            chembl_refreshed = sum(1 for e in entities if e.get('last_chembl_refresh')) if entity_type != 'indication' else 0

            stats[entity_type] = {
                'total': total,
                'ot_refreshed': ot_refreshed,
                'chembl_refreshed': chembl_refreshed
            }
        except Exception as e:
            stats[entity_type] = {'error': str(e)}

    return stats


def print_freshness_report():
    """Print a human-readable freshness report."""
    print("\n📊 Data Freshness Report")
    print("=" * 50)

    stats = get_refresh_stats()

    for entity_type, data in stats.items():
        if 'error' in data:
            print(f"\n{entity_type.title()}s: ⚠️ {data['error']}")
        else:
            print(f"\n{entity_type.title()}s ({data['total']} total):")
            print(f"  Open Targets: {data['ot_refreshed']}/{data['total']} refreshed")
            if entity_type != 'indication':
                print(f"  ChEMBL: {data['chembl_refreshed']}/{data['total']} refreshed")

    # Check for stale data (>30 days old)
    print("\n⏰ Stale Data (>30 days):")
    for entity_type in ['target', 'drug']:
        stale_ot = get_stale_entities(entity_type, 'open_targets', days=30)
        if stale_ot:
            print(f"  {entity_type.title()}s needing OT refresh: {len(stale_ot)}")


if __name__ == "__main__":
    print_freshness_report()
