import requests
import json

GRAPHQL_ENDPOINT = "https://api.platform.opentargets.org/api/v4/graphql"

def run_ot_query(query: str, variables: dict = None) -> dict:
    print(f"Sending query to {GRAPHQL_ENDPOINT}...")
    response = requests.post(
        GRAPHQL_ENDPOINT,
        json={"query": query, "variables": variables or {}},
        headers={"Content-Type": "application/json"}
    )
    print(f"Status Code: {response.status_code}")
    try:
        data = response.json()
        print(f"Response Body: {json.dumps(data, indent=2)}")
        return data
    except Exception as e:
        print(f"Failed to parse JSON: {e}")
        print(f"Raw text: {response.text}")
        return None

query = """
query Search($queryString: String!) {
  search(queryString: $queryString, entityNames: ["disease"], page: {index: 0, size: 1}) {
    hits {
      id
      name
    }
  }
}
"""

diseases = [
    "major depressive disorder",
    "generalized anxiety disorder",
    "attention deficit hyperactivity disorder",
    "type 2 diabetes mellitus"
]

for d in diseases:
    print(f"Searching for {d}...")
    run_ot_query(query, {"queryString": d})
