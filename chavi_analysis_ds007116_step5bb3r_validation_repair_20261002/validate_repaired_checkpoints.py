from pathlib import Path
import csv,hashlib,json
BASE=Path(__file__).resolve().parent;B3=BASE.parent/'chavi_analysis_ds007116_step5bb3_confirmatory_simulation_20261002'
inv=list(csv.DictReader((BASE/'affected_replicate_inventory.csv').open()));expected={(r['stage'],r['scenario_id'],int(r['outer_id'])) for r in inv};seen=set();errors=[]
for stage,sid,o in sorted(expected):
 p=BASE/'runtime_repaired'/stage/f'{sid}__{o:04d}.json';src=B3/'runtime'/stage/f'{sid}__{o:04d}.json'
 if not p.exists():errors.append(f'missing:{stage}:{sid}:{o}');continue
 x=json.loads(p.read_text());s=json.loads(src.read_text());seen.add((stage,sid,o))
 checks=[x['stage']==stage,x['scenario_id']==sid,x['outer_id']==o,x['source_runtime_sha256']==hashlib.sha256(src.read_bytes()).hexdigest(),x['dataset_sha256']==s['dataset_sha256'],len(x['records'])==6,all(r['attempted']==999 for r in x['records']),{(r['scale_method'],r['endpoint']) for r in x['records']}=={(a,b) for a in ('MAD','SD') for b in ('level_icc_a1','mean_level_change','rms_shape_displacement')}]
 if not all(checks):errors.append(f'invalid:{stage}:{sid}:{o}')
contracts={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (BASE/'corrected_interval_execution_contract.json',BASE/'confirmatory_execution_contract.json')}
result={'status':'PASS' if not errors and seen==expected else 'FAIL','expected_repaired_outer_records':len(expected),'validated_repaired_outer_records':len(seen),'errors':errors,'original_runtime_provenance':'every repaired checkpoint records and revalidates original runtime SHA-256 plus dataset SHA-256','contract_sha256':contracts,'patched_source_sha256':{n:hashlib.sha256((BASE/n).read_bytes()).hexdigest() for n in ('simulation_core.py','run_stage.py','recalculate_affected.py')}}
(BASE/'checkpoint_validation_results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));raise SystemExit(result['status']!='PASS')
