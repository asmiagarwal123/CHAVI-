import csv, hashlib, json, re, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
C2 = REPO / 'chavi_analysis_ds007116_step5bc2_empirical_execution_20261003' / 'results' / 'public_aggregate'
B3 = REPO / 'chavi_analysis_ds007116_step5bb3r_validation_repair_20261002'
C3 = REPO / 'chavi_analysis_ds007116_step5bc3_scientific_synthesis_20261003'
ZIP = REPO / (ROOT.name + '.zip')

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()
def rows(p):
    with open(p, newline='', encoding='utf-8-sig') as f: return list(csv.DictReader(f))
def result(name, ok, evidence, detail):
    return {'requirement':name, 'status':'PASS' if ok else 'FAIL', 'evidence':evidence, 'observed':detail}

checks=[]
required=['CHAVI_FACULTY_REVIEW_MANUSCRIPT.md','METHODS_AND_REPRODUCIBILITY_SUPPLEMENT.md','JOURNAL_FIT_COMPARISON.md','AUTHOR_DECISIONS_NEEDED.md','PLAIN_LANGUAGE_FACULTY_BRIEF.md','C5_TO_C6_CHANGES.md','references.bib','README.md','figures/CAPTIONS.md','figures/figure1_primary_intervals_data.csv','figures/figure2_simulation_tradeoffs_data.csv','figures/figure3_sensitivity_estimates_data.csv','tables/empirical_all_planned_point_estimates.csv','tables/empirical_primary_intervals.csv','tables/simulation_synthesis_all_prespecified.csv','tables/simulation_failure_reason_summary.csv','tables/confirmatory_all_endpoint_tradeoffs.csv']
checks.append(result('C6 deliverables exist', all((ROOT/x).exists() for x in required), 'package paths listed in required set', f'{sum((ROOT/x).exists() for x in required)}/{len(required)} present'))

# Empirical source values and derived interval widths/ratios, never narrative source
src=rows(C2/'primary_bootstrap_intervals.csv')
need={('P2_fixed_transform','percentile','level_icc_a1'):0.4125909809161544,('P3_joint_unstratified','percentile','level_icc_a1'):0.4065966755874099,('P2_fixed_transform','percentile','mean_level_change'):0.37473104254314465,('P3_joint_unstratified','percentile','mean_level_change'):0.3686955058849172,('P2_fixed_transform','percentile','rms_shape_displacement'):0.38723585344002887,('P3_joint_unstratified','percentile','rms_shape_displacement'):0.5709395336924686}
got={}
for r in src:
    key=(r.get('method'),r.get('interval_family'),r.get('endpoint'))
    if key in need: got[key]=float(r['upper'])-float(r['lower'])
width_ok=all(abs(got.get(k,0)-v)<1e-12 for k,v in need.items())
ratio=got[('P3_joint_unstratified','percentile','rms_shape_displacement')]/got[('P2_fixed_transform','percentile','rms_shape_displacement')]
checks.append(result('C2 unrounded widths and RMS ratio',width_ok and abs(ratio-1.4743973953354241)<1e-12,'C2/results/public_aggregate/primary_bootstrap_intervals.csv',{'widths':{str(k):v for k,v in got.items()},'P3_over_P2_RMS':ratio}))
man=(ROOT/'CHAVI_FACULTY_REVIEW_MANUSCRIPT.md').read_text(encoding='utf-8')
checks.append(result('manuscript empirical values agree with C2 rounding', all(x in man for x in ['0.618912','0.365668','1.001646','47.4%']), 'manuscript Results; C2 endpoint_estimates.csv and primary_bootstrap_intervals.csv','all expected rounded values found'))

# Confirmatory simulation exact count checks from repaired B3-R table
b3rows=rows(B3/'confirmatory_performance_summary_repaired.csv')
def find(s,m,e):
    return [r for r in b3rows if r.get('scenario_id')==s and r.get('method')==m and r.get('endpoint')==e and r.get('scale_method')=='MAD' and r.get('interval_family')=='percentile']
