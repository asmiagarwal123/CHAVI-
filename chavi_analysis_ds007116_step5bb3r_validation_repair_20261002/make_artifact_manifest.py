from pathlib import Path
import csv,hashlib
BASE=Path(__file__).resolve().parent;exclude={'artifact_manifest.csv'};rows=[]
for p in sorted(BASE.rglob('*')):
 if not p.is_file() or '__pycache__' in p.parts or p.name in exclude:continue
 rel=str(p.relative_to(BASE)).replace('\\','/');rows.append({'relative_path':rel,'size_bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
with (BASE/'artifact_manifest.csv').open('w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
print({'manifest_rows':len(rows),'manifested_bytes':sum(int(r['size_bytes']) for r in rows)})
