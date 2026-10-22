from pathlib import Path
import csv,hashlib,json
BASE=Path(__file__).resolve().parent; ROOT=BASE.parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    old=list(csv.DictReader((ROOT/'chavi_analysis_ds007116_step5bb2_simulation_pilot_20261002/protected_inputs_before.csv').open(encoding='utf-8')))
    paths=[r['relative_path'] for r in old]
    for p in ['chavi_analysis_ds007116_step5bb2_simulation_pilot_20261002.zip','chavi_analysis_ds007116_step5bb2_simulation_pilot_20261002/simulation_execution_contract.json','chavi_analysis_ds007116_step5ba_clean_rebuild_20261001.zip','chavi_analysis_ds007116_step5ba_clean_rebuild_20261001/step5ba_rebuild_contract.json','chavi_analysis_ds007116_step5bb1_profile_protocol_20261001.zip','chavi_analysis_ds007116_step5bb1_profile_protocol_20261001/profile_analysis_specification_recommended.json']:
        if p not in paths: paths.append(p)
    rows=[]
    for rel in paths:
        p=ROOT/rel
        rows.append({'relative_path':rel,'before_exists':p.exists(),'before_size_bytes':p.stat().st_size if p.exists() else '','before_sha256':sha(p) if p.exists() else ''})
    with (BASE/'protected_inventory_before.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print(json.dumps({'rows':len(rows),'missing_before':sum(not r['before_exists'] for r in rows)}))
if __name__=='__main__':main()
