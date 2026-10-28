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
