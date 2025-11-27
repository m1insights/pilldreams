
import requests
import json

base_url = "https://clinicaltrials.gov/api/v2/studies"
sponsor_variations = [
    "Acurx Pharmaceuticals, Inc.",
    "Acurx Pharmaceuticals Inc.",
    "Acurx Pharmaceuticals Inc",
    "Acurx Pharmaceuticals",
    "Acurx"
]

print("Testing sponsor variations...")

for sponsor in sponsor_variations:
    query = f'AREA[LeadSponsorName]"{sponsor}"'
    params = {
        "format": "json",
        "query.cond": query,
        "pageSize": 1
    }
    
    try:
        r = requests.get(base_url, params=params)
        data = r.json()
        studies = data.get("studies", [])
        count = len(studies)
        print(f"'{sponsor}': {count} trials found")
        if count > 0:
            s = studies[0]["protocolSection"]["statusModule"]["overallStatus"]
            p = studies[0]["protocolSection"]["designModule"].get("phases", ["Unknown"])
            print(f"  - Status: {s}")
            print(f"  - Phase: {p}")
    except Exception as e:
        print(f"'{sponsor}': Error {e}")
