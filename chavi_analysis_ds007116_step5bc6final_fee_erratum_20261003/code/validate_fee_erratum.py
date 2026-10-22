import hashlib, json, re, subprocess, sys
from pathlib import Path

root=Path(__file__).resolve().parents[1]
prior=root.parent/'chavi_analysis_ds007116_step5bc6final_faculty_handoff_20261003'
subprocess.run([sys.executable,str(root/'code'/'validate_c6final.py')],check=False)
p=root/'validation'/'checks.json'; out=json.loads(p.read_text(encoding='utf-8'))
def sha(x):
 h=hashlib.sha256()
 with open(x,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''): h.update(b)
 return h.hexdigest()
def add(name,ok,evidence,observed): out['checks'].append({'requirement':name,'status':'PASS' if ok else 'FAIL','evidence':evidence,'observed':observed})
scientific=['CHAVI_FACULTY_REVIEW_MANUSCRIPT.md','METHODS_AND_REPRODUCIBILITY_SUPPLEMENT.md','references.bib']
scientific += [str(x.relative_to(root)).replace('\\','/') for x in (root/'tables').rglob('*') if x.is_file()]
scientific += [str(x.relative_to(root)).replace('\\','/') for x in (root/'figures').rglob('*') if x.is_file()]
changed=[x for x in scientific if sha(root/x)!=sha(prior/x)]
add('scientific-file preservation against C6-FINAL',not changed,'SHA-256 comparison with C6-FINAL scientific manuscript/supplement/bibliography/tables/figures',{'compared':len(scientific),'changed':changed})
reader=[]
for f in root.rglob('*'):
 if f.is_file() and f.suffix.lower() in ['.md','.csv','.json','.bib'] and f.name not in ['ERRATUM_FROM_C6_FINAL.md','output_manifest.csv','checks.json']:
  if re.search(r'US\$2,382|\b2382\b',f.read_text(encoding='utf-8',errors='replace')): reader.append(str(f.relative_to(root)))
add('superseded PLOS fee absent outside erratum',not reader,'all reader-facing C6-FINAL fee-erratum text files',reader)
err=(root/'ERRATUM_FROM_C6_FINAL.md').read_text(encoding='utf-8')
add('erratum documents source, access date, and uncertainty',all(x in err for x in ['US$2,382','US$2,477','2026-10-03','https://plos.org/fees/','not asserted']), 'ERRATUM_FROM_C6_FINAL.md','all required disclosure terms found')
out['overall']='PASS' if all(c['status']=='PASS' for c in out['checks']) else 'FAIL'
p.write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out,indent=2)); sys.exit(0 if out['overall']=='PASS' else 1)
