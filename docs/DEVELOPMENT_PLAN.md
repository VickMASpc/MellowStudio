# Mellow Studio — product specification & development cycle

**Canonical roadmap:** this file in GitHub. **Current merged baseline:** v0.2.1 on 2026-10-28; **active development:** v0.2.2 (PR #2); **next sprint:** 0.2.2 reliability and transactions ([Issue #3](https://github.com/VickMASpc/MellowStudio/issues/3)). Keep the [sprint log](SPRINT_LOG.md) synchronized with each implementation PR. Future phase targets below are not claims of verified functionality.

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

Legend: **0.1–0.2.1** completed source milestones with limitations; **0.2.2** reliability; **0.2.3** measured-reference pipeline; **0.3A** professional painting; **0.3B** animation; **0.4** production/interoperability; **0.5+** tiles/advanced systems; **1.0** release hardening. A phase is a target, **not evidence of implementation or acceptance**. Status lives in `SPRINT_LOG.md`.

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

**0.2.3 — flagship reference-to-animation:** retain source asset/provenance, measured calibration per frame and cropping/offset diagnostics; reversible landmark registration for same-size but misaligned screenshots; overlay/wipe/difference views; manual corrections and source-to-cel replay. **Exit:** F3 passes on 12 mixed-offset references, with after-reopen re-editable registration and no silent resampling changes.

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
8. **Same-size misregistration:** source dimensions do not reveal different crop offsets, palette halos or source scaling; per-frame registration is the 0.2.3 differentiator.
9. **Recovery collisions:** a shared autosave filename is not sufficient for multiple projects; 0.2.2 is explicitly a data-safety sprint.
10. **Viewport scaling:** composite rebuilds and eager timeline thumbnails risk stalls; invalidate selectively and benchmark.
11. **CI bypass:** the PR documentation gate is advisory until branch protection makes its successful status required.


## J. Sprint delivery status (2026-10-28)

- **Merged v0.2.0:** linked holds/cels, independently editable frames, multi-select/clipboard, v2 project archive with v1 read support, suggest-only auto-grid candidates, fractional manual calibration and batch exports.
- **Merged v0.2.1:** floating pixels with explicit commit/cancel, selected timeline drag reorder and bounded compressed snapshot undo/redo; [PR #2](https://github.com/VickMASpc/MellowStudio/pull/2) merged. Latest `main` CI passes on Windows/Linux. Manual Windows launch/testing was reported successful, but interaction-intensive acceptance remains ongoing.
- **Not shipped:** tile/run undo deltas; robust project-specific recovery; source-reference retention/alignment across different crops; render/thumbnail caches; advanced palette/brush/onion systems; full production interoperability and Windows installer validation.
- **Active next milestone:** 0.2.2 ([Issue #3](https://github.com/VickMASpc/MellowStudio/issues/3)). The evidence, defects, metrics and next actions live in [SPRINT_LOG.md](SPRINT_LOG.md).

## K. Mandatory sprint documentation and change control

1. **Always maintain both documents:** `docs/DEVELOPMENT_PLAN.md` for scope, phase changes, feature inventory, acceptance criteria, risks and architecture; `docs/SPRINT_LOG.md` for dated progress, evidence, failures, tests, remaining work and next actions.
2. **Every code PR** touching editor code, CLI, tests, packaging, scripts, dependencies or workflows must update **both** documents in the same PR. The CI docs gate checks file presence in the PR diff. Documentation-only changes can update just the relevant files.
3. **Never equate code written, automated test passed, manually tested and accepted.** Use statuses `PLANNED`, `IN PROGRESS`, `IMPLEMENTED`, `CI VERIFIED`, `MANUAL VERIFIED`, `ACCEPTED`, `BLOCKED` with scope/evidence links.
4. **No silent scope drop:** deferred work stays in the feature inventory; new risks and known regressions get GitHub issues, and changes in scope/order get dated rationale in the sprint log.
5. **For each sprint closeout:** record the GitHub PR/commit, Windows CI and hands-on status, baseline regressions, benchmark numbers or explicit `NOT MEASURED`, release readiness, and the successor sprint.
6. **Merge policy:** feature branches/PRs → CI → manual validation where necessary → merge to `main`; releases are tagged on tested commits. A branch protection rule should require the docs-gate check; until configured, CI cannot technically prevent bypass.

## K. Active code verification addendum (Sprint 0.2.2)

The editor now has **actual in-progress changes**, not just planning: a foreground/background Bayer dither brush (`D`, adjustable 0–16 mix); per-project recovery snapshots/chooser and legacy support; validating atomic project saves with pre-replacement integrity check and `.bak` preservation; frame/onion/thumbnail QImage caching with linked-cel invalidation; and a repeatable headless benchmark script. The change does **not** imply that region-delta undo, 12-frame per-source registration, 5700U performance validation or the 60-second Windows manual acceptance gate are complete. See [SPRINT_LOG.md](SPRINT_LOG.md) and [`PERFORMANCE_BASELINE_SANDBOX.json`](PERFORMANCE_BASELINE_SANDBOX.json) for evidence and limitations. On every next implementation PR update both documents with measured results, new failures and newly accepted or deferred tasks.
