"""GUI smoke test; runs on Windows when PySide6 is installed, skips in headless engine CI."""
import os
import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
pytest.importorskip('PySide6')
from PySide6.QtWidgets import QApplication
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
