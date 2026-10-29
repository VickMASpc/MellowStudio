# Repository development workflow

- **`main`** is the canonical tested source. Feature branches and PRs carry implementation, regression tests, roadmap and sprint-log changes. Releases are tagged tested commits; no per-sprint extracted environments or checked-in ZIPs.
- **One `.venv`** in repo root, ignored by Git and reused by `start_windows.bat`, `dev.ps1`, tests and builds.
- **Dependencies** are declared in `pyproject.toml`; requirements files are compatibility shims.
- **Every implementation PR updates BOTH documents:** `docs/DEVELOPMENT_PLAN.md` (scope, architecture, acceptance, risks) and `docs/SPRINT_LOG.md` (what changed, tests, evidence, limitations, next tasks). The CI `Sprint documentation gate` checks paired updates for editor, tests, scripts, workflows and packaging changes. Docs-only changes do not require both.
- **Don't overstate validation:** implemented, CI verified, manually verified, and accepted have different meanings. Windows Qt smoke tests and headless tests are mandatory; manual mouse/drag, lengthy sessions and Windows EXE remain explicit gates.
- **CI:** Linux headless and Windows GUI/engine tests on Python 3.11 and 3.13; separate documentation gate on PRs. Set GitHub branch protection to **require the docs gate** (and matrix tests) for an enforceable merge policy; without protection, checks can be bypassed.
- **Per sprint:** issue with acceptance → focused code+tests → reference Mellow fixture → measured performance/error evidence → roadmap+log → PR+CI → manual Windows review when relevant → merge/tag when accepted. When results fail, record the failure and keep the issue open.
- **Next:** [Issue #7](https://github.com/VickMASpc/MellowStudio/issues/7) extended reference registration and remaining [Issue #3](https://github.com/VickMASpc/MellowStudio/issues/3) reliability/benchmark gates; 0.3 painting follows the exit gates.
- **Branch hygiene:** merged PR branches are automatically deleted remotely only if their *current* SHA matches the verified merged PR head SHA. `./dev.ps1 sync` fetches GitHub `main` then discards conflicting **tracked source edits** to match that version, but **never runs `git clean`**, so the installed `.venv`, local artwork, exports and unrelated local branches survive.

## Sync policy correction (2026-10-29)

**User intent:** A zero-drama way to update Mellow Studio, **not a clean-room reinstall**. Earlier `sync` wrongly used `git clean -ffdx` and `git branch -D`, deleting the root environment and local art. That caused unnecessary installs, `pip` bootstrap failures and wasted time. That policy is superseded.

- `./dev.ps1 sync`: validate repo and origin, fetch first, then `git checkout --force -B main origin/main` and `git reset --hard origin/main`. This discards modifications to Git-tracked source to obtain the current build without merge/conflict prompts.
- **Never** run `git clean` or delete local branches in the local update command. The existing `.venv`, ignored files and ordinary untracked projects/exports survive. GitHub remote branch janitor remains separate. Any uncommon untracked file occupying exactly the same path as a newly tracked source file can be overwritten by force-checkout; store personal projects outside source paths.
- Avoid dependency reinstall on every sync. `setup_windows.bat` reuses the existing working `.venv` and installs missing packages only when imports fail. If a previous destructive sync already wiped `.venv`, one restoration may still be necessary; subsequent syncs preserve it.
- Integration test now requires preservation of fake `.venv` and untracked sprite assets, retention of an unpushed personal branch, and idempotent second sync.
