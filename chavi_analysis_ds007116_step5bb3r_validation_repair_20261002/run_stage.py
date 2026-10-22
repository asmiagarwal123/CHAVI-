"""Checkpointed corrected-pilot/confirmatory runner; simulated data only."""
from __future__ import annotations
import argparse,csv,hashlib,json,math,os,time
from pathlib import Path
import numpy as np
import simulation_core as core
from simulation_core import *

BASE=Path(__file__).resolve().parent
METHODS=("P1_oracle_conditional","P2_fixed_transform","P3_joint_unstratified","P4_joint_fold_stratified")
SCALES=("MAD","SD"); ENDS=("level_icc_a1","mean_level_change","rms_shape_displacement")
AUDIT_OUTER=range(5); AUDIT_REPS=(0,1,2,17,101,498,998)

def assert_stage_namespace(stage):
    if stage not in ('corrected_pilot','confirmatory'):
      raise ValueError(f'unsupported stage namespace: {stage}')
    if core.STREAM_NAMESPACE != stage:
      raise RuntimeError(f'stage/namespace mismatch: stage={stage}, namespace={core.STREAM_NAMESPACE}')

def hash_pair(pair,aux): return hashlib.sha256(np.asarray(pair,"<f8").tobytes()+np.asarray(aux,"<f8").tobytes()).hexdigest()
def batch_fixed(z,weights):
    z=np.asarray(z,float); w=np.asarray(weights,np.int64)
    if z.ndim==3 and len(w)==1 and not np.all(np.isfinite(z)):
      a,_=endpoints(z,w[0]); return np.array([[a[e] if a[e] is not None else np.nan for e in ENDS]],float)
    n=52.; level=z.mean(2); qz=z-level[:,:,None]; dl=level[:,1]-level[:,0]; ds2=np.sum((qz[:,1]-qz[:,0])**2,axis=1)/5
    mean=(w@dl)/n; rms=np.sqrt((w@ds2)/n); icc=np.full(len(w),np.nan); origin=float(level.mean()); unit=float(np.max(np.abs(level-origin)))
    if unit>0 and math.isfinite(unit):
      y=(level-origin)/unit; rm=y.mean(1); row2=np.sum(y*y,axis=1); sumrow=np.sum(y,axis=1); gm=(w@sumrow)/(2*n); cm=(w@y)/n
      msr=2*(w@(rm*rm)-n*gm*gm)/(n-1); msc=n*np.sum((cm-gm[:,None])**2,axis=1); sst=w@row2-2*n*gm*gm; ssr=(n-1)*msr; mse=(sst-ssr-msc)/(n-1); den=msr+mse+2*(msc-mse)/n; rel=np.maximum.reduce([np.abs(msr),np.abs(msc),np.abs(mse),np.abs(den)]); ok=(rel>0)&(np.abs(den)>64*EPS*rel); icc[ok]=(msr[ok]-mse[ok])/den[ok]
    return np.stack([icc,mean,rms],axis=1)
def batch_wmedian(x,w):
    """Weighted median for a batch of integer-frequency rows, independently equivalent to expansion."""
    order=np.argsort(x,axis=1,kind='stable'); xs=np.take_along_axis(x,order,axis=1); ws=np.take_along_axis(w,order,axis=1); cs=np.cumsum(ws,axis=1); n=ws.sum(axis=1); out=np.empty(len(x));
    hi=n//2; lo=(n-1)//2; ilo=np.argmax(cs>=lo[:,None]+1,axis=1); ihi=np.argmax(cs>=hi[:,None]+1,axis=1); out=np.where(n%2,(xs[np.arange(len(x)),ihi]),(xs[np.arange(len(x)),ilo]+xs[np.arange(len(x)),ihi])/2); return out
