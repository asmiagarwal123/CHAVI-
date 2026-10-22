from pathlib import Path
import csv,hashlib
BASE=Path(__file__).resolve().parent
excluded={'milestone_artifact_manifest.csv'}
rows=[]
for p in sorted(BASE.rglob('*')):
 if p.is_file() and p.name not in excluded and p.name not in {'pilot_full.log','pilot_full.err.log'} and 'runtime_checkpoint' not in p.parts and p.name not in {'simulated_outer_datasets.npz'}:
  h=hashlib.sha256(p.read_bytes()).hexdigest(); rows.append({'path':str(p.relative_to(BASE)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':h})
with (BASE/'milestone_artifact_manifest.csv').open('w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['path','bytes','sha256'],lineterminator='\n');w.writeheader();w.writerows(rows)
print(len(rows))
