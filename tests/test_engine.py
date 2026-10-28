from pathlib import Path
from zipfile import ZipFile
import pytest
from PIL import Image

from mellowstudio.model import (
    Document, draw_stroke, draw_shape, bucket_fill, move_selection,
    project_save, project_load, History, flip_cel
)
from mellowstudio.calibration import GridCalibration, MELLOW_EXACT, align_to_edges
from mellowstudio.samples import mellow_document

RED=(255,0,0,255)
BLUE=(0,0,255,255)
CLEAR=(0,0,0,0)


def test_native_mellow_size_and_single_pixel_highlights():
    d=mellow_document()
    assert (d.width,d.height)==(41,55)
    assert len(d.cel.getcolors(41*55))<=14
    assert d.cel.getpixel((16,19)) == (156,173,183,255)
    assert d.cel.getpixel((24,19)) == (156,173,183,255)
    assert d.cel.getpixel((15,19)) != d.cel.getpixel((16,19))
    assert d.cel.getpixel((23,19)) != d.cel.getpixel((24,19))


def test_mellow_grid_bounds_recover_original_screenshot_coordinates():
    assert MELLOW_EXACT.bounds_x()[0]==-1
    assert MELLOW_EXACT.bounds_x()[16]==105
    assert MELLOW_EXACT.bounds_x()[41]==269
    assert MELLOW_EXACT.bounds_y()[19]==124
    assert MELLOW_EXACT.bounds_y()[55]==360
    assert MELLOW_EXACT.cell_at(107,127)==(16,19)


def test_measured_reference_to_native_grid():
    source=mellow_document().cel
    # Variable cell widths: fractional pitch causes rounded boundaries 6 and 7.
    cfg=GridCalibration(41,55,6.58830,6.545454545,-.9093,0)
    displayed=Image.new('RGBA',(268,360),CLEAR)
    bx,by=cfg.bounds_x(),cfg.bounds_y()
    from PIL import ImageDraw
    paint=ImageDraw.Draw(displayed)
    for y in range(55):
        for x in range(41):
            paint.rectangle((bx[x],by[y],bx[x+1]-1,by[y+1]-1),fill=source.getpixel((x,y)))
    reconstructed=cfg.extract(displayed,mode='median')
    assert reconstructed.size==(41,55)
    # Boundary clipping affects external screenshot only, not logical cell identity.
    for xy in [(16,19),(24,19),(20,20),(3,5),(35,10)]:
        assert reconstructed.getpixel(xy)==source.getpixel(xy)


def test_calibration_count_does_not_use_screenshot_resolution():
    cfg=GridCalibration(2,2,5,5)
    im=Image.new('RGBA',(10,10),RED)
    from PIL import ImageDraw
    ImageDraw.Draw(im).rectangle((5,0,9,9),fill=BLUE)
    sampled=cfg.extract(im)
    assert sampled.size==(2,2)
    assert sampled.getpixel((0,0))==RED
    assert sampled.getpixel((1,1))==BLUE


def test_frame_duplicate_is_independent_and_preserves_layers():
    d=Document(8,8)
    draw_stroke(d.cel,[(1,1)],RED)
    d.add_layer('Detail')
    draw_stroke(d.cel,[(3,3)],BLUE)
    d.duplicate_frame()
    d.cel.putpixel((3,3),CLEAR)
    assert d.frames[0].cels[d.active_layer].getpixel((3,3))==BLUE
    assert d.frames[1].cels[d.active_layer].getpixel((3,3))==CLEAR
    assert d.composite().getpixel((1,1))==RED


def test_blank_frame_and_delete_final_guard():
    d=Document(8,8)
    draw_stroke(d.cel,[(3,3)],RED)
    d.add_frame()
    assert d.cel.getpixel((3,3))==CLEAR
    d.remove_frame()
    assert d.cel.getpixel((3,3))==RED
    with pytest.raises(ValueError):d.remove_frame()


def test_save_open_lossless_with_two_frames_two_layers(tmp_path):
    d=mellow_document()
    d.add_layer('Eyes')
    draw_stroke(d.cel,[(16,19)],BLUE)
    d.frames[0].duration_ms=200
    d.duplicate_frame()
    draw_stroke(d.cel,[(24,19)],RED)
    d.frames[1].duration_ms=75
    path=tmp_path/'project.mellowzip'
    project_save(d,path)
    with ZipFile(path) as z:
        assert 'project.json' in z.namelist()
        assert len([k for k in z.namelist() if k.endswith('.png')])==4
    restored=project_load(path)
    assert restored.name==d.name
    assert len(restored.layers)==2
    assert [f.duration_ms for f in restored.frames]==[200,75]
    for fi in range(2):
        assert restored.composite(fi).tobytes()==d.composite(fi).tobytes()
    assert restored.guides==d.guides


def test_shape_flood_erase_and_mirror():
    d=Document(8,8)
    draw_shape(d.cel,'rectangle',(1,1),(6,6),RED)
    bucket_fill(d.cel,(3,3),BLUE)
    assert d.cel.getpixel((3,3))==BLUE
    assert d.cel.getpixel((1,1))==RED
    bucket_fill(d.cel,(3,3),CLEAR)
    assert d.cel.getpixel((3,3))==CLEAR
    mirrored=flip_cel(d.cel,True)
    assert mirrored.getpixel((1,1))==d.cel.getpixel((6,1))


def test_symmetry_and_brush_size():
    d=Document(8,8)
    draw_stroke(d.cel,[(1,2)],RED,3,True,True)
    assert d.cel.getpixel((1,2))==RED
    assert d.cel.getpixel((6,2))==RED
    assert d.cel.getpixel((1,5))==RED
    assert d.cel.getpixel((6,5))==RED


def test_selection_move_not_copy():
    d=Document(8,8)
    draw_stroke(d.cel,[(1,1)],RED)
    move_selection(d.cel,(1,1,2,2),(3,4))
    assert d.cel.getpixel((1,1))==CLEAR
    assert d.cel.getpixel((4,5))==RED


def test_undo_redo_detects_rgb_changes_with_same_alpha():
    d=Document(8,8)
    h=History()
    h.begin(d)
    draw_stroke(d.cel,[(0,0)],RED)
    assert h.commit(d)
    h.begin(d)
    draw_stroke(d.cel,[(0,0)],BLUE)
    assert h.commit(d)
    d=h.back(d)
    assert d.cel.getpixel((0,0))==RED
    d=h.forward(d)
    assert d.cel.getpixel((0,0))==BLUE


def test_alpha_layer_opacity():
    d=Document(8,8)
    draw_stroke(d.cel,[(0,0)],RED)
    d.add_layer('Translucent')
    draw_stroke(d.cel,[(0,0)],BLUE)
    d.layer.opacity=128
    pixel=d.composite().getpixel((0,0))
    assert 100 <= pixel[0] <= 150
    assert 100 <= pixel[2] <= 150
    assert pixel[3]==255


def test_resize_preserves_native_pixels():
    d=Document(4,4)
    d.cel.putpixel((0,0),RED)
    d.resized(8,8,(2,2))
    assert d.cel.getpixel((2,2))==RED
    assert d.cel.getpixel((0,0))==CLEAR


def test_native_1x_reference_import_never_mixes_neighbor_colors():
    im=Image.new('RGBA',(3,2),RED)
    im.putpixel((1,0),BLUE)
    cfg=GridCalibration(3,2,1,1)
    assert cfg.extract(im,'median').tobytes()==im.tobytes()
