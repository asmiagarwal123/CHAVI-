# CHAVI Step 4A reproduction and focused tests

Run from the project root:

```powershell
python .\chavi_analysis_ds007116_step4a_face_memory_20260914\step4a_face_memory.py
python .\chavi_analysis_ds007116_step4a_face_memory_20260914\test_step4a_face_memory.py
```

The analysis is dependency-free and uses Python `3.14.0` standard-library calculations and deterministic custom SVG/PNG rendering. It reads the actual paths recorded in `step4a_provenance.json`.

Focused tests passed:

- strict decision-register schema and quoting validation
- actual malformed Step 3B decision register repaired only in memory with original hash retained
- finite score parsing rejects NaN and +/-infinity
- duplicate analytical keys are detected
- invalid, missing, and unresolved QC states remain distinct
- ambiguous chronology is not accepted as known positive timing
- continuation sessions cannot create a new CNB occasion
- known ICC(A,1) and ICC(C,1) synthetic values
- constant-score zero-variance handling
- participant bootstrap preserves duplicate sampled copies with unique IDs
- figures reproduce from the included pair table
- source-level Step 3B eligibility differences: 0

The primary cohort is `documented_valid_or_likely_valid` and `first_two_eligible_face_memory_observations`. The bootstrap uses `5000` participant-pair resamples with seed `20260914`. No MRI, derivative, unrelated phenotype, questionnaire outcome, prediction, or profile model is loaded or analysed.
