"""Generate demonstrative assets from the actual measured Mellow grid."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from mellowstudio.samples import mellow_document
from mellowstudio.model import project_save
from PIL import ImageDraw

root=Path(__file__).resolve().parent.parent
examples=root/'examples'
doc=mellow_document()
project_save(doc,examples/'mellow_original.mellowzip')
doc.composite().save(examples/'mellow_exact_native_41x55.png')
doc.frames[0].duration_ms=500
# Distinct editable cels: blink is a deliberately simple demo, not canonical artwork.
doc.duplicate_frame()
doc.frames[1].duration_ms=120
paint=ImageDraw.Draw(doc.cel)
paint.rectangle((12,18,20,23),fill=(255,255,255,255))
paint.rectangle((20,18,28,23),fill=(255,255,255,255))
paint.line((13,21,20,21),fill=(0,0,0,255))
paint.line((21,21,28,21),fill=(0,0,0,255))
doc.duplicate_frame()
doc.frames[2].duration_ms=400
# Restore one-frame open eyes as an independent third cel.
doc.frames[2].cels[doc.active_layer]=doc.frames[0].cels[doc.active_layer].copy()
doc.name='Mellow · blink workflow demo'
doc.active_frame=0
project_save(doc,examples/'mellow_blink_demo.mellowzip')
frames=[doc.composite(i) for i in range(len(doc.frames))]
frames[0].save(examples/'mellow_blink_preview.gif',save_all=True,append_images=frames[1:],
    duration=[f.duration_ms for f in doc.frames],loop=0,disposal=2)
print('Created Mellow exact project, native PNG, three-frame animation demo, and preview GIF')
