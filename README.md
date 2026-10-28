# Mellow Studio — v0.2.2 development build

## Sprint 0.2.2 — real additions

- **New 2-color Bayer dither brush (`D`)**: paints foreground and secondary color with exact-pixel 4×4 ordered dithering, deterministic across separate strokes and linked cels. Adjust **Mix** (0–16) on the drawing toolbar; brush size and symmetry work normally.
- **Fast frame painting and playback:** cached frame QImages and preview thumbnails; edits invalidate only affected linked frames, and frame switches reuse cached composites. Refreshing the timeline no longer scans every linked frame against every other frame.
- **Safer files:** every `.mellowzip` write is validated for ZIP integrity and project semantics before atomically replacing an existing file. A prior saved file is retained as `<project>.mellowzip.bak`. Failed Save As keeps the previous filename and unsaved state.
- **Project-specific recovery:** separate rotating snapshots (four per project) with timestamps, original filenames and a recovery chooser in **File → Recover autosaved project…**. Unsaved sessions don't collide; previous 0.2.1 single-slot recovery remains readable.
- **Regression and benchmarks:** deterministic save-failure/corruption/rotation/dither tests and repeatable `python scripts/benchmark.py` on representative sprite workloads. Read `docs/SPRINT_LOG.md` for measured results and remaining Windows manual tests.

**Status:** development sprint implementation, not a certified production release. The 0.2.2 acceptance gate also requires physical Windows drawing, file/recovery and performance validation. The canonical plan and log are updated in every code PR.


> **v0.2.0 source milestone (2026-10-28)** — animation timeline multi-select, linked exposures/holds, frame-block copy/paste and stepwise reordering, automatic pixel-grid size suggestions, manual right-drag alignment, version-2 project format and a headless batch exporter. See [`docs/SPRINT_LOG.md`](docs/SPRINT_LOG.md) for what is verified versus still pending.

### Sprint 0.2.1 — merged baseline (PR #2)

- **Float, then commit:** drag an existing marquee selection using the Move tool (`V`), or `Ctrl+V` to stage pasted pixels as a floating fragment. The cel is unchanged during movement.
- Position precisely with arrow keys (`Shift` = 10 logical cells). `Ctrl+Enter` commits one undoable action. `Esc` cancels the float and restores the untouched cel. Switching to a painting tool or another frame commits the pending pixels.
- **Timeline drag reordering:** Ctrl/Shift-select one or more thumbnails, then drag to a new insertion point. Underlying frame objects, timing and linked exposures move together.
- **Memory budget:** undo/redo now stores compressed cell buffers and deduplicates linked exposures; history is bounded to 128 commands or 128 MiB, whichever applies first. This is compressed snapshot history, not delta history.

### New shortcuts in 0.2

- `Ctrl+D` — duplicate selected frames, independent cels.
- `Ctrl+Shift+D` — duplicate selected frames as linked exposures. Painting linked pixels changes every linked exposure until unlinked.
- `Ctrl+Alt+H` — insert multiple exposure holds of the active pose.
- `Ctrl/Shift-click` in timeline — select multiple frames; `Ctrl+Alt+C/V` — copy/paste selected blocks.
- `Ctrl+Alt+Left/Right` — move selected frames one step; timeline **Link/Unlink** applies to the active layer.
- Duration control applies to the selected frames.
- Measured reference import: **Suggest native grid size + pitch** gives candidate grids, not an unconditional guess; right-drag overlay to adjust grid origin.

### Headless batch tools (no Qt necessary)

From the project folder, after installing `requirements.txt` or at least `Pillow` and `numpy`:

```powershell
python -m mellowstudio.cli info examples/mellow_hold_blink_v02.mellowzip
python -m mellowstudio.cli validate examples/mellow_hold_blink_v02.mellowzip
python -m mellowstudio.cli export examples/mellow_hold_blink_v02.mellowzip --format sheet --out sheet.png
python -m mellowstudio.cli export examples/mellow_hold_blink_v02.mellowzip --format frames --out exported_frames
```


**A native Python + Qt pixel-art and animation workstation for Windows.**

The editor is built around the corrected **Mellow 41×55 logical-pixel grid**, not the original 268×360 display screenshot. A measured pixel is a true editable cell. The two eye highlights occur at **(16,19)** and **(24,19)**. The full measured original, grid coordinates, and sample projects are included under `examples/`.

## Start on Windows

1. Clone this repository once: `git clone https://github.com/VickMASpc/MellowStudio.git`.
2. Install **Python 3.10+** (64-bit) with the Python launcher.
3. Run **`start_windows.bat`** from the repository root. It reuses one `.venv` in that folder for every sprint. No extraction or per-sprint environments.
4. Update by running `git pull`; run and tests reuse the existing environment.

Command-line alternative (PowerShell or CMD, from this folder):

```bat
py -3 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python run.py
```

To build a portable Windows application folder containing `MellowStudio.exe`, run `scripts\build_windows.bat` on **Windows**. This is a **build script**, not a prebuilt/tested EXE. For a normal developer setup, install editable package with `pip install -e .[dev]`.

## Native editor: implemented in v0.1

