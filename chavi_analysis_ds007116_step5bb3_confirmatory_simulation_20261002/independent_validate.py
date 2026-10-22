"""Substantive second calculation path; does not import production modules."""
from __future__ import annotations
import csv, hashlib, json, math, statistics
from pathlib import Path
import numpy as np

BASE=Path(__file__).resolve().parent
MU=np.array([10.,12.,14.,16.,18.]); MADK=.6744897501960817
FOLDS=np.array([0]*11+[1]*11+[2]*10+[3]*10+[4]*10)
METHODS=('P1_oracle_conditional','P2_fixed_transform','P3_joint_unstratified','P4_joint_fold_stratified')
SCALES=('MAD','SD'); ENDS=('level_icc_a1','mean_level_change','rms_shape_displacement')
H=np.zeros((5,4))
for j in range(4): H[:j+1,j]=1/math.sqrt((j+1)*(j+2)); H[j+1,j]=-(j+1)/math.sqrt((j+1)*(j+2))
C=np.fromfunction(lambda i,j:.3**np.abs(i-j),(5,5)); CH=np.linalg.cholesky(.5*C)

def keyed(namespace,*parts):
    raw='|'.join(map(str,(20261002,namespace)+parts)).encode()
    return np.random.Generator(np.random.PCG64DXSM(int.from_bytes(hashlib.sha256(raw).digest()[:16],'little')))

def scores(n,g,rl,rs):
    u=g.normal(size=n); v=g.normal(size=n)
    l1=math.sqrt(.5)*u; l2=math.sqrt(.5)*(rl*u+math.sqrt(1-rl*rl)*v)
    u=g.normal(size=(n,4)); v=g.normal(size=(n,4))
    s1=math.sqrt(.5)*u; s2=math.sqrt(.5)*(rs*u+math.sqrt(1-rs*rs)*v)
    e1=g.normal(size=(n,5))@CH.T; e2=g.normal(size=(n,5))@CH.T
    return MU+l1[:,None]+s1@H.T+e1, MU+l2[:,None]+s2@H.T+e2

def generate(sid,outer,namespace):
    cfg={'S1':(.8,.8,'none','continuous'),'S2':(.8,0.,'none','continuous'),'S3':(.8,.8,'common_0.5','continuous'),'S4':(.8,.8,'helmert1_0.5','continuous'),'S5':(.8,.8,'none','round'),'S6':(.8,.8,'none','mass')}[sid]
    g=keyed(namespace,'outer_dataset',sid,outer); y1,y2=scores(52,g,cfg[0],cfg[1]); aux,_=scores(57,g,cfg[0],cfg[1])
    if cfg[2]=='common_0.5': y2=y2+.5
    if cfg[2]=='helmert1_0.5': y2=y2+.5*H[:,0]
    if cfg[3]=='round': y1=np.rint(y1); y2=np.rint(y2); aux=np.rint(aux)
    if cfg[3]=='mass':
        y1=MU+(y1-MU)*(g.random(y1.shape)<.4); y2=MU+(y2-MU)*(g.random(y2.shape)<.4); aux=MU+(aux-MU)*(g.random(aux.shape)<.4)
    return np.stack([y1,y2],axis=1),aux

def wmed(x,w):
    e=np.repeat(np.asarray(x),np.asarray(w,dtype=int)); return float(np.median(e)) if len(e) else math.nan

def fit(pair,aux,tw,aw,scale,needed):
    fits={}; fails=[]
    for fold in needed:
        keep=FOLDS!=fold; x=np.vstack([pair[keep,0],aux]); w=np.r_[tw[keep],aw]
        center=np.array([float(np.dot(w,x[:,j])/sum(w)) for j in range(5)]); scales=[]
        for j in range(5):
            if scale=='MAD': s=wmed(np.abs(x[:,j]-wmed(x[:,j],w)),w)/MADK
            else: s=math.sqrt(float(np.dot(w,(x[:,j]-center[j])**2)/(sum(w)-1)))
            scales.append(s)
            if not math.isfinite(s) or s<=0: fails.append(fold)
        fits[fold]=(center,np.array(scales))
    return fits,fails

def transform(pair,fits):
    z=np.full_like(pair,np.nan)
    for fold,(center,scale) in fits.items(): z[FOLDS==fold]=(pair[FOLDS==fold]-center)/scale
    return z

def endpoint(z,w):
    active=w>0
    if not np.all(np.isfinite(z[active])): return np.full(3,np.nan)
    level=z.mean(2); q=z-level[:,:,None]; delta=level[:,1]-level[:,0]; shape=np.sum((q[:,1]-q[:,0])**2,axis=1)/5; x=level[active]; ww=w[active]; n=sum(ww)
    gm=float(np.sum(x*ww[:,None])/(2*n)); rm=x.mean(1); cm=np.sum(x*ww[:,None],axis=0)/n
    msr=2*np.dot(ww,(rm-gm)**2)/(n-1); msc=n*np.sum((cm-gm)**2); resid=x-rm[:,None]-cm[None,:]+gm; mse=np.sum(ww[:,None]*resid**2)/(n-1); den=msr+mse+2*(msc-mse)/n
    return np.array([(msr-mse)/den if den else np.nan,np.dot(ww,delta[active])/n,math.sqrt(np.dot(ww,shape[active])/n)])

