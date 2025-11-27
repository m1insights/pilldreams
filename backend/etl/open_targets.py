import requests
from typing import List, Dict

OT_API_URL = "https://api.platform.opentargets.org/api/v4/graphql"

def run_ot_query(query: str, variables: dict = None) -> dict:
    """Execute GraphQL query against Open Targets."""
    response = requests.post(
        OT_API_URL,
        json={"query": query, "variables": variables or {}},
        headers={"Content-Type": "application/json"}
    )
    if response.status_code == 400:
        print(f"❌ GraphQL 400 Error. Query: {query} Variables: {variables}")
        print(f"Response: {response.text}")
    response.raise_for_status()
    return response.json()

def fetch_known_drugs_for_disease(efo_id: str) -> List[Dict]:
    """
    Fetch all known drugs for a disease.
    Returns list of {drug, target, mechanism, phase, drugType}.
    """
    query = """
    query KnownDrugs($efoId: String!, $cursor: String) {
      disease(efoId: $efoId) {
        knownDrugs(size: 100, cursor: $cursor) {
          cursor
          rows {
            drug {
              id
              name
              maximumClinicalTrialPhase
            }
            drugType
            phase
            mechanismOfAction
            target {
              id
              approvedSymbol
            }
          }
        }
      }
    }
    """
    
    all_rows = []
    cursor = None
    
    while True:
        result = run_ot_query(query, {"efoId": efo_id, "cursor": cursor})
        data = result["data"]["disease"]["knownDrugs"]
        all_rows.extend(data["rows"])
        cursor = data.get("cursor")
        if not cursor:
            break
    
    return all_rows

def fetch_drug_details(drug_id: str) -> Dict:
    """
    Fetch drug cross-references and metadata.
    Returns {id, name, crossReferences, linkedTargets, ...}.
    """
    query = """
    query DrugDetails($drugId: String!) {
      drug(chemblId: $drugId) {
        id
        name
        crossReferences {
          source
          reference
        }
        linkedTargets {
          rows {
            id
            approvedSymbol
          }
        }
      }
    }
    """
    result = run_ot_query(query, {"drugId": drug_id})
    return result["data"]["drug"]

def fetch_disease_targets_scores(efo_id: str) -> Dict[str, float]:
    """
    Fetch associated targets for a disease and their overall association scores.
    Returns dict: {target_id: score}
    """
    query = """
    query DiseaseTargets($efoId: String!, $index: Int!) {
      disease(efoId: $efoId) {
        associatedTargets(page: {size: 50, index: $index}) {
          rows {
            target {
              id
            }
            score
          }
        }
      }
    }
    """
    scores = {}
    index = 0
    
    while True:
        # Fetch pages until empty or limit reached (e.g. 20 pages = 1000 targets)
        # We need more depth to capture weaker associations for pipeline assets.
        if index > 20: 
            break
            
        result = run_ot_query(query, {"efoId": efo_id, "index": index})
        data = result["data"]["disease"]["associatedTargets"]
        
        if not data["rows"]:
            break
            
        for row in data["rows"]:
            scores[row["target"]["id"]] = row["score"]
            
        index += 1
            
    return scores

def fetch_target_details(target_id: str) -> Dict:
    """
    Fetch target UniProt/Ensembl IDs.
    Returns {id, approvedSymbol, proteinAnnotations, ...}.
    """
    query = """
    query TargetDetails($targetId: String!) {
      target(ensemblId: $targetId) {
        id
        approvedSymbol
      }
    }
    """
    result = run_ot_query(query, {"targetId": target_id})
    return result["data"]["target"]
