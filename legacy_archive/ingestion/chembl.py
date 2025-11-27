"""
ChEMBL Data Ingestion Script
Fetches drug and target data from ChEMBL API and populates the database.
"""

import os
import sys
import requests
import structlog
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.supabase_client import get_client

logger = structlog.get_logger()

CHEMBL_BASE_URL = "https://www.ebi.ac.uk/chembl/api/data"

def search_drug_chembl(drug_name: str) -> Optional[Dict[str, Any]]:
    """
    Search for a drug in ChEMBL by name.
    """
    url = f"{CHEMBL_BASE_URL}/molecule/search?q={drug_name}&format=json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        molecules = data.get('molecules', [])
        if not molecules:
            return None
            
        # Return the best match (usually the first one, but could refine)
        # For now, return the first one
        return molecules[0]
    except Exception as e:
        logger.error("Error searching ChEMBL", drug_name=drug_name, error=str(e))
        return None

def get_drug_mechanisms(chembl_id: str) -> List[Dict[str, Any]]:
    """
    Get mechanisms of action for a drug.
    """
    url = f"{CHEMBL_BASE_URL}/mechanism?molecule_chembl_id={chembl_id}&format=json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get('mechanisms', [])
    except Exception as e:
        logger.error("Error fetching mechanisms", chembl_id=chembl_id, error=str(e))
        return []

def get_target_details(target_chembl_id: str) -> Optional[Dict[str, Any]]:
    """
    Get details for a target.
    """
    url = f"{CHEMBL_BASE_URL}/target/{target_chembl_id}?format=json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error("Error fetching target details", target_id=target_chembl_id, error=str(e))
        return None

def ingest_drug(drug_name: str, chembl_id: Optional[str] = None, tier: str = 'Bronze'):
    """
    Main function to ingest a single drug and its targets.
    """
    client = get_client()
    logger.info("Starting ingestion for drug", drug_name=drug_name, chembl_id=chembl_id, tier=tier)
    
    # 1. Search ChEMBL if ID not provided
    if not chembl_id:
        chembl_data = search_drug_chembl(drug_name)
        if not chembl_data:
            logger.warning("Drug not found in ChEMBL", drug_name=drug_name)
            return
        chembl_id = chembl_data.get('molecule_chembl_id')
        pref_name = chembl_data.get('pref_name') or drug_name
        molecule_type = chembl_data.get('molecule_type')
    else:
        # We have ID, but need details (type, pref_name)
        # We can fetch molecule details by ID
        url = f"{CHEMBL_BASE_URL}/molecule/{chembl_id}?format=json"
        try:
            response = requests.get(url)
            response.raise_for_status()
            chembl_data = response.json()
            pref_name = chembl_data.get('pref_name') or drug_name
            molecule_type = chembl_data.get('molecule_type')
        except Exception as e:
            logger.error("Error fetching drug details", chembl_id=chembl_id, error=str(e))
            return

    logger.info("Found drug in ChEMBL", chembl_id=chembl_id, name=pref_name)

    # 2. Insert into drugs table
    drug_record = {
        'name': pref_name,
        'chembl_id': chembl_id,
        'molecule_type': molecule_type,
        'synonyms': [drug_name] if drug_name.lower() != pref_name.lower() else [],
        'status': 'unknown', # To be updated from other sources
        'tier': tier,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    # Check if drug exists
    existing = client.client.table('drugs').select('id').eq('chembl_id', chembl_id).execute()
    if existing.data:
        drug_id = existing.data[0]['id']
        client.client.table('drugs').update(drug_record).eq('id', drug_id).execute()
        logger.info("Updated existing drug", drug_id=drug_id)
    else:
        res = client.client.table('drugs').insert(drug_record).execute()
        drug_id = res.data[0]['id']
        logger.info("Inserted new drug", drug_id=drug_id)

    # 3. Get Mechanisms (Targets)
    mechanisms = get_drug_mechanisms(chembl_id)
    
    for mech in mechanisms:
        target_chembl_id = mech.get('target_chembl_id')
        action_type = mech.get('action_type')
        description = mech.get('mechanism_of_action')
        
        if not target_chembl_id:
            continue
            
        # Get target details
        target_info = get_target_details(target_chembl_id)
        if not target_info:
            continue
            
        target_symbol = target_info.get('target_components', [{}])[0].get('target_component_synonyms', [{}])[0].get('component_synonym')
        # Fallback for symbol
        if not target_symbol:
             target_symbol = target_info.get('pref_name')

        uniprot_id = None
        # Try to find uniprot ID
        for comp in target_info.get('target_components', []):
            for xref in comp.get('target_component_xrefs', []):
                if xref.get('xref_src_db') == 'UniProt':
                    uniprot_id = xref.get('xref_id')
                    break
            if uniprot_id:
                break
        
        # Insert Target
        target_record = {
            'chembl_id': target_chembl_id,
            'symbol': target_symbol or 'Unknown',
            'uniprot_id': uniprot_id,
            'description': target_info.get('pref_name'),
            'created_at': datetime.now().isoformat()
        }
        
        # Check if target exists
        existing_target = client.client.table('targets').select('id').eq('chembl_id', target_chembl_id).execute()
        if existing_target.data:
            target_id = existing_target.data[0]['id']
        else:
            res_t = client.client.table('targets').insert(target_record).execute()
            target_id = res_t.data[0]['id']
            
        # Insert Drug-Target Link
        link_record = {
            'drug_id': drug_id,
            'target_id': target_id,
            'role_on_target': action_type,
            'confidence_score': 1.0, # ChEMBL mechanism is high confidence
            'created_at': datetime.now().isoformat()
        }
        
        # Check if link exists
        existing_link = client.client.table('drug_targets').select('id').eq('drug_id', drug_id).eq('target_id', target_id).execute()
        if not existing_link.data:
            client.client.table('drug_targets').insert(link_record).execute()
            logger.info("Linked drug to target", drug=pref_name, target=target_symbol)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--drug", help="Name of drug to ingest")
    parser.add_argument("--test", action="store_true", help="Run test with sample drugs")
    parser.add_argument("--seed", action="store_true", help="Seed database with neuropsych drugs")
    args = parser.parse_args()
    
    if args.test:
        test_drugs = ["Ketamine", "Fluoxetine", "Lisdexamfetamine"]
        for drug in test_drugs:
            ingest_drug(drug)
    elif args.seed:
        # Curated list of drugs for Depression, Anxiety, ADHD
        SEED_DRUGS = [
            # Depression (SSRIs, SNRIs, Atypical, Novel)
            "Fluoxetine", "Sertraline", "Escitalopram", "Venlafaxine", 
            "Bupropion", "Ketamine", "Esketamine", "Zuranolone",
            # Anxiety (Benzos, Others)
            "Alprazolam", "Diazepam", "Buspirone", "Pregabalin",
            # ADHD (Stimulants, Non-stimulants)
            "Methylphenidate", "Lisdexamfetamine", "Atomoxetine", "Guanfacine"
        ]
        logger.info(f"Seeding database with {len(SEED_DRUGS)} neuropsych drugs...")
        for drug in SEED_DRUGS:
            ingest_drug(drug)
    elif args.drug:
        ingest_drug(args.drug)
    else:
        print("Please provide --drug, --test, or --seed")
