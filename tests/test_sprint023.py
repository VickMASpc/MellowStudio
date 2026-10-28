"""0.2.3 native-pixel reference persistence and deliberate frame registration."""
import json
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

import pytest
from PIL import Image, ImageDraw

from mellowstudio.calibration import GridCalibration
from mellowstudio.model import Document, Frame, History, documents_equal, project_load, project_save
from mellowstudio.reference import ReferenceAsset, calibration_dict, suggest_translation, reference_difference


def make_source():
    art = Image.new('RGBA', (90, 80), '#fafafa')
    d = ImageDraw.Draw(art)
    d.rectangle((9, 11, 62, 63), fill='#143fbe')
    d.rectangle((16, 20, 25, 29), fill='#ff4f33')
    d.line((29, 39, 78, 16), fill='#00e58e', width=4)
    return art


def offset(im, dx, dy):
    result=Image.new('RGBA',im.size,'#fafafa')
    result.paste(im,(dx,dy))
    return result


def cfg():
    return GridCalibration(15,10,6,8)


def test_translation_suggestion_is_diagnostic_not_automatic():
    orig=make_source()
    shifted=offset(orig,4,-3)
    suggested=suggest_translation(orig,shifted,max_shift=8)
    assert (suggested.dx,suggested.dy)==(4,-3)
    assert suggested.status=='candidate offset; explicit review required'
    assert suggested.confidence>.25
    different=suggest_translation(orig,orig.crop((0,0,84,80)),max_shift=8)
    assert 'different source dimensions' in different.status
    assert (different.dx,different.dy)==(0,0)
    assert suggest_translation(Image.new('RGB',orig.size,'white'),Image.new('RGB',orig.size,'white')).confidence==0
    preview=reference_difference(orig,shifted,4,-3)
    assert preview.size==orig.size
    assert preview.getpixel((15,15)) != (0,0,0,0)


def test_sources_are_retained_across_roundtrip_and_rebuilt_exactly(tmp_path):
    base=make_source()
    moved=offset(base,4,-3)
    d=Document(15,10,'Reference Test')
    first=d.add_reference(0,base,'original.png',cfg(),sampling='center',rebuild=True)
    d.add_frame()
    second=d.add_reference(1,moved,'shifted.png',cfg(),sampling='center',
        registration={'dx':4,'dy':-3,'confidence':.9,'status':'candidate; review required'},rebuild=True)
    assert second.calibration['origin_x']==0 # proposed shifts have NOT been applied
    unaligned=d.cel.tobytes()
    c=second.config(); c.origin_x+=4;c.origin_y-=3
    second.calibration=calibration_dict(c)
    d.rebuild_reference(1)
    assert d.cel.tobytes()!=unaligned
    assert d.cel.getpixel((3,2))==d.frames[0].cels[d.active_layer].getpixel((3,2))
    old_refs={r.id:r.png for r in d.references}
    p=tmp_path/'source.mellowzip'
    project_save(d,p)
    with ZipFile(p) as z:
        meta=json.loads(z.read('project.json'))
        assert meta['schema']==3
        assert len(meta['references'])==2
        assert len([k for k in z.namelist() if k.startswith('references/')])==2
        assert z.testzip() is None
    loaded=project_load(p)
    assert loaded.frames[0].reference_id==first.id
    assert loaded.frames[1].reference_id==second.id
    assert loaded.reference_for_frame(1).image().tobytes()==moved.tobytes()
    assert loaded.reference_for_frame(1).calibration==second.calibration
    assert {r.id:r.png for r in loaded.references}==old_refs
    assert documents_equal(d,loaded)


def test_rebuild_is_per_frame_even_if_raster_linked_and_undo_restores_metadata():
    d=Document(15,10)
    d.add_reference(0,make_source(),'origin.png',cfg(),rebuild=True)
    d.duplicate_frame(linked=True)
    assert d.linked_frames()==[0,1]
    d.add_reference(1,offset(make_source(),2,0),'shifted.png',cfg(),rebuild=False)
    history=History()
    history.begin(d)
    reference=d.reference_for_frame(1)
    shifted=reference.config();shifted.origin_x=2
    reference.calibration=calibration_dict(shifted)
    d.rebuild_reference(1)
    assert d.linked_frames()==[1]
    assert d.frames[0].cels[d.active_layer] is not d.frames[1].cels[d.active_layer]
    assert history.commit(d)
    restored=history.back(d)
    assert restored.linked_frames()==[0,1]
    assert restored.reference_for_frame(1).config().origin_x==0
    redo=history.forward(restored)
    assert redo.reference_for_frame(1).config().origin_x==2


