# Reproduction Commands

Due to absolute paths embedded in early stage scripts, reproduction must currently happen from `C:\Users\asmi\Desktop\Projects\ML Projects` or equivalent paths. Moving the workspace would break script execution.

## Example Available Commands

### Step 4B Validation
```powershell
python chavi_analysis_ds007116_step4b_review_20260916/validate_step4b.py
pytest chavi_analysis_ds007116_step4b_review_20260916/test_validate_step4b.py
```

### Step 5A Preparation
```powershell
python chavi_analysis_ds007116_step5a_measurement_specification_20260916/prepare_step5a_measurement_specification.py
pytest chavi_analysis_ds007116_step5a_measurement_specification_20260916/test_step5a_measurement_specification.py
```

*Note: Generating full reproduction command lists requires replacing absolute paths in older audit scripts (`audit_v3.py`, `audit_v4.py`, etc.).*
