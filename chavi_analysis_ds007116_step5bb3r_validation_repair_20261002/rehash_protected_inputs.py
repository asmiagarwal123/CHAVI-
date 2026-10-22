from pathlib import Path
import csv,hashlib,json
BASE=Path(__file__).resolve().parent;ROOT=BASE.parent
before=list(csv.DictReader((BASE/'protected_inputs_before.csv').open(encoding='utf-8')));rows=[]
for r in before:
    p=ROOT/r['relative_path']; exists=p.exists(); size=p.stat().st_size if exists else ''; sha=hashlib.sha256(p.read_bytes()).hexdigest() if exists else ''
    rows.append({**r,'after_exists':exists,'after_size_bytes':size,'after_sha256':sha,'status':'UNCHANGED' if exists and str(size)==r['before_size_bytes'] and sha==r['before_sha256'] else ('MISSING' if not exists else 'CHANGED')})
with (BASE/'protected_inputs_before_after.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
out={'status':'PASS' if all(r['status']=='UNCHANGED' for r in rows) else 'FAIL','rows':len(rows),'unchanged':sum(r['status']=='UNCHANGED' for r in rows),'changed':sum(r['status']=='CHANGED' for r in rows),'missing':sum(r['status']=='MISSING' for r in rows)}
(BASE/'protected_input_rehash_results.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out));raise SystemExit(out['status']!='PASS')
