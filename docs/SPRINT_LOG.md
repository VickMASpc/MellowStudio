# Mellow Studio — sprint log and release gates

**Updated:** 2026-10-29  
**Current merged baseline:** 0.2.4 artist-workspace implementation (PR #10), Windows/Linux CI verified; physical Windows UX acceptance remains open.  
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

**Evidence:** [PR #8](https://github.com/VickMASpc/MellowStudio/pull/8) merged as `b15d900c`; all five PR validation jobs passed, as did the four Linux/Windows post-merge CI jobs. [Branch janitor run 40705760359](https://github.com/VickMASpc/MellowStudio/actions/runs/40705760359) succeeded and logged **five successful deletions**: the four original stale sprint branches and the cleanup PR's temporary branch. GitHub's branches API was checked afterward and returned **only `main`**. Offline Node decision-rule test and Windows PowerShell syntax check passed; physical Windows sync execution and user-local Git state remain unverified.

**Remaining:** user-local authentication, DNS, proxy, uncommitted modifications or divergent history cannot be diagnosed via repository-side GitHub data alone. GitHub workflow permissions may prevent automatic deletion; report that explicitly if it occurs.


## Sprint 0.2.4 — Artist-first creative workspace (2026-10-28)

**Corrected product goal:** Professional means swift, enjoyable creative production in a polished and comprehensive native workspace. Earlier work emphasized archive/calibration/engineering depth at the expense of the actual artist experience.

**Implemented in feature branch (Issue #9):** Native Welcome dialog with new/open/recent/sample/recovery; approachable New Canvas presets; local vector icon tool rail; contextual brush size, dither mix, fill, symmetry and foreground/secondary colors; paint/secondary swap (X) and selected palette highlight; compact timeline with play/duplicate/blank, duration, More and right-click frame actions; F11 focus canvas; one Ctrl+E export dialog for PNG, GIF, spritesheet+JSON and numbered PNGs+JSON; calmer Qt styling and project/save/export bar. Existing pixel-exact rendering, undo, recovery and reference registration remain available.

**Local evidence:** 56 headless tests passed, including recent-project validation and lossless sheet timing export. Module compilation passed. New Windows Qt smoke exercises Welcome, presets, contextual tool visibility, palette swap, timeline, focus and quick export. **CI verified:** [PR #10 Windows/Linux matrix, run 40712096133](https://github.com/VickMASpc/MellowStudio/actions/runs/40712096133) passed all five jobs (documentation gate + Linux 3.11/3.13 + Windows 3.11/3.13). Each Windows job ran **62 passing tests**, including native Qt interactions. Initial Windows run exposed two regressions (a legacy header assertion and toolbar widget visibility), both fixed before the successful run. **Real user Windows visual acceptance remains open.**

**Acceptance still open:** physically review visual hierarchy and text/icon clarity on the user's Windows system, verify real mouse/keyboard interactions, check a new-to-export animation workflow and task time, ensure accessibility/HiDPI and preserve native-pixel Mellow regression. This is an implemented experience slice, not a completed Apple-level product.

**Next:** address Windows test failures, record actual Qt CI evidence, then use practical artist feedback to shape 0.2.5 palette/paint/animation refinements. Issues #3 (reliability) and #7 (registration) remain tracked, not abandoned.

## Maintenance change — force-refresh Windows sync (2026-10-29)

**User request:** The prior protective sync repeatedly refused updates when Git saw local edits, local branches or diverging commits. The desired behavior is explicitly to discard **everything local** and get GitHub's latest `main`, without prompts, merges or stash recovery.

**Implementation:** [PR #11](https://github.com/VickMASpc/MellowStudio/pull/11) merged as `ab992d22`. Replace `scripts/sync_windows.ps1` with fetch-first, origin-validated force checkout/reset, `git clean -ffdx`, and deletion of local branches except `main`. Deletes local edited files, commits not reachable from fetched main (branches removed), ignored `.venv`, temporary files, and local-only projects inside the repository. Preserves GitHub remote and primary `.git`; the next launch bootstraps a fresh environment.

**Safety boundary:** wrong origin or failed fetch exits before any destructive step. Git failures while cleaning or deleting other worktree branches are surfaced; external files outside the repo and separately linked worktrees are not deleted. First-time bootstrap from the pre-0.2.5 sync command still requires manual Git commands when that older sync refuses dirty files.

**Verification:** [PR #11 CI](https://github.com/VickMASpc/MellowStudio/actions/runs/40864298778) passed **all five jobs**; Windows Python 3.11 executed the actual offline Git integration fixture and reported `Force-sync integration: all checks passed`, followed by **62 passing engine/Qt tests**. Both Linux matrix jobs and Windows Python 3.13 also passed. The automatic merged-branch prune ran successfully. **This verifies the command with a disposable test repository, not execution on the user's PC.** This policy is user-authorized and deliberately replaces prior preservation behavior.


## Sprint 0.2.5 — Single-window creative studio rebuild (2026-10-29)

**Prompt/defect:** User explicitly rejects the entire old interface. The current docking architecture still treats colors as a window, tabs it under other windows, and can make the canvas unusable. Hiding panels does not offer an obvious way to restore them. An Apple-like product experience means stable spatial hierarchy, compositional clarity, and zero mystery panels.

**Code (PR in development, Issue #12):** Removed the `QDockWidget` layout from `main.py`, replaced QToolBars with inline Studio Header/Context Bar and fixed drawing rail, assembled a central resizable canvas + integrated timeline and a separately scrollable inspector that displays Colors and Layers simultaneously. Preview is compact; Reference is an optional inspector section. View has independent checkable section toggles and Ctrl+Shift+0 default restore; F11 preserves section visibility state. Persist integrated splitter sizes but ignore obsolete floating-dock QSettings state. Replaced dark dock-era presentation with a new light palette, accessible vector tool colors, and card-like inspector sections. No browser UI.

**Verification planned:** Windows offscreen Qt regression asserts no QDockWidget instances, visible Colors+Layers, nonoverlapping canvas/inspector geometry, reactivation from View, reset from all-hidden, exact F11 restoration and tool-aware context. Linux headless engine and Windows Qt matrix plus documentation gate must pass. Manual Windows inspection at ~1100px width and larger remains **NOT VERIFIED**; the user has not yet evaluated this layout. Existing Mellow, Reference Lab, undo/export and recovery regressions remain compulsory.

**CI verified:** [PR #13 Windows/Linux matrix, run 40868655365](https://github.com/VickMASpc/MellowStudio/actions/runs/40868655365) passed all five jobs, including the mandatory docs gate, two Linux engine suites, and **63 passing tests** on each Windows Python version (3.11 and 3.13). The new `test_qt_integrated_workspace_no_docks_and_recoverable_sections` passed on both. An initial run hung because the new test closed an intentionally unsaved test document and correctly triggered the discard confirmation; the fixture was fixed and `pytest-timeout` added to bound future Qt hangs. **Physical Windows visual/product acceptance is still NOT VERIFIED.**

**Status:** CI VERIFIED for the integrated workspace; no manual designer/artist acceptance yet. Scope is a major structural replacement, not a claim of final Apple-level experience. The next work should target observed artist-task friction and onboarding, not speculative architecture.

## 2026-10-29 — Windows sync root-check bugfix

**User-reported regression:** `./dev.ps1 sync` refused the actual MellowStudio checkout with `The script is not running from the MellowStudio repository root.` The earlier script compared Git's absolute root path with a PowerShell-resolved path. This comparison can be brittle on Windows with slash formats, canonicalization or path aliases. The user's error was emitted before any fetch/clean: the script did not wipe their files.

**Fix:** Validate using `git rev-parse --show-prefix` after moving into the script's parent folder: an empty prefix means this working directory is the Git root, while nonempty prefix explicitly refuses a script residing below another Git root (protecting the parent checkout). Retain the strict expected-origin and successful-fetch checks before any destructive action.

**Regression added:** Windows bare-remote fixture now clones into a path containing spaces and parentheses (`Nova pasta (8)/MellowStudio`), verifies a clean force-sync, and separately refuses an identical script run from a nested subdirectory without deleting parent edits. Existing wrong-origin and dirty/ignored file checks remain. **CI verified:** [PR #14 run 40869817353](https://github.com/VickMASpc/MellowStudio/actions/runs/40869817353) passed all five Windows/Linux/documentation jobs. The Windows Git integration fixture explicitly logged `spaces/parentheses root, nested checkout refusal, and all destructive checks passed`, followed by **63 passing Windows Qt/engine tests**. The fix merged as `9afaecf9`. Actual execution on the user's Windows installation remains unverified.
