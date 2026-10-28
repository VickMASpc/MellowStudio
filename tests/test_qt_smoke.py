"""GUI smoke test; runs on Windows when PySide6 is installed, skips in headless engine CI."""
import os
import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
pytest.importorskip('PySide6')
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt, QPoint
from PySide6.QtTest import QTest
from mellowstudio.main import Editor


def test_qt_window_draw_duplicate_undo(tmp_path, monkeypatch):
    monkeypatch.setenv('XDG_DATA_HOME', str(tmp_path/'data'))
    monkeypatch.setenv('XDG_CONFIG_HOME', str(tmp_path/'config'))
    app=QApplication.instance() or QApplication([])
    window=Editor()
    window.show()
    app.processEvents()
    assert (window.doc.width,window.doc.height)==(41,55)
    before=window.doc.cel.getpixel((3,3))
    window.foreground=(250,180,30,255)
    window.set_tool('pencil')
    target=QPoint(3*window.canvas.zoom+2,3*window.canvas.zoom+2)
    QTest.mouseClick(window.canvas,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,target)
    app.processEvents()
    assert window.doc.cel.getpixel((3,3))==(250,180,30,255)
    window.duplicate_frame()
    assert len(window.doc.frames)==2
    window.undo()
    assert len(window.doc.frames)==1
    window.undo()
    assert window.doc.cel.getpixel((3,3))==before
    window.file_path=tmp_path/'smoke.mellowzip'
    assert window.save_project()
    window.close()


def test_qt_floating_commit_cancel_and_frame_reorder(tmp_path, monkeypatch):
    from mellowstudio.model import Document
    monkeypatch.setenv('XDG_DATA_HOME', str(tmp_path/'data'))
    monkeypatch.setenv('XDG_CONFIG_HOME', str(tmp_path/'config'))
    app=QApplication.instance() or QApplication([])
    window=Editor()
    window.set_document(Document(8,8))
    assert window.history.limit == 128
    window.show(); app.processEvents()
    window.doc.cel.putpixel((1,1),(255,0,0,255))
    window.canvas.selection=(1,1,2,2)
    window.nudge_selection(1,0)
    assert window.canvas.floating is not None
    assert window.doc.cel.getpixel((1,1))==(255,0,0,255)
    window.cancel_floating()
    assert window.doc.cel.getpixel((1,1))==(255,0,0,255)
    window.canvas.selection=(1,1,2,2)
    window.nudge_selection(1,0)
    window.commit_floating()
    assert window.doc.cel.getpixel((1,1))==(0,0,0,0)
    assert window.doc.cel.getpixel((2,1))==(255,0,0,255)
    window.undo()
    assert window.doc.cel.getpixel((1,1))==(255,0,0,255)
    window.duplicate_frame()
    window.add_frame()
    window.select_frame_indices([0])
    window.reorder_selected_frames(3)
    assert window.doc.active_frame == 1  # active frame object preserved
    assert len(window.doc.frames)==3
    window.file_path=tmp_path/'sprint021-smoke.mellowzip'
    assert window.save_project()
    window.close()


def test_qt_dither_composite_cache_and_recovery(tmp_path, monkeypatch):
    """GUI smoke for visible two-color brush and invalidation across undo/saves."""
    from mellowstudio.model import Document
    monkeypatch.setenv('XDG_DATA_HOME', str(tmp_path/'data'))
    monkeypatch.setenv('XDG_CONFIG_HOME', str(tmp_path/'config'))
    app = QApplication.instance() or QApplication([])
    window = Editor()
    window.set_document(Document(16, 16, 'Dither Test'))
    window.show(); app.processEvents()
    window.recovery.root = tmp_path/'recovery'
    window.foreground = (255, 0, 0, 255)
    window.secondary = (0, 0, 255, 255)
    window.set_tool('dither')
    window.dither_spin.setValue(8)
    before = window.composite_qimage(0)
    assert before is window.composite_qimage(0)
    assert window.thumbnail(0, 76) is window.thumbnail(0, 76)
    QTest.mouseClick(window.canvas, Qt.MouseButton.LeftButton,
                     Qt.KeyboardModifier.NoModifier, QPoint(window.canvas.zoom * 2 + 2,
                                                            window.canvas.zoom * 2 + 2))
    app.processEvents()
    assert window.doc.cel.getpixel((2, 2)) == (255, 0, 0, 255)
    assert window.composite_qimage(0) is not before
    assert window.doc.cel.getpixel((3, 2)) == (0, 0, 0, 0)
    window.autosave()
    assert len(window.recovery.entries()) == 1
    window.undo()
    assert window.doc.cel.getpixel((2, 2)) == (0, 0, 0, 0)
    assert window._save_to_path(tmp_path/'dither-gui.mellowzip')
    assert len(window.recovery.entries()) == 0
    window.close()


