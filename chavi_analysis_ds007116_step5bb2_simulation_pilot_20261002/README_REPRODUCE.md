# CHAVI Step 5B-B2 simulation pilot

This directory is an isolated, simulated-data-only implementation. It does not import CHAVI profile coordinates or infer empirical CHAVI estimates.

Use the pinned interpreter from `C:\tmp\chavi_preflight_numpy_env\Scripts\python.exe` (Python 3.14.0, NumPy 2.5.2). Run `python test_simulation.py`, then `python run_pilot.py` to resume from `runtime_checkpoint`. The pilot is checkpointed after every outer dataset. After completion run `python finalize_pilot.py`, then `python independent_validate.py`.

The master seed, keyed scientific streams, scenario registry, estimator definitions, undefined behavior, and interval rules are frozen in `simulation_execution_contract.json` and `scenario_registry.json`.
