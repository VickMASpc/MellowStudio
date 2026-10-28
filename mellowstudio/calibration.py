"""Reference-to-logical-pixel measurement and snapping engine.

Works with fractional screen-space pixels, preserving the one-cell identity of
features. Avoid treating image resolution as sprite resolution.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
import numpy as np
from PIL import Image


@dataclass
class GridCalibration:
    cols: int
    rows: int
    pitch_x: float
    pitch_y: float
    origin_x: float = 0.0
    origin_y: float = 0.0

    def validate(self) -> None:
        if not (1 <= self.cols <= 2048 and 1 <= self.rows <= 2048):
            raise ValueError('Logical grid must be between 1 and 2048 in each direction.')
        if not (0.5 <= self.pitch_x <= 2000 and 0.5 <= self.pitch_y <= 2000):
            raise ValueError('Measured cell sizes must be between 0.5 and 2000 display pixels.')

    def bounds_x(self) -> list[int]:
        return [round(self.origin_x + self.pitch_x * x) for x in range(self.cols + 1)]

    def bounds_y(self) -> list[int]:
        return [round(self.origin_y + self.pitch_y * y) for y in range(self.rows + 1)]

    def cell_at(self, px: float, py: float) -> tuple[int, int]:
        return (math.floor((px - self.origin_x) / self.pitch_x),
                math.floor((py - self.origin_y) / self.pitch_y))

    def extract(self, image: Image.Image, mode: str = 'median') -> Image.Image:
        """Collapse each measured screenshot cell to exactly one logical pixel.

        Median interior samples resist JPEG halos / scaling artifacts better than
        nearest-neighbor. Nearest-center is available for exact source samples.
        """
        self.validate()
        src = np.asarray(image.convert('RGBA'))
        h, w = src.shape[:2]
        out = np.zeros((self.rows, self.cols, 4), dtype=np.uint8)
        bx, by = self.bounds_x(), self.bounds_y()
        for y in range(self.rows):
            y0, y1 = by[y], by[y+1]
            for x in range(self.cols):
                x0, x1 = bx[x], bx[x+1]
                # Sample only the interior 50%; borders can be antialiased.
                cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                if mode == 'center':
                    ix, iy = math.floor(cx), math.floor(cy)
                    if 0 <= ix < w and 0 <= iy < h:
                        out[y, x] = src[iy, ix]
                elif mode in ('median','dominant'):
                    # For native 1–2 screen-pixel cells, never blend adjacent logical pixels.
                    # On enlarged screenshots, reject uncertain border antialiasing.
                    inset_x = 0 if x1-x0 <= 2 else .25*(x1-x0)
                    inset_y = 0 if y1-y0 <= 2 else .25*(y1-y0)
                    ix0 = max(0, min(w, math.floor(x0 + inset_x)))
                    ix1 = max(0, min(w, math.ceil(x1 - inset_x)))
                    iy0 = max(0, min(h, math.floor(y0 + inset_y)))
                    iy1 = max(0, min(h, math.ceil(y1 - inset_y)))
                    block = src[iy0:iy1, ix0:ix1]
                    if block.size:
                        pixels = block.reshape(-1, 4)
                        median = np.median(pixels, axis=0)
                        if mode == 'dominant':
                            # Preserve an *actual* interior sample, not a blended halo color.
                            distances = np.sum((pixels.astype(np.float64) - median) ** 2, axis=1)
                            out[y, x] = pixels[np.argmin(distances)]
                        else:
                            out[y, x] = median.astype(np.uint8)
                else:
                    raise ValueError(f'Unsupported sampling mode: {mode}')
        return Image.fromarray(out, 'RGBA')


def default_calibration(image: Image.Image, cols: int, rows: int) -> GridCalibration:
    return GridCalibration(cols, rows, image.width / cols, image.height / rows)


def align_to_edges(image: Image.Image, cfg: GridCalibration) -> GridCalibration:
    """Estimate grid origin with screenshot edge contrast while keeping sizes fixed.

    Dimensions are supplied by the artist; automation suggests alignment instead
    of guessing native pixel counts and silently destroying details.
    """
    array = np.asarray(image.convert('RGB'), dtype=np.int16)
    diff_x = np.abs(np.diff(array, axis=1)).mean(axis=(0, 2))
    diff_y = np.abs(np.diff(array, axis=0)).mean(axis=(1, 2))

    def best_offset(energy: np.ndarray, pitch: float, count: int, previous: float) -> float:
        offsets = np.linspace(previous - pitch * .49, previous + pitch * .49, 81)
        best, best_score = previous, -1.0
        for offset in offsets:
            # Boundary x corresponds to color jump between x-1 and x.
            coords = [round(offset + i*pitch) - 1 for i in range(1, count)]
            coords = [v for v in coords if 0 <= v < len(energy)]
            if not coords:
                continue
            score = float(np.mean(energy[coords]))
            if score > best_score:
                best, best_score = float(offset), score
        return best

    return GridCalibration(cfg.cols, cfg.rows, cfg.pitch_x, cfg.pitch_y,
        best_offset(diff_x, cfg.pitch_x, cfg.cols, cfg.origin_x),
        best_offset(diff_y, cfg.pitch_y, cfg.rows, cfg.origin_y))


MELLOW_EXACT = GridCalibration(41, 55, 6.58830, 6.545454545, -0.9093, 0.0)

@dataclass(frozen=True)
class GridSuggestion:
    """Plausible screenshot grid, never automatically applied to source artwork."""
    calibration: GridCalibration
    confidence: float
    reason: str = 'Periodic color-boundary evidence; assumes tightly cropped screenshot'


def _pitch_candidates(energy: np.ndarray, max_pitch: float, count: int = 3) -> list[tuple[float, float]]:
    """Phase-concentration of cross-row/column color transitions.

    A repeated fractional pixel pitch creates a strong complex phase at grid
    boundaries. This handles alternating 6/7-pixel screenshot columns without
    requiring the user to preselect 41 columns or 55 rows.
    """
    highest = float(np.percentile(energy, 95))
    weights = np.maximum(0.0, energy - highest * 0.08).astype(np.float64)
    if weights.sum() <= 1e-5 or max_pitch < 2.0:
        return []
    positions = np.arange(1, len(weights) + 1, dtype=np.float64)
    pitches = np.arange(2.0, min(64.0, max_pitch) + 0.025, 0.025)
    scores = np.empty(len(pitches), dtype=np.float64)
    for begin in range(0, len(pitches), 80):
        grid = pitches[begin:begin+80]
        phases = np.exp(2j * np.pi * positions[None, :] / grid[:, None])
        scores[begin:begin+80] = np.abs(phases @ weights) / weights.sum()
    peaks = [i for i in range(1,len(scores)-1)
             if scores[i] >= scores[i-1] and scores[i] >= scores[i+1]]
    peaks.sort(key=lambda i: (scores[i], pitches[i]), reverse=True)
    result = []
    for i in peaks:
        pitch = float(pitches[i])
        confidence = float(scores[i])
        if confidence < 0.4:
            break
        if any(abs(pitch - prev[0]) < 0.2 for prev in result):
            continue
        result.append((pitch, confidence))
        if len(result) >= count:
            break
    return result


def suggest_grids(image: Image.Image, maximum: int = 5) -> list[GridSuggestion]:
    """Suggest logical grids for tightly cropped scaled pixel art.

    Scores are periodicity measurements (0–1), NOT probabilistic guarantees.
    Never changes the image or applies a guess without user confirmation.
    Photos/noisy images may have no acceptable candidates.
    """
    if image.width < 8 or image.height < 8:
        return []
    src = np.asarray(image.convert('RGB'), dtype=np.int16)
    edges_x = np.abs(np.diff(src, axis=1)).mean(axis=(0, 2))
    edges_y = np.abs(np.diff(src, axis=0)).mean(axis=(1, 2))
    xs = _pitch_candidates(edges_x, image.width / 2)
    ys = _pitch_candidates(edges_y, image.height / 2)
    candidates = []
    for px, xc in xs:
        for py, yc in ys:
            cols = round(image.width / px)
            rows = round(image.height / py)
            if not (1 <= cols <= 2048 and 1 <= rows <= 2048):
                continue
            cfg = GridCalibration(cols, rows, px, py)
            cfg = align_to_edges(image, cfg)
            candidates.append(GridSuggestion(cfg, min(xc, yc)))
    candidates.sort(key=lambda x: x.confidence, reverse=True)
    return candidates[:maximum]
