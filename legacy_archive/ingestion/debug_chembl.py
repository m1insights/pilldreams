
import requests
import xml.etree.ElementTree as ET

chembl_id = "CHEMBL5095142"
print(f"Checking ChEMBL data for {chembl_id}...")

# Check mechanism
url = f"https://www.ebi.ac.uk/chembl/api/data/mechanism?molecule_chembl_id={chembl_id}&format=json"
r = requests.get(url)
data = r.json()
mechanisms = data.get("mechanisms", [])
print(f"Mechanisms: {len(mechanisms)}")
for m in mechanisms:
    print(f"- {m.get('mechanism_of_action')} (Target: {m.get('target_chembl_id')})")

# Check activities
url = f"https://www.ebi.ac.uk/chembl/api/data/activity?molecule_chembl_id={chembl_id}&limit=5&format=json"
r = requests.get(url)
data = r.json()
activities = data.get("activities", [])
print(f"Activities: {len(activities)}")
for a in activities:
    print(f"- {a.get('type')} = {a.get('value')} {a.get('units')} (Target: {a.get('target_chembl_id')})")