def test_qt_failed_save_as_preserves_identity(tmp_path, monkeypatch):
    import mellowstudio.main as main_module
    app = QApplication.instance() or QApplication([])
    window = Editor()
    window.set_document(__import__('mellowstudio.model',fromlist=['Document']).Document(8,8))
    original = tmp_path / 'original.mellowzip'
    assert window._save_to_path(original)
    window.doc.cel.putpixel((1,1),(20,40,60,255))
    window.dirty = True
    def denied(*args,**kwargs):
        raise PermissionError('simulate write denial')
    monkeypatch.setattr(main_module, 'project_save', denied)
    monkeypatch.setattr(QMessageBox, 'critical', lambda *args,**kwargs: None)
    assert not window._save_to_path(tmp_path / 'wrong-path.mellowzip')
    assert window.file_path == original
    assert window.dirty
    # Avoid opening the unsaved confirmation dialog in automated GUI smoke.
    window.dirty=False
    window.close()


def test_qt_reference_workbench_and_refresh(tmp_path,monkeypatch):
    from mellowstudio.model import Document, documents_equal, project_load
    from mellowstudio.calibration import GridCalibration
    from mellowstudio.reference_ui import ReferenceWorkbench
    from PIL import Image, ImageDraw
    app=QApplication.instance() or QApplication([])
    window=Editor()
    frame0=Image.new('RGBA',(90,80),'white')
    draw=ImageDraw.Draw(frame0)
    draw.rectangle((20,16,60,54),fill='navy')
    frame1=Image.new('RGBA',frame0.size,'white')
    frame1.paste(frame0,(3,-2))
    doc=Document(15,10)
    cfg=GridCalibration(15,10,6,8)
    doc.add_reference(0,frame0,'base.png',cfg,rebuild=True)
    doc.add_frame()
    doc.add_reference(1,frame1,'shift.png',cfg,
        registration={'dx':3,'dy':-2,'confidence':.92,'status':'candidate; manual approval'})
    doc.active_frame=1
    window.set_document(doc)
    window.show();app.processEvents()
    assert window.reference_dock.objectName()=='ReferenceDock'
    assert window.mode_label.text().startswith('  PIXEL WORKSPACE')
    assert 'shift.png' in window.source_info.text()
    original=window.doc.copy()
    lab=ReferenceWorkbench(window.doc,window)
    assert lab.table.rowCount()==2
    lab.table.selectRow(1)
    lab.accept_candidate()
    assert lab.ox.value()==3.0
    assert lab.oy.value()==-2.0
    lab.commit_all()
    assert lab.result()==lab.DialogCode.Accepted
    assert lab.doc.reference_for_frame(1).config().origin_x==3.0
    window.history.begin(window.doc)
    window.doc=lab.doc
    assert window.history.commit(window.doc)
    window.refresh_all();app.processEvents()
    assert 'origin 3, -2' in window.source_info.text()
    window.undo()
    assert documents_equal(window.doc,original)
    assert window._save_to_path(tmp_path/'reference_ui.mellowzip')
    assert project_load(tmp_path/'reference_ui.mellowzip').reference_for_frame(1) is not None
    window.close()
