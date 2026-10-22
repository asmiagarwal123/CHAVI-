from pathlib import Path
import csv,hashlib
BASE=Path(__file__).resolve().parent; ROOT=BASE.parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
before=list(csv.DictReader((BASE/'protected_inventory_before.csv').open(encoding='utf-8'))); rows=[]
for r in before:
    p=ROOT/r['relative_path']; ex=p.exists(); after=sha(p) if ex else ''; rows.append({'relative_path':r['relative_path'],'before_exists':r['before_exists'],'after_exists':ex,'before_size_bytes':r['before_size_bytes'],'after_size_bytes':p.stat().st_size if ex else '','before_sha256':r['before_sha256'],'after_sha256':after,'status':'UNCHANGED' if ex and r['before_sha256']==after and str(r['before_size_bytes'])==str(p.stat().st_size) else ('MISSING' if not ex else 'CHANGED')})
with (BASE/'protected_inventory_before_after.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print({'rows':len(rows),'changed':sum(r['status']=='CHANGED' for r in rows),'missing':sum(r['status']=='MISSING' for r in rows)})
