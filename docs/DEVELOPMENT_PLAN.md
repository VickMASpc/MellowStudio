# Mellow Studio — product specification & development cycle

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

Legend: **[0.1]** v0.1 baseline / **[0.2]** target sprint / **[0.3]** / **[0.4]** / **[1.0]** forecast. A phase marking is a **target**, not evidence that every item in that row ships. See the verified status in `SPRINT_LOG.md`.

### Canvas, drawing, and color

| Feature | Scope | Phase |
|---|---|---|
| Pixel-exact canvas, nearest-neighbor integer zoom, grid, checker, coordinate inspection | core | [0.1] |
| Pencil, eraser, color picker, bucket, contiguous/global replace | core | [0.1] |
| Lines, rectangle/ellipse outline and fill, brush size, symmetry, flipping | core | [0.1] |
| Pixel-perfect line algorithm (remove doubled corners), brush masks, custom stamps, dithering brush | refinement | [0.2] |
| Linked foreground/background colors, swap/reset, alpha sliders, palette index view | refinement | [0.2] |
| Color wheel, HSV/RGB/hex input, palette groups, ASE/ACO/GPL import/export | standard | [0.3] |
| Indexed palette mode, remap all cels, duplicate-color merging, global palette swaps | pro | [0.3] |
| Gradients (stepped, dithering), shading/outline tools, pattern fills, replace color with tolerance | pro | [0.3] |
| Custom grid size/color, pixel aspect ratio, symmetry axis position, guides/rulers | pro | [0.3] |
| Tiled wrapping view, isometric assistance, tile repeat painting, selectable tile boundaries | pro | [0.4] |
| Input pressure curves/tablet support (non-blurry pixel brushes), gesture binding | pro | [0.4] |

### Selection and transforms

| Feature | Scope | Phase |
|---|---|---|
| Rectangular selection, move, keyboard nudge, all/deselect, copy/cut/paste, mirror | core | [0.1] |
| Floating selection layer, paste in place, paste at cursor, transform bounds, safe cancellation | essential | [0.2] |
| Lasso, polygon, elliptical marquee, magic wand with tolerance, contiguous toggle | standard | [0.3] |
| Boolean selection add/subtract/intersect, invert, feather disabled in pixel mode | standard | [0.3] |
| Resize/rotate (90°, fixed-angle nearest-neighbor), flip selection, anchor and pivot | standard | [0.3] |
| Smart bounding boxes, pixel-aware scale snapping, selection grow/shrink by cell | pro | [0.4] |

### Animation, timeline, and rapid iteration