def test_frame_operations_carry_reference_source_identity(tmp_path):
    d=Document(15,10)
    d.add_reference(0,make_source(),'first.png',cfg())
    d.duplicate_frame()
    d.add_reference(1,make_source(),'second.png',cfg())
    ids=[f.reference_id for f in d.frames]
    d.reorder_frames([0],2)
    assert [f.reference_id for f in d.frames]==[ids[1],ids[0]]
    d.active_frame=0
    pasted=d.copy_frames([0,1])
    d.paste_frames(pasted,after=1)
    assert [f.reference_id for f in d.frames]==[ids[1],ids[0],ids[1],ids[0]]
    project_save(d,tmp_path/'copy.mellowzip')
    result=project_load(tmp_path/'copy.mellowzip')
    assert [f.reference_id for f in result.frames]==[ids[1],ids[0],ids[1],ids[0]]


def test_v2_projects_still_load_without_embedded_sources(tmp_path):
    d=Document(8,8)
    d.duplicate_frame(linked=True)
    p=tmp_path/'v3.mellowzip'
    project_save(d,p)
    old=tmp_path/'v2.mellowzip'
    with ZipFile(p) as src, ZipFile(old,'w',ZIP_DEFLATED) as dst:
        for name in src.namelist():
            if name=='project.json':
                info=json.loads(src.read(name));info['schema']=2;info.pop('references',None)
                for f in info['frames']:f.pop('reference_id',None)
                dst.writestr(name,json.dumps(info))
            else:dst.writestr(name,src.read(name))
    loaded=project_load(old)
    assert not loaded.references
    assert loaded.linked_frames()==[0,1]


def test_corrupt_embedded_source_rejected_before_replacing_save(tmp_path):
    d=Document(15,10)
    d.add_reference(0,make_source(),'source.png',cfg())
    p=tmp_path/'valid.mellowzip';project_save(d,p)
    corrupt=tmp_path/'corrupt.mellowzip'
    with ZipFile(p) as src, ZipFile(corrupt,'w',ZIP_DEFLATED) as dst:
        for name in src.namelist():
            dst.writestr(name,b'not a png' if name.startswith('references/') else src.read(name))
    with pytest.raises(Exception):project_load(corrupt)
    assert project_load(p).reference_for_frame(0).image().size == make_source().size


def test_12_frame_mellow_reference_fixture_is_pixel_exact_and_reeditable(tmp_path):
    from mellowstudio.samples import mellow_document
    from mellowstudio.cli import project_info
    path=Path(__file__).resolve().parent.parent/'examples'/'reference_lab_12frame_demo.mellowzip'
    doc=project_load(path)
    expected=mellow_document().cel.tobytes()
    assert len(doc.frames)==len(doc.references)==12
    assert all(frame.cels[doc.active_layer].tobytes()==expected for frame in doc.frames)
    assert len(set(frame.reference_id for frame in doc.frames))==12
    assert len(project_info(doc)['embedded_references'])==12
    for i in range(12):
        ref=doc.reference_for_frame(i)
        assert ref.source_size==(268,360)
        assert (ref.config().cols,ref.config().rows)==(41,55)
        assert ref.extract().tobytes()==expected
    doc.active_frame=5
    ref=doc.reference_for_frame()
    original=ref.calibration.copy()
    ref.calibration['origin_x']+=3
    doc.rebuild_reference(5)
    assert doc.cel.tobytes()!=expected
    ref.calibration=original
    doc.rebuild_reference(5)
    assert doc.cel.tobytes()==expected
    project_save(doc,tmp_path/'replay.mellowzip')
    assert project_load(tmp_path/'replay.mellowzip').cel.tobytes()==expected


def test_shared_reference_metadata_detaches_before_edit():
    d=Document(15,10)
    d.add_reference(0,make_source(),'one.png',cfg())
    d.duplicate_frame(linked=True)
    assert d.frames[0].reference_id==d.frames[1].reference_id
    new=d.detach_reference(1)
    new.calibration['origin_x']=3.0
    assert d.reference_for_frame(0).config().origin_x==0
    assert d.reference_for_frame(1).config().origin_x==3.0
    assert d.frames[0].reference_id!=d.frames[1].reference_id


def test_center_sampler_on_shifted_half_pixel_boundary_is_stable():
    from mellowstudio.calibration import GridCalibration
    base=make_source()
    shifted=offset(base,4,-3)
    c=GridCalibration(15,10,6,8,0,0)
    original=c.extract(base,'center')
    c.origin_x=4;c.origin_y=-3
    extracted=c.extract(shifted,'center')
    assert extracted.getpixel((3,2))==original.getpixel((3,2))
