#!/usr/bin/env python3
"""Read-only entry point for the Phase 1 audit.

Run from the workspace root; delegates to the separately authored audit
implementation and never modifies files outside the recovery directory.
"""
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).parents[1] / "recovery_phase1_audit.py"), run_name="__main__")
