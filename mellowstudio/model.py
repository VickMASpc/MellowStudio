"""Headless document/animation engine for Mellow Studio.

The logical pixel is the fundamental editable unit. A 268x360 screenshot of a
41x55 sprite is NOT a 268x360 sprite. The GUI and importers always edit cells.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO
import json
import zlib
from struct import pack, unpack_from
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile, ZIP_DEFLATED

from PIL import Image, ImageDraw

RGBA = tuple[int, int, int, int]
TRANSPARENT: RGBA = (0, 0, 0, 0)


def blank(w: int, h: int) -> Image.Image:
    return Image.new('RGBA', (w, h), TRANSPARENT)


def validate_size(w: int, h: int) -> None:
    if not (1 <= w <= 2048 and 1 <= h <= 2048):
        raise ValueError('Canvas dimensions must each be between 1 and 2048.')


@dataclass
class Layer:
    id: str = field(default_factory=lambda: uuid4().hex)
    name: str = 'Artwork'
    visible: bool = True
    locked: bool = False
    opacity: int = 255


@dataclass
class Frame:
    duration_ms: int = 100
    cels: dict[str, Image.Image] = field(default_factory=dict)

    def copy(self, memo: dict[int, Image.Image] | None = None) -> Frame:
        """Deep-copy pixels; an optional shared memo preserves linked exposures."""
        if memo is None:
            memo = {}
        cels = {}
        for key, im in self.cels.items():
            if id(im) not in memo:
                memo[id(im)] = im.copy()
            cels[key] = memo[id(im)]
        return Frame(self.duration_ms, cels)


@dataclass
class Document:
    width: int = 32
    height: int = 32
    name: str = 'Untitled'
    layers: list[Layer] = field(default_factory=lambda: [Layer()])
    frames: list[Frame] = field(default_factory=lambda: [Frame()])
    active_frame: int = 0
    active_layer: str = ''
    palette: list[str] = field(default_factory=lambda: [
        '#171c28', '#f5f5f5', '#a83232', '#f32f37', '#3c3d70', '#5c6de3',
        '#70d8f2', '#98b0be', '#d0d0d0', '#d89f65', '#f5d78a', '#58b99d',
        '#417d6f', '#765e9c', '#be6eb6', '#dbb1cd',
    ])
    guides: list[dict] = field(default_factory=list)

    def __post_init__(self) -> None:
        validate_size(self.width, self.height)
        if not self.layers or not self.frames:
            raise ValueError('Document needs at least one layer and one frame.')
        if not self.active_layer:
            self.active_layer = self.layers[-1].id
        self.ensure_cels()

    def ensure_cels(self) -> None:
        keys = {layer.id for layer in self.layers}
        if self.active_layer not in keys:
            self.active_layer = self.layers[-1].id
        for frame in self.frames:
            for key in set(frame.cels) - keys:
                frame.cels.pop(key)
            for key in keys:
                if key not in frame.cels:
                    frame.cels[key] = blank(self.width, self.height)
                if frame.cels[key].size != (self.width, self.height):
                    raise ValueError('Cel size differs from document dimensions.')
                if frame.cels[key].mode != 'RGBA':
                    frame.cels[key] = frame.cels[key].convert('RGBA')

    def copy(self) -> Document:
        memo: dict[int, Image.Image] = {}
        return Document(self.width, self.height, self.name,
            [Layer(k.id, k.name, k.visible, k.locked, k.opacity) for k in self.layers],
            [f.copy(memo) for f in self.frames], self.active_frame, self.active_layer,
            list(self.palette), [dict(g) for g in self.guides])

    @property
    def cel(self) -> Image.Image:
        return self.frames[self.active_frame].cels[self.active_layer]

    @property
    def layer(self) -> Layer:
        return next(k for k in self.layers if k.id == self.active_layer)

    def composite(self, frame_index: int | None = None, cel_override: Image.Image | None = None) -> Image.Image:
        frame = self.frames[self.active_frame if frame_index is None else frame_index]
        out = blank(self.width, self.height)
        for layer in self.layers:
            if not layer.visible or layer.opacity == 0:
                continue
            im = (cel_override if cel_override is not None and layer.id == self.active_layer
                  and (frame_index is None or frame_index == self.active_frame)
                  else frame.cels[layer.id])
            if layer.opacity == 255:
                out.alpha_composite(im)
            else:
                adjusted = im.copy()
                adjusted.putalpha(im.getchannel('A').point(lambda v: v * layer.opacity // 255))
                out.alpha_composite(adjusted)
        return out

    def duplicate_frame(self, linked: bool = False) -> int:
        """Duplicate full frame. Linked exposures share *live* cel images until unlinked."""
        src = self.frames[self.active_frame]
        new = Frame(src.duration_ms, dict(src.cels)) if linked else src.copy()
        self.frames.insert(self.active_frame + 1, new)
        self.active_frame += 1
        return self.active_frame

    def linked_frames(self, layer_id: str | None = None, frame_index: int | None = None) -> list[int]:
        layer_id = layer_id or self.active_layer
        frame_index = self.active_frame if frame_index is None else frame_index
        image = self.frames[frame_index].cels[layer_id]
        return [i for i, f in enumerate(self.frames) if f.cels[layer_id] is image]

    def link_cel(self, source_frame: int, target_frame: int, layer_id: str | None = None) -> None:
        layer_id = layer_id or self.active_layer
        if not (0 <= source_frame < len(self.frames) and 0 <= target_frame < len(self.frames)):
            raise IndexError('Frame index outside animation.')
        self.frames[target_frame].cels[layer_id] = self.frames[source_frame].cels[layer_id]

    def unlink_cel(self, frame_index: int | None = None, layer_id: str | None = None) -> None:
        layer_id = layer_id or self.active_layer
        frame_index = self.active_frame if frame_index is None else frame_index
        self.frames[frame_index].cels[layer_id] = self.frames[frame_index].cels[layer_id].copy()

    def replace_cel(self, image: Image.Image, frame_index: int | None = None,
                    layer_id: str | None = None) -> None:
        """Replace an image without silently breaking other linked exposures."""
        if image.size != (self.width, self.height):
            raise ValueError('Replacement cel dimensions do not match.')
        layer_id = layer_id or self.active_layer
        frame_index = self.active_frame if frame_index is None else frame_index
        old = self.frames[frame_index].cels[layer_id]
        for frame in self.frames:
            if frame.cels[layer_id] is old:
                frame.cels[layer_id] = image

    def _frame_indices(self, indices) -> list[int]:
        chosen = sorted(set(int(i) for i in indices))
        if not chosen or chosen[0] < 0 or chosen[-1] >= len(self.frames):
            raise ValueError('Select one or more valid animation frames.')
        return chosen

    def copy_frames(self, indices) -> list[Frame]:
        """Block clipboard preserving links *within* the copied block."""
        memo: dict[int, Image.Image] = {}
        return [self.frames[i].copy(memo) for i in self._frame_indices(indices)]

    def paste_frames(self, block: list[Frame], after: int | None = None) -> list[int]:
        if not block:
            raise ValueError('Frame clipboard is empty.')
        if len(self.frames) + len(block) > 2000:
            raise ValueError('Maximum 2000 frames per project.')
        after = self.active_frame if after is None else after
        if not (0 <= after < len(self.frames)):
            raise IndexError('Insertion frame index outside animation.')
        memo: dict[int, Image.Image] = {}
        inserts = [f.copy(memo) for f in block]
        for frame in inserts:
            if set(frame.cels) != {x.id for x in self.layers} or any(
                im.size != (self.width, self.height) for im in frame.cels.values()
            ):
                raise ValueError('Clipboard is incompatible with the current document.')
        self.frames[after+1:after+1] = inserts
        self.active_frame = after+1
        return list(range(after+1, after+1+len(inserts)))

    def duplicate_frames(self, indices, linked: bool = False) -> list[int]:
        chosen = self._frame_indices(indices)
        if len(self.frames) + len(chosen) > 2000:
            raise ValueError('Maximum 2000 frames per project.')
        if linked:
            block = [Frame(self.frames[i].duration_ms, dict(self.frames[i].cels)) for i in chosen]
            after = chosen[-1]
            self.frames[after+1:after+1] = block
            self.active_frame = after+1
            return list(range(after+1, after+1+len(block)))
        return self.paste_frames(self.copy_frames(chosen), chosen[-1])

    def delete_frames(self, indices) -> None:
        chosen = self._frame_indices(indices)
        if len(chosen) == len(self.frames):
            raise ValueError('The last animation frame cannot be removed.')
        for i in reversed(chosen):
            del self.frames[i]
        self.active_frame = min(chosen[0], len(self.frames)-1)

    def move_frames(self, indices, direction: int) -> list[int]:
        """Move selected frames one position, keeping their relative order."""
        chosen = self._frame_indices(indices)
        if direction not in (-1, 1):
            raise ValueError('Direction must be -1 or +1.')
        selected = set(chosen)
        if direction < 0:
            for i in range(1, len(self.frames)):
                if i in selected and i - 1 not in selected:
                    self.frames[i-1], self.frames[i] = self.frames[i], self.frames[i-1]
                    selected.remove(i); selected.add(i-1)
        else:
            for i in range(len(self.frames)-2, -1, -1):
                if i in selected and i + 1 not in selected:
                    self.frames[i+1], self.frames[i] = self.frames[i], self.frames[i+1]
                    selected.remove(i); selected.add(i+1)
        self.active_frame = min(selected)
        return sorted(selected)

    def reorder_frames(self, indices, insertion: int) -> list[int]:
        """Drag a possibly discontiguous frame selection to an insertion boundary.

        ``insertion`` is measured in the *original* sequence (0..frame_count).
        Frame objects, duration and linked-cel aliases are preserved by identity.
        """
        chosen = self._frame_indices(indices)
        if not 0 <= insertion <= len(self.frames):
            raise IndexError('Invalid timeline insertion boundary.')
        selected = set(chosen)
        old_active = self.frames[self.active_frame]
        moved = [self.frames[i] for i in chosen]
        remain = [frame for i, frame in enumerate(self.frames) if i not in selected]
        target = insertion - sum(i < insertion for i in chosen)
        self.frames[:] = remain[:target] + moved + remain[target:]
        self.active_frame = next(i for i, f in enumerate(self.frames) if f is old_active)
        return list(range(target, target + len(moved)))

    def set_frame_durations(self, indices, milliseconds: int) -> None:
        if not (16 <= milliseconds <= 10000):
            raise ValueError('Frame duration must be between 16 and 10000 ms.')
        for i in self._frame_indices(indices):
            self.frames[i].duration_ms = milliseconds

    def insert_hold(self, count: int, duration_ms: int | None = None) -> list[int]:
        """Insert exposures of current pose without copying its raster buffers."""
        if not 1 <= count <= 100 or len(self.frames) + count > 2000:
            raise ValueError('Hold must be between 1 and 100 frames (max 2000 total).')
        src = self.frames[self.active_frame]
        duration = src.duration_ms if duration_ms is None else duration_ms
        if not 16 <= duration <= 10000:
            raise ValueError('Frame duration must be between 16 and 10000 ms.')
        anchor = self.active_frame
        self.frames[anchor+1:anchor+1] = [Frame(duration, dict(src.cels)) for _ in range(count)]
        self.active_frame = anchor+1
        return list(range(anchor+1,anchor+count+1))

    def add_frame(self) -> int:
        previous = self.frames[self.active_frame]
        self.frames.insert(self.active_frame + 1, Frame(previous.duration_ms, {
            layer.id: blank(self.width, self.height) for layer in self.layers
        }))
        self.active_frame += 1
        return self.active_frame

    def remove_frame(self) -> None:
        if len(self.frames) <= 1:
            raise ValueError('The final animation frame cannot be removed.')
        self.frames.pop(self.active_frame)
        self.active_frame = min(self.active_frame, len(self.frames) - 1)

    def add_layer(self, name: str = 'Layer') -> str:
        index = next(i for i, x in enumerate(self.layers) if x.id == self.active_layer) + 1
        layer = Layer(name=name)
        self.layers.insert(index, layer)
        for frame in self.frames:
            frame.cels[layer.id] = blank(self.width, self.height)
        self.active_layer = layer.id
        return layer.id

    def remove_layer(self) -> None:
        if len(self.layers) <= 1:
            raise ValueError('The final layer cannot be removed.')
        index = next(i for i, x in enumerate(self.layers) if x.id == self.active_layer)
        layer = self.layers.pop(index)
        for frame in self.frames:
            frame.cels.pop(layer.id)
        self.active_layer = self.layers[min(index, len(self.layers) - 1)].id

    def shift_layer(self, direction: int) -> None:
        i = next(i for i, x in enumerate(self.layers) if x.id == self.active_layer)
        dest = i + direction
        if 0 <= dest < len(self.layers):
            self.layers[i], self.layers[dest] = self.layers[dest], self.layers[i]

    def resized(self, width: int, height: int, offset: tuple[int, int] = (0, 0)) -> None:
        validate_size(width, height)
        resized: dict[int, Image.Image] = {}
        for frame in self.frames:
            for layer in self.layers:
                src = frame.cels[layer.id]
                if id(src) not in resized:
                    dst = blank(width, height)
                    dst.paste(src, offset)
                    resized[id(src)] = dst
                frame.cels[layer.id] = resized[id(src)]
        self.width, self.height = width, height


def project_save(doc: Document, filename: str | Path) -> None:
    """Lossless v2 archive, saving linked exposures once and retaining v1 support."""
    target = Path(filename)
    target.parent.mkdir(parents=True, exist_ok=True)
    seen: dict[tuple[str, int], int] = {}
    links: list[dict[str, int]] = []
    images: list[tuple[int, str, Image.Image]] = []
    for fi, frame in enumerate(doc.frames):
        frame_links = {}
        for layer in doc.layers:
            image = frame.cels[layer.id]
            key = (layer.id, id(image))
            if key in seen:
                frame_links[layer.id] = seen[key]
            else:
                seen[key] = fi
                images.append((fi, layer.id, image))
        links.append(frame_links)
    data = {
        'schema': 2, 'name': doc.name, 'width': doc.width, 'height': doc.height,
        'active_frame': doc.active_frame, 'active_layer': doc.active_layer,
        'layers': [vars(x) for x in doc.layers],
        'frames': [{'duration_ms': f.duration_ms, 'linked_to': links[i]}
                   for i, f in enumerate(doc.frames)],
        'palette': doc.palette, 'guides': doc.guides,
    }
    tmp = target.with_name(target.name + '.tmp')
    try:
        with ZipFile(tmp, 'w', ZIP_DEFLATED) as z:
            z.writestr('project.json', json.dumps(data, indent=2))
            for fi, layer_id, image in images:
                buf = BytesIO()
                image.save(buf, format='PNG')
                z.writestr(f'cels/{fi:04d}/{layer_id}.png', buf.getvalue())
        tmp.replace(target)
    finally:
        if tmp.exists():
            tmp.unlink()


def project_load(filename: str | Path) -> Document:
    with ZipFile(filename, 'r') as z:
        data = json.loads(z.read('project.json'))
        schema = data.get('schema')
        if schema not in (1, 2):
            raise ValueError('Unrecognized Mellow Studio project format.')
        w, h = int(data['width']), int(data['height'])
        validate_size(w, h)
        layers = [Layer(**layer) for layer in data['layers']]
        if not layers or not data['frames'] or len(layers) > 128 or len(data['frames']) > 2000:
            raise ValueError('Project exceeds supported layer/frame count.')
        frames = []
        for fi, info in enumerate(data['frames']):
            duration = int(info['duration_ms'])
            if not (16 <= duration <= 10000):
                raise ValueError('Invalid frame duration.')
            cels = {}
            links = info.get('linked_to', {}) if schema == 2 else {}
            for layer in layers:
                if layer.id in links:
                    source_index = int(links[layer.id])
                    if source_index < 0 or source_index >= fi:
                        raise ValueError('Invalid forward/self linked cel reference.')
                    cels[layer.id] = frames[source_index].cels[layer.id]
                else:
                    with z.open(f'cels/{fi:04d}/{layer.id}.png') as f:
                        with Image.open(f) as im:
                            if im.size != (w, h):
                                raise ValueError('Cel size mismatch in project.')
                            cels[layer.id] = im.convert('RGBA')
            frames.append(Frame(duration, cels))
        doc = Document(w, h, data.get('name', 'Untitled'), layers, frames,
            max(0, min(int(data.get('active_frame', 0)), len(frames)-1)),
            data.get('active_layer', layers[-1].id),
            data.get('palette', []), data.get('guides', []))
    return doc


def draw_stroke(img: Image.Image, points: list[tuple[int, int]], color: RGBA,
                size: int = 1, symmetry_x: bool = False, symmetry_y: bool = False) -> None:
    """No antialiasing: each coordinate refers to a whole logical sprite pixel."""
    if not points:
        return
    d = ImageDraw.Draw(img)
    w, h = img.size
    paths = [points]
    if symmetry_x:
        paths.append([(w - 1 - x, y) for x, y in points])
    if symmetry_y:
        paths.append([(x, h - 1 - y) for x, y in points])
    if symmetry_x and symmetry_y:
        paths.append([(w - 1 - x, h - 1 - y) for x, y in points])
    radius = max(1, size)
    left = (radius - 1) // 2
    right = radius // 2
    for path in paths:
        for x, y in path:
            d.rectangle((x - left, y - left, x + right, y + right), fill=color)
        if len(path) > 1:
            # Filling a brush-square at each integer along the line avoids gaps.
            for a, b in zip(path, path[1:]):
                dx, dy = abs(b[0] - a[0]), abs(b[1] - a[1])
                steps = max(dx, dy)
                for step in range(1, steps):
                    x = round(a[0] + (b[0] - a[0]) * step / steps)
                    y = round(a[1] + (b[1] - a[1]) * step / steps)
                    d.rectangle((x-left, y-left, x+right, y+right), fill=color)


def draw_shape(img: Image.Image, kind: str, start: tuple[int, int], end: tuple[int, int],
               color: RGBA, filled: bool = False) -> None:
    d = ImageDraw.Draw(img)
    x0, x1 = sorted((start[0], end[0]))
    y0, y1 = sorted((start[1], end[1]))
    if kind == 'line':
        d.line((start, end), fill=color, width=1)
    elif kind == 'rectangle':
        d.rectangle((x0, y0, x1, y1), fill=color if filled else None,
                    outline=None if filled else color, width=1)
    elif kind == 'ellipse':
        d.ellipse((x0, y0, x1, y1), fill=color if filled else None,
                  outline=None if filled else color, width=1)
    else:
        raise ValueError(f'Unknown shape: {kind}')


def bucket_fill(img: Image.Image, at: tuple[int, int], color: RGBA, contiguous: bool = True) -> None:
    x, y = at
    if not (0 <= x < img.width and 0 <= y < img.height):
        return
    original = img.getpixel((x, y))
    if original == color:
        return
    if contiguous:
        ImageDraw.floodfill(img, at, color, thresh=0)
    else:
        # Whole layer replace, not whole composed document.
        pixels = img.load()
        for py in range(img.height):
            for px in range(img.width):
                if pixels[px, py] == original:
                    pixels[px, py] = color


def flip_cel(img: Image.Image, horizontal: bool) -> Image.Image:
    return img.transpose(Image.Transpose.FLIP_LEFT_RIGHT if horizontal else Image.Transpose.FLIP_TOP_BOTTOM)


def move_selection(img: Image.Image, rect: tuple[int, int, int, int], delta: tuple[int, int]) -> None:
    """Move a rectangular selection without damaging pixels elsewhere."""
    x0, y0, x1, y1 = rect  # half-open
    fragment = img.crop(rect)
    ImageDraw.Draw(img).rectangle((x0, y0, x1-1, y1-1), fill=TRANSPARENT)
    overlay = blank(*img.size)
    overlay.paste(fragment, (x0 + delta[0], y0 + delta[1]))
    img.alpha_composite(overlay)


@dataclass
class FloatingSelection:
    """A non-destructive pixel fragment staged above the active cel.

    Preview operations never touch the document. The editor commits the result
    as one atomic undoable cel replacement or cancels it without side effects.
    Pixel positions may be outside the canvas; clipping occurs at render time.
    """
    base: Image.Image
    pixels: Image.Image
    x: int
    y: int

    @classmethod
    def from_cel(cls, cel: Image.Image, rect: tuple[int, int, int, int]) -> FloatingSelection:
        x0, y0, x1, y1 = rect
        if x0 >= x1 or y0 >= y1 or not (0 <= x0 < x1 <= cel.width and
                                        0 <= y0 < y1 <= cel.height):
            raise ValueError('Selection must be inside the sprite and nonempty.')
        pixels = cel.crop(rect)
        base = cel.copy()
        ImageDraw.Draw(base).rectangle((x0, y0, x1-1, y1-1), fill=TRANSPARENT)
        return cls(base, pixels, x0, y0)

    @classmethod
    def pasted(cls, cel: Image.Image, pixels: Image.Image, position: tuple[int, int]) -> FloatingSelection:
        if pixels.width < 1 or pixels.height < 1:
            raise ValueError('Cannot paste an empty selection.')
        return cls(cel.copy(), pixels.convert('RGBA').copy(), *position)

    @property
    def rect(self) -> tuple[int, int, int, int]:
        return self.x, self.y, self.x + self.pixels.width, self.y + self.pixels.height

    def move_to(self, x: int, y: int) -> None:
        self.x, self.y = int(x), int(y)

    def shift(self, dx: int, dy: int) -> None:
        self.move_to(self.x + dx, self.y + dy)

    def render(self) -> Image.Image:
        output = self.base.copy()
        # alpha_composite(dest=...) clips negative/off-canvas offsets correctly.
        output.alpha_composite(self.pixels, (self.x, self.y))
        return output


def _compressed_history_snapshot(doc: Document) -> bytes:
    """Compact in-memory snapshot. Each unique cel is zlib-compressed once.

    This format never goes to disk, is not pickle, and keeps linked exposure
    identity on restoration. The 4-byte JSON header length precedes the header;
    images are then stored in reference order as [length, compressed RGBA].
    """
    seen = {}
    buffers = []
    frames = []
    for frame in doc.frames:
        aliases = {}
        for layer in doc.layers:
            image = frame.cels[layer.id]
            key = (layer.id, id(image))
            if key not in seen:
                seen[key] = len(buffers)
                buffers.append(zlib.compress(image.tobytes(), level=1))
            aliases[layer.id] = seen[key]
        frames.append({'duration_ms': frame.duration_ms, 'cels': aliases})
    header = json.dumps({
        'width': doc.width, 'height': doc.height, 'name': doc.name,
        'layers': [vars(x) for x in doc.layers], 'frames': frames,
        'active_frame': doc.active_frame, 'active_layer': doc.active_layer,
        'palette': doc.palette, 'guides': doc.guides,
    }, separators=(',', ':')).encode('utf-8')
    return b''.join([pack('<I', len(header)), header] +
                    [pack('<I', len(buf)) + buf for buf in buffers])


def _restore_history_snapshot(snapshot: bytes) -> Document:
    (length,) = unpack_from('<I', snapshot, 0)
    header = json.loads(snapshot[4:4+length])
    position = 4 + length
    ids = {alias for f in header['frames'] for alias in f['cels'].values()}
    images = []
    for _ in range(len(ids)):
        (size,) = unpack_from('<I', snapshot, position)
        position += 4
        rgba = zlib.decompress(snapshot[position:position+size])
        position += size
        images.append(Image.frombytes('RGBA', (header['width'], header['height']), rgba))
    frames = [Frame(f['duration_ms'], {layer_id: images[alias]
                                       for layer_id, alias in f['cels'].items()})
              for f in header['frames']]
    return Document(header['width'], header['height'], header['name'],
                    [Layer(**layer) for layer in header['layers']], frames,
                    header['active_frame'], header['active_layer'], header['palette'],
                    header['guides'])


class History:
    """Memory-bounded, compressed undo/redo preserving linked frame exposures.

    User actions are still atomic snapshots; compressed unique cel buffers avoid
    the unbounded multi-frame RGBA retention of the original implementation.
    """
    def __init__(self, limit: int = 128, max_bytes: int = 128 * 1024 * 1024):
        self.limit = limit
        self.max_bytes = max_bytes
        self.undo: list[bytes] = []
        self.redo: list[bytes] = []
        self.pending: Document | None = None

    @property
    def memory_bytes(self) -> int:
        return sum(map(len, self.undo)) + sum(map(len, self.redo))

    def _trim(self, history: list[bytes]) -> None:
        while len(history) > self.limit or (self.memory_bytes > self.max_bytes and len(history) > 1):
            history.pop(0)

    def begin(self, doc: Document) -> None:
        if self.pending is None:
            self.pending = doc.copy()

    def commit(self, doc: Document) -> bool:
        before = self.pending
        self.pending = None
        if before is None or documents_equal(before, doc):
            return False
        self.undo.append(_compressed_history_snapshot(before))
        self.redo.clear()
        self._trim(self.undo)
        return True

    def cancel(self) -> None:
        self.pending = None

    def back(self, doc: Document) -> Document:
        if not self.undo:
            return doc
        self.redo.append(_compressed_history_snapshot(doc))
        result = _restore_history_snapshot(self.undo.pop())
        self._trim(self.redo)
        return result

    def forward(self, doc: Document) -> Document:
        if not self.redo:
            return doc
        self.undo.append(_compressed_history_snapshot(doc))
        result = _restore_history_snapshot(self.redo.pop())
        self._trim(self.undo)
        return result


def documents_equal(a: Document, b: Document) -> bool:
    if (a.width, a.height, a.name, a.active_frame, a.active_layer, a.palette, a.guides,
            [(vars(x)) for x in a.layers], [(x.duration_ms) for x in a.frames]) != \
       (b.width, b.height, b.name, b.active_frame, b.active_layer, b.palette, b.guides,
            [(vars(x)) for x in b.layers], [(x.duration_ms) for x in b.frames]):
        return False
    if len(a.frames) != len(b.frames):
        return False
    if _link_signature(a) != _link_signature(b):
        return False
    return all(a.frames[i].cels[layer.id].tobytes() == b.frames[i].cels[layer.id].tobytes()
               for i in range(len(a.frames)) for layer in a.layers)


def _link_signature(doc: Document) -> tuple:
    seen = {}
    result = []
    for i, frame in enumerate(doc.frames):
        for layer in doc.layers:
            key = (layer.id, id(frame.cels[layer.id]))
            if key not in seen:
                seen[key] = i
            result.append(seen[key])
    return tuple(result)
