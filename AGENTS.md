# CHAVI repository instructions

## Project architecture is mandatory

`PROJECT_ARCHITECTURE.md` is the authoritative filesystem architecture for this repository.

Whenever any file or directory is created, deleted, renamed, moved, or materially changes its architectural role:

1. Finish the requested filesystem changes.
2. Run `.\.venv\Scripts\python.exe tools\update_project_architecture.py` from the repository root.
3. Verify the command exits successfully and that `PROJECT_ARCHITECTURE.md` reflects the final repository state.
4. Include `PROJECT_ARCHITECTURE.md` in any package or handoff when a complete project map is requested.

Do not manually edit the generated inventory between the markers in `PROJECT_ARCHITECTURE.md`. Update the generator when the architecture format or exclusion policy must change, then regenerate the document.

The inventory excludes only implementation-neutral environment/cache internals listed in the generator, such as `.git`, `.venv`, `.uv-cache`, `__pycache__`, and `.pytest_cache`. Research artifacts, source data, reports, manifests, ZIPs, hashes, and validation records remain represented.
