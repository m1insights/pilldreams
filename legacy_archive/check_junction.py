from core.supabase_client import get_client

db = get_client()

# Count intervention links
intervention_count = db.client.table('trial_intervention').select('*', count='exact').limit(0).execute().count

# Count drugs with 0 trials
drugs = db.client.table('drug').select('id, name').execute().data

orphan_count = 0
for drug in drugs:
    interventions = db.client.table('trial_intervention').select('trial_id').eq('drug_id', drug['id']).execute()
    if not interventions.data:
        orphan_count += 1

print(f"✅ Intervention links: {intervention_count}")
print(f"📊 Total drugs: {len(drugs)}")
print(f"⚠️  Orphan drugs (0 trials): {orphan_count} ({orphan_count/len(drugs)*100:.1f}%)")
