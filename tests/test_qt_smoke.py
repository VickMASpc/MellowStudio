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
    window.file_path = tmp_path/'dither-gui.mellowzip'
    assert window.save_project()
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
