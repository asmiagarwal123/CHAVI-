from __future__ import annotations
import csv, hashlib, json, re, zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parents[1]
C2=ROOT/'chavi_analysis_ds007116_step5bc2_empirical_execution_20261003/results/public_aggregate'
B3=ROOT/'chavi_analysis_ds007116_step5bb3r_validation_repair_20261002'
ZIP=ROOT/f'{OUT.name}.zip'
def digest(p):
 h=hashlib.sha256();
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()
def rows(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def chk(name,ok,evidence,detail=''):return {'check':name,'status':'PASS' if ok else 'FAIL','evidence':evidence,'detail':detail}
def main():
 checks=[]; m=(OUT/'CHAVI_MANUSCRIPT_DRAFT.md').read_text(encoding='utf-8')
 required=['CHAVI_MANUSCRIPT_DRAFT.md','ABSTRACT_AND_CONTRIBUTION_STATEMENT.md','MEASUREMENT_METADATA_EVIDENCE.md','C3_PUBLICATION_STATUS_CORRECTION.md','MANUSCRIPT_CLAIM_SOURCE_MATRIX.csv','references.bib','TABLE_AND_FIGURE_MAP.md','REVIEWER_RISK_AND_REVISION_LOG.md','README.md','input_manifest.csv']
 checks.append(chk('required_deliverables',all((OUT/x).exists() for x in required),'C4 root'))
 checks.append(chk('c3_zip_hash',digest(ROOT/'chavi_analysis_ds007116_step5bc3_scientific_synthesis_20261003.zip')=='f3239b074638e4529988000f0bc5b39c46f41dc0372a93e377982809bac82c04','C3 ZIP SHA-256'))
 pts=rows(C2/'endpoint_estimates.csv'); ints=rows(C2/'primary_bootstrap_intervals.csv')
 values=[f'{float(r["estimate"]):.6f}' for r in pts]+[f'{float(r["lower"]):.6f}' for r in ints]+[f'{float(r["upper"]):.6f}' for r in ints]
 checks.append(chk('all_c2_headline_values_traceable',len(pts)==18 and len(ints)==12 and all(v in m for v in values),'C2 endpoint_estimates.csv and primary_bootstrap_intervals.csv',f'points={len(pts)} intervals={len(ints)}'))
 sim=rows(B3/'confirmatory_performance_summary_repaired.csv'); index={(r['scenario_id'],r['scale_method'],r['endpoint'],r['method'],r['interval_family']):r for r in sim}
 anchors=[index[('S1','MAD','rms_shape_displacement','P2_fixed_transform','percentile')],index[('S1','MAD','rms_shape_displacement','P3_joint_unstratified','percentile')],index[('S5','MAD','rms_shape_displacement','P2_fixed_transform','percentile')],index[('S5','MAD','rms_shape_displacement','P3_joint_unstratified','percentile')]]
 checks.append(chk('b3r_confirmatory_anchors',float(anchors[0]['coverage_available'])==.803 and float(anchors[1]['coverage_available'])==.9175 and int(anchors[2]['available_intervals'])==1994 and int(anchors[3]['available_intervals'])==1260 and 'exploratory' in m,'B3-R confirmatory_performance_summary_repaired.csv','S1/S5 anchors plus pilot boundary'))
 checks.append(chk('published_descriptor_correction','10.1038/s41597-026-08095-1' in m and 'Scientific Data' in m and 'preprint' not in m.lower(),'manuscript and correction note','preprint label excluded from manuscript'))
 pattern=re.compile(r'\bsub-\d+\b',re.I); hits=[]
 for p in OUT.rglob('*'):
  if p.is_file() and p.suffix.lower() in {'.md','.csv','.json','.bib','.py'} and pattern.search(p.read_text(encoding='utf-8',errors='ignore')):hits.append(p.relative_to(OUT).as_posix())
 checks.append(chk('public_privacy_scan',not hits,'C4 text data and code',str(hits)))
 figok=True
 for name in ['figure1_primary_intervals.svg','figure1_primary_intervals.pdf','figure1_primary_intervals.png','figure2_simulation_tradeoffs.svg','figure2_simulation_tradeoffs.pdf','figure2_simulation_tradeoffs.png','figure3_sensitivity_estimates.svg','figure3_sensitivity_estimates.pdf','figure3_sensitivity_estimates.png']:
  figok &= digest(OUT/'figures'/name)==digest(ROOT/'chavi_analysis_ds007116_step5bc3_scientific_synthesis_20261003/figures'/name)
 checks.append(chk('figures_unchanged_from_validated_c3',figok,'C3 and C4 figure SHA-256 comparisons'))
 status='PASS' if all(c['status']=='PASS' for c in checks) else 'FAIL'
 valid=OUT/'validation';valid.mkdir(exist_ok=True)
 (valid/'manuscript_checks.json').write_text(json.dumps({'overall_status':status,'automated_checks':checks,'scientific_judgment_note':'Automated tracing does not replace peer review or author approval.'},indent=2)+'\n',encoding='utf-8')
 if status!='PASS':raise SystemExit(status)
 manifest=[]
 for p in sorted(x for x in OUT.rglob('*') if x.is_file() and x.name!='output_manifest.csv'):
  manifest.append({'relative_path':p.relative_to(OUT).as_posix(),'size_bytes':p.stat().st_size,'sha256':digest(p)})
 with (OUT/'output_manifest.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=['relative_path','size_bytes','sha256']);w.writeheader();w.writerows(manifest)
 with zipfile.ZipFile(ZIP,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in sorted(x for x in OUT.rglob('*') if x.is_file()):z.write(p,f'{OUT.name}/{p.relative_to(OUT).as_posix()}')
 h=digest(ZIP);bad=zipfile.ZipFile(ZIP).testzip()
 (ROOT/f'{ZIP.name}.sha256.txt').write_text(f'{h}  {ZIP.name}\n',encoding='ascii')
 (ROOT/f'{ZIP.name}.verification.json').write_text(json.dumps({'zip':ZIP.name,'sha256':h,'zip_test_passed':bad is None},indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'status':status,'zip_sha256':h,'zip_test_passed':bad is None}))
if __name__=='__main__':main()

