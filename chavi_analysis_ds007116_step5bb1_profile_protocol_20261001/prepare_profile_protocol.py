"""Build the non-empirical Step 5B-B1 review artifacts and support audit."""
from __future__ import annotations

import csv, hashlib, json, math
from collections import defaultdict
from pathlib import Path

OUT=Path(__file__).resolve().parent; ROOT=OUT.parent
CLEAN=ROOT/"chavi_analysis_ds007116_step5ba_clean_rebuild_20261001"
STATUS="RECOMMENDED SCIENTIFIC PROTOCOL — NOT YET ADOPTED FOR EMPIRICAL EXECUTION."
CONTRACT_HASH="619aa1e05fedfc688484691cb1e54d363c8e8ff4a63b9a5e179d05d516ac23c6"
ZIP_HASH="5be859872962dd336e6fc0edd6f239167235ebdb09d1482c2862bea8eacf5fec"
TASKS=["letter_nback","face_memory","matrix_reasoning","emotion_recognition","dominant_finger_tapping"]

def sha(p):
 d=hashlib.sha256()
 with Path(p).open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):d.update(b)
 return d.hexdigest()
def readcsv(p):
 with Path(p).open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def writecsv(name,rows,fields=None):
 fields=fields or list(rows[0]);
 with (OUT/name).open("w",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n",extrasaction="ignore");w.writeheader();w.writerows(rows)
def text(name,s):(OUT/name).write_text(s.strip()+"\n",encoding="utf-8",newline="\n")

def verify_upstream():
 manifest=readcsv(CLEAN/"milestone_artifact_manifest.csv")
 if len(manifest)!=46:raise ValueError("clean manifest row count mismatch")
 for r in manifest:
  p=CLEAN/r["relative_path"]
  if not p.is_file() or p.stat().st_size!=int(r["size_bytes"]) or sha(p)!=r["sha256"]:raise ValueError(f"clean manifest mismatch: {p}")
 long=readcsv(CLEAN/"transformed_task_observations_long.csv");wide=readcsv(CLEAN/"transformed_profiles_wide.csv")
 lk=[tuple(r[x] for x in ["participant_id","analytical_stratum","session_id","task_key","model","scale_method"]) for r in long]
 wk=[tuple(r[x] for x in ["participant_id","analytical_stratum","session_id","model","scale_method"]) for r in wide]
 if len(long)!=5520 or len(lk)!=len(set(lk)) or len(wide)!=1104 or len(wk)!=len(set(wk)):raise ValueError("transformation key/count mismatch")
 expected={"reference_cohort_manifest.csv":(109,109,545),"primary_vf_source_rows.csv":(52,104,520),"vonly_reselected_source_rows.csv":(45,90,450),"fixed_primary_pair_strict_v_source_rows.csv":(41,82,410)}
 source_union=set()
 for name,(nperson,nsession,nrow) in expected.items():
  rr=readcsv(CLEAN/name);ids={r["participant_id"] for r in rr};sessions={(r["participant_id"],r["session_id"]) for r in rr};keys={(r["participant_id"],r["session_id"],r["task_key"]) for r in rr}
  if (len(ids),len(sessions),len(rr),len(keys))!=(nperson,nsession,nrow,nrow):raise ValueError(f"source identity mismatch: {name}")
  if name!="reference_cohort_manifest.csv":source_union|=keys
 if len(source_union)!=540:raise ValueError("physical source union mismatch")
 folds=readcsv(CLEAN/"fold_fitting_manifest.csv")
 if [int(r["held_out_target_count"]) for r in folds]!=[11,11,10,10,10] or [int(r["training_count"]) for r in folds]!=[98,98,99,99,99] or any(r["self_inclusion_count"]!="0" or r["auxiliary_count"]!="57" for r in folds):raise ValueError("fold identity/count mismatch")
 params=readcsv(CLEAN/"transformation_parameters.csv")
 pk={(r["reference_design"],r["target_fold"],r["task_key"],r["model"],r["scale_method"]) for r in params}
 if len(params)!=100 or len(pk)!=100:raise ValueError("parameter key/count mismatch")

def support_audit():
 rows=readcsv(CLEAN/"transformed_task_observations_long.csv")
 groups=defaultdict(list)
 for r in rows: groups[(r["participant_id"],r["analytical_stratum"],r["model"],r["scale_method"])].append(r)
 ledger=[]
 for (pid,stratum,model,scale),rs in sorted(groups.items()):
  sessions=sorted({r["session_id"] for r in rs},key=lambda x:int(x.split("-")[1]))
  if len(sessions)!=2: raise ValueError("pair must have two sessions")
  ok=[]; reasons=[]; refs=[]; params=[]
  for ses in sessions:
   sr=[r for r in rs if r["session_id"]==ses]
   if [r["task_key"] for r in sorted(sr,key=lambda x:TASKS.index(x["task_key"]))]!=TASKS:raise ValueError("task set/order failure")
   complete=all(r["supported"]=="yes" and r["coordinate"]!="" for r in sr);ok.append(complete)
   for r in sr:
    if not complete and r["supported"]!="yes":reasons.append(f'{ses}:{r["task_key"]}:{r["unsupported_reason"]}')
    refs.append(f'{ses}:{r["task_key"]}:{r["source_filename"]}#{r["source_row_reference"]}')
    params.append(f'{ses}:{r["task_key"]}:{r["parameter_key_sha256"]}')
  ledger.append({"participant_id":pid,"analytical_stratum":stratum,"session_1":sessions[0],"session_2":sessions[1],"coordinate_model":model,"scale_method":scale,"visit_1_all_five_supported":"yes" if ok[0] else "no","visit_2_all_five_supported":"yes" if ok[1] else "no","pair_fully_supported":"yes" if all(ok) else "no","exclusion_reasons":";".join(reasons),"task_source_references":";".join(refs),"parameter_provenance":";".join(params),"contract_sha256":CONTRACT_HASH})
 writecsv("profile_pair_support_manifest.csv",ledger)
 summary=[]
 for k in sorted({(r["analytical_stratum"],r["coordinate_model"],r["scale_method"]) for r in ledger}):
  rr=[r for r in ledger if (r["analytical_stratum"],r["coordinate_model"],r["scale_method"])==k]
  summary.append({"analytical_stratum":k[0],"coordinate_model":k[1],"scale_method":k[2],"candidate_pairs":len(rr),"complete_supported_pairs":sum(r["pair_fully_supported"]=="yes" for r in rr),"excluded_pairs":sum(r["pair_fully_supported"]=="no" for r in rr),"interpretation":"support audit only; no profile feature computed"})
 writecsv("profile_pair_support_summary.csv",summary)
 exp={('primary_vf','M1'):42,('vonly_reselected','M1'):36,('fixed_primary_pair_strict_v','M1'):33}
 for s in summary:
  if s["coordinate_model"]=="M1" and s["complete_supported_pairs"]!=exp[(s["analytical_stratum"],"M1")]:raise ValueError("M1 pair denominator mismatch")
 return summary

def evidence_inventory():
 items=[
 (CLEAN/"step5ba_rebuild_contract.json","contract","adopted transformation contract","current validated","downstream inputs and formulas"),
 (CLEAN/"contract_sha256.txt","integrity","contract digest","current validated","upstream integrity"),
 (ROOT/"chavi_analysis_ds007116_step5ba_clean_rebuild_20261001.zip","package","clean rebuild ZIP","current validated","upstream integrity"),
 (CLEAN/"milestone_artifact_manifest.csv","manifest","package membership/hashes","current validated","input integrity"),
 (CLEAN/"transformed_task_observations_long.csv","data","support/provenance audit only","current validated","profile eligibility"),
 (CLEAN/"transformed_profiles_wide.csv","data","schema and absence of profile outputs","current validated","profile input contract"),
 (CLEAN/"participant_fold_manifest.csv","identity map","target folds","current validated","joint bootstrap identity rules"),
 (CLEAN/"fold_fitting_manifest.csv","identity map","fit/holdout sets","current validated","joint bootstrap fitting rules"),
 (CLEAN/"prepare_contract.py","code","cohort/fold reconstruction","current validated","source definitions"),
 (CLEAN/"run_clean_rebuild.py","code","coordinate generation","current validated","transformation semantics"),
 (CLEAN/"independent_validator.py","code","independent upstream validation","current validated","trust boundary"),
 (ROOT/"chavi_audit_ds007116_step3b_20260909/task_observations_long.csv","source table","canonical task observations","current upstream","source trace"),
 (ROOT/"chavi_analysis_ds007116_step5a_measurement_specification_20260916/profile_estimand_specification.md","method draft","historical formulas","historical proposed","definition mapping"),
 (ROOT/"chavi_analysis_ds007116_step5a_measurement_specification_20260916/profile_formula_registry.csv","method table","historical formulas","historical proposed","definition mapping"),
 (ROOT/"chavi_analysis_ds007116_step5a_measurement_specification_20260916/uncertainty_specification.md","method draft","conditional bootstrap sketch","historical proposed","bootstrap revision"),
 (ROOT/"chavi_analysis_ds007116_step5a_measurement_specification_20260916/ipsative_scoring_risk.md","risk note","centering dependence","historical proposed","claim limits"),
 (ROOT/"chavi_analysis_ds007116_step5ad_decision_freeze_20260916/transformation_uncertainty_plan.md","method draft","refit bootstrap sketch","historical proposed/superseded","joint bootstrap revision"),
 (ROOT/"chavi_analysis_ds007116_step5ad_decision_freeze_20260916/profile_estimand_hierarchy.md","method draft","earlier hierarchy","historical proposed/superseded","primary set"),
 (ROOT/"chavi_analysis_ds007116_step4b_five_tasks_20260916/step4b_review_report.md","report","historical task-level results","historical different cohorts","baseline context only"),
 (ROOT/"CURRENT_PROJECT_STATE.md","handoff","status assertions checked against artifacts","summary only","scope reconstruction"),
 (ROOT/"PROJECT_MASTER_CONTEXT.md","handoff","project purpose and limitations","summary only","claim boundary"),
 (ROOT/"RESEARCH_STATUS.md","handoff","research roadmap","summary only","candidate contribution")]
 out=[]
 for p,t,role,status,decision in items:
  out.append({"relative_path":p.relative_to(ROOT).as_posix(),"artifact_type":t,"role":role,"size_bytes":p.stat().st_size if p.exists() else "","sha256":sha(p) if p.exists() else "","fully_inspected":"yes" if p.exists() else "no","evidence_class":"directly inspected" if p.exists() else "missing","scientific_status":status if p.exists() else "missing","relevant_content":role,"downstream_decision":decision})
 writecsv("research_evidence_inventory.csv",out)

def literature():
 rows=[
 ["Bulut, Davison & Rodriguez","Estimating Between-Person and Within-Person Subscore Reliability with Profile Analysis","2017","10.1080/00273171.2016.1253452","published","abstract verified (PubMed)","Partitions subscore reliability into between-/within-person components under its model","A framework for profile reliability exists","Does not validate CHAVI cross-fitted transformations or long-interval stability","Do not claim decomposition is novel; simulation needed before adoption"],
 ["Styck, Beaujean & Watkins","Profile Reliability of Cognitive Ability Subscores in a Referred Sample","2019","10.1037/arc0000064","published","full text located","Applies profile reliability to cognitive subscores","Profile interpretation needs evidence beyond global score stability","Different instruments, cohort, scaling, and design","Treat as closely related application"],
 ["Stephenson et al.","Long-Term Stability of IQ Scores for Children With Neurodevelopmental Disabilities: Stable Global IQ But Unstable Index, Subtest, and Profile IQ Scores","2026","10.1007/s10803-026-07352-x","published open access","full text verified","Long-term stability; profileR between-/within-person analysis; mixed-model ICCs","Shows a recent related longitudinal clinical application","SB-5 normed scores and 650 clinical cases do not establish CHAVI results","Motivates but cannot predict CHAVI level/shape ordering"],
 ["Kuchina, Bolsinova, Vermunt & Emons","Added Value of Subscores: Can We Accurately Evaluate It?","2026","10.3102/10769986261463520","published","abstract-only publisher access","Studies accuracy of methods assessing subscore added value","Added-value assessment is an existing problem","Abstract insufficient to transfer its methods; CHAVI prediction utility untested","No claim that five profiles add value over level"],
 ["Koo & Li","A Guideline of Selecting and Reporting Intraclass Correlation Coefficients for Reliability Research","2016","10.1016/j.jcm.2016.02.012","published; erratum 2017","full text/metadata and erratum verified","Requires model/type/definition specification","ICC labels are ambiguous without formula","Guideline thresholds are not biological truths","Report ICC(A,1)/ICC(C,1) formulas; heed erratum DOI 10.1016/j.jcm.2017.10.001"],
 ["Morris, White & Crowther","Using simulation studies to evaluate statistical methods","2019","10.1002/sim.8086","published open access","full text verified","ADEMP and Monte Carlo error reporting","Provides simulation planning framework","Does not supply CHAVI DGM or validate intervals","Use ADEMP and prespecified performance measures"],
 ["Sevchik et al.","A longitudinal data resource to study brain development and transdiagnostic variation in executive function","2026","10.1038/s41597-026-08095-1","published open access early version","abstract/descriptor metadata verified","Describes Penn LEAD: 132 adolescents and multimodal/cognitive longitudinal data","Establishes dataset purpose and boundary","Does not validate this five-task profile construct or exact timing assumptions","Use as dataset source, not psychometric validation"],
 ["Cronbach & Gleser","Assessing similarity between profiles","1953","10.1037/h0057173","published","citation and project evidence reviewed","Profile similarity is dimension-specific","Profile geometry is established mathematics","Does not choose a CHAVI primary estimand","Keep level/shape/scatter distinct"],
 ["McGraw & Wong","Forming Inferences About Some Intraclass Correlation Coefficients","1996","10.1037/1082-989X.1.1.30","published","citation and project evidence reviewed","Defines ICC model/type/agreement distinctions","Supports explicit formulas","Two-occasion developmental data challenge reliability language","Call estimates observed longitudinal agreement"],
 ]
 fields=["authors","title","year","doi_or_url","publication_status","access_level","method_and_assumptions","establishes","does_not_establish_for_chavi","protocol_implication"]
 writecsv("literature_evidence_matrix.csv",[dict(zip(fields,r)) for r in rows],fields)
 text("literature_search_log.md",f'''# Literature search log

Search date: 2026-10-01. Scope: profile reliability, longitudinal profile stability, subscore added value, ICC definition/correction, shared-reference uncertainty, clustered resampling, robust/discrete scoring, and ADEMP. Exact DOI/title queries were run against publisher pages, PubMed/PMC, Crossref-indexed results, Scientific Data, Springer Nature, Wiley, APA-hosted records, and official OpenNeuro/GitHub mirrors. Primary/official sources were prioritized.

Access was recorded conservatively. Stephenson et al. and Morris et al. were inspected as full text; Bulut was verified from PubMed abstract; Kuchina was abstract-only; the Penn LEAD descriptor was verified from the publisher record and official dataset mirror. No failed exact-phrase search was treated as proof of novelty. Search results support related-method mapping, not method transfer or CHAVI validation.

Verified corrections: Koo & Li's article has an erratum, DOI `10.1016/j.jcm.2017.10.001`; formulas in this package are independently stated rather than copied from an uncorrected table.
''')
 nov=[
 {"candidate":"level/centered-shape/scatter geometry","category":"established method","evidence":"Cronbach-Gleser lineage and elementary orthogonal projection","claim_allowed":"implementation-specific transparent decomposition"},
 {"candidate":"between-/within-person profile reliability","category":"existing closely related contribution","evidence":"Bulut et al.; Styck et al.; Stephenson et al.","claim_allowed":"comparison target only"},
 {"candidate":"five-task Penn LEAD application","category":"dataset-specific application","evidence":"current audited CHAVI pipeline","claim_allowed":"audited application if future empirical protocol adopted"},
 {"candidate":"joint propagation through overlapping cross-fitted MAD references","category":"possible methodological extension","evidence":"no direct validation located; exact-design method transfer unproven","claim_allowed":"candidate contribution"},
 {"candidate":"coverage and failure behavior of proposed bootstrap","category":"requires future experiments","evidence":"ADEMP study not executed","claim_allowed":"none until known-truth simulation"}]
 writecsv("novelty_and_contribution_matrix.csv",nov)

def estimands():
 fields=["estimand_id","name","question","formula","observational_unit","analysis_population","support_rule","held_fixed","estimated","interpretation","range_negative","undefined","assumptions","status","uncertainty","limitations"]
 rows=[
 ["LEVEL_ICC_A1","Level absolute agreement","Do participants retain absolute overall five-task level across selected occasions?","(MS_R-MS_E)/(MS_R+(k-1)MS_E+k(MS_C-MS_E)/n), k=2","participant pair","Primary V/F M0/MAD","both visits complete five","selected occasions; task set; transformation contract","variance components from paired levels","absolute observed longitudinal agreement; occasions fixed","unbounded in finite samples; negative possible","zero numerical denominator","independent participants; comparable occasions; variance-model adequacy","primary","conditional percentile bootstrap candidate; joint refit only after simulation","not pure measurement reliability; level is not validated g"],
 ["LEVEL_MEAN_CHANGE","Mean level change","Is there systematic observed level shift?","mean_i(L_i2-L_i1)","participant pair","same as primary","complete pairs","same","mean difference","descriptive shift","real; negative allowed","no pairs","independent participants","primary descriptive","cluster bootstrap candidate","cannot separate development/practice/state"],
 ["SHAPE_RMS_DISPLACEMENT","RMS absolute shape displacement","How large is centered-profile movement?","sqrt(mean_i D_shape_i^2); D_shape_i=sqrt(||q_i2-q_i1||^2/5)","participant pair","same as primary","complete pairs","task order and scaling","pair displacements","absolute shape movement in coordinate units","[0,infinity)","no pairs","commensurate transformed coordinates","primary descriptive","cluster bootstrap candidate","not reliability; combines signal change and error"],
 ["SHAPE_TRACE_ASSOC","Shape trace association","Do participant deviations in 4D shape align across occasions?","sum_i <c_i1-cbar1,c_i2-cbar2>/sqrt(sum_i||c_i1-cbar1||^2 sum_i||c_i2-cbar2||^2)","participant pair","same as primary","complete pairs","orthonormal basis class","cross-occasion centered contrasts","rotation-invariant vector association/consistency; not ICC","[-1,1]; negative possible","zero contrast variance at either occasion","independent participants; linear association","secondary descriptive; adoption unresolved pending simulation","bootstrap candidate after validation","not absolute agreement or true-score reliability"],
 ["SCATTER_ICC_A1","Scatter absolute agreement","Is within-occasion dispersion absolutely stable?","ICC(A,1) applied to S_it=sqrt(||q_it||^2/5)","participant pair","same as primary","complete pairs","scatter denominator 5","paired scatter values","absolute agreement","finite-sample negative possible","zero numerical denominator","same ICC assumptions","secondary","conditional bootstrap candidate","nonlinear and scale-dependent"],
 ["PROFILE_CORR_DIST","Profile-correlation distribution","How often are within-person shapes directionally similar?","r_i=q_i1^Tq_i2/(||q_i1||||q_i2||)","participant pair","same as primary","both norms above declared threshold","task set","participant correlations","descriptive direction similarity","[-1,1]","flat/near-flat shapes","five components; nonlinear fragile measure","descriptive only","report distribution and unsupported count; intervals not primary","high correlation can coexist with magnitude disagreement"],
 ["TASK_ICC_MATCHED","Matched-cohort task ICC(A,1)","What is each task's agreement on the exact profile cohort?","ICC(A,1) per task","participant pair","same configuration/pairs","complete profile pair","cohort and occasions","task variance components","matched baseline","negative possible","zero denominator","ICC assumptions","secondary baseline","same bootstrap framework","five comparisons; not profile reliability"]]
 writecsv("profile_estimand_dictionary.csv",[dict(zip(fields,r)) for r in rows],fields)

def decisions():
 rows=[
 ["D01","Design B fold map and transformation contract","Established upstream decision","use unchanged","upstream accepted contract"],
 ["D02","Primary configuration","Recommended decision with rationale","Primary V/F, M0, MAD","clean complete cohort and adopted robust scale"],
 ["D03","Primary estimands","Recommended decision with rationale","level ICC(A,1), mean level change, RMS shape displacement","small coherent set separating agreement, shift, and movement"],
 ["D04","Vector shape association","Unresolved decision requiring researcher adoption","secondary descriptive trace association after simulation","rotation-invariant but not classical reliability"],
 ["D05","M0/SD","Optional sensitivity","same Primary pairs","isolates scale choice"],
 ["D06","M1 comparison","Recommended decision with rationale","M0 versus M1 on identical M1-supported pairs; full M0 separately","prevents N=52 versus N=42 confounding"],
 ["D07","Strict-V definitions","Recommended decision with rationale","fixed-pair QC and reselected-occasion sensitivities remain separate","different selection interventions"],
 ["D08","Conditional interval","Unresolved decision requiring researcher adoption","percentile candidate after simulation","coverage not established"],
 ["D09","Joint refit interval","Unresolved decision requiring researcher adoption","identity-linked unstratified target/auxiliary bootstrap candidate","must validate variable-fold failures and coverage"],
 ["D10","M1 bootstrap support","Recommended decision with rationale","hold original matched-support population fixed initially","avoids changing estimand across replicates"],
 ["D11","Causal/developmental or clinical interpretation","Prohibited inference","do not infer","two occasions and uncertain timing cannot decompose sources"],
 ["D12","Empirical execution","Unresolved decision requiring researcher adoption","not authorized","this milestone is review plus synthetic validation only"]]
 writecsv("scientific_decision_register.csv",[dict(zip(["decision_id","decision","status","recommendation","rationale"],r)) for r in rows])

def docs(summary):
 text("BOOTSTRAP_AND_REFERENCE_UNCERTAINTY_PROTOCOL.md",f'''# Bootstrap and reference-uncertainty protocol

{STATUS}

## A. Conditional bootstrap

Freeze the accepted coordinate table, selected two-visit pairs, folds, parameters, task order, M1 support mask, and estimand definition. For replicate `b`, draw `N` participant identities with replacement; carry both visits and all five tasks with each identity's multiplicity; compute the statistic with multiplicity weights. Never sample visits or tasks separately. Record undefined statistics. Candidate: 10,000 replicates, PCG64 seed recorded in a run contract, equal-tailed percentile limits using NumPy's linear quantile interpolation. Report valid/invalid counts and Monte Carlo uncertainty by rerunning quantile estimation over deterministic batches; do not redraw failures.

This conditions on estimated transformations and selected roles/occasions. It excludes reference-fitting, recruitment, missingness, eligibility, and occasion-reselection uncertainty.

## B. Joint refitting bootstrap candidate

1. Draw 52 original target identities and 57 original auxiliary identities separately with replacement; these fixed roles and counts condition on selection.
2. Attach each target's original fold and both visits. Its target multiplicity is identical in Reference-A fitting and analysis. Use the same auxiliary multiplicity in all five folds; duplicates are frequency weights, never newly independent identities.
3. For fold `f`, remove every copy of every original target identity held out in `f`; fit using remaining target multiplicities plus shared auxiliary multiplicities. Preserve original fold membership. Variable represented fitting counts are expected under unstratified resampling.
4. Re-estimate M0 centers and MAD/SD scales; for M1 re-estimate age coefficients, effective support, and residual scales. Apply each replicate fit to both selected visits.
5. Compute the replicate statistic with target analysis multiplicities. For the initial M1 candidate, retain the original M1-supported identity set and mark a replicate invalid if its refit cannot support those identities; do not pool changing populations.
6. Empty represented folds, too few/distinct ages, zero/numerically degenerate scales, nonfinite values, or undefined statistics are logged once and retained as invalid. No redraw-until-success.

Alternative fold-stratified target resampling guarantees represented folds and conditions on the realized fold counts (11/11/10/10/10); it is a diagnostic comparator, not automatically preferable. Leave-one-target-out, auxiliary-only common reference, and fold-assignment alternatives are future diagnostic designs, not fit here. Shared fold-specific parameters applied to both visits can induce persistence through common location/scale errors; refitting can widen or narrow an interval.

Candidate intervals remain unapproved until ADEMP coverage/failure evidence exists. BCa is not default because small/discrete samples, nonsmooth MADs, and undefined replicates can destabilize acceleration. Percentile limits are a transparent candidate, selected for evaluability—not narrowness. Simulation must compare percentile, basic, and where stable BCa intervals at the same target.

## Deterministic multiplicity fixture

The validator encodes target multiplicities `a=2,b=0`, identical analysis/fit/visit multiplicities, one auxiliary multiplicity map reused in both folds, and exclusion of all copies of each held-out target. Corruptions independently trigger actual validator failures for self-inclusion, decoupled multiplicities, per-fold auxiliary redraws, and independently sampled visits.
''')
 text("SIMULATION_VALIDATION_PLAN.md",f'''# Future ADEMP simulation-validation plan

{STATUS}

## Aims

Evaluate bias, RMSE, interval coverage/width, invalid-estimate and invalid-replicate rates, false-positive behavior under null stability, and sensitivity to transformation/reference uncertainty for the exact proposed statistics. This is method comparison, distinct from the completed deterministic software demonstration.

## Data-generating mechanisms

Generate a superpopulation with five task-specific discrete or continuous source scores, explicit auxiliary and target roles, age, folds, two clustered occasions, latent person level and four-dimensional shape, occasion shift, correlated task noise, and reference-induced dependence. Cross scenarios: no stable person shape; stable shape plus noise; stable level/unstable shape; mean shifts with stable ordering; discrete/tied/ceiling scores; small/zero MAD; heavy tails/influential observations; linear versus nonlinear age; target/reference age mismatch; and reference/target sizes including 57/52 and larger benchmarks. Separate stable differences, genuine change, occasion shifts, correlated noise, shared-reference effects, and nonlinear/support failures factorially where feasible.

## Estimands and truth

Define truth as an analytic population functional when derivable or as a preregistered, independently computed limit using a very large reference population—not the realized sample estimate. Truths include population level ICC(A,1) under the specified two-occasion model, population mean level change, RMS centered-shape displacement, and descriptive trace association. Undefined population cases remain explicit.

## Methods

Compare fixed-parameter conditional bootstrap, unstratified identity-linked joint refitting, fold-stratified joint refitting, and interval types (percentile/basic; BCa only when defined). Compare M0/MAD, M0/SD and fixed-support M1. Evaluate auxiliary-only and leave-one-target-out references as diagnostic methods.

## Performance measures

For each scenario report bias, relative/absolute bias as appropriate, RMSE, empirical 95% coverage, mean/median width, lower/upper tail miss rates, invalid point/replicate/run rates, and null false-positive rate for any adopted hypothesis. Report Monte Carlo standard errors: `sqrt(p(1-p)/R)` for proportions and replicate-based SEs for means. Choose `R` from a prespecified maximum MCSE (e.g. <=0.005 for coverage near .95 requires at least 1,900 successful runs; use a larger round number after pilot failure rates). No claim of power or adequate N=52 precision is made here.
''')
 text("PROFILE_PROTOCOL_REVIEW.md",f'''# CHAVI Step 5B-B1 — Profile estimand, analysis, and uncertainty protocol review

**Status:** {STATUS}

## Outcome and evidence boundary

The accepted Step 5B-A contract hash and clean ZIP hash were directly recomputed and matched. The package manifest, cohort/fold identities, source/provenance keys, transformation code, historical method drafts, reviews, and handoffs were inspected. Handoff assertions are recorded as summaries unless corroborated. Historical Design-C and task-level results are context only; quarantined numerical outputs are not current Design-B results. This review generated no empirical level, scatter, shape, correlation, ICC, bootstrap interval, simulation, classification, or prediction.

The support audit reproduces M1 complete pairs (per MAD or SD): Primary 42/52, reselected strict-V 36/45, and fixed-primary-pair strict-V 33/41. M0 is complete at 52/52, 45/45, and 41/41. Unsupported M1 coordinates remain null; fallbacks are not counted. Expanded transformation rows are representations, not new observations.

## Recommended scientific question

Quantify how observed longitudinal five-task profile stability changes under sample-reference estimation, reference sharing, transformation choice, support restriction, and uncertainty propagation in this small developmental cohort. This is stronger and more feasible than an application UI, task ICCs alone, an assumed “shape is less stable” conclusion, or intervals pasted onto unvalidated methods because it makes the transformation/reference mechanism itself testable. The candidate contribution is the dataset-specific, identity-aware evaluation of cross-fitted MAD transformation uncertainty; novelty and operating performance still require simulation and comparison with existing profile methods.

Observed longitudinal stability is not pure measurement reliability. Two selected occasions with uncertain timing cannot distinguish error, development, practice, state, administration, or task-version change. Such interpretation would require known assessment timing, standardized repeated administration, short-interval replicates and/or multiple waves, version metadata, measurement-invariance evidence, and a longitudinal measurement/error model.

## Geometry and mapping

For task-ordered `z`, use `L=mean(z)`, `q=z-L1`, and `S=sqrt(||q||²/5)`. The fixed 5×4 Helmert matrix has column `k` (1–4) equal to `1/sqrt(k(k+1))` in rows 1..k, `-k/sqrt(k(k+1))` in row k+1, and zero afterward; `c=Hᵀz`. Thus `q=Hc`, `sum(q)=0`, `||q||²=||c||²`, and `||z||²=5L²+||c||²`. Historical formulas agree on denominator 5 but an earlier document incorrectly described five centered entries as five orthogonal components; this protocol records four independent contrasts.

Pair changes are `ΔL`, `ΔS`, `D_shape=sqrt(||q2-q1||²/5)`, and `D_total=sqrt(||z2-z1||²/5)`, with `D_total²=ΔL²+D_shape²`. Profile correlation is defined only above `64*eps*max(||z||,sqrt(5)|L|,tiny)` for each shape norm. This conservative floating-point rule is declared before empirical viewing; a flat/near-flat profile is unsupported. Correlation measures direction and can be high despite magnitude disagreement. Unit-scatter normalization is not default because it changes the estimand.

## Estimand recommendation and comparisons

The small primary set is level ICC(A,1), mean level change, and RMS absolute shape displacement. Shape trace association is a secondary descriptive candidate pending simulation; it is a Frobenius/cosine association of centered 4D person-by-contrast matrices, invariant to a common orthonormal contrast rotation, but is neither an ICC nor classical true-score reliability. Scatter ICC(A,1), participant profile-correlation distribution, and matched-cohort task ICC(A,1)s are secondary/descriptive. ICC(C,1) for level may be reported descriptively to expose consistency versus agreement, never as an interchangeable primary.

Primary is Primary V/F–M0–MAD. M0/SD uses the same pairs. M0 versus M1 uses identical M1-supported pairs, with full-cohort M0 separately labelled. Fixed-primary-pair strict-V isolates QC on fixed occasions; reselected strict-V changes occasion selection. Cross-sectional age residualization is not a developmental trajectory model. Historical task ICCs with other denominators are context, not matched baselines.

## Readiness and unresolved adoption

Geometry, code paths, support rules, identity-linked bootstrap pseudocode, schemas, and synthetic checks are decision-ready. Empirical execution, interval family, the secondary trace statistic, and joint-bootstrap design require researcher adoption. Coverage and failure behavior require the specified ADEMP study. Reference alternatives—auxiliary-only common fitting, leave-one-target-out, and fold sensitivity—are future diagnostics, not assumed improvements.

## Consolidated recommended project scope

CHAVI should study observed longitudinal level and four-dimensional relative-shape behavior of five explicitly named task measures in Penn LEAD `ds007116` v1.0.6, bounded to the audited 52-person Primary cohort and its declared strict-V and M1-support sensitivities; its proposed methodological contribution is an identity-aware assessment of how cross-fitted internal reference estimation, shared parameters, robust scaling, and support rules affect profile-stability summaries, evaluated by independent synthetic verification and a preregistered ADEMP known-truth simulation before empirical intervals or method claims; it must not interpret the five tasks as validated latent domains, the level as general intelligence, observed changes as decomposed development or measurement error, or any output as diagnostic, clinical, predictive, individually reportable, or proof of reliability.
''')

def spec_and_other(summary):
 h=[]
 for j in range(4):
  k=j+1;col=[1/math.sqrt(k*(k+1))]*k+[-k/math.sqrt(k*(k+1))]+[0.0]*(4-k);h.append(col)
 H=[[h[j][i] for j in range(4)] for i in range(5)]
 spec={"schema_version":"1.0.0","status":STATUS,"authorization_boundary":{"allowed":"review, support audit, deterministic synthetic validation","not_authorized":["empirical profile features","empirical ICCs","empirical bootstrap","Monte Carlo","individual interpretation"]},"accepted_upstream":{"contract_sha256":CONTRACT_HASH,"clean_zip_sha256":ZIP_HASH,"dataset":"ds007116 v1.0.6"},"input_artifacts":[{"path":"../chavi_analysis_ds007116_step5ba_clean_rebuild_20261001/step5ba_rebuild_contract.json","sha256":CONTRACT_HASH},{"path":"../chavi_analysis_ds007116_step5ba_clean_rebuild_20261001.zip","sha256":ZIP_HASH}],"task_order":TASKS,"contrast_matrix_H_5x4":H,"formulas":{"level":"sum(z)/5","centered_shape":"q=z-L*1","scatter":"sqrt(sum(q^2)/5)","contrasts":"c=H^T z","shape_displacement":"sqrt(||q2-q1||^2/5)","total_displacement":"sqrt(||z2-z1||^2/5)","profile_correlation":"q1^T q2/(||q1||||q2||)"},"identities":["q=Hc","sum(q)=0","||q||^2=||c||^2","||z||^2=5L^2+||c||^2","D_total^2=delta_level^2+D_shape^2"],"numerical_policy":{"dtype":"IEEE float64","comparison_atol":1e-12,"comparison_rtol":1e-10,"correlation_degenerate_if":"||q|| <= 64*eps*max(||z||,sqrt(5)*abs(L),tiny)","flat_policy":"unsupported correlation","missing_policy":"require five finite supported coordinates","m1_fallback_policy":"never insert fallback into M1 coordinate"},"complete_rules":{"profile":"exact task order; five finite supported coordinates","pair":"two selected sessions, each complete","m1":"identical supported pairs for M0-M1 comparison"},"roles":{"primary":"primary_vf/M0/MAD/Design B","scale_sensitivity":"primary_vf/M0/SD same pairs","age_sensitivity":"M0 vs M1 identical M1-supported; full M0 separate","qc_sensitivity":"fixed_primary_pair_strict_v","occasion_sensitivity":"vonly_reselected"},"estimands":{"primary":["LEVEL_ICC_A1","LEVEL_MEAN_CHANGE","SHAPE_RMS_DISPLACEMENT"],"secondary":["SHAPE_TRACE_ASSOC pending adoption/simulation","SCATTER_ICC_A1","TASK_ICC_MATCHED"],"descriptive":["PROFILE_CORR_DIST","LEVEL_ICC_C1"]},"comparisons":{"primary_hypothesis":"none until adoption; emphasize estimation","reference_diagnostics":["Design B","auxiliary-only common reference","leave-one-target-out if feasible","fold-assignment sensitivity"]},"bootstrap":{"conditional":"cluster target identities; transformations fixed","joint":"separate target/auxiliary identity multiplicities; link target fit/analysis; attach folds; exclude all held-out copies; reuse auxiliary multiplicities; refit parameters; no redraw","m1_support":"hold original matched-support population initially","candidate_interval":"equal-tailed percentile with linear quantiles, pending ADEMP","replicates":10000,"seed":"record exact PCG64 seed in adopted run contract","invalid":"retain/log; no redraw"},"simulation_requirements":"See SIMULATION_VALIDATION_PLAN.md; no Monte Carlo executed.","claim_boundaries":["observed stability is not pure reliability","no decomposition of error/development/practice/state/administration/version","five tasks are not five validated domains","level is not validated general intelligence","no individual or clinical inference"],"unresolved":["researcher adoption of empirical protocol","whether to retain shape trace association","interval method after simulation","joint versus fold-stratified bootstrap"],"output_schemas":"executable_output_schemas.json","validation":"independent expected values persisted before production import; actual corruption paths; fresh-process deterministic repeats"}
 (OUT/"profile_analysis_specification_recommended.json").write_text(json.dumps(spec,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 text("recommended_specification_sha256.txt",sha(OUT/"profile_analysis_specification_recommended.json")+"  profile_analysis_specification_recommended.json\nReview artifact only; not an approved empirical execution contract.")
 schemas={"profile_pair_support_manifest.csv":{"primary_key":["participant_id","analytical_stratum","coordinate_model","scale_method"],"rows":sum(int(x["candidate_pairs"]) for x in summary)},"synthetic/fixture_inputs.json":{"synthetic_only":True},"synthetic/independent_expected_outputs.json":{"written_before_production_import":True},"synthetic/production_outputs.json":{"synthetic_only":True},"validation_results.json":{"required_status":"PASS"},"future_empirical_profile_output":{"authorized":False,"required_keys":["participant_id","analytical_stratum","session_id","model","scale_method","spec_sha256"]}}
 (OUT/"executable_output_schemas.json").write_text(json.dumps(schemas,indent=2)+"\n",encoding="utf-8")
 claims=[
 ["C01","Upstream contract and ZIP hashes match","supported current","direct hash verification","yes"],
 ["C02","M1 complete pairs are 42/36/33","supported current","key-based support audit","yes"],
 ["C03","Profile geometry implementation is correct on declared fixtures","synthetic only","independent oracle","yes"],
 ["C04","CHAVI profile reliability is established","prohibited/unsupported","no empirical profile calculation","no"],
 ["C05","Joint bootstrap has correct coverage","unverified hypothesis","ADEMP not run","no"],
 ["C06","Candidate method is novel or publishable","unverified hypothesis","related methods exist; systematic proof absent","no"],
 ["C07","Profile changes reflect development","prohibited inference","confounding and timing uncertainty","no"]]
 writecsv("claims_register.csv",[dict(zip(["claim_id","claim","status","basis","may_state_as_conclusion"],r)) for r in claims])
 text("environment_requirements.txt","Validated: CPython 3.14.0, NumPy 2.5.2, Windows 11 (10.0.26200)\nMinimum declared: Python >=3.10\nPinned scientific dependency: numpy==2.5.2\nStandard library: csv, hashlib, json, math, pathlib, subprocess, unittest, zipfile\nNo pandas, scipy, statsmodels, or network access is required to reproduce synthetic validation.\n")
 text("README_REPRODUCE.md",f'''# Reproduce Step 5B-B1

Folder: `chavi_analysis_ds007116_step5bb1_profile_protocol_20261001/`

Status: {STATUS}

From the CHAVI workspace root:

```powershell
python .\\chavi_analysis_ds007116_step5bb1_profile_protocol_20261001\\prepare_profile_protocol.py
python .\\chavi_analysis_ds007116_step5bb1_profile_protocol_20261001\\independent_profile_validator.py
python -m unittest discover -s .\\chavi_analysis_ds007116_step5bb1_profile_protocol_20261001 -p 'test_profile_protocol.py' -v
python .\\chavi_analysis_ds007116_step5bb1_profile_protocol_20261001\\finalize_protocol.py
```

These commands perform only integrity/support auditing and deterministic synthetic validation. There is intentionally no empirical profile-analysis command. `finalize_protocol.py` verifies preservation, two fresh-process synthetic runs, the manifest convention, and creates the ZIP. The manifest lists every package member except itself and the enclosing ZIP, avoiding circular self-hashes.
''')

def main():
 if sha(CLEAN/"step5ba_rebuild_contract.json")!=CONTRACT_HASH:raise ValueError("contract hash mismatch")
 if sha(ROOT/"chavi_analysis_ds007116_step5ba_clean_rebuild_20261001.zip")!=ZIP_HASH:raise ValueError("clean ZIP hash mismatch")
 verify_upstream();evidence_inventory();summary=support_audit();literature();estimands();decisions();docs(summary);spec_and_other(summary)
 print(json.dumps({"status":"prepared","support":summary},indent=2))
if __name__=="__main__":main()
