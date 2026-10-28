"""Bundled measured Mellow sprite project. JSON is canonical native-grid source."""
from pathlib import Path
import json
from PIL import Image
from .model import Document


def mellow_document() -> Document:
    root = Path(__file__).resolve().parent.parent
    data = json.loads((root / 'examples' / 'mellow_pixel_coordinates_41x55.json').read_text(encoding='utf-8'))
    w, h = data['native_grid']['width'], data['native_grid']['height']
    src = Image.new('RGBA', (w, h))
    color = {k: tuple(bytes.fromhex(v.lstrip('#'))) for k, v in data['palette'].items()}
    for y, row in enumerate(data['rows']):
        if len(row) != w:
            raise ValueError('Bundled sample is not the recorded 41-column native grid.')
        for x, key in enumerate(row):
            src.putpixel((x, y), color[key])
    d = Document(w, h, 'Mellow · measured 41×55')
    d.cel.paste(src)
    d.palette = [f'#{c[0]:02x}{c[1]:02x}{c[2]:02x}' for k, c in color.items() if k != '.']
    d.guides.append({'name': 'Eye highlights', 'points': [[16, 19], [24, 19]]})
    return d
