
import requests
import json

API_URL = "https://api.platform.opentargets.org/api/v4/graphql"

def get_association_score(ensembl_id: str, efo_id: str) -> float:
    """Get overall association score."""
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
    
    variables = {"targetId": ensembl_id, "diseaseId": efo_id}
    r = requests.post(API_URL, json={"query": query, "variables": variables})
    print(json.dumps(r.json(), indent=2))

# ABL2 (ENSG00000143322) and Leukemia (EFO_0000565)
# ABL2 is known to be involved in CML (Chronic Myeloid Leukemia)
print("Checking ABL2 <-> Leukemia...")
get_association_score("ENSG00000143322", "EFO_0000565")
