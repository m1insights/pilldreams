
import sys
import time
import requests
from typing import List, Dict, Optional
from pathlib import Path
import structlog
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from core.supabase_client import get_client

load_dotenv()
logger = structlog.get_logger()

class OpenTargetsIngestion:
    API_URL = "https://api.platform.opentargets.org/api/v4/graphql"
    
    def __init__(self):
        self.db = get_client()
        self.session = requests.Session()
        
    def map_uniprot_to_ensembl(self, uniprot_id: str) -> Optional[str]:
        """Map UniProt ID to Ensembl Gene ID using Open Targets."""
        query = """
        query Search($queryString: String!) {
          search(queryString: $queryString, entityNames: ["target"], page: {index: 0, size: 1}) {
            hits {
              id
              name
            }
          }
        }
        """
        try:
            r = self.session.post(self.API_URL, json={"query": query, "variables": {"queryString": uniprot_id}}, timeout=10)
            if r.status_code == 200:
                hits = r.json().get("data", {}).get("search", {}).get("hits", [])
                if hits:
                    return hits[0]["id"] # This is the Ensembl ID (e.g., ENSG00000146648)
        except Exception as e:
            logger.error("Target mapping failed", error=str(e), uniprot=uniprot_id)
            
        return None

    def get_associated_diseases(self, ensembl_id: str) -> List[Dict]:
        """Get all associated diseases and scores for a target."""
        query = """
        query Association($targetId: String!) {
          target(ensemblId: $targetId) {
            associatedDiseases(enableIndirect: true) {
              rows {
                disease {
                  id
                  name
                }
                score
              }
            }
          }
        }
        """
        
        try:
            variables = {"targetId": ensembl_id}
            r = self.session.post(self.API_URL, json={"query": query, "variables": variables}, timeout=10)
            if r.status_code == 200:
                data = r.json()
                rows = data.get("data", {}).get("target", {}).get("associatedDiseases", {}).get("rows", [])
                return rows
        except Exception as e:
            logger.error("Association query failed", error=str(e))
            
        return []

    def run(self):
        logger.info("Starting Open Targets ingestion...")
        
        # 1. Get Targets (with UniProt)
        targets = self.db.client.table("target").select("id, name, uniprot_id").not_.is_("uniprot_id", "null").execute().data
        logger.info(f"Found {len(targets)} targets with UniProt IDs")
        
        # Process in batches or just loop (rate limit is key)
        # Process all targets
        targets_to_process = targets
        
        for i, target in enumerate(targets_to_process):
            uniprot_id = target["uniprot_id"]
            target_name = target["name"]
            target_id = target["id"]
            
            logger.info(f"Processing {i+1}/{len(targets_to_process)}: {target_name} ({uniprot_id})")
            
            # Map to Ensembl
            ensembl_id = self.map_uniprot_to_ensembl(uniprot_id)
            if not ensembl_id:
                logger.warning(f"Could not map {target_name} to Ensembl")
                continue
            
            # Get Associations
            associations = self.get_associated_diseases(ensembl_id)
            
            if not associations:
                logger.info(f"No associations found for {target_name}")
                continue
                
            # Filter for high confidence scores (> 0.5)
            high_conf_associations = [a for a in associations if a["score"] > 0.5]
            
            logger.info(f"Found {len(high_conf_associations)} high-confidence associations for {target_name}")
            
            # Insert into DB
            records = []
            for assoc in high_conf_associations:
                disease = assoc["disease"]
                records.append({
                    "target_id": target_id,
                    "disease_name": disease["name"],
                    "efo_id": disease["id"],
                    "association_score": assoc["score"],
                    "evidence_count": 0 # Not fetching detailed evidence count yet
                })
            
            if records:
                try:
                    # Upsert to avoid duplicates
                    self.db.client.table("target_disease_association").upsert(records, on_conflict="target_id, disease_name").execute()
                    logger.info(f"Upserted {len(records)} associations")
                except Exception as e:
                    logger.error(f"Failed to insert associations for {target_name}", error=str(e))
            
            time.sleep(0.5) # Be nice to API

if __name__ == "__main__":
    ingestion = OpenTargetsIngestion()
    ingestion.run()
