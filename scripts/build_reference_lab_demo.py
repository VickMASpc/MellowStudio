"""Deterministic 12-frame crop-offset reference registration demonstration."""
from pathlib import Path
from PIL import Image

from mellowstudio.calibration import MELLOW_EXACT
from mellowstudio.model import Document, project_save
from mellowstudio.reference import calibration_dict, suggest_translation

ROOT = Path(__file__).resolve().parent.parent
SHIFTS = [(0,0), (3,-2), (-3,2), (2,3), (-2,-3), (3,0),
          (-4,0), (0,3), (0,-3), (3,3), (-3,-3), (1,-1)]


def generate(out_path: Path = ROOT/'examples'/'reference_lab_12frame_demo.mellowzip') -> Path:
    with Image.open(ROOT/'examples'/'mellow_synthetic_scaled_reference_268x360.png') as img:
        base = img.convert('RGBA')
    doc = Document(41,55,'Mellow / 12 registered references')
    for i, (dx,dy) in enumerate(SHIFTS):
        screenshot=Image.new('RGBA',base.size,base.getpixel((0,0)))
        screenshot.paste(base,(dx,dy))
        cfg=MELLOW_EXACT.__class__(**calibration_dict(MELLOW_EXACT))
        cfg.origin_x+=dx;cfg.origin_y+=dy
        if i:doc.add_frame()
        doc.cel.paste(cfg.extract(screenshot,'dominant'))
        guess=suggest_translation(base,screenshot,max_shift=8)
        doc.add_reference(i,screenshot,f'Mellow take {i+1:02d} / offset {dx:+d},{dy:+d}.png',
                          cfg,sampling='dominant',registration={
                              'dx':guess.dx,'dy':guess.dy,'confidence':guess.confidence,
                              'status':'Manually confirmed reference alignment',
                              'applied': True})
        assert doc.cel.size == (41,55)
    doc.guides=[{'name':'Eye highlights / regression', 'points': [[16,19],[24,19]]}]
    doc.active_frame=0
    project_save(doc,out_path,backup=False)
    return out_path


if __name__=='__main__':
    print(generate())
