# STEP 5B-C2 — Empirical results and validation report

## Primary results

**Level ICC(A,1) was 0.619; mean level change was 0.366 internal-reference units; pooled RMS centered-shape displacement was 1.002 units.** All P3 and P2 intervals were available with 999/999 valid endpoint estimates. P3 percentile intervals were [0.380, 0.787], [0.178, 0.547], and [0.801, 1.372], respectively. P2 percentile intervals were [0.373, 0.786], [0.182, 0.557], and [0.811, 1.198].

Main sensitivities were: M0/SD yielded ICC 0.599, mean change 0.308, and RMS 0.857; among the identical 42 M1-supported pairs, M0/MAD versus M1/MAD yielded ICC 0.602 versus 0.605, mean change 0.387 versus 0.105, and RMS 1.054 versus 1.107. These are descriptive changes in coordinate definition, not tests.

## What did we learn from the real data?

| Question | Empirical observation | Bounded interpretation |
|---|---:|---|
| Between-person agreement in mean profile level | ICC(A,1) 0.619; P3 95% percentile [0.380, 0.787] | Sample-level absolute agreement for these 52 pairs and this transformation; not individual reliability |
| Average signed level displacement | 0.366; P3 [0.178, 0.547] | Observed average change; not causal development or pure error |
| Absolute centered-shape displacement | RMS 1.002; P3 [0.801, 1.372] | Nonzero descriptive displacement in internal units; no clinical threshold |
| Directional profile similarity | median 0.549, IQR [0.121, 0.874], range [-0.689, 1.000], 52 defined/0 undefined | Direction only; high correlation can coexist with magnitude disagreement |

## Bootstrap execution

Exactly 999 paired target draws were attempted and shared by P2/P3. P3 used an independently keyed auxiliary draw shared across represented folds, linked target analysis/reference multiplicities, original folds, and complete held-out exclusion. All six endpoint-method combinations had 999 valid and zero invalid estimates; therefore all 12 percentile/basic rows were available. There were no numerical fit failures or malformed-input/software exceptions. P3 and P2 widths were similar for ICC and mean change; P3 was wider for RMS because it propagated reference refitting. Empirical coverage is unknowable and is not reported. Earlier B3-R simulations informed method labels but do not prove calibration here.

The first ten actual scheduled draws (replicates 0–9, retained within the 999) ran at 94.4 paired P2/P3 attempts per second, giving an initial 999-attempt ETA of 10.6 seconds on this machine. The complete fresh-process recalculation took 7.01 seconds. Versioned atomic checkpoints record completed and remaining attempts; incompatible or incomplete checkpoints are rejected.

## Descriptive sensitivities

- Fixed-primary-pair strict-V (41) produced ICC 0.665, mean change 0.261, and RMS 0.819.
- Reselected strict-V (45) produced ICC 0.675, mean change 0.281, and RMS 0.840. It combines eligibility and pair choice; four changed pairs remain in the linkage audit.
- M0/SD changes the coordinate definition. M0/M1 uses identical 42 pairs. No secondary bootstrap intervals or difference tests were added.

## Validation

The three reviewed C1 validation gaps were reproduced before repair. C2 rejects them with exact reasons. C2 passed 23/23 executable tests, and the unchanged C1 suite passed 27/27. Unit-weight refitting matched all 25 Step 5B-A M0/MAD fold-task parameter sets and all 520 coordinates (maximum absolute coordinate difference 2.22e-15).

The independent raw-data path imported no production fitting, statistic, plan, quantile, or interval helpers. It matched all 18 point estimates, 25 fits, seven correlation fields, 5,994 replicate endpoint values/classifications, 999 linkage records, and 12 interval rows with zero failures. A fresh full process recalculated all 999 draws and matched every scientific record. An isolated interruption after three draws resumed to seven identically to a clean seven-draw run. Protected dependencies were unchanged.

## Limits

These are empirical descriptions plus bootstrap uncertainty, not diagnosis, population norms, causal development, pure measurement error, latent ability, task-version equivalence, verified individual reliability, prediction, or publication-ready novelty. Repository sessions do not establish verified elapsed assessment time. LNB denominator/load, CTAP unit/aggregation, task version/administration, complete-case selection, internal reference estimation, and the small sample restrict interpretation. Interval overlap is not a difference test; no hypothesis tests were performed.

## Completion checklist

- PASS — Frozen C1 adopted and provenance verified: execution specification and source manifest.
- PASS — Validation gaps repaired: defect record; C2 23/23 and C1 27/27 tests.
- PASS — 25 unit fits and 520 coordinates matched Step 5B-A.
- PASS — Six slices and profile-correlation summary completed.
- PASS — Exactly 999 P2/P3 attempts; all endpoint statuses retained.
- PASS — All 12 interval rows reported.
- PASS — Independent point/full-replicate/interval/linkage validation.
- PASS — Fresh-process, resume, and historical preservation checks.
- PASS — Findings and limitations reported without diagnostic or causal claims.
- PASS — Project index, README, manifest, ZIP, hash, and verification record.

## Verdict

**EMPIRICAL ANALYSIS COMPLETE AND INDEPENDENTLY VALIDATED.**
