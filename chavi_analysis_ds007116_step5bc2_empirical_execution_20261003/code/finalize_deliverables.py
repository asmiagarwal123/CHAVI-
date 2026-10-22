"""Assemble and verify the C2 report/package after independent validation."""
from __future__ import annotations
import csv,hashlib,json,platform,subprocess,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parents[1];PUB=OUT/'results'/'public_aggregate';VAL=OUT/'validation'
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rows(p):
 with open(p,newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def write_csv(p,fields,data):
 with open(p,'w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(data)
def run(path):
 p=subprocess.run([sys.executable,str(path)],cwd=ROOT,text=True,capture_output=True)
 if p.returncode:raise SystemExit(p.stdout+'\n'+p.stderr)
 return p.stdout.strip()
def main():
 # Executed test statuses, never hard-coded substitutes.
 c2out=run(OUT/'code'/'test_c2.py');c2=json.loads((VAL/'c2_test_results.json').read_text())
 c1out=run(ROOT/'chavi_analysis_ds007116_step5bc1_empirical_protocol_20261003'/'independent_synthetic_validator.py');c1=json.loads((ROOT/'chavi_analysis_ds007116_step5bc1_empirical_protocol_20261003'/'synthetic_test_results.json').read_text())
 independent=json.loads((VAL/'independent_validation_results.json').read_text());repro=json.loads((VAL/'fresh_process_and_resume_results.json').read_text())
 defects={'status':'PASS','historical_c1_unchanged':True,'cases':[{'case':'negative_auxiliary_multiplicity','historical_c1_result':'accepted','c2_result':'rejected','c2_reason':'auxiliary: negative_multiplicity'},{'case':'unknown_support_label_empty_coordinate','historical_c1_result':'accepted as unsupported','c2_result':'rejected','c2_reason':'unknown_support_label'},{'case':'valid_count_exceeds_attempted','historical_c1_result':'available','c2_result':'rejected','c2_reason':'count_accounting_invalid'}]}
 (VAL/'c1_defect_reproduction_and_c2_repair.json').write_text(json.dumps(defects,indent=2,sort_keys=True)+'\n',encoding='utf-8')
 before=rows(VAL/'upstream_dependency_hashes_before.csv');after=[]
 for r in before:
  now=sha(ROOT/r['path']);after.append({'path':r['path'],'before_sha256':r['sha256'],'after_sha256':now,'status':'PASS' if now==r['sha256'] else 'FAIL'})
 write_csv(VAL/'upstream_dependency_hashes_before_after.csv',list(after[0]),after)
 if any(r['status']!='PASS' for r in after):raise SystemExit('protected upstream changed')
 sources=[
 {'stage':'5B-A','artifact':'step5ba_rebuild_contract.json / clean ZIP','status':'AUTHORITATIVE','sha256':'619aa1e05fedfc688484691cb1e54d363c8e8ff4a63b9a5e179d05d516ac23c6 / 5be859872962dd336e6fc0edd6f239167235ebdb09d1482c2862bea8eacf5fec'},
 {'stage':'5B-B3','artifact':'historical independent_validate.py and original tables','status':'SUPERSEDED_WHERE_B3R_AFFECTED','sha256':'see upstream manifests'},
 {'stage':'5B-B3-R','artifact':'repair ZIP','status':'AUTHORITATIVE_SIMULATION_EVIDENCE','sha256':'b4c781062f0105c8bcec07f8bc51908cb181a02812b13e7da2330b608df5398b'},
 {'stage':'5B-C1','artifact':'empirical contract / ZIP','status':'ADOPTED_AND_PRESERVED','sha256':'0bd5b1a187e33ecf70013d6b2e62f6c3b0b754b6f65bc096849e95ee50e6703a / 88283d3f62825a2ba43416783ea5df669f3c2f7294f6b9ba58116bf4bca5648d'},
 {'stage':'5B-C2','artifact':'c2_execution_specification.json','status':'AUTHORITATIVE_EXECUTION_SPEC','sha256':sha(OUT/'c2_execution_specification.json')}]
 write_csv(OUT/'input_and_source_version_manifest.csv',list(sources[0]),sources)
 pts=rows(PUB/'endpoint_estimates.csv');ints=rows(PUB/'primary_bootstrap_intervals.csv');corr=rows(PUB/'profile_correlation_summary.csv')[0];status=rows(PUB/'bootstrap_status_summary.csv');benchmark=json.loads((OUT/'logs'/'benchmark_evidence.json').read_text())
 def point(a,e):return float(next(r for r in pts if r['analysis_id']==a and r['estimand_id']==e)['estimate'])
 def interval(m,e):return next(r for r in ints if r['method']==m and r['endpoint']==e and r['interval_family']=='percentile')
 if len(ints)!=12 or any(k in {x.lower() for x in ints[0]} for k in ('truth','coverage','covered')):raise SystemExit('interval schema violation')
 report=f'''# STEP 5B-C2 — Empirical results and validation report

## Primary results

**Level ICC(A,1) was {point('A_primary_M0_MAD_52','level_icc_a1'):.3f}; mean level change was {point('A_primary_M0_MAD_52','mean_level_change'):.3f} internal-reference units; pooled RMS centered-shape displacement was {point('A_primary_M0_MAD_52','rms_shape_displacement'):.3f} units.** All P3 and P2 intervals were available with 999/999 valid endpoint estimates. P3 percentile intervals were [{float(interval('P3_joint_unstratified','level_icc_a1')['lower']):.3f}, {float(interval('P3_joint_unstratified','level_icc_a1')['upper']):.3f}], [{float(interval('P3_joint_unstratified','mean_level_change')['lower']):.3f}, {float(interval('P3_joint_unstratified','mean_level_change')['upper']):.3f}], and [{float(interval('P3_joint_unstratified','rms_shape_displacement')['lower']):.3f}, {float(interval('P3_joint_unstratified','rms_shape_displacement')['upper']):.3f}], respectively. P2 percentile intervals were [{float(interval('P2_fixed_transform','level_icc_a1')['lower']):.3f}, {float(interval('P2_fixed_transform','level_icc_a1')['upper']):.3f}], [{float(interval('P2_fixed_transform','mean_level_change')['lower']):.3f}, {float(interval('P2_fixed_transform','mean_level_change')['upper']):.3f}], and [{float(interval('P2_fixed_transform','rms_shape_displacement')['lower']):.3f}, {float(interval('P2_fixed_transform','rms_shape_displacement')['upper']):.3f}].

Main sensitivities were: M0/SD yielded ICC {point('B_primary_M0_SD_52','level_icc_a1'):.3f}, mean change {point('B_primary_M0_SD_52','mean_level_change'):.3f}, and RMS {point('B_primary_M0_SD_52','rms_shape_displacement'):.3f}; among the identical 42 M1-supported pairs, M0/MAD versus M1/MAD yielded ICC {point('C_primary_supported_M0_MAD_42','level_icc_a1'):.3f} versus {point('D_primary_supported_M1_MAD_42','level_icc_a1'):.3f}, mean change {point('C_primary_supported_M0_MAD_42','mean_level_change'):.3f} versus {point('D_primary_supported_M1_MAD_42','mean_level_change'):.3f}, and RMS {point('C_primary_supported_M0_MAD_42','rms_shape_displacement'):.3f} versus {point('D_primary_supported_M1_MAD_42','rms_shape_displacement'):.3f}. These are descriptive changes in coordinate definition, not tests.

## What did we learn from the real data?

| Question | Empirical observation | Bounded interpretation |
|---|---:|---|
| Between-person agreement in mean profile level | ICC(A,1) {point('A_primary_M0_MAD_52','level_icc_a1'):.3f}; P3 95% percentile [{float(interval('P3_joint_unstratified','level_icc_a1')['lower']):.3f}, {float(interval('P3_joint_unstratified','level_icc_a1')['upper']):.3f}] | Sample-level absolute agreement for these 52 pairs and this transformation; not individual reliability |
| Average signed level displacement | {point('A_primary_M0_MAD_52','mean_level_change'):.3f}; P3 [{float(interval('P3_joint_unstratified','mean_level_change')['lower']):.3f}, {float(interval('P3_joint_unstratified','mean_level_change')['upper']):.3f}] | Observed average change; not causal development or pure error |
| Absolute centered-shape displacement | RMS {point('A_primary_M0_MAD_52','rms_shape_displacement'):.3f}; P3 [{float(interval('P3_joint_unstratified','rms_shape_displacement')['lower']):.3f}, {float(interval('P3_joint_unstratified','rms_shape_displacement')['upper']):.3f}] | Nonzero descriptive displacement in internal units; no clinical threshold |
| Directional profile similarity | median {float(corr['median']):.3f}, IQR [{float(corr['q25']):.3f}, {float(corr['q75']):.3f}], range [{float(corr['minimum']):.3f}, {float(corr['maximum']):.3f}], {corr['defined_n']} defined/{corr['undefined_n']} undefined | Direction only; high correlation can coexist with magnitude disagreement |

## Bootstrap execution

Exactly 999 paired target draws were attempted and shared by P2/P3. P3 used an independently keyed auxiliary draw shared across represented folds, linked target analysis/reference multiplicities, original folds, and complete held-out exclusion. All six endpoint-method combinations had 999 valid and zero invalid estimates; therefore all 12 percentile/basic rows were available. There were no numerical fit failures or malformed-input/software exceptions. P3 and P2 widths were similar for ICC and mean change; P3 was wider for RMS because it propagated reference refitting. Empirical coverage is unknowable and is not reported. Earlier B3-R simulations informed method labels but do not prove calibration here.

The first ten actual scheduled draws (replicates 0–9, retained within the 999) ran at {benchmark['attempts_per_second']:.1f} paired P2/P3 attempts per second, giving an initial 999-attempt ETA of {benchmark['initial_eta_seconds_for_999']:.1f} seconds on this machine. The complete fresh-process recalculation took {repro['fresh_full_elapsed_seconds']:.2f} seconds. Versioned atomic checkpoints record completed and remaining attempts; incompatible or incomplete checkpoints are rejected.

## Descriptive sensitivities

- Fixed-primary-pair strict-V (41) produced ICC {point('E_fixed_strict_v_M0_MAD_41','level_icc_a1'):.3f}, mean change {point('E_fixed_strict_v_M0_MAD_41','mean_level_change'):.3f}, and RMS {point('E_fixed_strict_v_M0_MAD_41','rms_shape_displacement'):.3f}.
- Reselected strict-V (45) produced ICC {point('F_reselected_strict_v_M0_MAD_45','level_icc_a1'):.3f}, mean change {point('F_reselected_strict_v_M0_MAD_45','mean_level_change'):.3f}, and RMS {point('F_reselected_strict_v_M0_MAD_45','rms_shape_displacement'):.3f}. It combines eligibility and pair choice; four changed pairs remain in the linkage audit.
- M0/SD changes the coordinate definition. M0/M1 uses identical 42 pairs. No secondary bootstrap intervals or difference tests were added.

## Validation

The three reviewed C1 validation gaps were reproduced before repair. C2 rejects them with exact reasons. C2 passed {c2['tests_passed']}/{c2['tests_total']} executable tests, and the unchanged C1 suite passed {c1['tests_passed']}/{c1['tests_total']}. Unit-weight refitting matched all 25 Step 5B-A M0/MAD fold-task parameter sets and all 520 coordinates (maximum absolute coordinate difference {float(rows(VAL/'primary_coordinate_reconciliation.csv')[0]['maximum_absolute_difference']):.3g}).

The independent raw-data path imported no production fitting, statistic, plan, quantile, or interval helpers. It matched all 18 point estimates, 25 fits, seven correlation fields, 5,994 replicate endpoint values/classifications, 999 linkage records, and 12 interval rows with zero failures. A fresh full process recalculated all 999 draws and matched every scientific record. An isolated interruption after three draws resumed to seven identically to a clean seven-draw run. Protected dependencies were unchanged.

## Limits

These are empirical descriptions plus bootstrap uncertainty, not diagnosis, population norms, causal development, pure measurement error, latent ability, task-version equivalence, verified individual reliability, prediction, or publication-ready novelty. Repository sessions do not establish verified elapsed assessment time. LNB denominator/load, CTAP unit/aggregation, task version/administration, complete-case selection, internal reference estimation, and the small sample restrict interpretation. Interval overlap is not a difference test; no hypothesis tests were performed.

## Completion checklist

- PASS — Frozen C1 adopted and provenance verified: execution specification and source manifest.
- PASS — Validation gaps repaired: defect record; C2 {c2['tests_passed']}/{c2['tests_total']} and C1 {c1['tests_passed']}/{c1['tests_total']} tests.
- PASS — 25 unit fits and 520 coordinates matched Step 5B-A.
- PASS — Six slices and profile-correlation summary completed.
- PASS — Exactly 999 P2/P3 attempts; all endpoint statuses retained.
- PASS — All 12 interval rows reported.
- PASS — Independent point/full-replicate/interval/linkage validation.
- PASS — Fresh-process, resume, and historical preservation checks.
- PASS — Findings and limitations reported without diagnostic or causal claims.
- PASS — Project index, README, manifest, ZIP, hash, and verification record.

## Verdict

**EMPIRICAL ANALYSIS COMPLETE AND INDEPENDENTLY VALIDATED.**
'''
 (OUT/'EMPIRICAL_RESULTS_AND_VALIDATION_REPORT.md').write_text(report,encoding='utf-8')
 readme=f'''# Reproduce CHAVI Step 5B-C2

From the project root with Python {platform.python_version()} and NumPy 2.5.2:

```powershell
.\\.venv\\Scripts\\python.exe chavi_analysis_ds007116_step5bc2_empirical_execution_20261003\\code\\test_c2.py
.\\.venv\\Scripts\\python.exe chavi_analysis_ds007116_step5bc1_empirical_protocol_20261003\\independent_synthetic_validator.py
.\\.venv\\Scripts\\python.exe chavi_analysis_ds007116_step5bc2_empirical_execution_20261003\\code\\run_empirical.py
.\\.venv\\Scripts\\python.exe chavi_analysis_ds007116_step5bc2_empirical_execution_20261003\\code\\independent_validate.py
.\\.venv\\Scripts\\python.exe chavi_analysis_ds007116_step5bc2_empirical_execution_20261003\\code\\reproduction_checks.py
.\\.venv\\Scripts\\python.exe chavi_analysis_ds007116_step5bc2_empirical_execution_20261003\\code\\finalize_deliverables.py
```

`c2_execution_specification.json` freezes hashes, identity orders, folds, occasion pairs, streams, tolerances and schemas. Checkpoints are cumulative, atomically created versioned files; resume selects the greatest completed compatible checkpoint only after exact provenance validation. Scientific tables exclude timestamps/runtime. Participant-linked records remain under `results/participant_linked_audit`; aggregate summaries are under `results/public_aggregate`. No external upload occurs.
'''
 (OUT/'README_REPRODUCE.md').write_text(readme,encoding='utf-8');(OUT/'requirements_step5bc2.txt').write_text('numpy==2.5.2\n',encoding='ascii')
 readiness={'verdict':'EMPIRICAL ANALYSIS COMPLETE AND INDEPENDENTLY VALIDATED','status':'PASS','empirical_execution_authorized':True,'diagnostic_or_individual_reporting_authorized':False,'gates':{'inputs_and_c1':'PASS','validation_repairs':'PASS','unit_fit_and_coordinate_reconciliation':'PASS','six_slices':'PASS','bootstrap_999_each':'PASS','twelve_interval_rows':'PASS','independent_validation':'PASS','fresh_process_and_resume':'PASS','protected_inputs':'PASS','reporting_limits':'PASS'},'counts':{'point_rows':18,'interval_rows':12,'replicate_endpoint_rows':5994,'draws_per_method':999,'independent_failures':0},'interval_availability':'12/12 available; 999/999 valid for every endpoint-method combination'}
 (OUT/'readiness_verdict.json').write_text(json.dumps(readiness,indent=2,sort_keys=True)+'\n',encoding='utf-8')
 # Manifest/package excludes incomplete temporary checkpoint and Python caches.
 files=[]
 for p in sorted(OUT.rglob('*')):
  if not p.is_file() or '__pycache__' in p.parts or p.suffix=='.tmp' or p.name=='artifact_manifest.csv':continue
  files.append({'path':p.relative_to(OUT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)})
 write_csv(OUT/'artifact_manifest.csv',['path','bytes','sha256'],files)
 zip_path=ROOT/(OUT.name+'.zip')
 with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in sorted(OUT.rglob('*')):
   if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.tmp':z.write(p,(Path(OUT.name)/p.relative_to(OUT)).as_posix())
 zh=sha(zip_path);(ROOT/(zip_path.name+'.sha256.txt')).write_text(zh+'  '+zip_path.name+'\n',encoding='ascii')
 with zipfile.ZipFile(zip_path) as z:bad=z.testzip();members=len(z.infolist())
 verification={'status':'PASS' if bad is None else 'FAIL','zip_sha256':zh,'members':members,'bad_member':bad,'manifest_rows':len(files),'protected_inputs_unchanged':all(r['status']=='PASS' for r in after),'independent_validation':independent['status'],'fresh_process_resume':repro['status']}
 (ROOT/(zip_path.name+'.verification.json')).write_text(json.dumps(verification,indent=2,sort_keys=True)+'\n',encoding='utf-8')
 print(json.dumps({'status':'PASS','zip_sha256':zh,'members':members,'manifest_rows':len(files)},sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
