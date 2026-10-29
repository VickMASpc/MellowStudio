# Mellow Studio — product specification & development cycle

**Canonical roadmap:** this file in GitHub. **Current merged baseline:** 0.2.4 artist-first creative workspace (PR #10, CI verified; physical Windows UX acceptance open), following v0.2.3 Reference Lab ([PR #6](https://github.com/VickMASpc/MellowStudio/pull/6)); **remaining reference registration:** [Issue #7](https://github.com/VickMASpc/MellowStudio/issues/7). Reliability work in [Issue #3](https://github.com/VickMASpc/MellowStudio/issues/3) also remains open. Keep the [sprint log](SPRINT_LOG.md) synchronized with each implementation PR. Future phase targets below are not claims of verified functionality.



## 0.2.5 — Complete workspace replacement, not another dock reskin (2026-10-29)

**User experience finding:** In 0.2.4 the toolbars changed, but the underlying QDockWidget model let Colors, Layers, Preview and Reference stack or detach, leaving a tiny canvas. An artist sometimes had to close the color window before painting and could not easily recover hidden panes. This is a fundamental workflow failure: more features and cleaner styling cannot compensate for unpredictable physical UI.

**New interaction architecture (Issue #12):** Replace all QDockWidget usage with one stable native layout: fixed left tool rail, centered canvas, always-independent Colors and Layers sections in a scrollable right inspector, and integrated timeline beneath the canvas. Preview is a compact additional section; Reference stays available via View and Ctrl+Alt+R without occupying a giant blank area by default. The two user-resizable splitters resize regions; they cannot float over or obscure the canvas. The top command row and contextual tool settings are inline widgets, not dockable toolbars. All sections have View toggles; Restore default workspace (`Ctrl+Shift+0`) restores Colors, Layers, Preview and Timeline regardless of previous visibility. F11 restores its exact prior visibility state. Old saved Qt dock layout blobs are intentionally ignored.

**Visual language:** Replace the old dark dock styling with a calm, light, high-contrast workspace; clear section boundaries, generous canvas space, legible dark vector icons, subtle teal primary actions and less visual noise. Presentation supports the user workflow but is not the sole deliverable.

**Acceptance:** An artist can choose colors, paint on the canvas, manage layers, animate, preview and export *without closing or stacking any windows*. Reset/View is discoverable; core sections are visible simultaneously. Real Windows visual tests at common screen sizes (including 1100px window width) and artist usability remain required, beyond offscreen Qt CI. Existing 41×55 native-pixel regression, project schemas, Reference Lab, undo and export remain supported. Design testing (task completion and real visual review) is the next acceptance gate, not another backend sprint.

## Product direction correction — artist-first studio (2026-10-28)

**Professional means producing swiftly in a polished and comprehensive creative environment.** The earlier implementation overemphasized technical mechanics and exposed too many controls. Correctness remains required, but the experience of starting, drawing, animating and exporting is the primary product outcome.

**0.2.4 — Creator workspace (Issue #9):** Native Welcome screen for new/recent projects and recovery; approachable canvas presets; dedicated icon-only tool rail; contextual brush/dither/symmetry/fill options; visible color swap and selected palette state; compact playable timeline with overflow actions; F11 canvas focus; one Ctrl+E export dialog for sheet+JSON, GIF, PNG and numbered frames. Keep the full capabilities beneath this simpler organization. Status: code implemented on the feature branch, 56 local headless tests passing; Windows Qt CI verified 62 tests on each Windows Python version; manual visual acceptance remains separate.

**0.2.5 — Everyday creative completeness:** Improve painting/palette workflows, frame/onion controls, keyboard discoverability, onboarding and artist task-time. Prioritize friction measured in actual Windows creative sessions over generic infrastructure sprints. Existing feature inventory, advanced reference alignment (Issue #7) and recovery/performance concerns (Issue #3) remain in scope, but must not dominate the everyday workspace unless they block reliability.

**Artist acceptance scenario:** Open Mellow; choose 64×64; draw a small character; duplicate/edit 2–4 poses; preview; save/reopen; export usable PNG sheet+JSON. Validate with real user timing, click count, visibility and success without reading a manual. Preserve the 41×55 exact-cell regression as a hard guardrail. Green CI is not proof of a beautiful or intuitive interface.

## A. The problem worth solving

The original Mellow revision exposed the central mistake of using **scaled screenshot pixels as native sprite pixels**. The source could be 268×360 while the actual art is 41×55, a noninteger x pitch around 6.5883 and y pitch around 6.5455. A one-cell eye highlight is not a multi-pixel blob: it is precisely one logical cell. This lesson must remain central through every implementation. The original 41×55 grid and the coordinates (16,19), (24,19) are regression fixtures.

There are **two modes of work in one editor**, not two separate simplified apps:

- **Fast mode:** sketch → duplicate frame → change pose in a few pixels → onion skin → playback → repeat. Keyboard-friendly, no needless dialogs, adjustable per-frame holds and timings. Frame import, copy/paste, and calibration should take seconds, not hundreds of clicks.
- **Production mode:** layer organization, predictable exact-cell edits, coherent palettes, reusable grid profiles, non-destructive transforms, precise selection, reference images, tiles, careful timing, project recovery, export presets, and large-project responsiveness.

No browser-window UI, no server, no cloud dependency, no mandatory external configuration files. User customizations eventually live inside **Preferences** and project UI. Windows 11 first, with Linux/macOS possible later through the same Qt code.

## B. Invariant: one real pixel

1. Every cel is an actual W×H RGBA raster. View zoom is never part of stored pixel data.
2. Reference images can have fractional pitch and drifting edge boundaries due to screenshot scaling. Grid measurement is stored separately, preferably with rational/fractional pitch, origin, and optional explicit boundary corrections.
3. Every import must disclose **source screenshot dimensions vs logical output grid** before confirmation. Never guess that 268×360 implies 268×360 editable pixels.
4. Grid-to-pixel conversion samples within measured cells (center/median/mode) to avoid bleeding from antialiasing. For true 1:1 sources, never average neighboring cells.
5. One-pixel landmarks are regression tests; Mellow's two eye highlights may not spread into multiple output pixels.
6. Repeated frames share a consistent logical coordinate system. Different reference crops or scales require a visible transform, never silent stretching.

## C. Full professional feature inventory (tracked, not forgotten)

Legend: **0.1–0.2.2** merged source milestones with limitations; **0.2.2** reliability; **0.2.3** measured-reference pipeline; **0.3A** professional painting; **0.3B** animation; **0.4** production/interoperability; **0.5+** tiles/advanced systems; **1.0** release hardening. A phase is a target, **not evidence of implementation or acceptance**. Status lives in `SPRINT_LOG.md`.

### Canvas, drawing, and color

| Feature | Scope | Phase |
|---|---|---|
| Pixel-exact canvas, nearest-neighbor integer zoom, grid, checker, coordinate inspection | core | [0.1] |
| Pencil, eraser, color picker, bucket, contiguous/global replace | core | [0.1] |
| Lines, rectangle/ellipse outline and fill, brush size, symmetry, flipping | core | [0.1] |
| Pixel-perfect line algorithm (remove doubled corners), brush masks, custom stamps, dithering brush | refinement | 0.3A |
| Linked foreground/background colors, swap/reset, alpha sliders, palette index view | refinement | 0.3A |
| Color wheel, HSV/RGB/hex input, palette groups, ASE/ACO/GPL import/export | standard | 0.3A |
| Indexed palette mode, remap all cels, duplicate-color merging, global palette swaps | pro | 0.4 |
| Gradients (stepped, dithering), shading/outline tools, pattern fills, replace color with tolerance | pro | 0.3A |
| Custom grid size/color, pixel aspect ratio, symmetry axis position, guides/rulers | pro | 0.3A |
| Tiled wrapping view, isometric assistance, tile repeat painting, selectable tile boundaries | pro | 0.5+ |
| Input pressure curves/tablet support (non-blurry pixel brushes), gesture binding | pro | 0.4 |

### Selection and transforms

| Feature | Scope | Phase |
|---|---|---|
| Rectangular selection, move, keyboard nudge, all/deselect, copy/cut/paste, mirror | core | [0.1] |
| Floating selection layer, paste in place, paste at cursor, transform bounds, safe cancellation | essential | 0.2.1 / 0.3A |
| Lasso, polygon, elliptical marquee, magic wand with tolerance, contiguous toggle | standard | 0.3A |
| Boolean selection add/subtract/intersect, invert, feather disabled in pixel mode | standard | 0.3A |
| Resize/rotate (90°, fixed-angle nearest-neighbor), flip selection, anchor and pivot | standard | 0.3A |
| Smart bounding boxes, pixel-aware scale snapping, selection grow/shrink by cell | pro | [0.4] |

### Animation, timeline, and rapid iteration

| Feature | Scope | Phase |
|---|---|---|
| Add, duplicate, delete frames; per-frame ms duration; preview; onion skin | core | [0.1] |
| Independently editable cels for every layer/frame | core | [0.1] |
| Measured screenshot sequence importer with one shared calibration | unique workflow | [0.1] |
| Native spritesheet → individual frames, lossless sprite sheet export + durations | standard | [0.1] |
| Timeline drag-reorder, multi-select frames, copy/paste frame blocks, batch duplicate | speed | 0.2.1 |
| Linked/exposure cels and holds (don't duplicate 10 identical cel buffers) | speed/performance | 0.2.0 |
| Per-layer onion skin ranges, previous/next tint, opacity and temporal offsets | standard | 0.3B |
| Real-time alternate-pose preview, A/B compare, frame pinning and reference pose | speed | 0.3B |
| Frame tags/loops (idle/walk/run/etc.), playback direction/ping-pong, timeline zoom | standard | 0.3B |
| Cel operations: nudge linked frame regions, align with markers, copy an edit across a range | speed | 0.3B |
| Tileset and tilemap animation, collision/property metadata, animated tiles | pro | 0.5+ |
| Audio track reference, loop markers, frame-accurate sound cue playback | pro | 0.5+ |
| Keyframe/tween assistance *only as optional pixel-grid-safe automation* | experimental | 0.5+ |

### Measurement, reference, grid reconstruction (flagship)

| Feature | Scope | Phase |
|---|---|---|
| Manual cols/rows, fractional cell pitch, x/y origin, live grid overlay | flagship | [0.1] |
| Measure pixel period from two boundary clicks N cells apart, independently on X/Y | flagship | [0.1] |
| Suggest grid offset using pixel-edge contrast for a known logical grid | flagship | [0.1] |
| Measured 41×55 Mellow calibration profile, exact eye-highlight guides | regression | [0.1] |
| Multi-frame aligned reference import, exact-cell sampling | flagship | [0.1] |
| Fully automatic pixel-pitch and grid-size **suggestion with confidence**, not silent auto-commit | flagship | 0.2.0 |
| Interactive drag-to-adjust grid boundaries, snapping and preview of reconstructed cells | flagship | 0.2.0 / 0.2.3 |
| Adaptive palette quantization/mode sampling, nearest exact color, edge halo repair | flagship | 0.2.3 |
| Split screenshots with uneven zoom/cropping; per-frame calibration profiles, landmark alignment | flagship | 0.2.3 |
| Alignment between poses using anchor pixels / bounding-box origin / ghost comparisons | flagship | 0.2.3 |
| Reference dock, opacity/blend/wipe/difference comparisons and audit heatmap | pro | 0.2.3 |
| Import and reconstruct animated GIF/APNG into editable cels and preserve timings | pro | 0.4 |
| Grid distortions/perspective and explicit per-column/per-row boundary overrides | specialized | 0.5+ |

### Layers, files, export, usability

| Feature | Scope | Phase |
|---|---|---|
| Multiple independent layers, reorder, rename, lock, visibility, opacity | standard | [0.1] |
| Lossless zipped native project with per-layer per-frame PNG, schema and metadata | standard | [0.1] |
| Undo/redo, autosave recovery, dirty flag, confirmation on discard | standard baseline | [0.1] |
| PNG, GIF, spritesheet + metadata, numbered frame PNG exports | baseline | [0.1] |
| Docking panels, persistent dock layout, keyboard tool selection | standard baseline | [0.1] |
| Delta/compressed undo (performance), journal/transaction integrity, robust crash recovery | essential | 0.2.1 / 0.2.2 |
| Layer groups, clipping masks, reference-only layers, cel linking, drag-drop | pro | 0.3A |
| More export layouts (rows/columns), trim/padding/extrude, multi-scale packs, JSON atlas | production | 0.3B |
| APNG, WebP, Aseprite interoperability, GIF transparency/palette validation | production | 0.4 |
| Fully editable shortcuts, mouse customization, command palette and action search | productivity | 0.3A |
| Tile/sprite library, batch importer, project explorer, asset tagging | pro | 0.4 |
| Workspace presets (quick animator, paint, tilemap), multi-document tabs | pro | 0.4 |
| High-DPI/multi-monitor, pen tablets, accessible controls, localization, undo persistence | polish | 0.2.2 / 1.0 |
| Signed/portable Win64 release, updater optional, Windows file association, crash telemetry opt-in | ship | [1.0] |

## D. Interface plan

- **Center:** native canvas with fast zoom, pan, grid and reference overlays. No floating opaque UI covering the art.
- **Left toolbar:** tools, quick brush size, symmetry, paint modes. Direct click and hotkeys are equivalent.
- **Right docks:** layers, palette, live preview, reference/measurement (last planned dock). Collapsible/dockable/save positions.
- **Bottom timeline:** frame thumbnails with timing, duplication, multi-selection, layer cel sheet, onion toggles and eventual frame tags.
- **Bottom status bar:** exact logical (x,y), RGBA/index, canvas dimensions, zoom, current frame/layer, action progress.
- **Modes:** Quick Animator workspace reduces chrome but *does not hide data or remove features*; Production layout presents more controls.

## E. Event/command architecture

**Current implementation (verified code, not future diagram):** `main.py` coordinates many Qt actions and mutations, `canvas.py` owns paint/input, `model.py` owns raster cels, frames, shared link identity, persistence and compressed history; `calibration.py` and `importer.py` measure source pixels. There is **no full command dispatcher, region-delta engine or composite/thumbnail caching yet**.

**Incremental target, without a large rewrite:**

```text
Qt canvas / timeline / actions / shortcuts
                    |
          Editor command dispatcher
          (transaction + validation)
                    |
          Logical Document Model
          /         |           \
     Cel/layer   Animation    Source reference
       store     + exposure   + calibration
                 linking     + registration
          \         |           /
        Dirty-region invalidation
                    |
       Cached composite + thumbnails
                    |
      Atomic save / recovery / export
```

**Invariants:** linked exposures intentionally share edits until explicit unlink; independent cels do not; an operation is one undoable transaction; floating selections do not change project bytes before commit; reference-source alignment/provenance is stored independently of pixel art; zoom never modifies the logical grid.

**Order:** save and recovery safety → explicit edit transaction boundaries → targeted composite/thumbnail invalidation → region-delta history if profiling justifies it → reference model/provenance. Keep the engine Qt-free so tests can reproduce bugs. Do not label compressed snapshots as delta history.

## F. Fast iteration procedures, with acceptance tests

**Workflow F1 — two-frame loop:** Load 41×55 Mellow; duplicate (`Ctrl+D`), alter a single cell; set 100ms/100ms; play; edit again; export PNG sheet/GIF. **Pass**: identical original frame preserved; no 268×360 scaling artifacts; Ctrl+Z undoes the single stroke, not the frame switch.

**Workflow F2 — manual measured screenshot:** Input 268×360; set 41×55; either use Mellow preset or measure X/Y boundaries and origins. **Pass**: output exactly 41×55; eye marks at (16,19), (24,19) are one output cell each.

**Workflow F3 — batch grid-to-animation:** Import 12 screenshots including visually misaligned sources with *identical* screenshot dimensions. Calibrate once, detect differing crops/origins, register and manually correct per-frame landmarks. **Pass**: aligned editable 41×55 output with original reference data and reversible calibration kept, timing intact, undo correct and no silent stretch/warp.

**Workflow F4 — craft sprite:** Create blank 128×128, 8 layers, 24 frames; work at 8×; flip, select, use bucket, copy/paste and palettes. **Pass**: pixel edges never anti-aliased; lossless project round-trip, compositing reliable; snapshots do not corrupt layers.

**Workflow F5 — production loop:** Establish frame tags, palette indices, reference overlays, linked holds, validate game-engine sheet + JSON exports, reopen project and continue with keyboard only. **Pass**: all action shortcuts discoverable/configurable; no missing frame duration data; memory use bounded. Future milestone.

**Workflow F6 — recovery faults:** Edit two projects, autosave both, deny/interrupt saves, corrupt a ZIP, then reopen. **Pass**: no shared recovery slot, no overwritten valid save, no unannounced recovery into wrong project, actionable errors and preserved dirty state.

## G. Development cycle — rapid, gated, honest

**Status on 2026-10-28:** Source milestones 0.1 and 0.2.0 shipped; Sprint **0.2.1 merged** in [PR #2](https://github.com/VickMASpc/MellowStudio/pull/2), with four green CI jobs (Windows Python 3.11/3.13 including Qt smoke, Linux Python 3.11/3.13 headless). The user confirmed their Windows test works. This establishes a working baseline, **not** completion of all manual acceptance gates or production features.

**0.2.2 — reliability and interaction quality (NEXT; [Issue #3](https://github.com/VickMASpc/MellowStudio/issues/3)):** per-project recovery identity/history; save-failure, archive corruption and rollback tests; GUI mutation/undo transaction boundaries; cached composites and lazy thumbnail invalidation; keyboard focus/high-DPI interactions; and measured performance on 41×55 and 128×128/8 layers/24 frames. **Exit:** no silent loss in fault-injection tests, 20 consecutive duplicate/edit/undo cycles, a clean 60-second Windows drawing session, meaningful RAM and latency readings. Capture 5700U results when available; CI is not a substitute.

**0.2.3 — flagship reference-to-animation (IN PROGRESS):** implemented phase one: v3 embedded source assets and sampling provenance, per-frame calibration/registration, suggest-only translation offsets, red/cyan difference preview, manual reconstruction via Reference Lab, and 12 cropped/offset same-dimension references whose 41×55 output is identical. **Still in phase:** distinct crop/scale changes beyond translations, manually marked landmark registration, wipe/heatmap comparison modes, detection of content lost beyond image boundaries, advanced sampling and reference-cel provenance in further edits. **Exit:** F3 passes on 12 mixed-offset references, with after-reopen re-editable registration and no silent resampling changes; separately verify variable-scale and occluded crops before full sprint acceptance.

**0.3A — professional painting:** pixel-perfect strokes, dither/custom brushes, full color input/palettes, advanced selections/boolean masks/transforms, layer groups/clipping and shortcut customization. **Exit:** create and refine a finished layered 128×128 sprite without another painting program; selection/undo/reopen tests pass.

**0.3B — professional animation:** per-layer onion controls, frame tags and loop modes, pose pinning/A-B comparison, copy edits across frame ranges and game-engine-ready spritesheet/atlas exports with reliable timing. **Exit:** create idle/walk/run cycles and export/reopen all cels and durations without a second animation application.

**0.4 — production and interoperability:** indexed palettes, APNG/WebP/Aseprite interoperability, customizable workspaces, multi-document organization, asset management, project migration/versioning, performance profiles and export presets. **Exit:** repeated save/reopen/export/edit of production-sized projects is verified, with measured memory limits.

**0.5+ — tiles and advanced workflows:** tilemaps, animated tiles/collision metadata, advanced batch transforms, audio cues, optional pixel-safe tweening, specialized grid distortions and asset library. Retained scope, **not** a blocker to a reliable standalone pixel animation editor.

**1.0 — release gate:** verified Windows portable/installer builds, compatibility and long-session tests, accessibility/HiDPI checks, versioned migration, recovery, crash tests and reproducible packaging; no open data-loss or untested critical export/save paths. Signed executable and updater remain optional release-engineering enhancements.

**Per feature PR:** scoped issue/acceptance criteria → smallest vertical implementation → engine and Qt tests → Mellow one-pixel regression/demo → measured results/known limitations → update **BOTH** [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) and [SPRINT_LOG.md](SPRINT_LOG.md) → CI → manual acceptance when interaction-sensitive → merge. GitHub `main` is the canonical project; no separate per-sprint ZIP folders. Tag tested milestones for packaged releases. A CI document gate enforces paired updates for code PRs; branch protection is required to make this non-bypassable.

## H. Performance & quality budgets

Target test machine: Ryzen 7 5700U with integrated graphics and 16 GB RAM. **Targets, not measured results**:

- Cursor-to-pixel response below one 60Hz frame for common 16–256px sprites, with playback not rebuilding the whole timeline.
- 60fps viewport repaint target with integer nearest-neighbor scaling; preview frame timing respects project durations.
- Undo memory bounded by a configurable memory budget. **Current:** compressed full-state snapshots with deduplicated linked cels, default 128 actions / 128 MiB. **Future target:** region-delta history informed by measured workloads; not yet implemented.
- Reference calibration usable up to screenshot-size images without per-frame 100ms stalls, performed off UI thread if it grows heavy.
- Save/recovery target: tested atomic writes, per-project rotating recovery snapshots, interruption/corruption fault injection and export checks. Temporary-file replacement exists today; power-loss recovery is not yet fully verified.
- Project files are verified on load for sizes, version, layer ids, missing/corrupt cels, and invalid timing; future migrations explicit.

## I. Risks tracked up front

1. **Auto-grid confidence:** a feature repeating every 2 cells can masquerade as a doubled pixel period. Suggest candidate pitches, show overlay and confidence, and let the user correct it. Never auto-commit inferred native dimensions without a preview.
2. **JPG/scaled image artifacts:** halo/blur from screenshot preprocessing can hide the original palette; support center/median/mode and palette repair in imports.
3. **RAM growth:** 0.2.1 stores compressed snapshots with deduplicated linked exposures, but each edit still records the document; caching and real benchmarks precede region deltas.
4. **GIF limitations:** indexed transparency and palette reduction can degrade colors. Treat native PNG sheets and project format as sources of truth, test GIF compatibility explicitly.
5. **Keyboard conflicts:** single-letter tools must not fire while editing labels/spin boxes. GUI smoke tests must focus these edge cases.
6. **Windows packaging:** initial source ZIP runs after installing Python/requirements. EXE must be built and smoke-tested on Windows, not merely assumed from build scripts.
7. **Scope creep:** the complete feature inventory remains visible, but each increment must be a working end-to-end path, not a UI button attached to a placeholder.
8. **Same-size misregistration:** source dimensions do not reveal crop offsets or actual pose movements. Suggest translations only with explicit review; variable zoom, scale and irrecoverable edge cropping remain open. Original 268×360 → 41×55 stays a hard regression.
9. **Recovery collisions:** a shared autosave filename is not sufficient for multiple projects; 0.2.2 is explicitly a data-safety sprint.
10. **Viewport scaling:** composite rebuilds and eager timeline thumbnails risk stalls; invalidate selectively and benchmark.
11. **CI bypass:** the PR documentation gate is advisory until branch protection makes its successful status required.


## J. Sprint delivery status (2026-10-28)

- **Merged v0.2.0:** linked holds/cels, independently editable frames, multi-select/clipboard, v2 project archive with v1 read support, suggest-only auto-grid candidates, fractional manual calibration and batch exports.
- **Merged v0.2.1:** floating pixels with explicit commit/cancel, selected timeline drag reorder and bounded compressed snapshot undo/redo; [PR #2](https://github.com/VickMASpc/MellowStudio/pull/2) merged. Latest `main` CI passes on Windows/Linux. Manual Windows launch/testing was reported successful, but interaction-intensive acceptance remains ongoing.
- **Still open:** tile/run undo deltas; full registration across unequal scales and true crop loss; manual UI polish/Windows testing; advanced palette/brush/onion systems; full production interoperability and Windows installer validation.
- **Active next milestone:** 0.2.3 reference registration. 0.2.2 issue #3 remains open for deferred acceptance gates. The evidence, defects, metrics and next actions live in [SPRINT_LOG.md](SPRINT_LOG.md).

## J.1 Sprint 0.2.3 working implementation (2026-10-28)

- **Now implemented in code:** `ReferenceAsset` data model, immutable embedded PNG source bytes per registered frame, schema 3 persistence plus v1/v2 loading, stored per-frame fractional origin/pitch and sampling mode; frame reorders and history preserve provenance. Shared duplicated reference assets detach before single-frame calibration edits.
- **Reference Lab Qt UI:** file import opens a reference registration review dialog (when a measured sequence is selected); manual origin adjustment, red/cyan difference, explicit suggested-offset adoption, per-frame source-to-logical reconstruction and a right-side reference dock; calibration remains editable after loading a saved document. Workspace header and palette refresh are deliberately secondary to this pipeline.
- **Verified headless fixture:** `examples/reference_lab_12frame_demo.mellowzip` contains twelve original 268×360 offset screenshots whose registered cels are exactly 41×55. At baseline all cels compare byte-for-byte to Mellow, including one-cell eye highlights at (16,19)/(24,19); source bytes and calibrations survive project round trips and undo.
- **Correctness fix:** source center sampling now consistently uses the floor of the actual source-space cell center, avoiding Python round-to-even half-pixel drift.
- **Not yet finished:** affine/scale or perspective registration, landmark placement in the workbench, robust detection of lost boundary content, full wipe/heatmap reference inspector, stress profiling of large screenshot sequences. Qt UI smoke and physical Windows test are distinct from headless CI.

## K. Mandatory sprint documentation and change control

1. **Always maintain both documents:** `docs/DEVELOPMENT_PLAN.md` for scope, phase changes, feature inventory, acceptance criteria, risks and architecture; `docs/SPRINT_LOG.md` for dated progress, evidence, failures, tests, remaining work and next actions.
2. **Every code PR** touching editor code, CLI, tests, packaging, scripts, dependencies or workflows must update **both** documents in the same PR. The CI docs gate checks file presence in the PR diff. Documentation-only changes can update just the relevant files.
3. **Never equate code written, automated test passed, manually tested and accepted.** Use statuses `PLANNED`, `IN PROGRESS`, `IMPLEMENTED`, `CI VERIFIED`, `MANUAL VERIFIED`, `ACCEPTED`, `BLOCKED` with scope/evidence links.
4. **No silent scope drop:** deferred work stays in the feature inventory; new risks and known regressions get GitHub issues, and changes in scope/order get dated rationale in the sprint log.
5. **For each sprint closeout:** record the GitHub PR/commit, Windows CI and hands-on status, baseline regressions, benchmark numbers or explicit `NOT MEASURED`, release readiness, and the successor sprint.
6. **Merge policy:** feature branches/PRs → CI → manual validation where necessary → merge to `main`; releases are tagged on tested commits. A branch protection rule should require the docs-gate check; until configured, CI cannot technically prevent bypass.

## K. Active code verification addendum (Sprint 0.2.2)

The editor now has **actual in-progress changes**, not just planning: a foreground/background Bayer dither brush (`D`, adjustable 0–16 mix); per-project recovery snapshots/chooser and legacy support; validating atomic project saves with pre-replacement integrity check and `.bak` preservation; frame/onion/thumbnail QImage caching with linked-cel invalidation; and a repeatable headless benchmark script. The change does **not** imply that region-delta undo, 12-frame per-source registration, 5700U performance validation or the 60-second Windows manual acceptance gate are complete. See [SPRINT_LOG.md](SPRINT_LOG.md) and [`PERFORMANCE_BASELINE_SANDBOX.json`](PERFORMANCE_BASELINE_SANDBOX.json) for evidence and limitations. On every next implementation PR update both documents with measured results, new failures and newly accepted or deferred tasks.

## M. Git branch and local-checkout hygiene (2026-10-28)

- `main` is the authoritative, CI-tested integration branch; feature PRs are squash-merged once validated. A squash merge does **not** leave the feature tip as an ancestor of `main`, so plain `git branch -d` is insufficient for cleaning those particular local branches.
- After each push to `main`, GitHub Actions (`prune-merged-branches.yml`) enumerates branches and removes a nonprotected `feat/`, `fix/`, `chore/` or `docs/` ref **only when** an already-merged PR to `main` in this very repository has an identical head branch name **and commit SHA**. Branches with unmerged work or new post-merge commits are preserved. The workflow tests its decision rule offline.
- **Corrected Windows update behavior (2026-10-29):** `./dev.ps1 sync` validates the configured `origin`, fetches the latest GitHub `main`, and replaces tracked source files to match it without a merge/rebase or dirty-tree prompts. **Never** call `git clean -ffdx`; retain `.venv`, ordinary untracked/ignored project artwork, exports, and personal local branches. This explicitly supersedes the earlier destructive `sync` interpretation that deleted the Python environment on every update. Existing virtual environment packages remain available, avoiding repeat downloads. A conflicting tracked source edit is intentionally discarded to get the latest version; a rare untracked path that collides with a newly tracked GitHub file may still be overwritten by forced checkout, so personal art should be kept in its own files. Verify this in Windows Git integration tests.
- A GitHub-side deletion does not alter a person's local repository until their next fetch. Manual or automated Git maintenance cannot repair credential, DNS, proxy, or non-fast-forward problems on a machine without examining that machine. The script reports those rather than rewriting history.
- Repository housekeeping changes still update this document and `SPRINT_LOG.md` as required by CI.
- **Verified outcome (2026-10-28):** cleanup PR #8 merged; the GitHub Actions branch janitor removed five verified merged branches, and the GitHub branch listing now contains only `main`. Both Windows/Linux CI and the branch safety contract passed. This does not alter local branches until the user runs a fetch/sync.

- **Sync root-detection correction (2026-10-29):** The force-sync's original absolute string comparison between Git's reported top-level path and PowerShell's resolved path incorrectly rejected a user's Windows checkout. Replace it with `git rev-parse --show-prefix` from the script-owned working directory (empty only when at the actual repository root). This handles path formatting/alias differences without relaxing the protection against cleaning a parent repository. Add a Windows fixture under `Nova pasta (8)/MellowStudio` and a nested-script refusal test.

### Windows launch reliability — pip-less virtual environments (2026-10-29)

**Observed defect:** After the explicitly destructive sync removes `.venv`, the launcher can encounter a newly created or existing environment without `pip`. Previous setup checked imports and immediately invoked `python -m pip install -e .`, which failed with `No module named pip`. The next incremental release adds a dedicated automatic `ensurepip --upgrade` repair before dependency installation, clear failure messages when Python has no `ensurepip`, and explicit startup diagnostics. Maintain the no-extra-environments rule. The Windows CI acceptance fixture deliberately builds a pip-less venv under a path with spaces/parentheses, tests restoration, idempotency and invalid-interpreter refusal. Actual physical-machine startup still requires verification.

### Development workflow correction — preserve user environment (2026-10-29)

The user's request to 'wipe' was a request to stop update conflicts and always get the latest Mellow build, **not** to reinstall Python dependencies or destroy art. The old `sync` implementation used `git clean -ffdx` and removed local branches. This caused the previously working environment to be deleted and introduced pip/bootstrap failures. Revert that product mistake. The correct acceptance criteria are: update tracked editor code even after local tracked edits or divergent commits; keep existing `.venv` bit-for-bit; keep ordinary untracked sprite files, exports and independent branches; fail safely before editing if the fetch or origin check fails; and support repeated syncs without package reinstall. Do not suggest reinstalling system Python as the first response to an application-created virtual environment issue.

### Qt binary startup reliability — Windows DLL load failure (2026-10-29)

**Reported incident:** After code sync and environment recreation, Mellow reached `run.py` but failed at `from PySide6.QtCore import ...` with a Windows DLL-load error. This is an error in the **native Qt runtime loading path**. The previous setup only tested `import PySide6`, which may succeed when `PySide6.QtCore` cannot load. The underlying missing native DLL cannot be inferred from that traceback alone; do not attribute it to a broken system Python installation.

**Correction:** Pin PySide6 to a consistent tested version (6.10.2), preflight actual `QtCore`/`QtGui`/`QtWidgets` native imports, and, if they fail, attempt at most one focused reinstall of matching Qt packages inside the existing `.venv`. Keep Pillow, NumPy, artwork, Python itself and the virtual environment untouched. If the import remains broken, print Python/Qt package versions, Qt binary locations, Windows VC runtime checks, and Qt environment overrides instead of reinstalling repeatedly. GitHub Windows CI verifies the native import and a failure-diagnostic path. The precise DLL missing on the user's PC remains unknown until diagnosed; Windows CI is not manual acceptance.

### Qt package-version reconciliation, Python 3.14 (2026-10-29)

**Confirmed on user's machine:** Windows Python 3.14.3 x64; PySide6, Essentials, Addons and shiboken6 **all 6.12.0** despite the project pin **6.10.2**. QtCore.pyd and Qt6Core.dll are present but QtCore native import fails. The checked vcruntime140, vcruntime140_1 and msvcp140 DLLs are loadable. No evidence that Python installation or those three runtime DLLs need reinstalling. Qt 6.10.2 declares support for Python 3.14 on PyPI. The actual unresolved transitive DLL and effectiveness of a targeted package repair on this PC remain unconfirmed.

**Actual code defect:** The earlier setup's dependency check accepted *any* PySide6 metadata version and only ran a native Qt import check after that. Its legacy `.mellow_qt_repair_attempted` marker could suppress subsequent repairs, leaving 6.12.0 in place despite a 6.10.2 pin. Fix by checking all four Qt component versions **first**, then QtCore/QtGui/QtWidgets imports; on mismatch or failed native import perform one version-specific targeted repair of Qt packages only. Ignore the legacy generic marker. Use a version-scoped new marker to prevent infinite repeat downloads. Never remove `.venv`, reinstall system Python, or wipe artwork. Add unit tests for healthy, stale, mixed and absent bindings; add **Windows Python 3.14** to the full CI matrix. Only claim laptop success after it actually launches.


## 0.2.6 — Dockable windows AND usable color editing (2026-10-29)

**Correct user interpretation (Issue #19):** They never asked us to eliminate windows. They objected to an obstructive Colors window, no practical color editing, and losing panels after closing them. The 0.2.5 removal of windows was the wrong solution. Artist-first design supports **both** flexible windows **and** a sane, unobstructed default arrangement.

**Working interaction contract:** Reintroduce actual QDockWidgets for Colors, Layers, Preview and Reference: movable, floatable, closable, with initial Colors and Layers independently docked at the right of the canvas (not overlapping, not tab-hidden). View always exposes a toggle to reopen them. Ctrl+Shift+0 restores normal default docking; dock positions are saved only under a new v3 key, deliberately ignoring obsolete problematic geometry. The timeline remains below the canvas, with a View toggle and focus mode.

**Colors is a tool, not a launch button for a dialog:** A color editing field for saturation/brightness, a hue control, RGB numeric fields, and hex editing operate directly in the panel while drawing. Foreground and secondary remain distinct; palette swatches choose paint on left click and secondary on right, and the current color may be saved/replaced/removed from the project palette with undo. The native QColorDialog remains optional under More.

**Acceptance:** Paint while seeing and using Colors, with Layers accessible; detach any panel as a window, move it, close it, reopen from View, and reset the layout. Test precise RGB/hex assignments, palette mutation and undo, persistence and canvas nonoverlap. Windows Qt automated tests plus real user visual review required. Do not mistake removal of user choice for polish.

## 0.2.7 — Restore full docking freedom from the actual pre-removal commit (2026-10-29)

**Exact historical baseline:** commit `9edc3488aa11cffee84662782c663dc3ed437034`, the parent of destructive PR #13's merge commit `0a64ca9c`. The user explicitly clarified that they **deliberately** stacked windows on top/within the main editor. They did not want stacking prohibited. The resulting shrinking canvas was the problem; F11 focus partially addressed it. 0.2.5 eliminated original QMainWindow docking in response, and 0.2.6 restored a restrictive subset (left/right only, timeline permanently integrated), reducing creative freedom.

**Implementation:** Rebuild `mellowstudio/main.py` from the exact pre-#13 Qt QMainWindow and QToolBar implementation, bringing forward only the 0.2.6 working direct Colors editor (hue, saturation/value field, RGB/HEX, independently selectable paint/secondary, palette add/replace/remove), 0.2.6 versioned project handling, and essential recovery improvements. The restored dock architecture supports ALL sides, tabbed docks, nested docks, freely floating/closable panels and a fully dockable timeline. Nothing silently redirects a deliberate user drop. Keep Colors + Layers simultaneously accessible by default, rather than forcing them into a tab group. Preview and Reference remain optional. Wrap Colors in an independently scrollable dock so it stays editable if the user docks it into a short region. Reserve a useful 340×240 central canvas viewport minimum to reduce the squeeze from additional dock stacks; F11 preserves/restores full Qt dock topology and active tab arrangement.

**Easy recovery without removing choice:** Each dock registers its native View toggle action. Closing a window is reversible via View → Windows. Ctrl+Shift+0 resets dock positions, floating state and visibility to Colors/Layers beside the canvas and Timeline below. Store new Qt state under `window/state_full_docks_v1` to avoid old broken versions resurfacing, while preserving fresh user-customized topology on the next launch. Existing source reconstruction, animations, project saves, undo, exports and the full drawing toolkit remain intact. No changes to dependency bootstrap or sync policy.

**Acceptance test:** Drag Colors/Timeline to any side, tab two docks, deliberately nest windows within the main editor, float/close/reopen, focus F11 and restore the exact dock group, then reset all windows. Confirm original selected painting color and palette features still work. Windows 3.11/3.13/**3.14** GUI CI is essential but not a substitute for real Windows hands-on visual usability, including the worst-case compressed canvas case.
