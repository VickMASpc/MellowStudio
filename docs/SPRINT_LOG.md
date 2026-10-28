# Mellow Studio — sprint log and release gates

**Version:** 0.2.0 source milestone  
**Date:** 2026-10-28  
**Design constraint:** native logical grid; measured screenshot pixel scaling must never become editable art resolution.

## Sprint 0.1.1 — stability (included in 0.2.0)

| Item | Evidence | Status |
|---|---|---|
| Preserve the Mellow 41×55 fixture and 1-pixel eye highlights | Original regression tests | PASS |
| Warn on abandoning a new/imported unsaved project | Code path audited and corrected | Implemented; GUI smoke pending |
| Reject invalid linked references and broken frame metadata in project files | Schema validation + tests | PASS |
| Preserve full linked state across undo/redo, cel flips and resize | `test_sprint02.py` | PASS |
| Validate GUI tool interaction on Windows | Windows machine with PySide6 required | OPEN |

## Sprint 0.2.0 — animation speed + measured reference suggestions

| Deliverable | Built? | Validation |
|---|---|---|
| Ctrl/Shift multi-select timeline | Yes | Qt code compiles; live Qt unverified |
| Independent multi-frame duplicate | Yes | Engine automated tests |
| Linked multi-frame duplicate and exposure holds | Yes | Engine automated tests |
| Per-layer Link/Unlink selected cels | Yes | Engine automated tests; GUI smoke pending |
| Frame copy/paste, delete, stepwise move, batch timing | Yes | Engine automated tests |
| Native project schema v2 link deduplication, v1 read | Yes | Archive roundtrip tests |
| Detect approximate pixel pitch and native cell count | Yes | Mellow 268×360 → 41×55 fixture |
| Candidate confidence and manual review | Yes | Algorithm and UI code; live Qt unverified |
| Right-drag overlay alignment | Yes | Code implemented; live Qt unverified |
| Nearest-real-color sampling for measured cells | Yes | Headless code |
| Qt-free batch PNG exporter | Yes | Automated CLI test |
| Delta-compressed history | No | Deferred |
| Timeline drag-and-drop ordering | No | Stepwise move currently |
| Floating selection transform | No | Deferred |

## High-priority next sprint: 0.2.1 — actual editor reliability and editing ergonomics

1. **Windows interactive smoke pass:** launch, zoom, draw, resize, file dialogs, multi-select, undo, paint linked exposures, export. Capture failures in tests immediately. No EXE readiness claim before this.
2. **Selection architecture:** floating selection on paste, commit/cancel, move preview and precise keyboard nudging without destructive repeated raster operations.
3. **Undo memory:** delta or compressed cel history; benchmark small sprite and multi-frame layered documents. Target 100+ interactive operations without a visible freeze.
4. **Timeline:** real drag reorder, scrolling/performance of thumbnails, frame index behavior with selections.
5. **Reference grid:** candidate choice UI validation on Mellow and screenshots with border padding/nonuniform scaling. Store manual adjustments in import profiles.
6. **Drawing:** pixel-perfect brush corner option, custom dither, palette controls and no smoothing anywhere.

## Native Windows smoke checklist

Run `start_windows.bat`, then:

- Open bundled Mellow. Confirm **41 × 55** logical pixels and eye landmarks `(16,19)`, `(24,19)`.
- Draw on frame 1. Duplicate independent with `Ctrl+D`; change frame 2 and verify frame 1 does **not** change.
- Duplicate linked with `Ctrl+Shift+D`; paint frame 3 and verify its linked frame changes. Select frame 3 and click Unlink; repaint, verify independent.
- Shift-select frames 1–3, press `Ctrl+Alt+C`, then `Ctrl+Alt+V` and verify the block, timings and link independence across blocks.
- Use timeline arrow buttons to move selected block. Undo and redo. Close and reopen saved v2 project. All links must be preserved.
- Open measured screenshot import. Click `Suggest native grid size + pitch`; check 41×55 appears for Mellow-style 268×360 screenshot. Use right-drag to align grid and inspect one-pixel highlights.
- Use `python -m mellowstudio.cli validate examples\mellow_hold_blink_v02.mellowzip` and batch PNG export.

## Release acceptance

Source distribution is intentionally distinct from a **Windows-verified executable**. The engine test suite passes under this environment. PySide6 is not available here, so Qt UI behavior and EXE packaging have not been runtime-verified. Do not claim otherwise. Next release gate is a real Windows/Qt smoke run.

## Sprint 0.2.1 — feature branch work (unreleased)

- Floating selection model keeps preview detached from actual cel pixels until Ctrl+Enter or another operation commits. Esc cancels; linked exposure aliases propagate on commit only.
- Reorder across timeline insertion boundaries supports multi-select/discontiguous blocks. Frame identity, duration and link aliases are retained. Engine tests cover reordering and history restoration.
- Undo/redo now uses compressed unique RGBA image buffers, respecting a 128 MiB limit and 128 actions; still snapshot-based, not region-delta history.
- Autosave captures floating previews into a separate recovery snapshot, and unsaved prompts recognize pending floats.
- Expanded test cases: `tests/test_sprint021.py`, and a Qt interaction test in `tests/test_qt_smoke.py`.
- **Release gate**: Windows CI must run the Qt interaction smoke, then real Windows interactive dragging should be checked before marking the feature stable.
