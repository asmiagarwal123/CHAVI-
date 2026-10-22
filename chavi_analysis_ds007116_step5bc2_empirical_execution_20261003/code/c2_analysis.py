"""Production primitives and keyed data adapter for CHAVI Step 5B-C2."""
from __future__ import annotations
import csv, hashlib, json, math, os, time
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np

TASKS=("letter_nback","face_memory","matrix_reasoning","emotion_recognition","dominant_finger_tapping")
EPS=np.finfo(float).eps;TINY=np.finfo(float).tiny;MAD_DEN=0.6744897501960817
ENDPOINTS=("level_icc_a1","mean_level_change","rms_shape_displacement")
class ValidationError(ValueError):pass
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def sha_file(p):return sha_bytes(Path(p).read_bytes())
def read_csv(p):
 with open(p,newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def write_csv(p,fields,rows):
 Path(p).parent.mkdir(parents=True,exist_ok=True)
 with open(p,'w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def int_weights(values,n,total,label):
 a=np.asarray(values)
 if a.shape!=(n,) or np.issubdtype(a.dtype,np.bool_) or not np.issubdtype(a.dtype,np.integer):raise ValidationError(label+': weights_not_integer_nonboolean')
 if np.any(a<0):raise ValidationError(label+': negative_multiplicity')
 if int(a.sum())!=total:raise ValidationError(label+': incorrect_total')
 return a.astype(np.int64,copy=False)
def weighted_median(x,w):
 x=np.asarray(x,float);w=np.asarray(w,dtype=np.int64);keep=w>0;x=x[keep];w=w[keep]
 if len(x)==0:return None
 if not np.all(np.isfinite(x)):raise ValidationError('active_nonfinite_reference_score')
 order=np.argsort(x,kind='stable');x=x[order];w=w[order];cs=np.cumsum(w);n=int(w.sum())
 def at(r):return float(x[np.searchsorted(cs,r+1,side='left')])
 return at(n//2) if n%2 else (at(n//2-1)+at(n//2))/2
def fit_m0_mad(y,w):
 y=np.asarray(y,float);w=np.asarray(w,dtype=np.int64);keep=w>0;y=y[keep];w=w[keep]
 if len(y)<2 or not np.all(np.isfinite(y)):raise ValidationError('insufficient_or_nonfinite_reference')
 center=float(np.dot(y,w)/w.sum());raw=weighted_median(np.abs(y-weighted_median(y,w)),w);scale=raw/MAD_DEN
 D=float(y.max()-y.min())
 if not math.isfinite(scale) or scale<=0:raise ValidationError('nonpositive_or_nonfinite_scale')
 if scale<=64*EPS*max(D,abs(scale)):raise ValidationError('numerically_degenerate_scale')
 return center,scale
def stable_icc(x,w):
 x=np.asarray(x,float);w=np.asarray(w,dtype=np.int64);keep=w>0;x=x[keep];w=w[keep];n=int(w.sum());k=2
 if n<2 or not np.all(np.isfinite(x)):return None,'insufficient_or_nonfinite'
 origin=float(np.sum(w[:,None]*x)/(n*k));c=x-origin;unit=float(np.max(np.abs(c)))
 if unit==0 or not math.isfinite(unit):return None,'constant_or_nonfinite'
 y=c/unit;gm=float(np.sum(w[:,None]*y)/(n*k));rm=y.mean(1);cm=np.sum(w[:,None]*y,0)/n
 msr=k*float(np.dot(w,(rm-gm)**2))/(n-1);msc=n*float(np.sum((cm-gm)**2));res=y-rm[:,None]-cm[None,:]+gm;mse=float(np.sum(w[:,None]*res**2))/(n-1)
 den=msr+mse+2*(msc-mse)/n;rel=max(abs(msr),abs(msc),abs(mse),abs(den))
 if rel==0 or abs(den)<=64*EPS*rel:return None,'degenerate_denominator'
 return float((msr-mse)/den),'defined'
def endpoints(z,w=None):
 z=np.asarray(z,float);w=np.ones(len(z),dtype=np.int64) if w is None else np.asarray(w,dtype=np.int64);active=w>0
 if z.ndim!=3 or z.shape[1:]!=(2,5):raise ValidationError('coordinate_shape')
 if int(w.sum())<2:return {e:(None,'insufficient_frequency_n') for e in ENDPOINTS}
 if not np.all(np.isfinite(z[active])):return {e:(None,'active_nonfinite_coordinate') for e in ENDPOINTS}
 a=z[active];ww=w[active];levels=a.mean(2);q=a-levels[:,:,None];dl=levels[:,1]-levels[:,0];sq=np.sum((q[:,1]-q[:,0])**2,1)/5
 icc,reason=stable_icc(levels,ww)
 return {'level_icc_a1':(icc,reason),'mean_level_change':(float(np.dot(ww,dl)/ww.sum()),'defined'),'rms_shape_displacement':(math.sqrt(float(np.dot(ww,sq)/ww.sum())),'defined')}
def corr_summary(z):
 vals=[];undefined=0
 for pair in np.asarray(z,float):
  qs=[];bad=False
  for a in pair:
   L=float(a.mean());q=a-L;threshold=64*EPS*max(float(np.linalg.norm(a)),math.sqrt(5)*abs(L),TINY)
   if np.linalg.norm(q)<=threshold:bad=True;break
   qs.append(q)
  if bad:undefined+=1;continue
  vals.append(float(np.dot(qs[0],qs[1])/(np.linalg.norm(qs[0])*np.linalg.norm(qs[1]))))
 a=np.array(vals,float);q=np.quantile(a,[.25,.5,.75],method='linear') if len(a) else [None]*3
 return {'defined_n':len(vals),'undefined_n':undefined,'minimum':None if not len(a) else float(a.min()),'q25':q[0],'median':q[1],'q75':q[2],'maximum':None if not len(a) else float(a.max())}
def seed(master,namespace,label,replicate):return int.from_bytes(hashlib.sha256(f'{master}|{namespace}|{label}|{replicate}'.encode()).digest()[:16],'little')
def draws(rep,n_t,n_a):
 rt=np.random.Generator(np.random.PCG64DXSM(seed(20261003,'empirical_v1','shared_target',rep)))
 ra=np.random.Generator(np.random.PCG64DXSM(seed(20261003,'empirical_v1','p3_auxiliary',rep)))
 return np.bincount(rt.integers(0,n_t,size=n_t),minlength=n_t).astype(np.int64),np.bincount(ra.integers(0,n_a,size=n_a),minlength=n_a).astype(np.int64)
def validate_plan(tids,aids,fold_map,tw,aw,fit_by_fold,aux_by_fold,frozen_fold_map=None):
 if set(tids)&set(aids):raise ValidationError('role_identities_not_disjoint')
 if len(set(tids))!=len(tids) or len(set(aids))!=len(aids):raise ValidationError('duplicate_role_identity')
 if set(fold_map)!=set(tids):raise ValidationError('externally_frozen_fold_map_mismatch')
 if frozen_fold_map is not None and dict(fold_map)!=dict(frozen_fold_map):raise ValidationError('externally_frozen_fold_map_mismatch')
 tw=int_weights(tw,len(tids),len(tids),'target');aw=int_weights(aw,len(aids),len(aids),'auxiliary')
 represented=sorted({fold_map[tids[i]] for i in range(len(tids)) if tw[i]>0})
 if set(fit_by_fold)!=set(represented) or set(aux_by_fold)!=set(represented):raise ValidationError('represented_fold_fit_keys_mismatch')
 for f in represented:
  ft=np.asarray(fit_by_fold[f]);fa=np.asarray(aux_by_fold[f])
  if ft.shape!=(len(tids),) or fa.shape!=(len(aids),):raise ValidationError('fit_identity_set_mismatch')
  if np.issubdtype(ft.dtype,np.bool_) or not np.issubdtype(ft.dtype,np.integer) or np.any(ft<0):raise ValidationError('target_fit_invalid_multiplicity')
  if np.issubdtype(fa.dtype,np.bool_) or not np.issubdtype(fa.dtype,np.integer) or np.any(fa<0):raise ValidationError('auxiliary_fit_invalid_multiplicity')
  expected=np.array([0 if fold_map[tids[i]]==f else tw[i] for i in range(len(tids))])
  if not np.array_equal(ft,expected):raise ValidationError('held_out_leakage_or_altered_fold')
  if not np.array_equal(fa,aw):raise ValidationError('auxiliary_draw_not_shared')
 return represented
def interval_gate(attempted,valid,invalid,point_defined):
 if type(attempted) is not int or type(valid) is not int or type(invalid) is not int:raise ValidationError('counts_not_integer')
 if attempted<0 or valid<0 or invalid<0 or valid>attempted or valid+invalid!=attempted:raise ValidationError('count_accounting_invalid')
 if attempted!=999:return False,'attempt_count_not_999'
 if valid<950:return False,'fewer_than_950_valid'
 if math.floor(.025*valid)<20:return False,'insufficient_tail_count'
 if not point_defined:return False,'undefined_point_estimate'
 return True,'available'
def validate_support_value(label,value):
 if label not in {'yes','no'}:raise ValidationError('unknown_support_label')
 present=value not in {None,''}
 if label=='yes':
  if not present:raise ValidationError('supported_coordinate_missing')
  try:x=float(value)
  except (TypeError,ValueError):raise ValidationError('supported_coordinate_nonnumeric')
  if not math.isfinite(x):raise ValidationError('supported_coordinate_nonfinite')
  return x
 if present:raise ValidationError('unsupported_coordinate_not_null')
 return None

class Adapter:
 def __init__(self,root,spec):
  self.root=Path(root);self.ba=self.root/'chavi_analysis_ds007116_step5ba_clean_rebuild_20261001';self.spec=spec
  self.tids=spec['canonical_identity_order']['targets'];self.aids=spec['canonical_identity_order']['auxiliaries'];self.fold={k:int(v) for k,v in spec['fold_map'].items()}
  self.pairs=spec['ordered_occasion_keys'];self.task_index={t:i for i,t in enumerate(TASKS)}
  self.ref_rows=read_csv(self.ba/'reference_cohort_manifest.csv');self.fold_rows=read_csv(self.ba/'fold_fitting_manifest.csv')
  self._validate_reference();self.ref_scores,self.ref_sources=self._reference_arrays()
  allids=self.tids+self.aids;idx={x:i for i,x in enumerate(allids)};self.target_ref=np.array([self.ref_scores[idx[x]] for x in self.tids]);self.aux_ref=np.array([self.ref_scores[idx[x]] for x in self.aids])
 def _validate_reference(self):
  keys=set();by=defaultdict(set)
  for r in self.ref_rows:
   k=(r['participant_id'],r['session_id'],r['task_key'],r['source_filename'],r['source_row_reference'])
   if k in keys:raise ValidationError('duplicate_reference_physical_source_key')
   keys.add(k);by[r['participant_id']].add(r['task_key'])
   if not math.isfinite(float(r['parsed_score'])):raise ValidationError('nonfinite_reference_score')
  if set(by)!=set(self.tids+self.aids) or any(v!=set(TASKS) for v in by.values()):raise ValidationError('reference_identity_or_task_set_mismatch')
 def _reference_arrays(self):
  allids=self.tids+self.aids;idx={x:i for i,x in enumerate(allids)};a=np.full((109,5),np.nan);src={}
  for r in self.ref_rows:
   i=idx[r['participant_id']];j=self.task_index[r['task_key']];a[i,j]=float(r['parsed_score']);src[(r['participant_id'],r['task_key'])]=(r['session_id'],r['source_filename'],r['source_row_reference'],r['raw_score'])
  if not np.all(np.isfinite(a)):raise ValidationError('incomplete_reference_array')
  return a,src
 def slice(self,stratum,model,scale,pair_kind,expected_n):
  stem={'primary_vf':'primary_vf','fixed_primary_pair_strict_v':'fixed_primary_pair_strict_v','vonly_reselected':'vonly_reselected'}[stratum]
  source=read_csv(self.ba/(stem+'_source_rows.csv'));coords=read_csv(self.ba/(stem+'_transformed_long.csv'))
  source_map={};
  for r in source:
   key=(r['participant_id'],r['session_id'],r['task_key'])
   if key in source_map:raise ValidationError('duplicate_physical_source_key')
   source_map[key]=r
  selected=[r for r in coords if r['model']==model and r['scale_method']==scale]
  cmap={};
  for r in selected:
   key=(r['participant_id'],r['session_id'],r['task_key'])
   if key in cmap:raise ValidationError('duplicate_coordinate_key')
   validate_support_value(r['supported'],r['coordinate'])
   if key not in source_map:raise ValidationError('coordinate_missing_physical_source')
   s=source_map[key]
   for field in ('source_filename','source_row_reference','raw_score'):
    if r[field]!=s[field]:raise ValidationError('mismatched_physical_source_key')
   cmap[key]=r
  ids=sorted({r['participant_id'] for r in selected})
  if pair_kind=='M1_supported_primary':
   m1=read_csv(self.ba/'primary_vf_transformed_long.csv');m1=[r for r in m1 if r['model']=='M1' and r['scale_method']=='MAD'];support=defaultdict(list)
   for r in m1:support[r['participant_id']].append(r)
   ids=sorted(i for i,v in support.items() if len(v)==10 and all(x['supported']=='yes' and x['coordinate']!='' for x in v))
  z=np.full((len(ids),2,5),np.nan);audit=[]
  for i,pid in enumerate(ids):
   kind='primary' if pair_kind=='M1_supported_primary' else pair_kind;sessions=self.pairs[pid][kind]
   if len(sessions)!=2:raise ValidationError('frozen_ordered_occasion_pair_missing')
   for v,ses in enumerate(sessions):
    for j,t in enumerate(TASKS):
     key=(pid,ses,t)
     if key not in cmap:raise ValidationError('missing_frozen_pair_coordinate')
     r=cmap[key]
     if r['supported']!='yes':raise ValidationError('unsupported_coordinate_in_complete_slice')
     z[i,v,j]=float(r['coordinate']);audit.append({'participant_id':pid,'occasion_index':v+1,'session_id':ses,'task_key':t,'model':model,'scale':scale,'source_filename':r['source_filename'],'source_row_reference':r['source_row_reference']})
  expected_source={(pid,self.pairs[pid]['primary' if pair_kind=='M1_supported_primary' else pair_kind][v],t) for pid in ids for v in range(2) for t in TASKS}
  if set(k for k in source_map if k[0] in ids)!=expected_source:raise ValidationError('missing_extra_or_mismatched_physical_source_keys')
  if len(ids)!=expected_n:raise ValidationError('slice_denominator_mismatch')
  return ids,z,audit
 def primary_raw_pairs(self):
  rows=read_csv(self.ba/'primary_vf_source_rows.csv');m={(r['participant_id'],r['session_id'],r['task_key']):float(r['parsed_score']) for r in rows};z=np.full((52,2,5),np.nan)
  for i,pid in enumerate(self.tids):
   for v,s in enumerate(self.pairs[pid]['primary']):
    for j,t in enumerate(TASKS):z[i,v,j]=m[(pid,s,t)]
  return z
 def unit_fits_and_coordinates(self):
  raw=self.primary_raw_pairs();params=[];coords=np.full_like(raw,np.nan)
  for f in range(5):
   held=np.array([self.fold[x]==f for x in self.tids]);y=np.vstack([self.target_ref[~held],self.aux_ref]);w=np.ones(len(y),dtype=np.int64)
   for j,t in enumerate(TASKS):
    c,s=fit_m0_mad(y[:,j],w);params.append({'target_fold':f,'task_key':t,'center':c,'scale':s,'training_count':len(y)})
    ix=[i for i,x in enumerate(self.tids) if self.fold[x]==f];coords[ix,:,j]=(raw[ix,:,j]-c)/s
  return params,coords
 def p3(self,raw,tw,aw):
  fit_t={};fit_a={};represented=sorted({self.fold[self.tids[i]] for i in range(52) if tw[i]>0})
  for f in represented:
   fit_t[f]=np.array([0 if self.fold[x]==f else tw[i] for i,x in enumerate(self.tids)],dtype=np.int64);fit_a[f]=aw.copy()
  validate_plan(self.tids,self.aids,self.fold,tw,aw,fit_t,fit_a,self.fold)
  z=np.full_like(raw,np.nan);fail=[]
  for f in represented:
   y=np.vstack([self.target_ref,self.aux_ref]);w=np.r_[fit_t[f],aw];ix=[i for i,x in enumerate(self.tids) if self.fold[x]==f]
   for j,t in enumerate(TASKS):
    try:c,s=fit_m0_mad(y[:,j],w)
    except ValidationError as e:fail.append(f'fold_{f}:{t}:{e}');continue
    z[ix,:,j]=(raw[ix,:,j]-c)/s
  return z,represented,fail
