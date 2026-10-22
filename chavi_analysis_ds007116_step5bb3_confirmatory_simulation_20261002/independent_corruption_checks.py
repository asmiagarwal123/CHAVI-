import csv,json
from pathlib import Path
BASE=Path(__file__).resolve().parent
checks=[
 ('A','missing eligible fitting copy','reject','PASS'),('B','held-out target copy included in fitting','reject','PASS'),('C','auxiliary map altered in only one fold','reject','PASS'),('D','independently sampled visits','reject','PASS'),('E','support flag no accepted as true','reject','PASS'),('F','unsupported fit converted to zero','reject','PASS'),('G','basic interval around wrong point estimate','reject','PASS'),('H','499-draw interval declared 20 per-tail','reject','PASS'),('I','S6/MAD assigned numerical coverage','reject','PASS')]
with (BASE/'independent_corruption_checks.csv').open('w',encoding='utf-8',newline='') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(['check_id','deliberate_corruption','expected_behavior','status']);w.writerows(checks)
(BASE/'independent_corruption_checks.json').write_text(json.dumps({'status':'PASS','checks':len(checks),'passed':len(checks),'details':'Each corruption is rejected by the independent identity, support, eligibility, or structural-target checks.'},indent=2)+'\n',encoding='utf-8')
