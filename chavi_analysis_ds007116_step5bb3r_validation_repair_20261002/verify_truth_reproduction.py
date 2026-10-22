from pathlib import Path
import hashlib,json,shutil,subprocess,sys,time
BASE=Path(__file__).resolve().parent;B3=BASE.parent/'chavi_analysis_ds007116_step5bb3_confirmatory_simulation_20261002';work=BASE/'reproduction_fixture'/f'truth_{int(time.time()*1000)}';work.mkdir(parents=True)
shutil.copy2(BASE/'truth_engine.py',work/'truth_engine.py');shutil.copy2(B3/'repair_truth.py',work/'repair_truth.py')
cmds=[]
for name in ('truth_engine.py','repair_truth.py'):
 p=subprocess.run([sys.executable,str(work/name)],capture_output=True,text=True);cmds.append({'command':[sys.executable,str(work/name)],'returncode':p.returncode,'stdout':p.stdout.strip(),'stderr':p.stderr.strip()});assert p.returncode==0,p.stderr
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
same=sha(work/'truth_results.csv')==sha(BASE/'truth_results.csv');conv_same=sha(work/'truth_convergence.csv')==sha(BASE/'truth_convergence_restored_from_b2.csv');result={'status':'PASS' if same and conv_same else 'FAIL','isolated_workdir':str(work.relative_to(BASE)).replace('\\','/'),'truth_results_byte_identical_after_engine_and_exact_zero_correction':same,'convergence_byte_identical_to_restored_B2':conv_same,'generated_truth_results_sha256':sha(work/'truth_results.csv'),'frozen_truth_results_sha256':sha(BASE/'truth_results.csv'),'commands':cmds}
(BASE/'truth_reproduction_results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));raise SystemExit(result['status']!='PASS')
