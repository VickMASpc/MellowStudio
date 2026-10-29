# Changelog


## Windows startup — native QtCore dependency repair (2026-10-29)

- Pin PySide6 6.10.2 instead of selecting a different Qt wheel on every fresh environment.
- Preflight actual QtCore, QtGui and QtWidgets imports, not only the top-level PySide6 package.
- On Qt DLL load failure, repair matching Qt packages once in the existing environment without reinstalling Python or the editor's other packages.
- Print useful missing-DLL/runtime diagnostics if the Qt repair cannot make the application start; add Windows CI checks for native Qt imports and missing-Qt diagnostics.


## Windows update fix — no more repeated reinstall (2026-10-29)

- Corrected `dev.ps1 sync` to fetch the newest `main` and replace only tracked Mellow source, preserving the existing `.venv`, ordinary local artwork, exports, ignored files, and separate branches.
- Removed the unintended `git clean -ffdx` and automatic local-branch deletion. This prevents an update from triggering a fresh Python dependency installation on every run.
- Added a Windows integration regression with a dirty working tree, unpushed commit and persistent virtual environment, including two consecutive updates.



## Windows bootstrap repair — pip-less environments (2026-10-29)

- The launcher now repairs a missing `pip` in the root `.venv` automatically with `ensurepip` before installing Mellow dependencies.
- Startup explicitly reports preparation, launch and errors; no more ambiguous blank terminal failures.
- Windows CI creates a deliberately pip-less virtual environment, tests repair, repeated startup checks and invalid interpreter detection.


## 0.2.5 — One-window studio: full layout replacement (development)

- Removed all live Qt dock widgets, floating/tabs and old saved window/dock state. No color window to close before drawing.
- True integrated workspace: fixed tool rail, a large central canvas, independent persistent Colors and Layers sidebar cards, compact Preview and optional Reference, and resizable timeline below.
- Tool-aware contextual controls and top project controls moved to inline layout instead of QToolBars.
- View menu exposes every section for instant recovery; Ctrl+Shift+0 restores the full workspace, F11 focus restores the exact previous section visibility.
- New light, high-contrast visual design and correctly colored vector icons. Sidebar scrolls; it cannot float over the canvas.
- Qt regression specifically checks simultaneous Colors/Layers, zero floating docks, canvas/sidebar nonoverlap, section recovery and focus state. Windows manual visual review remains a separate release gate.


## 0.2.4 — Artist-first studio experience (development preview)

- A real **Welcome / Start** screen with New Canvas, Open Project, bundled sample, recent native projects, optional startup toggle, and access to saved crash recovery.
- Friendlier **New Canvas** presets; no pixel-grid math necessary for everyday sprite work.
- A drawing-only left **tool rail** with local vector icons and keyboard shortcuts. Brush size, dither mix, symmetry, shape fill, and bucket region switches appear **contextually** for the active tool, not permanently alongside unrelated tools.
- A dramatically calmer **Timeline** with visible frame count, transport, duplicate/blank actions, compact duration and right-click/More operations for linked holds, block copy/paste, and reordering.
- A **Quick Export** dialog with four useful outcomes: PNG, sheet+JSON, numbered frames+JSON, and looping GIF. Previous individual export paths remain available.
- A **Focus canvas (F11)** mode, foreground/background swap (`X`), more evident palette selection, and a better project/status and save/export control bar.
- Project history, native reference registration, undo, recovery and technical pixel precision remain unchanged in their core engine.
- Coverage: 56 local headless tests, plus new Windows Qt smoke for home/presets/tool context/timeline/focus/export. User acceptance and visual review remain outstanding.

## Unreleased — Sprint 0.2.3 Reference Lab + Qt UI refinement

