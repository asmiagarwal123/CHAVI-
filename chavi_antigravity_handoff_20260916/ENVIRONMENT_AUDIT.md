# Environment Audit

## Software Environment
- Operating System: Windows
- Python Version: Python 3.14.0

## Key Available Packages
(Based on `pip freeze` capture)
- pandas==3.0.5
- numpy==2.5.2
- scikit-learn==1.9.0
- scipy==1.17.0
- statsmodels==0.14.6
- matplotlib==3.10.8
- seaborn==0.13.2
- jupyterlab==4.5.6

## Path Risks
**High Risk**: Absolute paths were found embedded in earlier stage scripts.
For example, `chavi_audit_ds007116_step2_20260907\audit_v3.py` contains instructions or configurations referencing `C:\Users\asmi\Desktop\Projects\ML Projects`. 
Moving the CHAVI workspace to a different path or machine will currently break the reproduction assumptions of these older scripts. Refactoring to relative paths (e.g. `pathlib.Path(__file__).parent`) is recommended but explicitly skipped during this read-only handoff.
