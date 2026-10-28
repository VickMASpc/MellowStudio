"""Persistent source-image provenance and explicit alignment suggestions.

Reference images are never resized or overwritten. Registration is an offered
translation, not an instruction to move actual animation pose pixels. Artists
review the candidate before applying it to the sampling calibration.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO
import math
from uuid import uuid4

import numpy as np
from PIL import Image

from .calibration import GridCalibration

MAX_REFERENCE_PIXELS = 16_000_000
MAX_SOURCE_PNG_BYTES = 48 * 1024 * 1024


@dataclass
class ReferenceAsset:
    id: str
    name: str
    png: bytes = field(repr=False)
    calibration: dict = field(default_factory=dict)
    sampling: str = 'median'
    source_size: tuple[int, int] = (0, 0)
    registration: dict = field(default_factory=dict)

    @classmethod
    def from_image(cls, image: Image.Image, name: str, cfg: GridCalibration,
                   sampling: str = 'median', registration: dict | None = None):
        if image.width * image.height > MAX_REFERENCE_PIXELS:
            raise ValueError('Reference exceeds the supported 16 megapixel source limit.')
        cfg.validate()
        if sampling not in ('center', 'median', 'dominant'):
            raise ValueError('Unknown source sampling mode.')
        buffer = BytesIO()
        image.convert('RGBA').save(buffer, format='PNG')
        payload = buffer.getvalue()
        if len(payload) > MAX_SOURCE_PNG_BYTES:
            raise ValueError('Source reference exceeds the 48 MiB encoded limit.')
        return cls(uuid4().hex, str(name), payload, calibration_dict(cfg), sampling,
                   image.size, dict(registration or {}))

    def image(self) -> Image.Image:
        with Image.open(BytesIO(self.png)) as f:
            if f.size != tuple(self.source_size) or f.width*f.height > MAX_REFERENCE_PIXELS:
                raise ValueError('Reference dimensions are invalid.')
            return f.convert('RGBA')

    def config(self) -> GridCalibration:
        c = GridCalibration(**self.calibration)
        c.validate()
        return c

    def extract(self) -> Image.Image:
        return self.config().extract(self.image(), self.sampling)

    def copy(self):
        return ReferenceAsset(self.id, self.name, self.png, dict(self.calibration),
                              self.sampling, tuple(self.source_size), dict(self.registration))

    def info(self) -> dict:
        return {'id': self.id, 'name': self.name, 'calibration': self.calibration,
                'sampling': self.sampling, 'source_size': list(self.source_size),
                'registration': self.registration}

    @classmethod
    def from_info(cls, data: dict, png: bytes):
        if not isinstance(data.get('id'), str) or len(data['id']) != 32 or not all(ch in '0123456789abcdef' for ch in data['id']):
            raise ValueError('Invalid reference asset identifier.')
        if len(png) > MAX_SOURCE_PNG_BYTES:
            raise ValueError('Embedded reference exceeds file size limit.')
        obj = cls(data['id'], str(data['name']), png, dict(data['calibration']),
                  data['sampling'], tuple(data['source_size']), dict(data.get('registration', {})))
        obj.config()
        if obj.sampling not in ('center','median','dominant'):
            raise ValueError('Unknown reference sampling mode.')
        obj.image() # verify PNG decodes and dimensions actually agree
        return obj


def calibration_dict(c: GridCalibration) -> dict:
    return {'cols': c.cols, 'rows': c.rows, 'pitch_x': c.pitch_x,
            'pitch_y': c.pitch_y, 'origin_x': c.origin_x, 'origin_y': c.origin_y}


@dataclass(frozen=True)
class RegistrationSuggestion:
    dx: int
    dy: int
    confidence: float
    improvement: float
    status: str


def _edge_signature(image: Image.Image, max_side: int = 1100) -> tuple[np.ndarray, float]:
    """Return normalized contrast edges, optionally decimated for bounded work."""
    if max(image.size) > max_side:
        scale = math.ceil(max(image.size) / max_side)
        image = image.resize(((image.width + scale - 1)//scale,
                              (image.height + scale - 1)//scale), Image.Resampling.BOX)
    else:
        scale = 1
    rgb = np.asarray(image.convert('RGB'), np.float32)
    gray = .299*rgb[:,:,0] + .587*rgb[:,:,1] + .114*rgb[:,:,2]
    edge = np.zeros_like(gray)
    edge[:,1:] += np.abs(gray[:,1:] - gray[:,:-1])
    edge[1:,:] += np.abs(gray[1:,:] - gray[:-1,:])
    return edge, float(scale)


def suggest_translation(base: Image.Image, other: Image.Image,
                        max_shift: int = 12) -> RegistrationSuggestion:
    """Propose screen-space translation of OTHER relative to BASE.

    The result means 'other grid origin = base origin + (dx,dy)'. Exact dimensions
    are NOT taken as evidence that the images are aligned. Confidence is a
    bounded heuristic, not a probabilistic accuracy estimate. Never auto-apply.
    """
    if max_shift < 0 or max_shift > 128:
        raise ValueError('Maximum translation must be between 0 and 128 pixels.')
    a, scale_a = _edge_signature(base)
    b, scale_b = _edge_signature(other)
    if scale_a != scale_b:
        # Different source sizes/decimation cannot be compared directly.
        return RegistrationSuggestion(0, 0, 0, 0, 'different source dimensions; manual registration required')
    # Preserve a modest reference overlap. Different source dimensions are
    # explicitly flagged even when their first overlap happens to match.
    if a.shape != b.shape:
        return RegistrationSuggestion(0, 0, 0, 0, 'different source dimensions; manual registration required')
    h, w = a.shape
    shift = min(max_shift // int(scale_a), (min(h,w)-1)//4)
    if shift < 0 or max(float(a.max()), float(b.max())) < 5:
        return RegistrationSuggestion(0,0,0,0,'insufficient contrast; inspect manually')
    # Base at (x,y) matches Other at (x+dx,y+dy). Compare actual overlapping
    # source windows; no wrapping and no correlation at fabricated borders.
    aa = a/(max(float(a.max()),1))
    bb = b/(max(float(b.max()),1))
    scores = []
    for dy in range(-shift, shift+1):
        y0=max(0,-dy); y1=min(h,h-dy)
        for dx in range(-shift,shift+1):
            x0=max(0,-dx);x1=min(w,w-dx)
            x=aa[y0:y1,x0:x1]
            y=bb[y0+dy:y1+dy,x0+dx:x1+dx]
            # Edge-space cosine similarity, bounded by overlap support; improves
            # robustness against palette changes and partial pose edits.
            denom=float(np.linalg.norm(x)*np.linalg.norm(y))
            similarity=float(np.sum(x*y)/denom) if denom > 1e-8 else 0
            coverage=(x.shape[0]*x.shape[1])/(h*w)
            scores.append((similarity*coverage, dx, dy))
    scores.sort(reverse=True)
    best=scores[0]
    zero=next(score for score,dx,dy in scores if dx==0 and dy==0)
    # Ambiguity across offsets is important: repeated tile patterns can correlate
    # at several shifts. Compare non-neighbor offsets to avoid broad peaks.
    alternatives=[score for score,dx,dy in scores if abs(dx-best[1])>=2 or abs(dy-best[2])>=2]
    competitor=max(alternatives, default=0)
    improvement=max(0.,best[0]-zero)
    confidence=max(0.,min(1.,(best[0]-competitor)*3+improvement*1.5))
    if best[1]==0 and best[2]==0:
        status='no offset suggested; inspect poses and crops'
    elif confidence < .14 or best[0] < .28:
        status='ambiguous alignment; inspect manually'
    else:
        status='candidate offset; explicit review required'
    return RegistrationSuggestion(best[1]*int(scale_a),best[2]*int(scale_a),
                                  round(confidence,3),round(improvement,3),status)


def reference_difference(base: Image.Image, other: Image.Image, dx: int, dy: int) -> Image.Image:
    """Red/green comparison for inspection; offsets never modify the originals."""
    # Base is represented red, translated other is represented cyan.
    a=base.convert('RGBA')
    b=other.convert('RGBA')
    if a.size!=b.size:
        w,h=max(a.width,b.width),max(a.height,b.height)
        back=Image.new('RGBA',(w,h),(0,0,0,255))
        back.paste(a,(0,0));a=back
    shifted=Image.new('RGBA',a.size,(0,0,0,255))
    shifted.paste(b,(-int(dx),-int(dy)))
    lhs=np.asarray(a.convert('RGB'),np.uint8).astype(np.float32)
    rhs=np.asarray(shifted.convert('RGB'),np.uint8).astype(np.float32)
    luminance_a=(lhs[:,:,0]*.299+lhs[:,:,1]*.587+lhs[:,:,2]*.114).astype('uint8')
    luminance_b=(rhs[:,:,0]*.299+rhs[:,:,1]*.587+rhs[:,:,2]*.114).astype('uint8')
    result=np.stack((luminance_a, luminance_b, luminance_b, np.full_like(luminance_a,255)),axis=2)
    return Image.fromarray(result,'RGBA')
