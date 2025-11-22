from core.supabase_client import get_client

db = get_client()

# Previously orphan drugs from audit
orphan_samples = ["Atezolizumab", "Bevacizumab", "Pembrolizumab", "Nivolumab", "Psilocybin"]

print("🔍 Spot Check: Previously Orphan Drugs\n")
print("=" * 60)

for drug_name in orphan_samples:
    # Get drug
    drug = db.client.table('drug').select('id, name').eq('name', drug_name).execute().data
    if not drug:
        print(f"\n❌ {drug_name}: NOT FOUND")
        continue
    
    drug_id = drug[0]['id']
    
    # Get intervention links
    interventions = db.client.table('trial_intervention').select('trial_id, intervention_role').eq('drug_id', drug_id).execute()
    trial_ids = [i['trial_id'] for i in interventions.data] if interventions.data else []
    
    # Get trial details
    if trial_ids:
        trials = db.client.table('trial').select('nct_id, phase, status').in_('nct_id', trial_ids).execute()
        phases = [t['phase'] for t in trials.data]
        statuses = [t['status'] for t in trials.data]
        
        print(f"\n✅ {drug_name}:")
        print(f"   • {len(trial_ids)} trials linked")
        print(f"   • Phases: {', '.join(sorted(set(phases)))}")
        print(f"   • Sample NCT IDs: {', '.join(trial_ids[:3])}")
    else:
        print(f"\n⚠️  {drug_name}: Still 0 trials (unexpected!)")

print("\n" + "=" * 60)