- Embedded losslessly decoded source reference pixels in v3 `.mellowzip` archives; v1 and v2 remain readable.
- Per-frame reference IDs persist across frame reorders, clipboard, compressed undo, recovery and save/reopen.
- Added explicit source-grid registration review with red/cyan comparison, exact fractional origins, reconstruction previews and reversible per-frame application.
- Added suggest-only edge-contrast translation diagnostics; mismatched dimensions are flagged instead of silently registered.
- Introduced a distinct Reference Lab dock and studio command header; refined Qt dark theme and action contrast.
- Fixed center-sampling tie behavior when grid boundaries have fractional shifts.
- Included a 12-frame, mixed-offset, exactly reconstructed 41×55 Mellow regression project and tests.
- Pending: landmark-assisted alignment, real scale differences, occluded/cropped edge recovery, source-level JPEG byte preservation, full visual audit heatmap, and physical Windows visual acceptance.


## Unreleased — Sprint 0.2.2 development

- Added two-color adjustable ordered-dither paint tool, shortcut D, and 4×4 Bayer pattern with exact-cell continuity.
- Cached canvas/animation composites, onion frames and thumbnails with selective linked-cel invalidation; reduced timeline alias counting from quadratic to linear.
- Added validated unique-temp atomic project writes, previous-save `.bak`, and failure-preserving Save As behavior.
- Added per-project rotating recovery archives, chooser and legacy single-slot recovery compatibility.
- Added repeatable 41×55, 128×128 and 256×256 benchmarks; updated roadmap and sprint log.
- Added file-integrity, backup, failure-injection, multi-project recovery, dither/undo and Windows Qt interaction regression tests.
- Not completed yet: delta-undo, comprehensive keyboard/high-DPI checks, physical Windows drawing and 5700U performance validation.

# Mellow Studio — changelog

## v0.2.0 — 2026-10-28

**Source milestone: linked animation + measured-grid suggestions.**

- Multiple timeline frame selection (`Ctrl/Shift`), frame-block copy/paste (`Ctrl+Alt+C/V`), stepwise frame movement (`Ctrl+Alt+Left/Right`), batch duration changes and batch deletion.
- Fast independent frame/block duplication (`Ctrl+D`), linked exposure duplication (`Ctrl+Shift+D`) and pose hold insertion (`Ctrl+Alt+H`).
- Per-layer linked cel group operations from the timeline. Edits on linked frames propagate; unlinking makes a frame independent.
- V2 project archive saves each shared cel once and reloads alias links exactly. Original schema-v1 documents are still readable.
- Automatic reference-grid **candidates** with periodicity scores, plus right-drag manual origin adjustment and actual-color interior sampling.
- CLI (`python -m mellowstudio.cli`) for project introspection, integrity check and image/spritesheet/frame-sequence batch export.
- Correctly warn for unsaved new/imported projects. History now detects guide and link changes.
- 27 headless tests pass and one Qt smoke test skips (PySide6 unavailable in execution environment).

**Not yet finished:** GUI runtime verification, EXE testing, actual compressed undo, frame drag reorder, floating selections, full palette workflows, sophisticated pixel brushes and nonuniform/noisy screenshot alignment.

## v0.1.0 — 2026-10-28

- Native PySide6 pixel canvas; layer and frame tools, timeline and preview.
- Screenshot measurement dialog, source-to-logical grid calibration, Mellow exact 41×55 fixture.
- Basic tools, undo/redo, per-frame durations, onion skin and image exports.
- Native project format schema 1; native-resolution examples and headless engine tests.

## Unreleased — Sprint 0.2.1 (development PR)

- Non-destructive floating selections: cut/lift/move, preview, keyboard nudging, explicit commit/cancel, alpha-correct clipboard paste. Linked cels only change on commit.
- Drag selected timeline frames to reorder using a model-owned insertion boundary, retaining frame object identity, timing and linked exposures.
- In-memory compressed, memory-budgeted history snapshots (unique linked cel image compressed once) replacing uncompressed full document snapshots. This is **not yet region-delta undo**.
- Autosave can include an uncommitted selection preview without modifying the live document; save commits floats; discard warns.
- Dedicated regression suite for selection cancellation, partially off-canvas clipping, undo/redo linked aliases, discontiguous timeline reorder, and bounded history.