def multiplicities(sid,outer,B,namespace):
    rt=keyed(namespace,'bootstrap_target_unstratified',sid,outer); ra=keyed(namespace,'bootstrap_auxiliary',sid,outer); rs=keyed(namespace,'bootstrap_target_stratified',sid,outer)
    tw=np.zeros((B,52),int); aw=np.zeros((B,57),int)
    for b in range(B): tw[b]=np.bincount(rt.integers(0,52,52),minlength=52); aw[b]=np.bincount(ra.integers(0,57,57),minlength=57)
    sw=np.zeros((B,52),int)
    for fold in range(5):
        ix=np.flatnonzero(FOLDS==fold)
        for b in range(B): sw[b,ix]=np.bincount(rs.integers(0,len(ix),len(ix)),minlength=len(ix))
    return tw,aw,sw

def main(stage):
    namespace='corrected_pilot' if stage=='corrected_pilot' else 'confirmatory'; scenarios=('S1','S2','S3','S4','S5','S6') if stage=='corrected_pilot' else ('S1','S5'); R=100 if stage=='corrected_pilot' else 2000; B=999; runtime=BASE/'runtime'/stage
    truth=json.loads((BASE/'truth_reference_parameters.json').read_text()); expected=[]; mism=[]
    for sid in scenarios:
      for outer in range(R):
        pair,aux=generate(sid,outer,namespace); h=hashlib.sha256(pair.astype('<f8').tobytes()+aux.astype('<f8').tobytes()).hexdigest(); p=runtime/f'{sid}__{outer:04d}.json'; obs=json.loads(p.read_text()) if p.exists() else {}
        expected.append({'stage':stage,'scenario_id':sid,'outer_id':outer,'expected_dataset_hash':h,'observed_dataset_hash':obs.get('dataset_sha256'),'hash_match':h==obs.get('dataset_sha256')})
        if outer<5:
            for scale in SCALES:
                fits,fail=fit(pair,aux,np.ones(52,int),np.ones(57,int),scale,range(5)); vals=endpoint(transform(pair,fits),np.ones(52,int)) if not fail else np.full(3,np.nan)
                for method in METHODS[1:]:
                    for ei,endpoint_name in enumerate(ENDS):
                        row=next((r for r in obs.get('point',[]) if r['method']==method and r['scale_method']==scale and r['endpoint']==endpoint_name),{}); v=None if not math.isfinite(vals[ei]) else float(vals[ei])
                        if (row.get('estimate') is None)!=(v is None) or (v is not None and abs(float(row.get('estimate'))-v)>1e-9): mism.append({'check':'point','scenario_id':sid,'outer_id':outer,'method':method,'scale':scale,'endpoint':endpoint_name,'expected':v,'observed':row.get('estimate')})
        if outer in (0,1):
            tw,aw,sw=multiplicities(sid,outer,B,namespace)
            for scale in SCALES:
              for mi,method in enumerate(METHODS):
                vals=np.full((B,3),np.nan)
                for b in range(B):
                    W=tw[b] if mi in (0,1,2) else sw[b]; needed=sorted(set(FOLDS[W>0].tolist()))
                    if mi==0:
                        ref=truth.get(f'{sid}|{scale}'); fits={} if not ref or ref.get('status')!='defined' else {f:(np.array(ref['center']),np.array(ref['scale'])) for f in range(5)}; vals[b]=endpoint(transform(pair,fits),W)
                    elif mi==1:
                        fits,fail=fit(pair,aux,np.ones(52,int),np.ones(57,int),scale,range(5)); vals[b]=endpoint(transform(pair,fits),W) if not fail else np.full(3,np.nan)
                    else:
                        fits,fail=fit(pair,aux,W,aw[b],scale,needed); vals[b]=endpoint(transform(pair,fits),W) if not fail else np.full(3,np.nan)
                for ei,endpoint_name in enumerate(ENDS):
                    audit=[r for r in obs.get('audit',[]) if r['method']==method and r['scale_method']==scale and r['endpoint']==endpoint_name]; amap={int(r['replicate_id']):r for r in audit}
                    for b in (0,1,2,17,101,498,998):
                        v=None if not math.isfinite(vals[b,ei]) else float(vals[b,ei]); row=amap.get(b,{})
                        if (row.get('value') is None)!=(v is None) or (v is not None and abs(float(row.get('value'))-v)>1e-8): mism.append({'check':'bootstrap','scenario_id':sid,'outer_id':outer,'method':method,'scale':scale,'endpoint':endpoint_name,'replicate':b,'expected':v,'observed':row.get('value')})
    with (BASE/f'{stage}_independent_expected_dataset_hashes.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(expected[0])); w.writeheader(); w.writerows(expected)
    result={'stage':stage,'expected_records':len(expected),'hash_mismatches':sum(not r['hash_match'] for r in expected),'numeric_mismatch_count':len(mism),'numeric_mismatches':mism[:1000],'status':'PASS' if not mism and all(r['hash_match'] for r in expected) else 'FAIL'}
    (BASE/f'{stage}_independent_comparison_records.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8'); print(json.dumps(result))
if __name__=='__main__':
    import argparse; ap=argparse.ArgumentParser(); ap.add_argument('--stage',required=True); main(ap.parse_args().stage)