def batch_refit(pair,aux,tw,aw,scale,fold_stratified):
    """Vectorized P3/P4 fit and endpoint path; leaves undefined rows as NaN."""
    B=len(tw); z=np.full((B,52,2,5),np.nan); bad=np.zeros(B,dtype=bool)
    for fold in range(5):
      ix=np.flatnonzero(FOLDS==fold); keep=np.flatnonzero(FOLDS!=fold); active=tw[:,ix].sum(axis=1)>0; active_rows=np.flatnonzero(active)
      if not len(active_rows): continue
      x=np.concatenate([np.broadcast_to(pair[keep,0],(len(active_rows),len(keep),5)),np.broadcast_to(aux,(len(active_rows),57,5))],axis=1); w=np.concatenate([tw[active_rows][:,keep],aw[active_rows]],axis=1); n=w.sum(axis=1)
      center=np.einsum('bn,bnj->bj',w,x)/n[:,None]
      if scale=='SD': sc=np.sqrt(np.einsum('bn,bnj->bj',w,(x-center[:,None,:])**2)/(n[:,None]-1))
      else:
       med=np.column_stack([batch_wmedian(x[:,:,j],w) for j in range(5)]); dev=np.abs(x-med[:,None,:]); sc=np.column_stack([batch_wmedian(dev[:,:,j],w)/MAD_DENOM for j in range(5)])
      present=w>0; n_present=present.sum(axis=1); xmax=np.max(np.where(present[:,:,None],x,-np.inf),axis=1); xmin=np.min(np.where(present[:,:,None],x,np.inf),axis=1); span=xmax-xmin
      supported=np.isfinite(sc)&(sc>0)&(n_present[:,None]>=2)&(sc>64*EPS*np.maximum(span,np.abs(sc)))
      fail=~np.all(supported,axis=1); bad[active_rows[fail]]=True
      target_ix=np.flatnonzero(FOLDS==fold)
      # Assign explicitly by row blocks; this preserves the fold-exclusion map.
      for local,b in enumerate(active_rows):
       if not fail[local]: z[b,target_ix]=(pair[target_ix]-center[local])/sc[local]
    vals=np.full((B,3),np.nan)
    for b in np.flatnonzero(~bad): vals[b]=batch_fixed(z[b],tw[b:b+1])[0]
    return vals,bad
def fit_transform(pair,aux,tw,aw,scale,needed=None):
    if needed is None: needed=range(5)
    fits,fail=fit_references(pair[:,0],aux,tw,aw,needed,scale); return transform_targets(pair,fits,needed),fits,fail
def endpoint_array(z,w):
    vals,reason=endpoints(z,w); return np.array([vals[e] if vals[e] is not None else np.nan for e in ENDS],float),reason
def reason_code(reason,fitfail=False): return "unsupported_fit" if fitfail else (reason or "valid")
def truth_table():
    out={}
    with (BASE/'truth_results.csv').open(encoding='utf-8',newline='') as f:
      for r in csv.DictReader(f): out[(r['scenario_id'],r['scale_method'],r['endpoint_id'])]=float(r['truth_value']) if r['truth_value'] else float('nan')
    return out
