"""Home-screen paths and exporter behavior without loading any Qt widgets."""
from pathlib import Path
from mellowstudio.recent import tidy_recent
from mellowstudio.model import Document
from mellowstudio.cli import export


def test_recents_only_existing_unique_native_projects(tmp_path):
    p=tmp_path/'Character.mellowzip'
    p.write_bytes(b'project fixture')
    missing=tmp_path/'missing.mellowzip'
    other=tmp_path/'frame.png';other.write_bytes(b'raw')
    assert tidy_recent([str(missing),str(p),str(p),str(other),'']) == [str(p.resolve())]
    assert tidy_recent(str(p)) == [str(p.resolve())]
    assert tidy_recent(None) == []


def test_recent_limit_and_newest_first(tmp_path):
    paths=[]
    for i in range(12):
        f=tmp_path/f'{i}.mellowzip'
        f.touch();paths.append(str(f))
    assert tidy_recent(paths) == paths[:8]


def test_fast_export_writes_lossless_sprite_sheet_with_timings(tmp_path):
    d=Document(8,8)
    d.cel.putpixel((4,2),(202,19,88,255))
    d.duplicate_frame()
    d.frames[0].duration_ms=100
    d.frames[1].duration_ms=250
    outputs=export(d,tmp_path/'walk.png','sheet',layout='vertical')
    assert len(outputs)==2
    from PIL import Image
    import json
    with Image.open(outputs[0]) as image:
        assert image.size==(8,16)
        assert image.getpixel((4,2))==(202,19,88,255)
    metadata=json.loads(outputs[1].read_text())
    assert metadata['durations_ms']==[100,250]
    assert metadata['layout']=='vertical'
