"""Mutation tests: valid controls must pass and corruptions must fail."""
from pathlib import Path
import copy,csv,json,sys
import numpy as np
from simulation_core import make_plan,TARGET_IDS,AUX_IDS
from validation_rules import *
BASE=Path(__file__).resolve().parent; rows=[]
tw=np.ones(52,dtype=int);aw=np.ones(57,dtype=int);base=make_plan(tw,aw)
def check(cid,name,control,corrupt,expected):
    control_ok=False; rejected=False;reason=''
    try: control(); control_ok=True
    except Exception as e: reason='control failed: '+str(e)
    try: corrupt()
    except Exception as e: rejected=True;reason=str(e)
    status='PASS' if control_ok and rejected and expected in reason else 'FAIL'
    rows.append({'check_id':cid,'mutation':name,'control_accepted':control_ok,'corruption_rejected':rejected,'expected_reason':expected,'actual_reason':reason,'status':status})
check('C1','missing eligible identity',lambda:validate_plan(copy.deepcopy(base)),lambda:validate_plan((lambda p:(p['target_analysis'].pop(TARGET_IDS[0]),p)[1])(copy.deepcopy(base))),'omitted or added identities')
check('C2','extra identity',lambda:validate_plan(copy.deepcopy(base)),lambda:validate_plan((lambda p:(p['auxiliary_draw'].__setitem__('EXTRA',0),p)[1])(copy.deepcopy(base))),'omitted or added identities')
check('C3','held-out target leakage',lambda:validate_plan(copy.deepcopy(base)),lambda:validate_plan((lambda p:(p['target_fit_by_fold']['0'].__setitem__(TARGET_IDS[0],1),p)[1])(copy.deepcopy(base))),'target fit multiplicity mismatch')
check('C4','auxiliary map differs in one fold',lambda:validate_plan(copy.deepcopy(base)),lambda:validate_plan((lambda p:(p['auxiliary_fit_by_fold']['0'].__setitem__(AUX_IDS[0],2),p)[1])(copy.deepcopy(base))),'auxiliary fit multiplicity mismatch')
check('C5','independently resampled visits',lambda:validate_plan(copy.deepcopy(base)),lambda:validate_plan((lambda p:(p['visit_multiplicity'].__setitem__(TARGET_IDS[0],0),p['visit_multiplicity'].__setitem__(TARGET_IDS[1],2),p)[2])(copy.deepcopy(base))),'independently sampled visits')
check('C6','unsupported coordinate converted to zero',lambda:validate_support_result(['yes','no'],[1.0,None]),lambda:validate_support_result(['yes','no'],[1.0,0.0]),'unsupported coordinate assigned numerical value')
check('C7','basic interval wrong point center',lambda:validate_basic_interval(2,1,3,1,3),lambda:validate_basic_interval(2,1,3,3,5),'wrong point estimate')
check('C8','499-draw false tail eligibility',lambda:validate_eligibility(999,999,True,True,True),lambda:validate_eligibility(499,499,True,True,True),'499 draws')
check('C9','fabricated S6/MAD coverage',lambda:validate_structural_coverage('S6','MAD',False,None),lambda:validate_structural_coverage('S6','MAD',False,0.95),'structural S6/MAD')
with (BASE/'independent_corruption_checks.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
out={'status':'PASS' if all(r['status']=='PASS' for r in rows) else 'FAIL','checks':len(rows),'passed':sum(r['status']=='PASS' for r in rows)}
(BASE/'independent_corruption_checks.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out))
if out['status']!='PASS': raise SystemExit(1)
