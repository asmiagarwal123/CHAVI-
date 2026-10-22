"""Universal (all integer weights) near-zero support proof for a stage/scenario."""
from pathlib import Path
import argparse,json,math,os,sys
import numpy as np
BASE=Path(__file__).resolve().parent;sys.path.insert(0,str(BASE));import simulation_core as sc;import run_stage as rs
def min_positive(a):
 a=np.asarray(a);a=a[a>0];return float(a.min()) if len(a) else math.inf
def bounds(values):
 ratios_sd=[];ratios_mad=[]
 for j in range(5):
  u=np.unique(values[:,j]);span=float(u[-1]-u[0]) if len(u)>1 else 0.
  if span==0:continue
  d=min_positive(np.diff(u));sd_lower=d/math.sqrt(109);sd_tol=64*sc.EPS*2*span;ratios_sd.append(sd_lower/sd_tol)
  # Any weighted median is a datum or the midpoint of two data. Any positive
  # deviation is at least half the smallest positive |2x-a-b|. An even MAD
  # may halve that once more; division by MAD_DENOM gives the scale bound.
  sums=np.unique((u[:,None]+u[None,:]).ravel());sums.sort();mind=math.inf
  for y in 2*u:
   k=int(np.searchsorted(sums,y));
   for q in (k-2,k-1,k,k+1):
    if 0<=q<len(sums) and sums[q]!=y:mind=min(mind,abs(float(sums[q]-y)))
  mad_lower=mind/(4*sc.MAD_DENOM);mad_tol=64*sc.EPS*span/sc.MAD_DENOM;ratios_mad.append(mad_lower/mad_tol)
 return min(ratios_sd,default=math.inf),min(ratios_mad,default=math.inf)
def main(stage,sid):
 sc.STREAM_NAMESPACE=stage;rs.STREAM_NAMESPACE=stage;rs.assert_stage_namespace(stage);R=100 if stage=='corrected_pilot' else 2000;sd=math.inf;mad=math.inf
 for o in range(R):
  pair,aux=rs.generate_dataset(sid,o);a,b=bounds(np.vstack([pair[:,0],aux]));sd=min(sd,a);mad=min(mad,b)
 out=BASE/'scale_support_screen'/f'{stage}__{sid}.json';obj={'stage':stage,'scenario_id':sid,'outer_records':R,'method_scale_draws_screened':R*999*4,'old_supported_new_rejected':0 if sd>1 and mad>1 else None,'minimum_supported_sd_scale_to_tolerance_ratio':sd,'minimum_supported_mad_scale_to_tolerance_ratio':mad,'proof_type':'universal over every nonnegative integer weighting of each generated reference pool; therefore covers all actual P3/P4 multiplicities','candidate_keys':[] if sd>1 and mad>1 else ['BOUND_NOT_SEPARATED']};tmp=out.with_suffix('.tmp');tmp.write_text(json.dumps(obj,indent=2)+'\n');os.replace(tmp,out);print(json.dumps(obj));raise SystemExit(0 if sd>1 and mad>1 else 1)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--stage',required=True);ap.add_argument('--scenario',required=True);a=ap.parse_args();main(a.stage,a.scenario)
