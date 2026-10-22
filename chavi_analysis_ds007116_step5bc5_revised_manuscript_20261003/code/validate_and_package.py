import csv,hashlib,json,zipfile,re
from pathlib import Path
R=Path(__file__).resolve().parents[2]; O=Path(__file__).resolve().parents[1]; Z=R/(O.name+'.zip')
def h(p):
 x=hashlib.sha256();x.update(p.read_bytes());return x.hexdigest()
def ck(n,v,e):return {'check':n,'status':'PASS' if v else 'FAIL','evidence':e}
m=(O/'CHAVI_MANUSCRIPT_REVISED.md').read_text(); checks=[]
checks+=[ck('C4 hash',h(R/'chavi_analysis_ds007116_step5bc4_manuscript_draft_20261003.zip')=='cdd4ae91183cf18b5fdc95132ca5cb93fd99f923da33c5406d487482f6ecc5fb','C4 ZIP'),ck('all endpoints',all(x in (O/'supplementary_tables/confirmatory_all_endpoint_tradeoffs.csv').read_text() for x in ['ICC(A,1)','Mean level change','RMS centered shape displacement']),'supplementary table'),ck('privacy',not any(re.search(r'\bsub-\d+\b',p.read_text(errors='ignore'),re.I) for p in O.rglob('*') if p.is_file() and p.suffix in ['.md','.csv','.py','.bib']),'C5 text scan'),ck('narrow route','complete resampling procedures' in m and 'pure reference-variance component' in m,'revised manuscript')]
s='PASS' if all(x['status']=='PASS' for x in checks) else 'FAIL';(O/'validation').mkdir(exist_ok=True);(O/'validation'/'checks.json').write_text(json.dumps({'overall':s,'automated_checks':checks,'scientific_judgment':'Route B is an interpretive reviewer judgment, not an automated result.'},indent=2));
if s!='PASS':raise SystemExit(s)
files=[p for p in O.rglob('*') if p.is_file() and p.name!='output_manifest.csv'];
with (O/'output_manifest.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=['path','sha256']);w.writeheader();w.writerows({'path':p.relative_to(O).as_posix(),'sha256':h(p)} for p in files)
with zipfile.ZipFile(Z,'w',zipfile.ZIP_DEFLATED) as z:
 for p in O.rglob('*'):
  if p.is_file():z.write(p,O.name+'/'+p.relative_to(O).as_posix())
(R/(Z.name+'.sha256.txt')).write_text(h(Z)+'  '+Z.name+'\n');(R/(Z.name+'.verification.json')).write_text(json.dumps({'zip_test_passed':zipfile.ZipFile(Z).testzip() is None,'sha256':h(Z)},indent=2));print(s,h(Z))

