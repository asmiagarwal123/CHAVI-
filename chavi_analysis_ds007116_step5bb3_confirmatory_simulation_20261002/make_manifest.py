from pathlib import Path
import csv,hashlib
BASE=Path(__file__).resolve().parent; EXCLUDE={'milestone_artifact_manifest.csv'}; OMIT_PREFIX=('runtime',); OMIT_SUFFIX=('.log','.err')
rows=[]
for p in sorted(BASE.rglob('*')):
 if not p.is_file() or p.name in EXCLUDE or any(part in ('runtime','__pycache__') for part in p.relative_to(BASE).parts) or p.name.endswith(OMIT_SUFFIX): continue
 rows.append({'path':str(p.relative_to(BASE)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
with (BASE/'milestone_artifact_manifest.csv').open('w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['path','bytes','sha256'],lineterminator='\n');w.writeheader();w.writerows(rows)
print(len(rows))