def one(stage,sid,outer,B):
    assert_stage_namespace(stage)
    pair,aux=generate_dataset(sid,outer); ones_t=np.ones(52,dtype=int); ones_a=np.ones(57,dtype=int); tw,aw,sw=draw_multiplicities(sid,outer,B); truth=truth_table(); rec={"stage":stage,"scenario_id":sid,"outer_id":outer,"dataset_sha256":hash_pair(pair,aux),"target_n":52,"auxiliary_n":57,"fold_counts":[11,11,10,10,10],"point":[],"bootstrap":[],"audit":[]}
    for scale in SCALES:
      oracle=None; tr=truth[(sid,scale,'mean_level_change')]
      # P1 uses frozen population transformation; S6/MAD is intentionally undefined.
      refs=truth.get((sid,scale,'level_icc_a1'),float('nan'))
      refpar=json.loads((BASE/'truth_reference_parameters.json').read_text(encoding='utf-8')).get(f'{sid}|{scale}')
      if refpar and refpar.get('status')=='defined': oracle={f:{'center':np.array(refpar['center']), 'scale':np.array(refpar['scale']), 'status':'supported'} for f in range(5)}
      ez,efits,efail=fit_transform(pair,aux,ones_t,ones_a,scale)
      for mi,method in enumerate(METHODS):
        z = transform_targets(pair,oracle) if mi==0 and oracle else ez if mi>0 else np.full_like(pair,np.nan)
        pv,preason=endpoint_array(z,ones_t) if oracle or mi>0 else (np.full(3,np.nan),'structural_undefined')
        for ei,e in enumerate(ENDS): rec['point'].append({'method':method,'scale_method':scale,'endpoint':e,'estimate':None if not np.isfinite(pv[ei]) else float(pv[ei]),'status':'valid' if np.isfinite(pv[ei]) else 'undefined','reason':reason_code(preason,bool(efail))})
      # P1/P2 vectorized; P3/P4 refit each replicate and retain every failure count.
      fixed={0:(transform_targets(pair,oracle) if oracle else None),1:ez if not efail else None}
      for mi,method in enumerate(METHODS):
       vals=np.full((B,3),np.nan); reasons=np.full((B,3),'undefined',dtype=object)
       if mi in (0,1) and fixed[mi] is not None:
         vals=batch_fixed(fixed[mi],tw)
         reasons=np.where(np.isfinite(vals),'valid','undefined')
       elif mi in (2,3):
         W=tw if mi==2 else sw
         vals,bad=batch_refit(pair,aux,W,aw,scale,mi==3)
         reasons=np.where(np.isfinite(vals),'valid',np.where(bad[:,None],'unsupported_fit','undefined'))
       for e,endpoint in enumerate(ENDS):
        v=vals[:,e]; valid=np.isfinite(v); counts={"valid":int(valid.sum()),"undefined":int((~valid).sum()),"unsupported_fit":int(np.sum(reasons[:,e]=='unsupported_fit'))}
        for b in AUDIT_REPS:
         if b<B and outer in AUDIT_OUTER: rec['audit'].append({'method':method,'scale_method':scale,'endpoint':endpoint,'replicate_id':b,'value':None if not np.isfinite(v[b]) else float(v[b]),'status':'valid' if valid[b] else 'invalid','reason':str(reasons[b,e])})
        point=next(x for x in rec['point'] if x['method']==method and x['scale_method']==scale and x['endpoint']==endpoint)
        target=truth.get((sid,scale,endpoint),float('nan')); n=int(valid.sum()); nelig=(n>=950); tail=(int(math.floor(.025*n))>=20); eligible=bool(nelig and tail and point['status']=='valid' and math.isfinite(target))
        q025=float(np.quantile(v[valid],.025,method='linear')) if n else None; q975=float(np.quantile(v[valid],.975,method='linear')) if n else None
        rec['bootstrap'].extend([{'method':method,'scale_method':scale,'endpoint':endpoint,'attempted':B,'valid':n,'invalid':B-n,'failure_reasons':counts,'n_gate':nelig,'tail_gate':tail,'point_gate':point['status']=='valid','truth_gate':math.isfinite(target),'available':eligible,'q025':q025,'q975':q975,'percentile_lower':q025 if eligible else None,'percentile_upper':q975 if eligible else None,'basic_lower':2*point['estimate']-q975 if eligible else None,'basic_upper':2*point['estimate']-q025 if eligible else None,'truth':None if not math.isfinite(target) else target}])
    return rec
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--stage',choices=['corrected_pilot','confirmatory']); ap.add_argument('--scenarios',default=None,help='comma-separated scenario IDs for parallel execution'); ap.add_argument('--start',type=int,default=0); ap.add_argument('--limit',type=int,default=None); ap.add_argument('--B',type=int,default=None); args=ap.parse_args(); B=args.B or 999; scenarios=tuple(x for x in (args.scenarios.split(',') if args.scenarios else (SCENARIOS.keys() if args.stage=='corrected_pilot' else ('S1','S5')))); R=100 if args.stage=='corrected_pilot' else 2000; root=BASE/'runtime'/args.stage; root.mkdir(parents=True,exist_ok=True); total=len(tuple(scenarios))*R; done=0
    globals()['STREAM_NAMESPACE']=args.stage
    core.STREAM_NAMESPACE=args.stage
    assert_stage_namespace(args.stage)
    for si,sid in enumerate(scenarios):
      for o in range(R):
       idx=si*R+o
       if idx<args.start: continue
       if args.limit is not None and done>=args.limit: return
       p=root/f'{sid}__{o:04d}.json'
       if p.exists(): continue
       rec=one(args.stage,sid,o,B); p.write_text(json.dumps(rec,separators=(',',':'))+'\n',encoding='utf-8'); done+=1
       if done%10==0: print(json.dumps({'stage':args.stage,'newly_completed':done,'total':total}),flush=True)
    print(json.dumps({'stage':args.stage,'status':'complete','total':total}))
if __name__=='__main__':main()
