# Mellow Studio — sprint log and release gates

**Updated:** 2026-10-28  
**Current merged baseline:** `main`, v0.2.3 Reference Lab merged in [PR #6](https://github.com/VickMASpc/MellowStudio/pull/6), passing Windows/Linux CI. Physical Windows acceptance gates remain open.  
**Active work:** completion of flagship reference registration in [Issue #7](https://github.com/VickMASpc/MellowStudio/issues/7) and remaining recovery/performance gates in [Issue #3](https://github.com/VickMASpc/MellowStudio/issues/3). **Status: implementation, not a fully accepted physical-Windows release.**  
**Roadmap:** [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md). A source implementation is not a release acceptance.

## Evidence conventions (mandatory)

- `PLANNED`: scoped but no code. `IN PROGRESS`: partial implementation. `IMPLEMENTED`: code exists, validation not enough. `CI VERIFIED`: targeted automated suite passed. `MANUAL VERIFIED`: an actual Windows interaction has been executed and recorded. `ACCEPTED`: explicit exit gate passed with reproducible evidence. `BLOCKED`: defect or dependency prevents gate.
- Each sprint change records **code, tests, failures, measurable results, limitations and follow-ups**. A green CI build doesn't imply usability or EXE verification. Track Windows runtime separately.
- Every code PR must change this file **and** `DEVELOPMENT_PLAN.md`; documentation-only PRs are exempt from paired updates.

## Historical baseline

| Sprint | Implemented | Verification and outstanding limitations | Status |
|---|---|---|---|
| 0.1.0 / 0.1.1 | Qt desktop editor, logical raster canvas, layers, tools, basic timeline, manual measurement and Mellow calibration | Initial 14 headless tests; later Windows GUI smoke added; 60-second drawing and long-run gates were not recorded | IMPLEMENTED; partial CI VERIFIED |
| 0.2.0 | Frame multi-selection, linked holds, frame block operations, v2 archive with v1 support, auto grid suggestions, measured sequence importer, CLI exports | 27 headless regression tests at milestone, Mellow 41×55 and 268×360 fixture; coarse shared calibration still fails different-crop alignment | CI VERIFIED for specified tests |
| 0.2.1 | Non-destructive floating moves/paste, explicit commit/cancel, timeline drag reorder, compressed bounded snapshot undo; default 128 actions/128 MiB | [PR #2 merged](https://github.com/VickMASpc/MellowStudio/pull/2); latest main [4/4 CI jobs passed](https://github.com/VickMASpc/MellowStudio/actions/runs/40690278158) on Windows and Linux. Original 35 headless tests plus Windows Qt smoke. Windows application run/testing reported working by user; full drag usability and long-session gate not yet recorded | CI VERIFIED; MANUAL VERIFIED for launch only; not fully ACCEPTED |

**0.2.1 distinctions:** compressed *document* snapshots are not tile/run delta undo. Qt smoke tests do not prove subjective drag responsiveness. Float preview remains separate until commit, but project-wide recovery and save-failure hardening are pending.

## Sprint 0.2.2 — next implementation sprint ([Issue #3](https://github.com/VickMASpc/MellowStudio/issues/3))

**Goal:** make daily drawing and animation trustworthy before 0.3A/B feature expansion. **State:** IMPLEMENTED (partial sprint; Windows CI and manual gate outstanding).

| Deliverable | Evidence required | Status |
|---|---|---|
| Per-project recovery identity, retention, isolation and restore UI | `recovery.py`, snapshot rotation/chooser, legacy load; multi-project tests | IMPLEMENTED; headless tests passed |
| Durable save and error handling | `project_save()` validates archive before atomic replace, `.bak` preserves prior file, Save As identity retained on failure; fault injection tests | IMPLEMENTED; headless tests passed; Windows Qt pending |
| Explicit mutation transactions | Existing history begin/commit and linked-cel semantics retained; full command dispatcher and pixel-run deltas not yet implemented | PARTIAL |
| Composite QImage/onion caches, lazy invalidated timeline thumbnails | Frame/preview cache and changed-linked-cel invalidation; linear alias count; Qt smoke added | IMPLEMENTED; Windows CI pending |
| High-DPI and keyboard-focus Qt tests | Added dither drawing / save-error / cache smoke; full High-DPI, focus and drag testing pending | PARTIAL |
| Workload & memory benchmarks | `scripts/benchmark.py`; Linux Python 3.13 sandbox baseline saved in `PERFORMANCE_BASELINE_SANDBOX.json`; 5700U / GUI FPS unmeasured | HEADLESS BASELINE ONLY |
| Preserve flagship regression | Existing 41×55 exact regression, new save/link/dither tests; mixed-offset 12-frame registration still in 0.2.3 | PARTIAL |

**Exit gate:** 20 duplicate/edit/undo cycles, a documented 60-second continuous Windows drawing session, save failure and two-project recovery tests without silent loss, green Windows/Linux CI, measured performance. No claims of acceptance before evidence.

## Sprint 0.2.3 — Reference Lab, schema 3 and workspace refresh (2026-10-28)

**Objective:** turn a grid-only screenshot import into a source-preserving, correctable animation pipeline. UI changes support that task and stay smaller than the registration work.

| Deliverable | Evidence | Status before CI |
|---|---|---|
| Embed screen-space source PNG pixels in each native project and keep original filename, size, sampling mode, registration and fractional calibration | `mellowstudio/reference.py`, `model.py`; project schema 3 and v1/v2 load tests | IMPLEMENTED; 53 headless tests pass locally |
| Preserve provenance on frame move/copy, history and save/reopen; editing one frame cannot mutate linked artwork or shared ref metadata unexpectedly | `test_sprint023.py` tests with duplicate/linked/undo | IMPLEMENTED; headless tests pass |
| Detect likely translation between same-dimension screenshots, never auto-commit | `suggest_translation` edge correlation; mismatched image sizes flagged | IMPLEMENTED; heuristic limitations documented |
| GUI source inspector / calibration after project reopen | `ReferenceWorkbench`, right Reference dock, import sequence review, red/cyan difference, manual origins and reconstruct | IMPLEMENTED; Windows Qt test queued / manual pending |
| Reconstruct 12 differently shifted 268×360 sources into the original 41×55 grid | `examples/reference_lab_12frame_demo.mellowzip` and deterministic script + tests | HEADLESS VERIFIED: 12 of 12 exact cels |
| Fix center sampling drift at transformed fractional grid boundaries | `calibration.py` and source-offset regression | HEADLESS VERIFIED |
| Minor visual design pass | Studio command strip, Reference Lab dock, more deliberate dark colors / action highlighting | IMPLEMENTED; physical visual review pending |
| Full uneven-scale and landmark-assisted registration, image-boundary crop damage detection, full wipe/heatmap UI | Dedicated additional tests / Windows manual testing | OPEN; not implicitly accepted |

**Local validation:** 53 headless tests passed on Python in this environment. Qt tests cannot run locally without PySide6; CI must run on Windows. Fixture: twelve source images with screen-space offsets (some positive/negative); outputs match the measured Mellow original *byte for byte*. The sources are separately stored in the v3 archive. Raster size remains 41×55 regardless of reference size.

**Risk:** An offset suggestion cannot distinguish deliberate sprite motion from a screen crop; confidence is heuristic and review is mandatory. Pixels literally clipped outside a screenshot cannot be restored. The original JPEG bitstream/EXIF is not retained, only original decoded pixels converted losslessly to embedded PNG.

**Next:** after CI and physical Windows use, focus on variable-scale alignment and landmark registration, then 0.3A drawing fundamentals. Keep 0.2.2 manual stability/performance gates tracked on Issue #3 rather than falsely declaring them complete.

## Remaining sprint order / forward gates

1. **0.2.3:** source-preserving reference registration, per-frame offsets/crops and landmark corrections, 12 mixed-offset references, preview/overlay comparisons. This is the product differentiator and precedes generic professional-tool expansion.
2. **0.3A:** palette/color, custom precision brushes, dither/pixel-perfect lines, selection masks/transforms, layer groups and configurable shortcuts.
3. **0.3B:** animation tags/holds/range edits, configurable onion and A/B pose preview, optimized exposure timeline and production atlas export.
4. **0.4:** indexed modes, project exchange, workspaces, performance scaling, export compatibility.
5. **0.5+:** tilemaps, asset library, advanced transforms/audio/optional tweening; **1.0:** tested packaging, recovery and compatibility gate.

## Sprint change record — 2026-10-28

- **Decision:** reviewed original roadmap against merged 0.2.1; retained professional feature inventory but split overfull 0.3 into 0.3A/0.3B; moved reference/provenance work to 0.2.3 and reliability to 0.2.2. Why: data integrity and distinctively fast measured animation are more valuable than accumulating unverified buttons.
- **Documentation process:** source repo is canonical; each implementation PR must update roadmap and sprint log, with a dedicated CI guard. Versioned ZIP per sprint retired; releases are tagged commits when accepted.
- **Outstanding risks:** current shared autosave slot, save-as failure semantics, unregistered same-size reference crops, eager recompositing/thumbnails and snapshot-only history. None marked fixed by this documentation-only sprint.
- **CI status:** documentation-governance PR must pass its own CI before merge; append the PR/commit and CI evidence in a future implementation sprint. No 0.2.2 engine improvements are claimed here.

## Sprint 0.2.2 implementation record — 2026-10-28

**Code:** `model.py`, `recovery.py`, `main.py`, `canvas.py`, new `test_sprint022.py` and Qt smoke, new `scripts/benchmark.py`. Visible result: deterministic two-color dither painting via `D` with Mix spinner. Faster frame switching through cached QImages and thumbnails. Recovery now retains **four snapshots per project** rather than a single global slot, and File menu includes recovery chooser.

**Headless validation (local sandbox):** 44 passed, one Qt module skipped because PySide6 unavailable in this container; Windows CI required for UI tests. Existing 41×55 eye/highlight regressions remain in the suite. Interrupted last-step save simulation preserves old target. Project archive is verified before replace and prior version is backed up as `.bak`.

**Measured baseline:** see [`PERFORMANCE_BASELINE_SANDBOX.json`](PERFORMANCE_BASELINE_SANDBOX.json). Median Linux sandbox (Python 3.13): 41×55 / 2 layers / 8 frames **0.026ms** single-frame composite; 128×128 / 8 layers / 24 frames **0.162ms**; 256×256 / 4 layers / 24 frames **0.229ms**. Save medians 13.7/130.0/191.4ms respectively. These are headless synthetic workloads, **not** end-user Qt frame latency or Ryzen 5700U measurements; Python `tracemalloc` does not include all native/Qt memory.

**Gates still open:** real Windows drag/60-second drawing and recovery tests; actual Windows/5700U latency and RAM; precise region-delta history, per-pixel invalidation, complete keyboard/HiDPI interaction suite and crash/power-failure simulation. 0.2.2 remains **in progress** regardless of green CI; next sprint 0.2.3 still prioritizes reference registration over general editor expansion.

## Repository maintenance — merged-branch cleanup (2026-10-28)

**Audit before changes:** five GitHub branches existed: `main` plus `feat/sprint-021-floating-selections-timeline`, `chore/roadmap-sprint-governance-022`, `feat/sprint-022-safe-projects-fast-canvas-dither`, `feat/sprint-023-reference-lab-studio-ui`. All four feature/chore branches were PR heads of PR #2, #4, #5, #6, respectively; all PRs were merged with identical historical branch-head SHAs. No open PRs. Latest `main` workflow had passed. The branches were stale after squash merge, not four new development lines.

**Change:** add GitHub Actions branch janitor (runs after pushes to `main`) with strict same-repository merged-PR/head-SHA checking, protected/default branch exclusion, and a test that proves unmerged, changed, forked and protected branches survive. Add Windows `./dev.ps1 sync`: fetch/prune, fast-forward-only main, optional exact-SHA-verified old local branch removal; refuses dirty worktree/diverged main/unexpected remote and never deletes `.venv`.

**Evidence:** offline JavaScript decision-rule test passes. GitHub deletion counts and post-merge Actions outcome to be recorded after this PR merges; physical Windows command execution not yet validated. No claim of changing the user's local Git checkout remotely.

**Remaining:** user-local authentication, DNS, proxy, uncommitted modifications or divergent history cannot be diagnosed via repository-side GitHub data alone. GitHub workflow permissions may prevent automatic deletion; report that explicitly if it occurs.
