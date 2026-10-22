"""Validate and package Step 5B-C1. Never calculates empirical endpoints."""
from __future__ import annotations
import csv, hashlib, json, subprocess, sys, zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent; ROOT=HERE.parent
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def run(*args):
 p=subprocess.run([sys.executable,*map(str,args)],cwd=ROOT,text=True,capture_output=True)
 if p.returncode: raise SystemExit(p.stdout+'\n'+p.stderr)
 return p.stdout.strip()
def main():
 run(HERE/'independent_synthetic_validator.py')
 dry=run(HERE/'analysis_interface.py','--dry-run','--coordinates',ROOT/'chavi_analysis_ds007116_step5ba_clean_rebuild_20261001'/'primary_vf_transformed_long.csv','--source',ROOT/'chavi_analysis_ds007116_step5ba_clean_rebuild_20261001'/'primary_vf_source_rows.csv','--model','M0','--scale','MAD','--stratum','primary_vf')
 d=json.loads(dry); assert d['empirical_estimands_calculated'] is False and d['coordinate_validation']['participants']==52
 tests=json.loads((HERE/'synthetic_test_results.json').read_text(encoding='utf-8'));assert tests['status']=='PASS'
 protected=json.loads((HERE/'protected_input_hash_comparison.json').read_text(encoding='utf-8'));assert protected['status']=='PASS'
 schemas=json.loads((HERE/'empty_planned_output_schemas.json').read_text(encoding='utf-8'))
 for name in schemas['files']:
  with open(HERE/'empty_planned_outputs'/name,newline='',encoding='utf-8') as f: assert sum(1 for _ in csv.reader(f))==1
 verdict=json.loads((HERE/'readiness_verdict.json').read_text(encoding='utf-8'));verdict['gates']['independent_synthetic_tests']='PASS';verdict['synthetic_tests']={'passed':tests['tests_passed'],'total':tests['tests_total']};verdict['dry_run']=d
 (HERE/'readiness_verdict.json').write_text(json.dumps(verdict,indent=2,sort_keys=True)+'\n',encoding='utf-8')
 package_check={'status':'PASS','empirical_outcome_rows':0,'synthetic_tests_passed':tests['tests_passed'],
  'dry_run_participants':d['coordinate_validation']['participants'],'protected_files_checked':protected['files_checked'],
  'empty_schema_files_checked':len(schemas['files']),'contract_sha256':sha(HERE/'empirical_analysis_contract.json')}
 (HERE/'package_verification.json').write_text(json.dumps(package_check,indent=2,sort_keys=True)+'\n',encoding='utf-8')
 fields=['path','bytes','sha256','role'];rows=[]
 for p in sorted(HERE.rglob('*')):
  if not p.is_file() or p.name in {'artifact_manifest.csv'} or '__pycache__' in p.parts:continue
  rel=p.relative_to(HERE).as_posix();role='empty_planned_schema' if rel.startswith('empty_planned_outputs/') else 'deliverable'
  rows.append({'path':rel,'bytes':p.stat().st_size,'sha256':sha(p),'role':role})
 with open(HERE/'artifact_manifest.csv','w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
 zip_path=ROOT/(HERE.name+'.zip')
 with zipfile.ZipFile(zip_path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in sorted(HERE.rglob('*')):
   if p.is_file() and '__pycache__' not in p.parts:z.write(p,(Path(HERE.name)/p.relative_to(HERE)).as_posix())
 digest=sha(zip_path);(ROOT/(zip_path.name+'.sha256.txt')).write_text(digest+'  '+zip_path.name+'\n',encoding='ascii')
 with zipfile.ZipFile(zip_path) as z: bad=z.testzip();members=len(z.infolist())
 verification={'status':'PASS' if bad is None else 'FAIL','zip':zip_path.name,'zip_sha256':digest,'members':members,'bad_member':bad}
 (ROOT/(zip_path.name+'.verification.json')).write_text(json.dumps(verification,indent=2,sort_keys=True)+'\n',encoding='utf-8')
 print(json.dumps({'status':'PASS','tests':tests['tests_total'],'dry_run_participants':52,'zip':zip_path.name,'zip_sha256':digest},sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
