# Reproduction and tests

Run from this directory:

`python validate_step4a.py`

`python -m unittest -v test_validate_step4a.py`

The validator reads the pinned raw Face Memory payload and participant registry, never imports the Step 4A production module, and writes only this review directory. It runs the 5,000-replicate participant-pair bootstrap twice with the fixed seed to verify bit-for-bit resampling reproducibility.
