from pathlib import Path
import csv,hashlib,json
BASE=Path(__file__).resolve().parent; ROOT=BASE.parent; B3=ROOT/'chavi_analysis_ds007116_step5bb3_confirmatory_simulation_20261002'
paths=[p for p in B3.rglob('*') if p.is_file()]
paths.append(ROOT/'chavi_analysis_ds007116_step5bb3_confirmatory_simulation_20261002.zip')
paths.append(ROOT/'chavi_analysis_ds007116_step5bb3_confirmatory_simulation_20261002.zip.sha256.txt')
for r in csv.DictReader((B3/'protected_inventory_before.csv').open(encoding='utf-8')):
    p=ROOT/r['relative_path']
    if p.exists() and p not in paths: paths.append(p)
rows=[]
for p in sorted(set(paths)):
    rows.append({'relative_path':str(p.relative_to(ROOT)).replace('\\','/'),'before_size_bytes':p.stat().st_size,'before_sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
with (BASE/'protected_inputs_before.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
print(json.dumps({'protected_files':len(rows),'total_bytes':sum(int(r['before_size_bytes']) for r in rows)}))
