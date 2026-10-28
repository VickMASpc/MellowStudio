"""Sprint 0.2.2: durable edits, independent recovery slots, precision dither."""
from pathlib import Path
from zipfile import ZipFile
import json
import pytest
from PIL import Image

from mellowstudio.model import (Document, History, project_save, project_load,
                                draw_dither_stroke, BAYER_4)
from mellowstudio.recovery import RecoveryStore

RED = (255, 0, 0, 255)
BLUE = (0, 0, 255, 255)


def test_oversave_validates_and_retains_previous_as_backup(tmp_path):
    filename = tmp_path / 'sprite.mellowzip'
    d = Document(6, 6)
    d.cel.putpixel((2, 2), RED)
    project_save(d, filename)
    original = filename.read_bytes()
    d.cel.putpixel((2, 2), BLUE)
    project_save(d, filename)
    assert filename.read_bytes() != original
    assert filename.with_name(filename.name + '.bak').read_bytes() == original
    assert project_load(filename).cel.getpixel((2, 2)) == BLUE
    assert project_load(filename.with_name(filename.name + '.bak')).cel.getpixel((2, 2)) == RED
    assert not list(tmp_path.glob('.*.tmp'))


def test_failed_final_replace_preserves_existing_file(tmp_path, monkeypatch):
    from mellowstudio import model
    filename = tmp_path / 'sprite.mellowzip'
    d = Document(4, 4)
    project_save(d, filename)
    original = filename.read_bytes()
    d.cel.putpixel((1, 1), RED)
    replacement = model.os.replace

    def fail_final(source, target):
        if Path(target) == filename:
            raise PermissionError('simulated filesystem failure')
        return replacement(source, target)
    monkeypatch.setattr(model.os, 'replace', fail_final)
    with pytest.raises(PermissionError):
        project_save(d, filename)
    assert filename.read_bytes() == original
    assert project_load(filename).cel.getpixel((1, 1)) == (0, 0, 0, 0)
    assert not list(tmp_path.glob('.*.mellowzip.tmp'))


def test_project_save_rejects_invalid_unserializable_metadata_without_replacement(tmp_path):
    filename = tmp_path / 'original.mellowzip'
    d = Document(4, 4)
    project_save(d, filename)
    original = filename.read_bytes()
    d.guides.append({'bad': object()})
    with pytest.raises(TypeError):
        project_save(d, filename)
    assert filename.read_bytes() == original
    assert project_load(filename).width == 4


def test_distinct_projects_and_unsaved_sessions_have_isolated_recovery(tmp_path):
    root = tmp_path / 'snapshots'
    store = RecoveryStore(root, keep_per_document=2)
    d1 = Document(6, 6, 'Sprite Alpha')
    d2 = Document(6, 6, 'Sprite Beta')
    d1.cel.putpixel((1, 1), RED)
    d2.cel.putpixel((1, 1), BLUE)
    p1 = tmp_path / 'alpha.mellowzip'
    p2 = tmp_path / 'beta.mellowzip'
    a = store.write(d1, p1, 'session-1')
    b = store.write(d2, p2, 'session-2')
    c = store.write(d1, None, 'unsaved-session')
    entries = store.entries()
    assert len(entries) == 3
    assert len({e.token for e in entries}) == 3
    assert project_load(a.archive).cel.getpixel((1, 1)) == RED
    assert project_load(b.archive).cel.getpixel((1, 1)) == BLUE
    assert project_load(c.archive).cel.getpixel((1, 1)) == RED
    store.discard_token(a.token)
    assert len(store.entries()) == 2
    assert b.archive.is_file() and c.archive.is_file()


def test_recovery_rotates_only_within_own_identity(tmp_path):
    store = RecoveryStore(tmp_path, keep_per_document=2)
    d = Document(4, 4)
    other = store.write(d, tmp_path / 'different.mellowzip', 's')
    for i in range(6):
        d.cel.putpixel((0, 0), (i, 0, 0, 255))
        store.write(d, tmp_path / 'same.mellowzip', 's')
    entries = store.entries()
    assert len(entries) == 3
    assert other.archive.is_file()
    same = [e for e in entries if e.project_path == str((tmp_path / 'same.mellowzip').resolve())]
    assert len(same) == 2
    assert {project_load(e.archive).cel.getpixel((0, 0))[0] for e in same} == {4, 5}


def test_recovery_ignores_incomplete_or_bad_manifests(tmp_path):
    store = RecoveryStore(tmp_path)
    (tmp_path / 'orphan.json').write_text('{bad json')
    (tmp_path / 'incomplete.json').write_text(json.dumps({
        'schema': 1, 'token': 'a'*24, 'archive': 'absent.mellowzip',
        'project_name': 'x', 'created_at': 0,
    }))
    assert store.entries() == []


def test_dither_has_exact_bayer_pattern_with_no_interpolation(tmp_path):
    d = Document(8, 8)
    draw_dither_stroke(d.cel, [(0, 0), (7, 7)], RED, BLUE, size=8, level=8)
    for y in range(8):
        for x in range(8):
            assert d.cel.getpixel((x, y)) == (RED if BAYER_4[y%4][x%4] < 8 else BLUE)
    project_save(d, tmp_path/'dither.mellowzip')
    assert project_load(tmp_path/'dither.mellowzip').cel.tobytes() == d.cel.tobytes()


def test_dither_joins_contiguous_and_separated_strokes_in_logical_coordinates():
    one = Image.new('RGBA',(16,16))
    two = Image.new('RGBA',(16,16))
    draw_dither_stroke(one,[(1,4),(14,4)],RED,BLUE,level=8)
    draw_dither_stroke(two,[(1,4),(7,4)],RED,BLUE,level=8)
    draw_dither_stroke(two,[(8,4),(14,4)],RED,BLUE,level=8)
    assert one.tobytes() == two.tobytes()
    for level,color in ((0,BLUE),(16,RED)):
        im=Image.new('RGBA',(16,16))
        draw_dither_stroke(im,[(0,2),(15,2)],RED,BLUE,level=level)
        assert all(im.getpixel((x,2)) == color for x in range(16))
    with pytest.raises(ValueError):
        draw_dither_stroke(two,[(0,0)],RED,BLUE,level=17)


def test_stroke_history_single_atomic_undo_and_linked_exposures(tmp_path):
    d = Document(8, 8)
    d.duplicate_frame(linked=True)
    h = History()
    h.begin(d)
    draw_dither_stroke(d.cel, [(0,0),(7,0)], RED, BLUE)
    assert h.commit(d)
    assert d.frames[0].cels[d.active_layer] is d.frames[1].cels[d.active_layer]
    restored = h.back(d)
    assert restored.frames[0].cels[restored.active_layer] is restored.frames[1].cels[restored.active_layer]
    assert restored.cel.getpixel((0,0)) == (0,0,0,0)
    replay = h.forward(restored)
    assert replay.cel.getpixel((0,0)) == RED