selected=find('S1','P2_fixed_transform','rms_shape_displacement')+find('S1','P3_joint_unstratified','rms_shape_displacement')+find('S5','P2_fixed_transform','rms_shape_displacement')+find('S5','P3_joint_unstratified','rms_shape_displacement')
obs=[(r.get('scenario_id'),r.get('method'),r.get('attempted_outer'),r.get('available_intervals'),str(round(float(r.get('available_and_covered_all'))*float(r.get('attempted_outer'))))) for r in selected]
expected=[('S1','P2_fixed_transform','2000','2000','1606'),('S1','P3_joint_unstratified','2000','2000','1835'),('S5','P2_fixed_transform','2000','1994','1832'),('S5','P3_joint_unstratified','2000','1260','1205')]
checks.append(result('repaired B3-R confirmatory counts',obs==expected,'B3-R/confirmatory_performance_summary_repaired.csv',obs))

# copied aggregates are byte-identical to their stated C3/C5 sources
copied=['empirical_all_planned_point_estimates.csv','empirical_primary_intervals.csv','empirical_profile_correlation_summary.csv','simulation_synthesis_all_prespecified.csv','simulation_failure_reason_summary.csv']
same=all(sha(ROOT/'tables'/x)==sha(C3/'aggregate_tables'/x) for x in copied)
checks.append(result('copied C3 public aggregates preserve source bytes',same,'C6/tables and C3/aggregate_tables', {x:sha(ROOT/'tables'/x) for x in copied}))

# reader and privacy checks, after archive exists
manifest_paths=[str(p.relative_to(ROOT)).replace('\\','/') for p in ROOT.rglob('*') if p.is_file() and 'output_manifest.csv' not in str(p)]
bad_paths=[]
for p in ROOT.rglob('*.md'):
    t=p.read_text(encoding='utf-8',errors='replace')
    if re.search(r'[A-Za-z]:\\',t): bad_paths.append(str(p.relative_to(ROOT)))
checks.append(result('no Windows paths in reader-facing Markdown',not bad_paths,'all C6 Markdown files',bad_paths))
public='\n'.join(p.read_text(encoding='utf-8',errors='replace') for p in ROOT.rglob('*') if p.is_file() and p.suffix.lower() in ['.md','.csv','.bib','.json'])
ids=re.findall(r'\bsub-[A-Za-z0-9]+\b|\bparticipant[_ -]?id\s*[:=]\s*\S+',public,re.I)
checks.append(result('public outputs lack participant identifiers',not ids,'all text/CSV/JSON/Bib C6 outputs',ids[:10]))
if ZIP.exists():
    with zipfile.ZipFile(ZIP) as z:
        names=set(z.namelist()); bad=z.testzip(); missing=[x for x in required if x not in names]
    checks.append(result('ZIP integrity and cited component presence',bad is None and not missing,str(ZIP.name),{'bad_member':bad,'missing':missing,'members':len(names)}))
else:
    checks.append(result('ZIP integrity and cited component presence',False,'ZIP absent','run pack step first'))

upstreams=['chavi_analysis_ds007116_step5bc1_empirical_protocol_20261003.zip','chavi_analysis_ds007116_step5bc2_empirical_execution_20261003.zip','chavi_analysis_ds007116_step5bb3r_validation_repair_20261002.zip','chavi_analysis_ds007116_step5bc3_scientific_synthesis_20261003.zip','chavi_analysis_ds007116_step5bc5_revised_manuscript_20261003.zip']
checks.append(result('upstream packages preserved and hashed',all((REPO/x).exists() for x in upstreams),'root ZIP artifacts',{x:sha(REPO/x) for x in upstreams if (REPO/x).exists()}))
out={'overall':'PASS' if all(x['status']=='PASS' for x in checks) else 'FAIL','checks':checks}
(ROOT/'validation'/'checks.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out,indent=2))
sys.exit(0 if out['overall']=='PASS' else 1)
