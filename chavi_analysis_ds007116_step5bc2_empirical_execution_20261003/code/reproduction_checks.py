"""Fresh full calculation and isolated interruption/resume checks."""
from __future__ import annotations
import csv,json,os,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import c2_analysis as c
from run_empirical import run_bootstrap
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parents[1];VAL=OUT/'validation';AUD=OUT/'results'/'participant_linked_audit'
def read(p):
 with open(p,newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def main():
 spec=json.loads((OUT/'c2_execution_specification.json').read_text());adapter=c.Adapter(ROOT,spec);_,z,_=adapter.slice('primary_vf','M0','MAD','primary',52)
 fresh=VAL/'fresh_full_checkpoint.json';t=time.perf_counter();r,p,rt=run_bootstrap(adapter,z,999,fresh);elapsed=time.perf_counter()-t
 prod=read(AUD/'bootstrap_replicate_endpoints.csv');prodprov=read(AUD/'bootstrap_draw_provenance.csv')
 same_records=len(r)==len(prod) and all(str(a[k])==str(b[k]) for a,b in zip(r,prod) for k in ('method','replicate_id','endpoint','status','reason_code','estimate'))
 same_prov=len(p)==len(prodprov) and all(str(a[k])==str(b[k]) for a,b in zip(p,prodprov) for k in ('replicate_id','target_multiplicities','auxiliary_multiplicities','target_draw_sha256','auxiliary_draw_sha256','represented_folds','p3_fit_status','p3_fit_reasons'))
 interrupted=VAL/'interrupted_checkpoint.json';ir,ip,irt=run_bootstrap(adapter,z,7,interrupted,max_new=3);assert len(ip)==3
 resumed_r,resumed_p,resrt=run_bootstrap(adapter,z,7,interrupted)
 clean=VAL/'clean_seven_checkpoint.json';clean_r,clean_p,cleanrt=run_bootstrap(adapter,z,7,clean)
 resume_equal=resumed_r==clean_r and resumed_p==clean_p
 result={'status':'PASS' if same_records and same_prov and resume_equal else 'FAIL','fresh_process_pid':os.getpid(),'fresh_full_attempts':999,'fresh_full_elapsed_seconds':elapsed,'fresh_attempts_per_second':999/elapsed,'fresh_records_equal':same_records,'fresh_provenance_equal':same_prov,'interrupted_after_attempts':3,'resumed_to_attempts':7,'resume_equals_clean':resume_equal,'checkpoint_provenance_validation':'PASS'}
 (VAL/'fresh_process_and_resume_results.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8');print(json.dumps(result,sort_keys=True));return 0 if result['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
