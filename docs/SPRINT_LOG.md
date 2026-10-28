# Mellow Studio — sprint log and release gates

**Updated:** 2026-10-28  
**Current canonical baseline:** `main`, v0.2.1 implementation merged in [PR #2](https://github.com/VickMASpc/MellowStudio/pull/2).  
**Active sprint:** 0.2.2 reliability, fast rendering and visible professional tooling, [Issue #3](https://github.com/VickMASpc/MellowStudio/issues/3). **Implementation underway; do not mark acceptance until manual Windows checks pass.**  
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
| Durable save and error handling | `project_save()` validates archive before atomic replace, `.bak` preserves prior file, Save As identity retained on failure; fault injection tests | CI VERIFIED; physical Windows tests pending |
| Explicit mutation transactions | Existing history begin/commit and linked-cel semantics retained; full command dispatcher and pixel-run deltas not yet implemented | PARTIAL |
| Composite QImage/onion caches, lazy invalidated timeline thumbnails | Frame/preview cache and changed-linked-cel invalidation; linear alias count; Qt smoke added | CI VERIFIED; real Windows manual gate pending |
| High-DPI and keyboard-focus Qt tests | Added dither drawing / save-error / cache smoke; full High-DPI, focus and drag testing pending | PARTIAL |
| Workload & memory benchmarks | `scripts/benchmark.py`; Linux Python 3.13 sandbox baseline saved in `PERFORMANCE_BASELINE_SANDBOX.json`; 5700U / GUI FPS unmeasured | HEADLESS BASELINE ONLY |
| Preserve flagship regression | Existing 41×55 exact regression, new save/link/dither tests; mixed-offset 12-frame registration still in 0.2.3 | PARTIAL |

**Exit gate:** 20 duplicate/edit/undo cycles, a documented 60-second continuous Windows drawing session, save failure and two-project recovery tests without silent loss, green Windows/Linux CI, measured performance. No claims of acceptance before evidence.

## Future sprint order (not started)

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

**Headless validation (local sandbox):** 44 passed, one Qt module skipped because PySide6 unavailable in this container. **GitHub CI on PR #5:** 4/4 OS/Python test jobs and mandatory documentation gate passed ([workflow run](https://github.com/VickMASpc/MellowStudio/actions/runs/40695887243)); Windows Python 3.11 executed **48 passed** including four Qt tests. This is automated smoke coverage, not physical interactive acceptance. Existing 41×55 eye/highlight regressions remain in the suite. Interrupted last-step save simulation preserves old target. Project archive is verified before replace and prior version is backed up as `.bak`.

**Measured baseline:** see [`PERFORMANCE_BASELINE_SANDBOX.json`](PERFORMANCE_BASELINE_SANDBOX.json). Median Linux sandbox (Python 3.13): 41×55 / 2 layers / 8 frames **0.026ms** single-frame composite; 128×128 / 8 layers / 24 frames **0.162ms**; 256×256 / 4 layers / 24 frames **0.229ms**. Save medians 13.7/130.0/191.4ms respectively. These are headless synthetic workloads, **not** end-user Qt frame latency or Ryzen 5700U measurements; Python `tracemalloc` does not include all native/Qt memory.

**Gates still open:** real Windows drag/60-second drawing and recovery tests; actual Windows/5700U latency and RAM; precise region-delta history, per-pixel invalidation, complete keyboard/HiDPI interaction suite and crash/power-failure simulation. 0.2.2 remains **in progress** regardless of green CI; next sprint 0.2.3 still prioritizes reference registration over general editor expansion.
