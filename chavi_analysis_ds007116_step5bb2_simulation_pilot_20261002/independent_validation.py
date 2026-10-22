"""Independent validation entry point for the simulation pilot."""
from mechanism_checks import run as run_mechanism_checks
__all__ = ["run_mechanism_checks"]

if __name__ == "__main__":
    import json
    from pathlib import Path
    out = run_mechanism_checks()
    Path(__file__).with_name("mechanism_validation_results.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(out,sort_keys=True))
