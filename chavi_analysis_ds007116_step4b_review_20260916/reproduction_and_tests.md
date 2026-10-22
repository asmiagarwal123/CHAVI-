# Step 4B-R reproduction and tests

Run `python validate_step4b.py`, then `python -m unittest -v test_validate_step4b.py`. The validator is independent of Step 4B production functions and uses the pinned raw payloads, direct ANOVA ICC calculations, a fixed-seed participant-pair bootstrap, and recorded input/output hashes. All required focused tests are listed in `test_validate_step4b.py`.
