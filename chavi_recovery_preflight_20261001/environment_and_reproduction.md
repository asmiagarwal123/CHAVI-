# Environment and Reproduction Record

## Freshly observed environment

Observed on 1 October 2026 in `C:\Users\asmi\Desktop\Projects\CHAVI`:

- Host platform reported by the isolated run: Windows 11 (`Windows-11-10.0.26200-SP0`).
- Base `python`: Python 3.14.0 at `C:\Python314\python.exe`.
- Base environment did not provide `pytest`, NumPy, pandas, SciPy, scikit-learn, statsmodels, or matplotlib when checked during the preceding workspace audit.
- No `requirements.txt`, `pyproject.toml`, environment YAML, Pipfile, or lockfile was found in the project.
- Project root has no `.git`; only `ds007116/` is version-controlled.
- Dataset Git was freshly verified as clean `main...origin/main`, tag `1.0.6`, commit `fc7dc36fa2598b0b2e4579baef37d148cc085207`.

Historical environment documents list Python 3.14.0, pandas 3.0.5, NumPy 2.5.2, scikit-learn 1.9.0, SciPy 1.17.0, statsmodels 0.14.6, matplotlib 3.10.8, seaborn 0.13.2, and JupyterLab 4.5.6. Those are historical claims, not current base-environment observations.

## Isolated preflight environment

To reproduce the contract's exact NumPy RNG wording without altering the project environment, a temporary virtual environment was created at:

`C:\tmp\chavi_preflight_numpy_env`

Installed package:

```text
numpy==2.5.2
```

The environment is intentionally outside the project and is not included in the milestone ZIP. `isolated_environment_requirements.txt` records the one installed package. No pandas, SciPy, statsmodels, scikit-learn, plotting package, or pytest was needed for source/cohort/fold reconstruction.

## Script safety review

Before execution, `reconstruct_source_cohorts.py` was syntax-compiled and searched for mutation operations. It:

- reads only declared historical/source artifacts;
- invokes Git read-only commands against `ds007116` with a command-local safe-directory setting;
- writes only inside `chavi_recovery_preflight_20261001/`;
- does not import or execute quarantined transformation code;
- does not write parameters, transformed coordinates, profiles, simulations, thresholds, predictions, or UI artifacts.

The script reads Step 5A manifests only after independent reconstruction, solely for identity comparison.

## Commands executed

Create the isolated environment and install the exact RNG dependency:

```powershell
python -m venv C:\tmp\chavi_preflight_numpy_env
& 'C:\tmp\chavi_preflight_numpy_env\Scripts\python.exe' -m pip install --disable-pip-version-check --no-input numpy==2.5.2
```

Compile and run the independent reconstruction:

```powershell
& 'C:\tmp\chavi_preflight_numpy_env\Scripts\python.exe' -m py_compile .\chavi_recovery_preflight_20261001\reconstruct_source_cohorts.py
& 'C:\tmp\chavi_preflight_numpy_env\Scripts\python.exe' .\chavi_recovery_preflight_20261001\reconstruct_source_cohorts.py
```

The reconstruction intentionally returns exit code `2` while the fold identity conflict remains unresolved. Its source/cohort/count checks pass; the aggregate readiness gate fails because literal seed-42 identities do not equal Recovery Phase 1 expected identities.

Run artifact tests:

```powershell
python -m unittest discover -s .\chavi_recovery_preflight_20261001 -p 'test_preflight.py' -v
```

Validate JSON and CSV readability, then create the package:

```powershell
python -m json.tool .\chavi_recovery_preflight_20261001\step5ba_rebuild_specification_candidate.json
python -m json.tool .\chavi_recovery_preflight_20261001\readiness_verdict.json
python .\chavi_recovery_preflight_20261001\finalize_package.py
```

## Fresh versus historical testing

- Fresh: source reconstruction, 41 payload hash/size checks, dataset Git checks, QC dictionary checks, identity/count reconciliation, literal NumPy fold reconstruction, deterministic repeat, Recovery fold comparison, JSON/CSV validation, and preflight unit tests.
- Previously fresh in the broader audit: 43 upstream Step 4A/4B/5A standard-library tests passed.
- Historical only: Step 5A-D-R 48/48, R2 74/74, R3 5/5 wrappers.
- Not accepted as scientific validation: quarantined Step 5B self-consistency tests and validators.

## Portability notes

Historical scripts contain absolute paths to both the former `ML Projects` location and the present CHAVI directory. The new reconstruction script resolves all project inputs relative to its own location. The temporary environment path is recorded but is not a project dependency; recreate it from the one-line requirements file.
