# Repository development workflow

- **`main`** is the canonical tested source. Feature branches and PRs carry implementation, regression tests, roadmap and sprint-log changes. Releases are tagged tested commits; no per-sprint extracted environments or checked-in ZIPs.
- **One `.venv`** in repo root, ignored by Git and reused by `start_windows.bat`, `dev.ps1`, tests and builds.
- **Dependencies** are declared in `pyproject.toml`; requirements files are compatibility shims.
- **Every implementation PR updates BOTH documents:** `docs/DEVELOPMENT_PLAN.md` (scope, architecture, acceptance, risks) and `docs/SPRINT_LOG.md` (what changed, tests, evidence, limitations, next tasks). The CI `Sprint documentation gate` checks paired updates for editor, tests, scripts, workflows and packaging changes. Docs-only changes do not require both.
- **Don't overstate validation:** implemented, CI verified, manually verified, and accepted have different meanings. Windows Qt smoke tests and headless tests are mandatory; manual mouse/drag, lengthy sessions and Windows EXE remain explicit gates.
- **CI:** Linux headless and Windows GUI/engine tests on Python 3.11 and 3.13; separate documentation gate on PRs. Set GitHub branch protection to **require the docs gate** (and matrix tests) for an enforceable merge policy; without protection, checks can be bypassed.
- **Per sprint:** issue with acceptance → focused code+tests → reference Mellow fixture → measured performance/error evidence → roadmap+log → PR+CI → manual Windows review when relevant → merge/tag when accepted. When results fail, record the failure and keep the issue open.
- **Next:** [Issue #7](https://github.com/VickMASpc/MellowStudio/issues/7) extended reference registration and remaining [Issue #3](https://github.com/VickMASpc/MellowStudio/issues/3) reliability/benchmark gates; 0.3 painting follows the exit gates.
- **Branch hygiene:** merged PR branches are automatically deleted remotely only if their *current* SHA matches the verified merged PR head SHA. To synchronize a Windows checkout safely, use `./dev.ps1 sync`; no hard resets, no force pulls, no extra environments.
