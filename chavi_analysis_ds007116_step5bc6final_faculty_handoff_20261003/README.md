# CHAVI C6 faculty-review package

This is a self-contained review package for the failure-aware resampling manuscript. It is a faculty-review draft, not a journal submission.

Open `CHAVI_FACULTY_REVIEW_MANUSCRIPT.md` first. Its supporting aggregate tables are in `tables/`, publication-quality figures and their data/captions are in `figures/`, and the methods details are in `METHODS_AND_REPRODUCIBILITY_SUPPLEMENT.md`.

`REQUIREMENT_TO_EVIDENCE_CHECKLIST.md` is the error-control record; `WHAT_I_TRIED_TO_FALSIFY.md` records the adversarial checks. `validation/checks.json` is the machine-readable validation result. `AUTHOR_DECISIONS_NEEDED.md` identifies unresolved author-controlled decisions. No participant-level or participant-linked records are included.

To reproduce the package checks, run `..\\.venv\\Scripts\\python.exe code\\validate_c6.py` from this directory. This validates source values, hashes, ZIP contents, and privacy patterns; it does not rerun the scientific pipeline.