| Feature | Scope | Phase |
|---|---|---|
| Add, duplicate, delete frames; per-frame ms duration; preview; onion skin | core | [0.1] |
| Independently editable cels for every layer/frame | core | [0.1] |
| Measured screenshot sequence importer with one shared calibration | unique workflow | [0.1] |
| Native spritesheet → individual frames, lossless sprite sheet export + durations | standard | [0.1] |
| Timeline drag-reorder, multi-select frames, copy/paste frame blocks, batch duplicate | speed | [0.2] |
| Linked/exposure cels and holds (don't duplicate 10 identical cel buffers) | speed/performance | [0.2] |
| Per-layer onion skin ranges, previous/next tint, opacity and temporal offsets | standard | [0.2] |
| Real-time alternate-pose preview, A/B compare, frame pinning and reference pose | speed | [0.2] |
| Frame tags/loops (idle/walk/run/etc.), playback direction/ping-pong, timeline zoom | standard | [0.3] |
| Cel operations: nudge linked frame regions, align with markers, copy an edit across a range | speed | [0.3] |
| Tileset and tilemap animation, collision/property metadata, animated tiles | pro | [0.4] |
| Audio track reference, loop markers, frame-accurate sound cue playback | pro | [0.4] |
| Keyframe/tween assistance *only as optional pixel-grid-safe automation* | experimental | [0.4] |

### Measurement, reference, grid reconstruction (flagship)

| Feature | Scope | Phase |
|---|---|---|
| Manual cols/rows, fractional cell pitch, x/y origin, live grid overlay | flagship | [0.1] |
| Measure pixel period from two boundary clicks N cells apart, independently on X/Y | flagship | [0.1] |
| Suggest grid offset using pixel-edge contrast for a known logical grid | flagship | [0.1] |
| Measured 41×55 Mellow calibration profile, exact eye-highlight guides | regression | [0.1] |
| Multi-frame aligned reference import, exact-cell sampling | flagship | [0.1] |
| Fully automatic pixel-pitch and grid-size **suggestion with confidence**, not silent auto-commit | flagship | [0.2] |
| Interactive drag-to-adjust grid boundaries, snapping and preview of reconstructed cells | flagship | [0.2] |
| Adaptive palette quantization/mode sampling, nearest exact color, edge halo repair | flagship | [0.2] |
| Split screenshots with uneven zoom/cropping; per-frame calibration profiles, landmark alignment | flagship | [0.3] |
| Alignment between poses using anchor pixels / bounding-box origin / ghost comparisons | flagship | [0.3] |
| Reference dock, opacity/blend/wipe/difference comparisons and audit heatmap | pro | [0.3] |
| Import and reconstruct animated GIF/APNG into editable cels and preserve timings | pro | [0.3] |
| Grid distortions/perspective and explicit per-column/per-row boundary overrides | specialized | [0.4] |

### Layers, files, export, usability

| Feature | Scope | Phase |
|---|---|---|
| Multiple independent layers, reorder, rename, lock, visibility, opacity | standard | [0.1] |
| Lossless zipped native project with per-layer per-frame PNG, schema and metadata | standard | [0.1] |
| Undo/redo, autosave recovery, dirty flag, confirmation on discard | standard baseline | [0.1] |
| PNG, GIF, spritesheet + metadata, numbered frame PNG exports | baseline | [0.1] |
| Docking panels, persistent dock layout, keyboard tool selection | standard baseline | [0.1] |
| Delta/compressed undo (performance), journal/transaction integrity, robust crash recovery | essential | [0.2] |
| Layer groups, clipping masks, reference-only layers, cel linking, drag-drop | pro | [0.3] |
| More export layouts (rows/columns), trim/padding/extrude, multi-scale packs, JSON atlas | production | [0.3] |
| APNG, WebP, Aseprite interoperability, GIF transparency/palette validation | production | [0.3] |
| Fully editable shortcuts, mouse customization, command palette and action search | productivity | [0.3] |
| Tile/sprite library, batch importer, project explorer, asset tagging | pro | [0.4] |
| Workspace presets (quick animator, paint, tilemap), multi-document tabs | pro | [0.4] |
| High-DPI/multi-monitor, pen tablets, accessible controls, localization, undo persistence | polish | [1.0] |
| Signed/portable Win64 release, updater optional, Windows file association, crash telemetry opt-in | ship | [1.0] |

## D. Interface plan

- **Center:** native canvas with fast zoom, pan, grid and reference overlays. No floating opaque UI covering the art.
- **Left toolbar:** tools, quick brush size, symmetry, paint modes. Direct click and hotkeys are equivalent.
- **Right docks:** layers, palette, live preview, reference/measurement (last planned dock). Collapsible/dockable/save positions.
- **Bottom timeline:** frame thumbnails with timing, duplication, multi-selection, layer cel sheet, onion toggles and eventual frame tags.
- **Bottom status bar:** exact logical (x,y), RGBA/index, canvas dimensions, zoom, current frame/layer, action progress.
- **Modes:** Quick Animator workspace reduces chrome but *does not hide data or remove features*; Production layout presents more controls.

## E. Event/command architecture

```text
Native Qt window / Actions / Shortcuts / Widgets
            |
   Pixel canvas & timeline input gestures
            |
   Transaction / Undo command dispatcher
            |
    Document(width, height, palette, guides)
      |               |              |
   Layers          Frames           Calibration profiles
    |               |
   Cels: independent RGBA logical-pixel arrays
            |
  Composite / Pixel render / Onion / Preview
            |
 Mellow project ZIP / PNG / GIF / Sheets / JSON
```

Current source is deliberately split into `model.py` (headless document), `calibration.py` (measurement), `canvas.py` (tool rendering), `importer.py` (calibration UI), `main.py` (desktop shell and actions), `samples.py` (reference fixture), and tests. Expensive state mutations should evolve into **transactional commands with dirty-region updates**. UI widgets should never be required to run core tests or sample generation.

The v0.2 model upgrade will use a compact cel store with references for duplicated/exposed cels, copy-on-write edits, per-tile or pixel-run delta transactions, and time/size-limited undo. Preview and grid overlays get cached QImages. Timeline thumbs become lazy; animation playback will avoid rebuilding timeline models.

## F. Fast iteration procedures, with acceptance tests

**Workflow F1 — two-frame loop:** Load 41×55 Mellow; duplicate (`Ctrl+D`), alter a single cell; set 100ms/100ms; play; edit again; export PNG sheet/GIF. **Pass**: identical original frame preserved; no 268×360 scaling artifacts; Ctrl+Z undoes the single stroke, not the frame switch.

**Workflow F2 — manual measured screenshot:** Input 268×360; set 41×55; either use Mellow preset or measure X/Y boundaries and origins. **Pass**: output exactly 41×55; eye marks at (16,19), (24,19) are one output cell each.

**Workflow F3 — batch grid-to-animation:** Import 12 screenshots with same screenshot grid and crop; calibrate first once. **Pass**: 12 individual 41×55 frames with correct alignment and durations; undo and independent editing work. Where crops differ, user must be warned, not silently warped.

**Workflow F4 — craft sprite:** Create blank 128×128, 8 layers, 24 frames; work at 8×; flip, select, use bucket, copy/paste and palettes. **Pass**: pixel edges never anti-aliased; lossless project round-trip, compositing reliable; snapshots do not corrupt layers.

**Workflow F5 — production loop:** Establish frame tags, palette indices, reference overlays, linked holds, validate game-engine sheet + JSON exports, reopen project and continue with keyboard only. **Pass**: all action shortcuts discoverable/configurable; no missing frame duration data; memory use bounded. Future milestone.

## G. Development cycle — rapid, gated, honest

**Build 0.1.0 (included):** Actual source build + native UI implementation + measured Mellow sample/projects + 14 passing headless tests. Qt/Windows interaction **not yet runtime-verified here** because package install was blocked; this is the first validation gate on a Windows machine.

**Sprint 0.1.1 — stabilization (first):** Launch on Windows 11, smoke every tool; fix Qt signal issues and file dialogs; test HiDPI and Ctrl+wheel; GIF transparent pixels; ensure 1× screenshot import doesn't bleed; accessibility of shortcuts; add GUI automated smoke tests using Qt Test. **Exit:** cold start, 20 consecutive frame duplicates, save/reopen, 60-second drawing session with zero exceptions.

**Sprint 0.2 — animation-speed release:** multi-frame range shortcuts, drag/drop frame reorder, linked holds, floating transforms, grid auto-pitch suggestions, fast origin alignment, color sample modes, undo deltas and cache. **Exit:** create and adjust a 12-frame 41×55 animation from pre-aligned references in a short uninterrupted session; 128×128/24-frame workload remains responsive on 5700U iGPU/16GB RAM without GPU dependency.

**Sprint 0.3 — professional editing:** palette/index management, richer selection set, more brushes, full onion configurations, layer groups, tags, atlas export, reference inspection, per-frame calibration. **Exit:** complete a character's idle/walk/run cycles and export directly usable frame sheets/metadata without using a second editor.

**Sprint 0.4 — tiles, advanced workflows, scaling:** tilemap editor, animation assets library, scriptable batch transforms, reference registration, optional tween assistants, expanded file interchange; profile 256×256 and multi-layer animations. **Exit:** consistent files + memory budgets; repeated operations and undo are predictable.

**1.0 release gate:** Qt UI automated tests, Windows installation and portable EXE, long-session crash tests, forward-versioned project migrations, backup/recovery, keyboard access review, file compatibility suite, performance measurement and reproducible builds. **Exit:** no open data-loss bugs or untested critical save/export paths.

Per change: **(1) smallest vertical feature → (2) unit+UI smoke tests → (3) demo scene → (4) packaged runnable ZIP → (5) regression check on measured Mellow → (6) versioned release notes**. A demo that only looks good but cannot save/reopen/animate does **not** pass.

## H. Performance & quality budgets

Target test machine: Ryzen 7 5700U with integrated graphics and 16 GB RAM. **Targets, not measured results**:

- Cursor-to-pixel response below one 60Hz frame for common 16–256px sprites, with playback not rebuilding the whole timeline.
- 60fps viewport repaint target with integer nearest-neighbor scaling; preview frame timing respects project durations.
- Undo memory bounded by a configurable memory budget, delta edits copied by tile/range, not entire animated documents.
- Reference calibration usable up to screenshot-size images without per-frame 100ms stalls, performed off UI thread if it grows heavy.
- All saves atomic to temporary files and recoverable after power failure; no data silently dropped by export.
- Project files are verified on load for sizes, version, layer ids, missing/corrupt cels, and invalid timing; future migrations explicit.

## I. Risks tracked up front

1. **Auto-grid confidence:** a feature repeating every 2 cells can masquerade as a doubled pixel period. Suggest candidate pitches, show overlay and confidence, and let the user correct it. Never auto-commit inferred native dimensions without a preview.
2. **JPG/scaled image artifacts:** halo/blur from screenshot preprocessing can hide the original palette; support center/median/mode and palette repair in imports.
3. **RAM growth:** current full snapshots are an MVP technique, not a final animation architecture. Implement deltas/linked holds before large production scenes.
4. **GIF limitations:** indexed transparency and palette reduction can degrade colors. Treat native PNG sheets and project format as sources of truth, test GIF compatibility explicitly.
5. **Keyboard conflicts:** single-letter tools must not fire while editing labels/spin boxes. GUI smoke tests must focus these edge cases.
6. **Windows packaging:** initial source ZIP runs after installing Python/requirements. EXE must be built and smoke-tested on Windows, not merely assumed from build scripts.
7. **Scope creep:** the complete feature inventory remains visible, but each increment must be a working end-to-end path, not a UI button attached to a placeholder.


## J. Sprint delivery status (2026-10-28)

The v0.2.0 source milestone implements the following from the v0.2 target:

- Multi-selection of frames with Ctrl/Shift click, batch frame duplication (independent or linked), block copy/paste, deletion, stepwise reordering and batch timings.
- Linked exposures / holds, per-layer cel linking and unlinking. Linked raster edits propagate; use Unlink to make one cel independent.
- Lossless `.mellowzip` schema **2**: stores linked source cels only once; schema **1** files remain readable.
- Automatic logical grid **suggestions** for tightly cropped screenshots with periodic pixel boundaries; candidates include estimated column/row counts, fractional pitch, alignment and evidence score. Candidates are never auto-applied; manual measurement is still first-class.
- Right-mouse grid-origin dragging in the measurement dialog, and real-interior-color sampling.
- Qt-free `python -m mellowstudio.cli` project inspection, validation and lossless PNG batch export.
- Regression tests for v1 migration, link identity through undo/resize/flip/save/load, block edit, grid detection and CLI export.
- Dirty-state warning fix for newly imported/new unsaved projects.

**Not yet implemented from the 0.2 target:** true delta-compressed undo, drag-and-drop timeline ordering, pixel-perfect brush corner cleanup, floating selection transforms, per-layer onion settings, A/B pin comparison and full robust auto pitch estimation for padded/cropped/noisy references. Those remain explicitly open; see sprint backlog.
