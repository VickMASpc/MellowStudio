# Mellow Studio — 0.2.5 integrated creative workspace

**A proper studio, not floating windows.** Colors and Layers are now permanent, separate sections beside the canvas; the timeline stays underneath; tools live in a narrow left rail. The entire old docking system and its persisted floating positions have been removed. The interface has a new light, quieter visual language.

**Paint without closing anything:** Pick a color from **Colors** on the right and draw immediately in the center. **Layers** remains visible below it. The optional Preview and Reference sections never stack over Colors, and the inspector scrolls instead of overlapping the artwork.

**Can’t find a section?** Open **View → Colors / Layers / Preview / Reference / Timeline** to show it again, or use **View → Restore default workspace** (`Ctrl+Shift+0`) to restore the whole studio. **F11** temporarily hides sections and restores their previous state. The layout splitters adjust the inspector and timeline sizes without dragging a window over the canvas.

**Update on Windows:** From the repo run `.\dev.ps1 sync`, then `.\start_windows.bat`. **Sync is intentionally destructive:** it deletes local-only edits/projects/exports and `.venv` inside the clone, then checks out the latest GitHub `main`; the launcher recreates the virtual environment. Move personal artwork outside the repository folder before syncing.

**Validation:** Qt GUI smoke and regression matrix must pass; physical Windows layout feedback is still required. [Development plan](docs/DEVELOPMENT_PLAN.md) · [Sprint log](docs/SPRINT_LOG.md).

---

## Previous release notes

**Make something move.** A professional studio should feel fast, coherent and pleasant, not like a technical settings console. A new Welcome screen, contextual drawing controls, approachable timeline and one export dialog now put everyday creative work first.

**Start on Windows:** Run `./dev.ps1 sync` to wipe-refresh your clone from GitHub's latest `main`, then run `start_windows.bat`. Sync deletes `.venv`; the launcher recreates it. For the first upgrade from an old sync, see the one-time Git commands below. The Welcome screen offers New Canvas, Open, recently opened projects, the Mellow sample and available recovery. Reopen it anytime with Ctrl+Shift+H.

**Paint:** Tool-only vector icon rail (B pencil, D dither, E erase, F fill, I sample). Size, dither mix, symmetry and shape/fill switches appear contextually. X swaps foreground/secondary, and palette swatches make the current paint color visible.

**Animate:** The timeline keeps Play, Duplicate, Blank, current frame and duration visible. More or right-click exposes holds, linking/unlinking, frame blocks and reordering. Ctrl+D duplicates; Space plays.

**Focus and export:** F11 hides/restores dock panels to free painting room. Ctrl+E opens a single export dialog for PNG, GIF, sprite sheet+timing JSON or numbered PNGs+timing JSON. Reference Lab remains available via Ctrl+Alt+R.

**Validation:** 56 headless tests pass locally; Windows Qt smoke and real Windows artist acceptance remain separate. See [Development Plan](docs/DEVELOPMENT_PLAN.md) and [Sprint Log](docs/SPRINT_LOG.md).

---

## Previous milestones

## Sprint 0.2.3 — Reference Lab + studio UI refresh

**Flagship workflow:** import a measured screenshot sequence, inspect detected frame offsets,
correct the fractional sampling origin per frame and keep the complete original source pixels
embedded in the native project. A different pose is **not** automatically a different crop.

- **Reference Lab (`Ctrl+Alt+R`)**: source list, offset suggestions (diagnostic, not auto-applied),
  red/cyan overlay comparison, precise X/Y origin controls, exact logical-pixel preview,
  per-frame reconstruct, and explicit Apply/Cancel. Reopen and edit these settings after saving.
- **Native archive schema 3**: `.mellowzip` retains source PNG pixels, filenames, original sizes,
  registration notes, sampling mode, and fractional calibration per frame. Old v1/v2 projects still open.
  Original pixel data is retained; original JPEG file bytes/metadata are **not** retained.
- **12-frame fixture:** File → Open `examples/reference_lab_12frame_demo.mellowzip`, then
  `Ctrl+Alt+R`. All 12 268×360 sources have intentionally different offsets, but reconstruct
  to the same **41×55** logical Mellow. Try changing a calibration, reconstruct, cancel or undo,
  save/reopen and inspect the retained source.
- **More intentional native UI:** reorganized studio command bar, purpose-built Reference dock,
  clearer highlighted actions, better dark panel contrast and a dedicated Reference Lab workspace.
- **Regression improvements:** fixed exact-center sampling at half-pixel boundaries; source
  reference identities survive frame reorders, linked exposures, history, and saves.
- **Command line:** `python -m mellowstudio.cli info examples/reference_lab_12frame_demo.mellowzip`
  includes the complete embedded source and calibration inventory.

**Limitations:** Translation suggestions are heuristic and require review. Different-size sources
are flagged for manual alignment; scale changes, perspective and landmark-assisted registration
are still planned, not solved. The overlay is red/cyan difference, not a full inspection heatmap.
Manual Windows acceptance and real 5700U performance remain separate gates.

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

## Repair or update your Git checkout (Windows)

There is **one canonical branch**, `main`. After a PR is merged, GitHub automatically removes its obsolete remote feature branch only when the exact branch head matches the merged PR. No unmerged work is deleted. You do not need to manage sprint branches.

From an up-to-date checkout, run `./dev.ps1 sync` (PowerShell) to safely fetch/prune deleted remote branches and fast-forward `main`. It preserves the shared `.venv`, all local edits, independent branches, and commits. If your copy predates the `sync` command, bootstrap with `git fetch --prune origin`, `git switch main`, then `git pull --ff-only origin main` once. Future runs use the single `./dev.ps1 sync` command.

The updater **never resets or stashes your work**. If Git reports local changes, a different remote, an authentication/network error, or a diverged `main`, it stops and explains why. The GitHub cleanup cannot reach or modify your PC automatically.

## GitHub development workflow

This repository is the **single source of truth** from v0.2.0 forward. Do not unpack new versions into new folders. Make small feature branches, run tests, open PRs, and merge once green. Avoid committing generated `.venv`, caches, packaging output, or autosaves.

On Windows, `.\dev.ps1 run` launches the editor, `.\dev.ps1 test` runs the tests, `.\dev.ps1 build` makes an EXE and `.\dev.ps1 cli ...` accesses headless batch commands. The normal commands reuse **one root `.venv`**; `sync` intentionally wipes it. Direct launch `start_windows.bat` works too. To force-recreate that one environment, delete `.venv` once and run setup again.

CI runs Python engine tests on Ubuntu and GUI smoke tests on Windows; the merged 0.2.1 baseline passed. **For every code PR, update both `docs/DEVELOPMENT_PLAN.md` and `docs/SPRINT_LOG.md`** or the new sprint-documentation CI gate will fail. See [`docs/REPOSITORY_WORKFLOW.md`](docs/REPOSITORY_WORKFLOW.md). Remaining targets: [extended Reference Lab registration / Issue #7](https://github.com/VickMASpc/MellowStudio/issues/7) and [reliability / Issue #3](https://github.com/VickMASpc/MellowStudio/issues/3).
