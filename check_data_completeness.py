"""
Check data completeness across all tables in pilldreams database
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from core.supabase_client import get_client

db = get_client()

print("=" * 60)
print("DATA COMPLETENESS CHECK")
print("=" * 60)

# 1. Drug table - ChEMBL ID coverage
print("\n1. DRUG TABLE - ChEMBL ID Coverage")
print("-" * 60)
drugs = db.client.table('drug').select('id, chembl_id').execute()
total_drugs = len(drugs.data)
with_chembl = sum(1 for d in drugs.data if d.get('chembl_id'))
print(f"Total drugs: {total_drugs:,}")
print(f"With ChEMBL ID: {with_chembl:,} ({with_chembl/total_drugs*100:.1f}%)")
print(f"Missing ChEMBL ID: {total_drugs - with_chembl:,} ({(total_drugs-with_chembl)/total_drugs*100:.1f}%)")

# 2. Trial table - Design quality score coverage
print("\n2. TRIAL TABLE - Design Quality Score Coverage")
print("-" * 60)
trials = db.client.table('trial').select('nct_id, design_quality_score').execute()
total_trials = len(trials.data)
with_score = sum(1 for t in trials.data if t.get('design_quality_score') is not None)
print(f"Total trials: {total_trials:,}")
print(f"With design score: {with_score:,} ({with_score/total_trials*100:.1f}%)")
print(f"Missing design score: {total_trials - with_score:,} ({(total_trials-with_score)/total_trials*100:.1f}%)")

# 3. DrugTarget table - Affinity data
print("\n3. DRUGTARGET TABLE - Binding Affinity Data")
print("-" * 60)
drugtargets = db.client.table('drugtarget').select('id, affinity_value').execute()
total_drugtargets = len(drugtargets.data)
with_affinity = sum(1 for dt in drugtargets.data if dt.get('affinity_value') is not None)
print(f"Total drug-target pairs: {total_drugtargets:,}")
print(f"With affinity data: {with_affinity:,} ({with_affinity/total_drugtargets*100:.1f}%)")
print(f"Missing affinity data: {total_drugtargets - with_affinity:,} ({(total_drugtargets-with_affinity)/total_drugtargets*100:.1f}%)")

# 4. AdverseEvent table - Coverage
print("\n4. ADVERSEEVENT TABLE - Safety Data Coverage")
print("-" * 60)
aes = db.client.table('adverseevent').select('id').execute()
total_aes = len(aes.data)
print(f"Total adverse events: {total_aes:,}")

# Count distinct drugs with adverse events
drug_ae_counts = {}
for ae in aes.data:
    drug_id = ae.get('drug_id')
    if drug_id:
        drug_ae_counts[drug_id] = drug_ae_counts.get(drug_id, 0) + 1

drugs_with_ae = len(drug_ae_counts)
print(f"Drugs with adverse event data: {drugs_with_ae:,} ({drugs_with_ae/total_drugs*100:.1f}%)")
print(f"Drugs without adverse event data: {total_drugs - drugs_with_ae:,} ({(total_drugs-drugs_with_ae)/total_drugs*100:.1f}%)")

# 5. Publication table - Evidence coverage
print("\n5. PUBLICATION TABLE - Evidence/RCT Data")
print("-" * 60)
pubs = db.client.table('publication').select('id').execute()
total_pubs = len(pubs.data)
print(f"Total publications: {total_pubs:,}")

# Count distinct drugs with publications
drug_pub_counts = {}
for pub in pubs.data:
    drug_id = pub.get('drug_id')
    if drug_id:
        drug_pub_counts[drug_id] = drug_pub_counts.get(drug_id, 0) + 1

drugs_with_pubs = len(drug_pub_counts)
print(f"Drugs with publications: {drugs_with_pubs:,} ({drugs_with_pubs/total_drugs*100:.1f}%)")
print(f"Drugs without publications: {total_drugs - drugs_with_pubs:,} ({(total_drugs-drugs_with_pubs)/total_drugs*100:.1f}%)")

# Summary
print("\n" + "=" * 60)
print("SUMMARY - Data Completeness Issues")
print("=" * 60)

issues = []
if (total_drugs - with_chembl) > 0:
    issues.append(f"⚠️  ChEMBL: {total_drugs - with_chembl:,} drugs missing ChEMBL IDs")
if (total_trials - with_score) > 0:
    issues.append(f"⚠️  Trial Scores: {total_trials - with_score:,} trials missing design quality scores")
if drugs_with_ae < total_drugs * 0.5:  # Less than 50% coverage
    issues.append(f"⚠️  Adverse Events: Only {drugs_with_ae:,}/{total_drugs:,} drugs have safety data")
if drugs_with_pubs < total_drugs * 0.5:  # Less than 50% coverage
    issues.append(f"⚠️  Publications: Only {drugs_with_pubs:,}/{total_drugs:,} drugs have evidence data")

if issues:
    for issue in issues:
        print(issue)
else:
    print("✅ All data looks complete!")

print("\n" + "=" * 60)
