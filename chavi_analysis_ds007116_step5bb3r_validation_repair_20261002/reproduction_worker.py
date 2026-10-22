"""Small atomic-checkpoint worker used only by the restart/reproduction test."""
from pathlib import Path
import argparse,hashlib,json,os,sys
import numpy as np
BASE=Path(__file__).resolve().parent;sys.path.insert(0,str(BASE));import simulation_core as sc;import run_stage as rs
CASES=[('corrected_pilot','S2',14),('confirmatory','S1',40)]
def main(outdir,limit):
 out=Path(outdir);out.mkdir(parents=True,exist_ok=True);new=0
 for stage,sid,o in CASES:
  p=out/f'{stage}__{sid}__{o}.json'
  if p.exists():
   obj=json.loads(p.read_text());assert obj['stage']==stage and obj['scenario_id']==sid and obj['outer_id']==o and obj['attempted']==999;continue
  if limit is not None and new>=limit:break
  sc.STREAM_NAMESPACE=stage;rs.STREAM_NAMESPACE=stage;rs.assert_stage_namespace(stage);pair,aux=rs.generate_dataset(sid,o);tw,aw,_=rs.draw_multiplicities(sid,o,999);vals,bad=rs.batch_refit(pair,aux,tw,aw,'SD',False);raw=np.asarray(vals,'<f8').tobytes()+np.asarray(bad,np.uint8).tobytes();obj={'stage':stage,'scenario_id':sid,'outer_id':o,'attempted':999,'dataset_sha256':rs.hash_pair(pair,aux),'calculation_sha256':hashlib.sha256(raw).hexdigest(),'valid_by_endpoint':np.isfinite(vals).sum(0).tolist(),'unsupported':int(bad.sum())};tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(obj,sort_keys=True)+'\n');os.replace(tmp,p);new+=1
 print(json.dumps({'outdir':str(out),'new':new,'complete':len(list(out.glob('*.json')))}))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--outdir',required=True);ap.add_argument('--limit',type=int);a=ap.parse_args();main(a.outdir,a.limit)
