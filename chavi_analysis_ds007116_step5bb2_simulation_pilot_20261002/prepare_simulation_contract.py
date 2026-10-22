"""Freeze Step 5B-B2 simulation scope before execution."""
from __future__ import annotations
import csv,hashlib,json,platform,sys
from pathlib import Path
import numpy as np
from simulation_core import H,C,SCENARIOS,TASK_ORDER,MASTER_SEED
BASE=Path(__file__).resolve().parent;ROOT=BASE.parent
AUTH="Researcher authorization for simulated-data implementation and pilot evaluation through execution of this prompt."
def sha(p):
 d=hashlib.sha256();d.update(Path(p).read_bytes());return d.hexdigest()
def writecsv(name,rows):
 with (BASE/name).open("w",encoding="utf-8",newline="") as f:w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n");w.writeheader();w.writerows(rows)
def text(name,s):(BASE/name).write_text(s.strip()+"\n",encoding="utf-8",newline="\n")
def main():
 expected={
 "../chavi_analysis_ds007116_step5ba_clean_rebuild_20261001/step5ba_rebuild_contract.json":"619aa1e05fedfc688484691cb1e54d363c8e8ff4a63b9a5e179d05d516ac23c6",
 "../chavi_analysis_ds007116_step5ba_clean_rebuild_20261001.zip":"5be859872962dd336e6fc0edd6f239167235ebdb09d1482c2862bea8eacf5fec",
 "../chavi_analysis_ds007116_step5bb1_profile_protocol_20261001.zip":"582508b67af43fe4723a4f781ad575ac9146c4ff032028987c74f047451650cd",
 "../chavi_analysis_ds007116_step5bb1_profile_protocol_20261001/profile_analysis_specification_recommended.json":"31d3109bddd9c5cee215c2b1a2e1d49781c227297f2de6ab10f0e696aed081ab"}
 for rel,h in expected.items():
  if sha((BASE/rel).resolve())!=h:raise ValueError(f"input hash mismatch: {rel}")
 registry={"status":"frozen_before_main_pilot","task_order":TASK_ORDER,"mu":[10,12,14,16,18],"helmert_H":H.tolist(),"level_variance":.5,"shape_covariance":"0.5*I4","noise_covariance":"0.5*C","C":C.tolist(),"independence":"identities independent; epsilon independent across visits; level/shape/noise mutually independent","reference_roles":"auxiliary baselines follow same visit-1 marginal; target baseline is linked target visit 1","rounding":"numpy.rint: nearest integer, ties to even; exact half ties have probability zero under continuous precursor","S6":"each task/occasion deviation independently retained with probability 0.4; otherwise exactly mu; point mass 0.6 implies median absolute deviation zero because P(|Y-mu|=0)>=0.6","scenarios":SCENARIOS}
 (BASE/"scenario_registry.json").write_text(json.dumps(registry,indent=2)+"\n",encoding="utf-8")
 contract={"schema_version":"1.0.0","date":"2026-10-02","authorization":AUTH,"scope":"M0 known-truth simulation pilot only; no empirical CHAVI analysis","inputs":expected,"upstream_b1_status":"recommended and unapproved for empirical execution","target_ids":["S{scenario}_{scale}_{endpoint}"],"target_definition":"common target-pair distribution transformed by population baseline-reference task means and population MAD or SD","target_formula":{"icc_a1_limit":"2*Cov(L1,L2)/(Var(L1)+Var(L2)+(E[L2]-E[L1])^2)","mean_level_change":"E[L2-L1]","rms_shape_displacement":"sqrt(E[||P(Z2-Z1)||^2]/5)","P":"I-11^T/5"},"reference":{"targets":52,"auxiliaries":57,"fold_counts":[11,11,10,10,10],"M0_center":"arithmetic mean","MAD":"median(abs(y-median(y)))/0.6744897501960817","SD":"sample SD ddof=1","baseline_only":True},"scenario_registry_sha256":sha(BASE/"scenario_registry.json"),"methods":{"P1":"oracle-reference conditional participant bootstrap","P2":"estimated-reference fixed-transform participant bootstrap","P3":"identity-linked unstratified joint refit","P4":"identity-linked fold-stratified joint refit; conditions on fold counts"},"intervals":{"families":["percentile","basic"],"level":.95,"quantile_method":"linear","eligible":"at least 475 of 499 valid and at least 20 valid estimates per nominal tail","failure":"no redraw; valid-only interval explicitly conditioned; unavailable counted unconditionally","basic":"[2*theta_hat-q0.975,2*theta_hat-q0.025]","clipping":False},"run_size":{"scenarios":6,"outer_per_scenario":100,"bootstrap_replicates":499,"scales":["MAD","SD"],"endpoints":["level_icc_a1","mean_level_change","rms_shape_displacement"]},"randomness":{"master_seed":MASTER_SEED,"algorithm":"NumPy PCG64DXSM","derivation":"first 128 bits of SHA-256 of UTF-8 pipe-joined master seed and scientific stream identifiers","dataset_stream":"outer_dataset|scenario|outer","shared_unstratified_target_draw":"bootstrap_target_unstratified|scenario|outer shared by P1/P2/P3","shared_auxiliary_draw":"bootstrap_auxiliary|scenario|outer shared by P3/P4","stratified_target_draw":"bootstrap_target_stratified|scenario|outer","replicate_id":"fixed row offset 0..498 within its keyed vector draw"},"software":{"python":sys.version.split()[0],"numpy":np.__version__,"platform":platform.platform()},"deferred":["M1","age support","strict-V","prediction/reportability","BCa","leave-one-target-out","large factorial design","empirical execution"],"structural_policy":{"S6_MAD":"population target undefined; failure behavior only","S6_SD":"defined","unused_fold":"fit not required when no analyzed target from that fold","negative_icc":"retain","undefined":"never replace by zero"},"manifest_convention":"all distributable members except manifest itself and enclosing ZIP"}
 (BASE/"simulation_execution_contract.json").write_text(json.dumps(contract,indent=2)+"\n",encoding="utf-8")
 text("contract_sha256.txt",sha(BASE/"simulation_execution_contract.json")+"  simulation_execution_contract.json")
 changes=[
 {"change_id":"C1","b1_gap":"generic bool cast accepts string 'no'","new_implementation":"explicit yes/no or Boolean parser; missing/unknown rejected","module":"simulation_core.py"},
 {"change_id":"C2","b1_gap":"absolute floor invalidates small valid ICC/trace variation","new_implementation":"stable common centering/rescaling and relative-only degeneracy checks; no clipping","module":"simulation_core.py"},
 {"change_id":"C3","b1_gap":"multiplicity maps not checked against exact expected fit","new_implementation":"full identity/key/weight/fold/linkage equality validation","module":"simulation_core.py"},
 {"change_id":"C4","b1_gap":"unused-fold policy implicit","new_implementation":"fit only folds represented among positive-weight analyzed targets","module":"run_pilot.py"},
 {"change_id":"C5","b1_gap":"no simulated fitting/bootstrap engine","new_implementation":"four procedures with integer-frequency semantics and no redraw","module":"run_pilot.py"}]
 writecsv("implementation_change_register.csv",changes)
 text("statistical_target_and_truth_derivations.md",'''# Statistical targets and truth derivations

The target distribution is the stated target-pair DGM, transformed by common population baseline-reference task means `m` and scales `d`; it is not a realized cross-fitted estimate. Let `Z_t=D^{-1}(Y_t-m)`, `a=1/5`, `L_t=a'Z_t`, and `P=I-11'/5`.

For two measurements, the large-`n` ANOVA components are `MS_R -> (v1+v2+2c)/2`, `MS_E -> (v1+v2-2c)/2`, and `2 MS_C/n -> (mu2-mu1)^2`. Therefore ICC(A,1) tends to `2c/[v1+v2+(mu2-mu1)^2]`, not merely a latent correlation. Mean change is `a'D^{-1}E(Y2-Y1)`. RMS shape displacement is `sqrt({tr[P D^{-1}Var(Y2-Y1)D^{-1}] + ||P D^{-1}E(Y2-Y1)||^2}/5)`.

A common task-wise reference center cancels from `Z2-Z1`. At fixed scales, mean level change and centered-shape displacement are invariant to center perturbation. Scale remains in both; fold-specific centers need not cancel across different participants when computing between-person level ICC, so level ICC can change. Population MAD and SD are distinct nuisance scales.

Continuous marginal scores are Gaussian with covariance `0.5*11' + 0.5*HH' + 0.5*C`; every marginal variance is 1.4, so normal-consistent MAD and SD equal `sqrt(1.4)`. Cross-visit covariance is `0.5*rho_level*11' + 0.5*rho_shape*HH'`. S5 reference scales use the exact rounded-normal marginal probabilities and two independent 500,000-pair numerical batches for endpoint truth. In S6 the independent retention mask gives `P(Y=mu)=0.6`, hence median absolute deviation zero, while variance is `0.4*1.4>0`; MAD targets are structurally undefined and SD targets are valid. Independent numerical streams validate analytic truths.

P1 targets ordinary sampling under a known population transformation. P2 is evaluated against that same unconditional population target but freezes an estimated transformation within each bootstrap; this does not establish fully conditional validity under overlap. P3/P4 propagate their specified role-conditioned reference resampling. None reproduce recruitment, selection, or empirical missingness.
''')
 text("environment_requirements.txt",f"Validated: Python {sys.version.split()[0]}\nNumPy {np.__version__}\nPlatform: {platform.platform()}\nPinned dependency: numpy=={np.__version__}\nStandard library only otherwise.\n")
 decisions=[
 {"decision_id":"D01","status":"established upstream","decision":"M0 geometry, Design-B fold structure, task order"},
 {"decision_id":"D02","status":"authorized for simulation only","decision":"six-scenario 100x499 pilot"},
 {"decision_id":"D03","status":"pilot comparison","decision":"P1-P4 with percentile/basic intervals"},
 {"decision_id":"D04","status":"deferred","decision":"M1, BCa, selection, LOTO and large factorial mechanisms"},
 {"decision_id":"D05","status":"requires confirmatory evidence","decision":"final interval/procedure selection"},
 {"decision_id":"D06","status":"prohibited inference","decision":"empirical, clinical, causal, individual or novelty conclusion"}]
 writecsv("scientific_readiness_and_decision_register.csv",decisions)
 claims=[
 {"claim_id":"CL1","status":"testable here","claim":"new implementation repairs specified defects"},
 {"claim_id":"CL2","status":"pilot finding only","claim":"procedure behavior in six frozen scenarios"},
 {"claim_id":"CL3","status":"not established","claim":"nominal coverage generally or for empirical CHAVI"},
 {"claim_id":"CL4","status":"not established","claim":"novel or superior method"},
 {"claim_id":"CL5","status":"prohibited","claim":"empirical participant/profile inference"}]
 writecsv("claims_register.csv",claims)
 print(json.dumps({"contract_sha256":sha(BASE/"simulation_execution_contract.json"),"scenario_registry_sha256":sha(BASE/"scenario_registry.json")},sort_keys=True))
if __name__=="__main__":main()