- **Pixel-exact editing:** integer zoom, checker transparency, logical-cell grid, actual cell coordinates, native-resolution output, Mellow eye-highlight guides.
- **Drawing:** pencil, eraser, bucket (contiguous / all matching pixels), color sampler, 1–32px brushes, line, outline/solid rectangle, outline/solid ellipse, horizontal/vertical symmetry.
- **Selections:** rectangular marquee, non-destructive floating move/paste preview with explicit commit/cancel, keyboard arrow nudging in logical pixels, copy/cut/paste (including system clipboard), select all, deselect.
- **Animation:** independently editable full frames, duplicate frame, blank frame, delete frame, frame durations, frame thumbnails, onion skin, looping preview, previous/next shortcuts.
- **Layers:** create, delete, rename, reorder, lock, show/hide, opacity, independent cels per layer *and* frame.
- **Measuring/import:** interactive source overlay, manual columns/rows, fractional cell pitch, grid origin, two-click boundary measurement, automatic **edge alignment** for an already-specified logical grid, Mellow exact preset, anti-halo median interior sampling or center sampling.
- **Production intake:** import a single measured reference, a multi-image reference sequence using a shared calibration, a native-resolution PNG, or a spritesheet sliced by exact native frame width/height.
- **Projects:** native `.mellowzip` saves all layers, frames, timing, palette, and grid metadata without losing pixel detail; bounded undo/redo; periodic local recovery snapshots; unsaved-work warnings; saved dock layout.
- **Export:** current frame as true-resolution PNG, animation spritesheet PNG + JSON timings, animated GIF, separate numbered PNG frames.
- **Windows UI:** Qt widgets (not a web view), dockable layers/palette/timeline/preview, keyboard shortcuts, mouse wheel zoom, middle-button pan, true native file dialogs, dark studio styling.

### Quick workflow

**Start with Mellow:** The application opens the 41×55 original. Select pencil (`B`), draw a pixel, then `Ctrl+D` to duplicate the whole frame and edit only what moves. Use `Shift+O` for onion skin and `Space` to play. Change individual frame duration directly in the timeline. Save with `Ctrl+S` and export a GIF or sheet from File.

**Reconstruct a screenshot:** File → Import measured screenshot. Specify the *logical* grid size (Mellow is 41×55), click **Fit pitch** and **Auto-align**, or enter measured pitch/origin exactly. The blue overlay must follow one true sprite pixel per cell. Use **Measure X/Y** with two grid-boundary clicks and an exact number of cells between them. Inspect then import. For Mellow's original reference, use the **Mellow preset**.

**Make animation from many screenshots:** File → **Import measured image sequence**. Select similarly scaled frames. Calibrate the first and apply the same mapping to all. Every input becomes a separate editable **native-resolution** frame. If frames have different screen-space scaling/alignment, import individually for now rather than applying an incorrect shared grid.

**Convert existing sheets:** File → **Import spritesheet as frames**. Enter each animation frame's real pixel width and height. Frame tiles become cels. Partial columns/rows require explicit approval to discard incomplete edges.

## Keyboard cheatsheet

| Action | Keys |
|---|---|
| Pencil / eraser / bucket / eyedropper | `B` / `E` / `F` / `I` |
| Line / rectangle / ellipse | `L` / `R` / `O` |
| Marquee / move / pan | `M` / `V` / `H` |
| Brush size | `[` / `]` |
| Toggle pixel grid / onion skin | `G` / `Shift+O` |
| Duplicate frame / add blank frame | `Ctrl+D` / `Alt+N` |
| Previous / next frame | `Alt+Left` / `Alt+Right` |
| Play or pause animation | `Space` |
| Undo / redo | `Ctrl+Z` / `Ctrl+Y` |
| Copy / cut / paste | `Ctrl+C` / `Ctrl+X` / `Ctrl+V` |
| Select all / deselect | `Ctrl+A` / `Ctrl+Shift+A` or `Esc` |
| Nudge selected pixels | Arrows; `Shift+Arrows` = 10 cells |
| Save / open / new | `Ctrl+S` / `Ctrl+O` / `Ctrl+N` |
| Calibrated image import | `Ctrl+I` |
| Frame PNG export | `Ctrl+E` |
| Zoom / pan | `Ctrl+wheel` / middle-drag |

## Quality and current boundaries

**Original baseline:** 14 headless tests passed for exact Mellow cell data, screenshot-to-grid reconstruction, native-resolution sampling, frame independence, layer compositing, alpha/shape/fill/mirror/symmetry, selection movement, multi-frame project round-trip, and undo/redo. Python bytecode compilation passed.

**Current validation:** Windows and Linux CI passed the tests for the merged 0.2.1 branch, including targeted Windows Qt smoke tests. The user reported a working Windows launch/test. This does **not** verify all interactive workflows, a long-running session, reference registration, or a packaged EXE. Those remain explicit roadmap gates.

The v0.2.1 history engine uses deduplicated compressed whole-document snapshots (128 actions / 128 MiB defaults), **not delta undo**. Compositor/thumbnails still require targeted caching. Large-project performance and GIF transparency need testing; lossless PNG sheets and `.mellowzip` remain authoritative.

Full professional feature matrix, architecture, workflow goals, and fast development cycle: **`docs/DEVELOPMENT_PLAN.md`**.

## GitHub development workflow

This repository is the **single source of truth** from v0.2.0 forward. Do not unpack new versions into new folders. Make small feature branches, run tests, open PRs, and merge once green. Avoid committing generated `.venv`, caches, packaging output, or autosaves.

On Windows, `.\dev.ps1 run` launches the editor, `.\dev.ps1 test` runs the tests, `.\dev.ps1 build` makes an EXE and `.\dev.ps1 cli ...` accesses headless batch commands. All commands reuse **one root `.venv`**. Direct launch `start_windows.bat` works too. To force-recreate that one environment, delete `.venv` once and run setup again.

CI runs Python engine tests on Ubuntu and GUI smoke tests on Windows; the merged 0.2.1 baseline passed. **For every code PR, update both `docs/DEVELOPMENT_PLAN.md` and `docs/SPRINT_LOG.md`** or the new sprint-documentation CI gate will fail. See [`docs/REPOSITORY_WORKFLOW.md`](docs/REPOSITORY_WORKFLOW.md). Next milestone: [Sprint 0.2.2 / Issue #3](https://github.com/VickMASpc/MellowStudio/issues/3).
