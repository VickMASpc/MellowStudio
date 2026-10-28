"""Generate a measured 268×360 test image from the canonical 41×55 Mellow grid.

This is a synthetic scaled reconstruction for grid-import validation, not the
original screenshot; the original native cells are in examples/*.json.
"""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from PIL import Image, ImageDraw
from mellowstudio.calibration import MELLOW_EXACT
from mellowstudio.samples import mellow_document


def main():
    root=Path(__file__).resolve().parents[1]/'examples'
    native=mellow_document().cel
    scaled=Image.new('RGBA',(268,360),(0,0,0,0))
    draw=ImageDraw.Draw(scaled)
    bx,by=MELLOW_EXACT.bounds_x(),MELLOW_EXACT.bounds_y()
    for y in range(55):
        for x in range(41):
            draw.rectangle((bx[x],by[y],bx[x+1]-1,by[y+1]-1),
                           fill=native.getpixel((x,y)))
    path=root/'mellow_synthetic_scaled_reference_268x360.png'
    scaled.save(path)
    print(path)


if __name__ == '__main__':
    main()
