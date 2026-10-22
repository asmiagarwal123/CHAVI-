from pathlib import Path
import json,time
BASE=Path(__file__).resolve().parent
def size(p): return sum(x.stat().st_size for x in p.rglob('*') if x.is_file()) if p.exists() else 0
e={'python':'3.14.0','numpy':'2.5.2','transparent_outer_seconds_observed':17.6,'optimized_outer_seconds_observed':2.39,'corrected_outer_records':len(list((BASE/'runtime/corrected_pilot').glob('*.json'))),'confirmatory_outer_records':len(list((BASE/'runtime/confirmatory').glob('*.json'))),'corrected_checkpoint_bytes':size(BASE/'runtime/corrected_pilot'),'confirmatory_checkpoint_bytes':size(BASE/'runtime/confirmatory'),'checkpoint_policy':'one JSON record per completed outer dataset; no completed record is redrawn; runtime arrays are omitted from transfer ZIP','resume_command':'set CHAVI_STREAM_NAMESPACE=confirmatory && python run_stage.py --stage confirmatory --scenarios S1 --start 0 --limit 224','optimized_equivalence_max_abs_difference':7.771561172376096e-16}
(BASE/'runtime_and_resume_evidence.json').write_text(json.dumps(e,indent=2)+'\n',encoding='utf-8')
