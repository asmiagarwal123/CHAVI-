"""Full-stream old-vs-repaired optimized scale-support screen (no endpoint work)."""
from pathlib import Path
import argparse,json,math,os,sys,time
import numpy as np
BASE=Path(__file__).resolve().parent;sys.path.insert(0,str(BASE));import simulation_core as sc;import run_stage as rs
def flags(pair,aux,W,aw,scale):
 B=len(W);oldbad=np.zeros(B,bool);newbad=np.zeros(B,bool);minratio=math.inf
 for fold in range(5):
  ix=np.flatnonzero(sc.FOLDS==fold);keep=np.flatnonzero(sc.FOLDS!=fold);active=W[:,ix].sum(1)>0;ar=np.flatnonzero(active)
  if not len(ar):continue
  x0=np.vstack([pair[keep,0],aux]);w=np.concatenate([W[ar][:,keep],aw[ar]],1);n=w.sum(1);present=w>0;npres=present.sum(1);x3=np.broadcast_to(x0,(len(ar),)+x0.shape);xmax=np.max(np.where(present[:,:,None],x3,-np.inf),1);xmin=np.min(np.where(present[:,:,None],x3,np.inf),1);span=xmax-xmin
  if scale=='SD':
   center=np.einsum('bn,nj->bj',w,x0)/n[:,None];s=np.sqrt(np.einsum('bn,bnj->bj',w,(x3-center[:,None,:])**2)/(n[:,None]-1));old=np.isfinite(s)&(s>0);tol=64*sc.EPS*np.maximum(span,np.abs(s));new=old&(npres[:,None]>=2)&(s>tol);rat=np.divide(s,tol,out=np.full_like(s,np.inf),where=old&(tol>0));minratio=min(minratio,float(np.min(rat)))
  else:
   # Exact rank/count prefilter: avoid sorting 999 identical value grids and
   # sort deviations only if a scale could lie within the 64-epsilon band.
   med=np.empty((len(ar),5));lo=(n-1)//2;hi=n//2
   for j in range(5):
    order=np.argsort(x0[:,j],kind='stable');cs=np.cumsum(w[:,order],1);il=np.argmax(cs>=lo[:,None]+1,1);ih=np.argmax(cs>=hi[:,None]+1,1);xs=x0[order,j];med[:,j]=np.where(n%2,xs[ih],(xs[il]+xs[ih])/2)
   dev=np.abs(x3-med[:,None,:]);zcount=np.sum(w[:,:,None]*(dev==0),1);old=zcount<hi[:,None]+1;tol=64*sc.EPS*span;limit=sc.MAD_DENOM*tol;close=np.sum(w[:,:,None]*(dev<=2*limit[:,None,:]),1);possible=old&(close>=hi[:,None]+1);new=old.copy()
   for rr,j in zip(*np.where(possible)):
    expanded=np.repeat(dev[rr,:,j],w[rr]);raw=float(np.median(expanded));new[rr,j]=(raw/sc.MAD_DENOM)>tol[rr,j]
   minratio=math.nan
  oldbad[ar]|=~np.all(old,1);newbad[ar]|=~np.all(new,1)
 return oldbad,newbad,minratio
def main(stage,sid):
 sc.STREAM_NAMESPACE=stage;rs.STREAM_NAMESPACE=stage;rs.assert_stage_namespace(stage);R=100 if stage=='corrected_pilot' else 2000;out=BASE/'scale_support_screen'/f'{stage}__{sid}.json';out.parent.mkdir(exist_ok=True);candidates=[];min_sd_ratio=math.inf;t=time.time()
 for o in range(R):
  pair,aux=rs.generate_dataset(sid,o);tw,aw,sw=rs.draw_multiplicities(sid,o,999)
  for method,W in [('P3_joint_unstratified',tw),('P4_joint_fold_stratified',sw)]:
   for scale in ('MAD','SD'):
    old,new,ratio=flags(pair,aux,W,aw,scale)
    if scale=='SD' and math.isfinite(ratio):min_sd_ratio=min(min_sd_ratio,ratio)
    for rep in np.flatnonzero((~old)&new):candidates.append({'outer_id':o,'method':method,'scale_method':scale,'replicate_id':int(rep)})
  if (o+1)%100==0:print(json.dumps({'stage':stage,'scenario':sid,'outer_complete':o+1,'outer_total':R,'elapsed_seconds':round(time.time()-t,2)}),flush=True)
 obj={'stage':stage,'scenario_id':sid,'outer_records':R,'method_scale_draws_screened':R*999*4,'old_supported_new_rejected':len(candidates),'minimum_supported_sd_scale_to_tolerance_ratio':min_sd_ratio,'mad_screen':'exact weighted-rank/count prefilter with exact expansion for every possible near-threshold row','candidate_keys':candidates};tmp=out.with_suffix('.tmp');tmp.write_text(json.dumps(obj,indent=2)+'\n');os.replace(tmp,out);print(json.dumps(obj))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--stage',required=True);ap.add_argument('--scenario',required=True);a=ap.parse_args();main(a.stage,a.scenario)
