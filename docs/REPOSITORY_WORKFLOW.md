# Repository development workflow

- **main**: integrated, tested source; do not check in sprint archives.
- **feature branches**: one focused change with tests; pull requests are the review/merge mechanism.
- **One `.venv`**: stored at repo root, ignored by Git; the Windows launcher and scripts all point to that exact path. Reuse after `git pull`.
- **Dependency ownership**: `pyproject.toml` is the canonical dependency declaration. `requirements*.txt` are compatibility shims, not separate dependency sets.
- **CI**: two OSes × two supported Python versions, headless Qt smoke when possible, CLI validation.
- **Release**: tag a tested commit; GitHub Actions can later build and attach the Windows artifact. Do not commit an EXE or ZIP snapshots.
- **Performance**: next sprint 0.2.1 prioritizes floating selection, more memory-efficient undo, and timeline drag reordering.
- **Calibration correctness**: preserve measured native grid conversion, fractional pitch, manual origin and the 41x55 Mellow regression.
- **Release gate**: engine tests green AND real Qt smoke test green on Windows AND manual import/paint/save/open/export validation.
