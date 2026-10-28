"""Sprint 0.2 regression suite: linked exposures, frame blocks, grid inference."""
import json
from zipfile import ZipFile
import pytest
from PIL import Image, ImageDraw

from mellowstudio.calibration import MELLOW_EXACT, suggest_grids
from mellowstudio.model import (Document, History, flip_cel, project_load,
                                project_save, documents_equal)
from mellowstudio.samples import mellow_document

RED=(255,0,0,255)
BLUE=(0,0,255,255)
CLEAR=(0,0,0,0)


def frame_colors(doc):
    return [frame.cels[doc.active_layer].getpixel((0,0)) for frame in doc.frames]


def test_linked_exposure_propagates_live_pixels_and_unlink_breaks_link():
    d=Document(8,8)
    d.cel.putpixel((2,2),RED)
    d.duplicate_frame(linked=True)
    assert d.linked_frames()==[0,1]
    d.cel.putpixel((2,2),BLUE)
    assert d.frames[0].cels[d.active_layer].getpixel((2,2))==BLUE
    d.unlink_cel()
    d.cel.putpixel((2,2),RED)
    assert d.frames[0].cels[d.active_layer].getpixel((2,2))==BLUE
    assert d.linked_frames()==[1]


def test_flip_and_resize_preserve_linked_exposure_behavior():
    d=Document(5,5)
    d.cel.putpixel((0,1),RED)
    d.duplicate_frame(linked=True)
    d.replace_cel(flip_cel(d.cel,True))
    assert d.frames[0].cels[d.active_layer].getpixel((4,1))==RED
    assert d.linked_frames()==[0,1]
    d.resized(7,7,(1,1))
    assert d.frames[0].cels[d.active_layer].getpixel((5,2))==RED
    assert d.linked_frames()==[0,1]


def test_v2_archive_deduplicates_cels_and_keeps_links(tmp_path):
    d=Document(8,8)
    d.cel.putpixel((2,2),RED)
    d.duplicate_frame(linked=True)
    d.duplicate_frame(linked=True)
    d.add_layer('Detail')
    d.cel.putpixel((4,4),BLUE)
    d.duplicate_frame()
    p=tmp_path/'linked.mellowzip'
    project_save(d,p)
    with ZipFile(p) as z:
        config=json.loads(z.read('project.json'))
        assert config['schema']==2
        # 2 layers x 4 frames = 8 cels without dedupe; three links + independent
        assert len([n for n in z.namelist() if n.endswith('.png')])<8
    r=project_load(p)
    assert r.linked_frames(d.layers[0].id,0)==[0,1,2]
    r.frames[1].cels[d.layers[0].id].putpixel((2,2),BLUE)
    assert r.frames[0].cels[d.layers[0].id].getpixel((2,2))==BLUE
    assert r.frames[3].cels[d.layers[0].id].getpixel((2,2))==RED


def test_history_restores_links_and_detects_guide_only_edit():
    d=Document(4,4)
    h=History()
    h.begin(d)
    d.duplicate_frame(linked=True)
    assert h.commit(d)
    h.begin(d)
    d.unlink_cel()
    assert h.commit(d)
    assert d.linked_frames()==[1]
    d=h.back(d)
    assert d.linked_frames()==[0,1]
    d=h.back(d)
    assert len(d.frames)==1
    h.begin(d)
    d.guides.append({'name':'Calibration','pitch_x':6.5})
    assert h.commit(d)
    d=h.back(d)
    assert d.guides==[]


def test_frame_clipboard_preserves_internal_links_not_original():
    d=Document(4,4)
    d.cel.putpixel((0,0),RED)
    d.duplicate_frame(linked=True)
    copied=d.copy_frames([0,1])
    pasted=d.paste_frames(copied,after=1)
    assert pasted==[2,3]
    assert d.linked_frames(frame_index=0)==[0,1]
    assert d.linked_frames(frame_index=2)==[2,3]
    d.frames[3].cels[d.active_layer].putpixel((0,0),BLUE)
    assert d.frames[2].cels[d.active_layer].getpixel((0,0))==BLUE
    assert d.frames[0].cels[d.active_layer].getpixel((0,0))==RED


def test_frame_block_movement_preserves_order_and_selection():
    d=Document(4,4)
    for n in range(1,5):
        d.add_frame()
        d.cel.putpixel((0,0),(n*20,0,0,255))
    assert d.move_frames([1,3],1)==[2,4]
    assert [c[0] for c in frame_colors(d)]==[0,40,20,80,60]
    assert d.move_frames([2,4],-1)==[1,3]
    assert [c[0] for c in frame_colors(d)]==[0,20,40,60,80]
    assert d.move_frames([0],-1)==[0]


def test_batch_duplicate_delete_and_duration():
    d=Document(4,4)
    d.cel.putpixel((0,0),RED)
    d.duplicate_frame()
    d.cel.putpixel((0,0),BLUE)
    d.add_frame()
    assert d.duplicate_frames([0,2])==[3,4]
    assert frame_colors(d)[3:]==[RED,CLEAR]
    d.set_frame_durations([1,3,4],250)
    assert [f.duration_ms for f in d.frames]==[100,250,100,250,250]
    d.delete_frames([0,2,4])
    assert len(d.frames)==2
    with pytest.raises(ValueError):
        d.delete_frames([0,1])


def test_linked_holds_are_exposures_not_independent_copies():
    d=Document(8,8)
    assert d.insert_hold(3,175)==[1,2,3]
    assert len(d.frames)==4
    assert [f.duration_ms for f in d.frames]==[100,175,175,175]
    assert d.linked_frames()==[0,1,2,3]
    d.cel.putpixel((3,3),BLUE)
    assert all(f.cels[d.active_layer].getpixel((3,3))==BLUE for f in d.frames)


def test_v1_backward_compatibility():
    from pathlib import Path
    p=Path(__file__).resolve().parents[1] / 'examples' / 'mellow_original.mellowzip'
    assert project_load(p).width==41
    assert project_load(p).height==55


def test_automatic_grid_suggestions_restore_mellow_logical_size():
    src=mellow_document().cel
    bounds_x,bounds_y=MELLOW_EXACT.bounds_x(),MELLOW_EXACT.bounds_y()
    ref=Image.new('RGBA',(268,360),CLEAR)
    draw=ImageDraw.Draw(ref)
    for y in range(55):
        for x in range(41):
            draw.rectangle((bounds_x[x],bounds_y[y],bounds_x[x+1]-1,bounds_y[y+1]-1),
                           fill=src.getpixel((x,y)))
    suggestions=suggest_grids(ref)
    assert suggestions
    candidate=suggestions[0]
    assert (candidate.calibration.cols,candidate.calibration.rows)==(41,55)
    assert candidate.confidence>.8
    sampled=candidate.calibration.extract(ref,mode='dominant')
    assert sampled.size==(41,55)
    assert sampled.getpixel((16,19))==src.getpixel((16,19))
    assert sampled.getpixel((24,19))==src.getpixel((24,19))


def test_uniform_screenshot_does_not_invent_grid():
    assert suggest_grids(Image.new('RGB',(100,100),'red'))==[]


def test_invalid_history_only_link_state_is_detected():
    d=Document(4,4)
    d.duplicate_frame()
    e=d.copy()
    assert documents_equal(d,e)
    e.link_cel(0,1)
    assert not documents_equal(d,e)
