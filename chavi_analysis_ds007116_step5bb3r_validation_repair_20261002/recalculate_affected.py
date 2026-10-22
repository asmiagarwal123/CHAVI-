"""Same-stream recalculation of every outer record containing an absent-fold P3 draw."""
from pathlib import Path
import argparse,csv,hashlib,json,math,os,sys,tempfile
import numpy as np
BASE=Path(__file__).resolve().parent;ROOT=BASE.parent;B3=ROOT/'chavi_analysis_ds007116_step5bb3_confirmatory_simulation_20261002';sys.path.insert(0,str(BASE))
import simulation_core as sc,run_stage as rs
ENDS=rs.ENDS
def legacy_endpoint(z,w):
    level=z.mean(axis=2);q=z-level[:,:,None];dl=level[:,1]-level[:,0];ds=np.sum((q[:,1]-q[:,0])**2,axis=1)/5
    return np.array([sc.stable_icc_a1(level,w),float(np.dot(w,dl)/w.sum()),math.sqrt(float(np.dot(w,ds)/w.sum()))],dtype=float)
def atomic_json(path,obj):
    tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(obj,separators=(',',':'))+'\n',encoding='utf-8');os.replace(tmp,path)
def main(stage,scenario):
    sc.STREAM_NAMESPACE=stage; rs.STREAM_NAMESPACE=stage; rs.assert_stage_namespace(stage); inventory=list(csv.DictReader((BASE/'affected_replicate_inventory.csv').open(encoding='utf-8'))); selected=[r for r in inventory if r['stage']==stage and r['scenario_id']==scenario and r['scale_method']=='MAD']; outers=sorted({int(r['outer_id']) for r in selected}); affected={(int(r['outer_id']),int(r['replicate_id'])) for r in selected};outdir=BASE/'runtime_repaired'/stage;outdir.mkdir(parents=True,exist_ok=True)
    for outer in outers:
        outpath=outdir/f'{scenario}__{outer:04d}.json'
        if outpath.exists():continue
        pair,aux=rs.generate_dataset(scenario,outer);tw,aw,sw=rs.draw_multiplicities(scenario,outer,999);source_path=B3/'runtime'/stage/f'{scenario}__{outer:04d}.json';source=json.loads(source_path.read_text());records=[];changes=[]
        for scale in ('MAD','SD'):
            vals,bad=rs.batch_refit(pair,aux,tw,aw,scale,False)
            point={r['endpoint']:r['estimate'] for r in source['point'] if r['method']=='P3_joint_unstratified' and r['scale_method']==scale}
            for ei,endpoint in enumerate(ENDS):
                v=vals[:,ei];valid=np.isfinite(v);n=int(valid.sum());truth=next(r['truth'] for r in source['bootstrap'] if r['method']=='P3_joint_unstratified' and r['scale_method']==scale and r['endpoint']==endpoint);q025=float(np.quantile(v[valid],.025,method='linear')) if n else None;q975=float(np.quantile(v[valid],.975,method='linear')) if n else None;p=point[endpoint];available=bool(n>=950 and math.floor(.025*n)>=20 and p is not None and truth is not None);records.append({'method':'P3_joint_unstratified','scale_method':scale,'endpoint':endpoint,'attempted':999,'valid':n,'invalid':999-n,'unsupported_fit':int(bad.sum()),'undefined_statistic':int(np.sum(~valid&~bad)),'n_gate':n>=950,'tail_gate':math.floor(.025*n)>=20,'point_gate':p is not None,'truth_gate':truth is not None,'available':available,'q025':q025,'q975':q975,'percentile_lower':q025 if available else None,'percentile_upper':q975 if available else None,'basic_lower':2*p-q975 if available else None,'basic_upper':2*p-q025 if available else None,'truth':truth})
            for rep in sorted(r for o,r in affected if o==outer):
                W=tw[rep];needed=sorted(set(sc.FOLDS[W>0].tolist()));fits,fail=sc.fit_references(pair[:,0],aux,W,aw[rep],needed,scale);z=sc.transform_targets(pair,fits,needed);legacy=legacy_endpoint(z,W);new=vals[rep]
                for ei,endpoint in enumerate(ENDS):
                    lv=None if not np.isfinite(legacy[ei]) else float(legacy[ei]);nv=None if not np.isfinite(new[ei]) else float(new[ei]);changed=(lv is None)!=(nv is None) or (lv is not None and abs(lv-nv)>1e-10);changes.append({'scale_method':scale,'endpoint':endpoint,'replicate_id':rep,'legacy_value':lv,'repaired_value':nv,'changed':changed})
        obj={'stage':stage,'scenario_id':scenario,'outer_id':outer,'source_runtime_path':str(source_path.relative_to(ROOT)).replace('\\','/'),'source_runtime_sha256':hashlib.sha256(source_path.read_bytes()).hexdigest(),'dataset_sha256':source['dataset_sha256'],'records':records,'affected_draw_values':changes}
        atomic_json(outpath,obj)
    print(json.dumps({'stage':stage,'scenario':scenario,'affected_outers':len(outers),'completed':sum(1 for o in outers if (outdir/f'{scenario}__{o:04d}.json').exists())}))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--stage',required=True);ap.add_argument('--scenario',required=True);a=ap.parse_args();main(a.stage,a.scenario)
