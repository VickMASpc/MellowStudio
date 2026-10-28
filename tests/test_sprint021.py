"""Sprint 0.2.1: floating pixel buffers, timeline drag semantics, compact history."""
import pytest
from PIL import Image
from mellowstudio.model import (
    Document, FloatingSelection, History, documents_equal, TRANSPARENT,
)

RED = (240, 20, 40, 255)
BLUE = (20, 80, 240, 255)


def test_floating_lift_stays_nondestructive_until_committed():
    doc = Document(8, 8)
    doc.cel.putpixel((2, 3), RED)
    original = doc.cel.tobytes()
    floating = FloatingSelection.from_cel(doc.cel, (2, 3, 3, 4))
    floating.shift(3, -2)
    assert floating.rect == (5, 1, 6, 2)
    assert doc.cel.tobytes() == original  # canvas is NEVER edited during dragging
    preview = floating.render()
    assert preview.getpixel((2, 3)) == TRANSPARENT
    assert preview.getpixel((5, 1)) == RED
    assert doc.cel.getpixel((2, 3)) == RED  # cancellation just drops the fragment
    doc.replace_cel(preview)
    assert doc.cel.getpixel((5, 1)) == RED
    assert doc.cel.getpixel((2, 3)) == TRANSPARENT


def test_paste_preview_alpha_preserves_layers_and_pixel_accuracy():
    doc = Document(6, 6)
    doc.cel.putpixel((0, 0), RED)
    incoming = Image.new('RGBA', (2, 2), BLUE)
    incoming.putpixel((0, 0), TRANSPARENT)
    f = FloatingSelection.pasted(doc.cel, incoming, (0, 0))
    preview = f.render()
    assert preview.getpixel((0, 0)) == RED  # alpha composites; no black background
    assert preview.getpixel((1, 0)) == BLUE
    assert doc.cel.getpixel((1, 0)) == TRANSPARENT
    f.move_to(-1, -1)
    clipped = f.render()
    assert clipped.getpixel((0, 0)) == BLUE
    assert doc.cel.getpixel((0, 0)) == RED


def test_floating_commit_on_linked_cels_propagates_and_undo_recovers_links():
    doc = Document(8, 8)
    doc.cel.putpixel((1, 1), RED)
    doc.duplicate_frame(linked=True)
    h = History()
    h.begin(doc)
    f = FloatingSelection.from_cel(doc.cel, (1, 1, 2, 2))
    f.shift(2, 0)
    doc.replace_cel(f.render())
    assert h.commit(doc)
    assert doc.linked_frames() == [0, 1]
    assert doc.frames[0].cels[doc.active_layer].getpixel((3, 1)) == RED
    doc = h.back(doc)
    assert doc.linked_frames() == [0, 1]
    assert doc.cel.getpixel((1, 1)) == RED
    doc = h.forward(doc)
    assert doc.linked_frames() == [0, 1]
    assert doc.cel.getpixel((3, 1)) == RED


def test_reorder_discontiguous_preserves_frame_instances_active_and_durations():
    doc = Document(8, 8)
    for _ in range(5):
        doc.add_frame()
    for i, f in enumerate(doc.frames):
        f.duration_ms = 100 + i * 50
    originals = doc.frames.copy()
    doc.active_frame = 2
    moved = doc.reorder_frames([1, 3], 6)
    assert moved == [4, 5]
    assert doc.frames == [originals[i] for i in [0, 2, 4, 5, 1, 3]]
    assert doc.frames[doc.active_frame] is originals[2]
    assert [f.duration_ms for f in doc.frames] == [100, 200, 300, 350, 150, 250]
    assert doc.reorder_frames([4, 5], 4) == [4, 5]  # no-op at current location


def test_reorder_linked_frames_then_history_undo_and_redo():
    doc = Document(5, 5)
    doc.cel.putpixel((1, 1), RED)
    doc.duplicate_frame(linked=True)
    doc.add_frame()
    doc.frames[2].cels[doc.active_layer].putpixel((1, 1), BLUE)
    h = History()
    before = doc.copy()
    h.begin(doc)
    assert doc.reorder_frames([0, 1], 3) == [1, 2]
    assert h.commit(doc)
    assert doc.linked_frames(frame_index=1) == [1, 2]
    doc = h.back(doc)
    assert documents_equal(before, doc)
    doc = h.forward(doc)
    assert doc.linked_frames(frame_index=1) == [1, 2]


def test_reorder_invalid_frames_raises_and_does_not_mutate():
    doc = Document(4, 4)
    doc.add_frame()
    before = doc.frames.copy()
    with pytest.raises(IndexError):
        doc.reorder_frames([0], 3)
    assert doc.frames == before
    with pytest.raises(ValueError):
        doc.reorder_frames([], 1)
    assert doc.frames == before


def test_history_snapshot_is_compressed_and_budget_bounded():
    doc = Document(128, 128)
    doc.duplicate_frame(linked=True)
    doc.duplicate_frame(linked=True)
    h = History(limit=100, max_bytes=1400)
    for i in range(30):
        h.begin(doc)
        doc.cel.putpixel((i, i), RED if i % 2 else BLUE)
        assert h.commit(doc)
    assert h.memory_bytes <= 1400 or len(h.undo) == 1
    assert len(h.undo) <= 100
    assert h.memory_bytes < (128 * 128 * 4 * 3)  # much less than one raw 3-frame copy
    before = doc.copy()
    doc = h.back(doc)
    assert not documents_equal(doc, before)
    doc = h.forward(doc)
    assert documents_equal(doc, before)


def test_history_detects_noop_and_clears_redo_on_new_edit():
    doc = Document(8, 8)
    h = History()
    h.begin(doc)
    assert not h.commit(doc)
    h.begin(doc)
    doc.cel.putpixel((0, 0), RED)
    assert h.commit(doc)
    doc = h.back(doc)
    assert h.redo
    h.begin(doc)
    doc.cel.putpixel((0, 0), BLUE)
    assert h.commit(doc)
    assert not h.redo
