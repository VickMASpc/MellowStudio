"""Mellow Studio — native, dockable Windows-first pixel animation workstation."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import sys
from uuid import uuid4

from PIL import Image, ImageOps
from PySide6.QtCore import Qt, QTimer, QSettings, QByteArray, QSize, QStandardPaths, Signal
from PySide6.QtGui import QAction, QColor, QIcon, QKeySequence, QPainter, QPixmap, QImage
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QScrollArea, QDockWidget, QVBoxLayout,
    QHBoxLayout, QGridLayout, QToolBar, QToolButton, QLabel, QPushButton, QListWidget,
    QListWidgetItem, QAbstractItemView, QSpinBox, QCheckBox, QInputDialog, QFileDialog,
    QMessageBox, QColorDialog, QFrame, QLineEdit, QDialog, QDialogButtonBox,
    QFormLayout, QSlider, QMenu, QScrollBar
)

from .model import (Document, History, project_load, project_save, blank,
                    flip_cel, draw_stroke, FloatingSelection)
from .recovery import RecoveryStore
from .samples import mellow_document
from .canvas import PixelCanvas, qimage_from_pil, pil_from_qimage
from .importer import ImportDialog

APP_TITLE = 'Mellow Studio'
VERSION = '0.2.2-dev'


class Swatch(QPushButton):
    def __init__(self, hexcode: str, callback, secondary_callback):
        super().__init__()
        self.hexcode=hexcode
        self.primary_cb=callback
        self.secondary_cb=secondary_callback
        self.setFixedSize(31, 31)
        self.setToolTip(f'{hexcode} · left: foreground · right: background')
        self.setStyleSheet('QPushButton {background:'+hexcode+'; border:2px solid #5a6477; border-radius:4px;} '
                           'QPushButton:hover {border:2px solid #ffffff;}')
        self.clicked.connect(lambda: self.primary_cb(hexcode))

    def mousePressEvent(self, event):
        if event.button()==Qt.MouseButton.RightButton:
            self.secondary_cb(self.hexcode)
            event.accept()
            return
        super().mousePressEvent(event)


def pixmap_thumb(image: Image.Image, size: int = 75) -> QPixmap:
    q = QPixmap.fromImage(qimage_from_pil(image))
    return q.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.FastTransformation)



class FrameTimeline(QListWidget):
    """Horizontal timeline with model-owned, multi-selection drag/drop ordering."""
    frameDropRequested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)

    def dropEvent(self, event):
        if event.source() is not self:
            event.ignore()
            return
        pos = event.position().toPoint()
        item = self.itemAt(pos)
        if item is None:
            insertion = 0 if pos.x() < 0 else self.count()
        else:
            insertion = self.row(item)
            if pos.x() > self.visualItemRect(item).center().x():
                insertion += 1
        self.frameDropRequested.emit(insertion)
        event.acceptProposedAction()


class NewDocumentDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle('New pixel-art document')
        form=QFormLayout(self)
        self.name=QLineEdit('Untitled')
        self.w=QSpinBox();self.w.setRange(1, 2048);self.w.setValue(64)
        self.h=QSpinBox();self.h.setRange(1, 2048);self.h.setValue(64)
        form.addRow('Project name',self.name)
        form.addRow('Width (logical pixels)',self.w)
        form.addRow('Height (logical pixels)',self.h)
        presets=QHBoxLayout()
        for width,height in [(16,16),(32,32),(64,64),(128,128),(256,256),(41,55)]:
            b=QPushButton(f'{width}×{height}')
            b.clicked.connect(lambda _,x=width,y=height: (self.w.setValue(x),self.h.setValue(y)))
            presets.addWidget(b)
        form.addRow('Presets',presets)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject)
        form.addRow(buttons)


class Editor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setObjectName('MellowStudioMainWindow')
        self.settings=QSettings('MellowStudio','MellowStudio')
        self.doc=mellow_document()
        self.history=History()
        self._composite_cache: dict[int, QImage] = {}
        self._thumb_cache: dict[tuple[int, int], QPixmap] = {}
        self._canvas_dirty_frames: set[int] = set()
        self.recovery = RecoveryStore(Path(QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppDataLocation)) / 'recovery')
        self._recovery_session = uuid4().hex
        self._recovered_entry = None
        self.file_path: Path | None=None
        self.dirty=False
        self.tool='pencil'
        self.space_pan=False
        self.foreground=(172,49,50,255)
        self.secondary=(255,255,255,255)
        self.brush_size=1
        self.dither_level=8
        self.contiguous=True
        self.preview_playing=False
        self._refreshing=False
        self.copied: tuple[Image.Image, int, int] | None=None
        self.frames_clipboard = []
        self._frame_selection_override = None
        self.setWindowTitle(APP_TITLE)
        self.resize(1370,850)
        self.setDockOptions(QMainWindow.DockOption.AllowTabbedDocks |
                            QMainWindow.DockOption.AllowNestedDocks |
                            QMainWindow.DockOption.AnimatedDocks)
        self.init_ui()
        self.connect_canvas()
        self.refresh_all()
        self.restore_workspace()
        self.recover_autosave()
        self.autosave_timer=QTimer(self)
        self.autosave_timer.setInterval(120000)
        self.autosave_timer.timeout.connect(self.autosave)
        self.autosave_timer.start()
        self.play_timer=QTimer(self)
        self.play_timer.timeout.connect(self.next_playback_frame)

    def init_ui(self):
        self.build_menus()
        self.build_tools()
        self.canvas=PixelCanvas(self)
        self.scroller=QScrollArea()
        self.scroller.setObjectName('PixelCanvasViewport')
        self.scroller.setWidget(self.canvas)
        self.scroller.setWidgetResizable(False)
        self.scroller.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroller.setStyleSheet('QScrollArea {background:#202735; border:0px;}')
        self.setCentralWidget(self.scroller)
        self.build_layers()
        self.build_palette()
        self.build_timeline()
        self.build_preview()
        self.status=QLabel('Pixel (–, –)')
        self.statusBar().addPermanentWidget(self.status)
        self.zoom_label=QLabel('12×')
        self.statusBar().addPermanentWidget(self.zoom_label)
        self.statusBar().showMessage('Mellow 41×55 loaded · Press Ctrl+D to duplicate a frame',6500)

    def connect_canvas(self):
        self.canvas.changed.connect(self.on_canvas_changed)
        self.canvas.cursorMoved.connect(self.show_pixel)
        self.canvas.sampled.connect(self.sample_color)
        self.canvas.zoomChanged.connect(self.show_zoom)

    def add_action(self, menu, text, func, shortcut=None, checkable=False):
        action=QAction(text,self)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        action.setCheckable(checkable)
        action.triggered.connect(func)
        if menu is not None:
            menu.addAction(action)
        self.addAction(action)
        return action

    def build_menus(self):
        bar=self.menuBar()
        file=bar.addMenu('&File')
        self.add_action(file,'New project…',self.new_project,'Ctrl+N')
        self.add_action(file,'Open project…',self.open_project,'Ctrl+O')
        self.add_action(file,'Save project',self.save_project,'Ctrl+S')
        self.add_action(file,'Save project as…',self.save_project_as,'Ctrl+Shift+S')
        self.add_action(file,'Recover autosaved project…',self.recover_autosave)
        file.addSeparator()
        self.add_action(file,'Open bundled Mellow (41×55)',self.open_mellow)
        self.add_action(file,'Import measured screenshot…',self.import_reference,'Ctrl+I')
        self.add_action(file,'Import measured image sequence…',self.import_measured_sequence)
        self.add_action(file,'Import spritesheet as frames…',self.import_spritesheet)
        self.add_action(file,'Import PNG as new project…',self.import_raw_png)
        file.addSeparator()
        self.add_action(file,'Export current frame PNG…',self.export_png,'Ctrl+E')
        self.add_action(file,'Export spritesheet PNG…',self.export_sheet)
        self.add_action(file,'Export animated GIF…',self.export_gif)
        self.add_action(file,'Export animation frames folder…',self.export_frames)
        file.addSeparator()
        self.add_action(file,'Exit',self.close,'Alt+F4')

        edit=bar.addMenu('&Edit')
        self.add_action(edit,'Undo',self.undo,'Ctrl+Z')
        self.add_action(edit,'Redo',self.redo,'Ctrl+Y')
        self.add_action(edit,'Redo (alternate)',self.redo,'Ctrl+Shift+Z')
        edit.addSeparator()
        self.add_action(edit,'Copy selection',self.copy_selection,'Ctrl+C')
        self.add_action(edit,'Cut selection',self.cut_selection,'Ctrl+X')
        self.add_action(edit,'Paste',self.paste_selection,'Ctrl+V')
        self.add_action(edit,'Commit floating selection',self.commit_floating,'Ctrl+Return')
        self.add_action(edit,'Cancel floating selection',self.cancel_floating)
        self.add_action(edit,'Select all',self.select_all,'Ctrl+A')
        self.add_action(edit,'Deselect',self.deselect,'Ctrl+Shift+A')
        edit.addSeparator()
        self.add_action(edit,'Flip active cel horizontally',lambda:self.flip_cel(True))
        self.add_action(edit,'Flip active cel vertically',lambda:self.flip_cel(False))
        self.add_action(edit,'Resize canvas…',self.resize_canvas)
        self.add_action(edit,'Clear cel',self.clear_cel,'Delete')

        animation=bar.addMenu('&Animation')
        self.add_action(animation,'Duplicate selected frames',self.duplicate_frame,'Ctrl+D')
        self.add_action(animation,'Duplicate as linked exposures',self.duplicate_linked,'Ctrl+Shift+D')
        self.add_action(animation,'Create linked holds…',self.insert_holds,'Ctrl+Alt+H')
        animation.addSeparator()
        self.add_action(animation,'Copy selected frames',self.copy_frame_block,'Ctrl+Alt+C')
        self.add_action(animation,'Paste frames after selection',self.paste_frame_block,'Ctrl+Alt+V')
        self.add_action(animation,'Move selected frames left',lambda:self.move_selected_frames(-1),'Ctrl+Alt+Left')
        self.add_action(animation,'Move selected frames right',lambda:self.move_selected_frames(1),'Ctrl+Alt+Right')
        self.add_action(animation,'Link selected cels to first selected',self.link_selected_cels)
        self.add_action(animation,'Unlink selected cels',self.unlink_selected_cels)
        self.add_action(animation,'Add blank frame',self.add_frame,'Alt+N')
        self.add_action(animation,'Delete current frame',self.delete_frame,'Ctrl+Shift+Backspace')
        self.add_action(animation,'Previous frame',self.previous_frame,'Alt+Left')
        self.add_action(animation,'Next frame',self.next_frame,'Alt+Right')
        self.add_action(animation,'Play / pause',self.toggle_play,'Space')
        animation.addSeparator()
        self.add_action(animation,'New layer',self.add_layer,'Ctrl+Shift+N')
        self.add_action(animation,'Delete layer',self.delete_layer)

        view=bar.addMenu('&View')
        self.action_grid=self.add_action(view,'Logical pixel grid',self.toggle_grid,'G',True)
        self.action_grid.setChecked(True)
        self.action_onion=self.add_action(view,'Onion skin',self.toggle_onion,'Shift+O',True)
        self.action_onion.setChecked(True)
        self.action_guides=self.add_action(view,'Measured guides',self.toggle_guides,None,True)
        self.action_guides.setChecked(True)
        self.add_action(view,'Zoom in',lambda:self.canvas.set_zoom(self.canvas.zoom+1),'Ctrl++')
        self.add_action(view,'Zoom out',lambda:self.canvas.set_zoom(self.canvas.zoom-1),'Ctrl+-')
        self.add_action(view,'Zoom actual logical pixels',lambda:self.canvas.set_zoom(1),'Ctrl+1')
        self.add_action(view,'Zoom to fit',self.zoom_fit,'Ctrl+0')
        self.add_action(view,'Reset panel layout',self.reset_layout)

        help=bar.addMenu('&Help')
        self.add_action(help,'Keyboard shortcuts',self.show_shortcuts,'F1')
        self.add_action(help,'About Mellow Studio',self.about)

    def build_tools(self):
        tb=QToolBar('Drawing tools',self)
        tb.setObjectName('DrawingTools')
        tb.setMovable(True)
        tb.setIconSize(QSize(20,20))
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea,tb)
        self.tool_buttons={}
        entries=[('pencil','Pencil','B'),('dither','2-color Dither','D'),('eraser','Eraser','E'),
                 ('bucket','Fill','F'),('picker','Eyedropper','I'),
                 ('line','Line','L'),('rectangle','Rectangle','R'),
                 ('ellipse','Ellipse','O'),('marquee','Marquee','M'),
                 ('move','Move selection','V'),('pan','Pan','H')]
        glyphs={'pencil':'✎','dither':'▦','eraser':'⌫','bucket':'▥','picker':'◉','line':'╱',
                'rectangle':'▭','ellipse':'◯','marquee':'▧','move':'✥','pan':'✋'}
        for tool, desc, key in entries:
            b=QToolButton();b.setText(glyphs[tool])
            b.setFixedSize(42,41)
            b.setToolTip(f'{desc} ({key})')
            b.setCheckable(True)
            b.clicked.connect(lambda _, t=tool:self.set_tool(t))
            tb.addWidget(b)
            self.tool_buttons[tool]=b
        tb.addSeparator()
        tb.addWidget(QLabel('Size'))
        self.brush_spin=QSpinBox()
        self.brush_spin.setRange(1,32)
        self.brush_spin.setValue(1)
        self.brush_spin.valueChanged.connect(lambda v:setattr(self,'brush_size',v))
        tb.addWidget(self.brush_spin)
        tb.addWidget(QLabel('Mix'))
        self.dither_spin=QSpinBox()
        self.dither_spin.setToolTip('Dither mix: 0=secondary color, 16=foreground; 8=50%')
        self.dither_spin.setRange(0,16)
        self.dither_spin.setValue(8)
        self.dither_spin.valueChanged.connect(lambda v:setattr(self,'dither_level',v))
        tb.addWidget(self.dither_spin)
        tb.addSeparator()
        self.sym_x_box=QCheckBox('X↔')
        self.sym_y_box=QCheckBox('Y↕')
        self.sym_x_box.setToolTip('Horizontal symmetry')
        self.sym_y_box.setToolTip('Vertical symmetry')
        self.sym_x_box.toggled.connect(lambda v:setattr(self.canvas,'sym_x',v)) if hasattr(self,'canvas') else None
        tb.addWidget(self.sym_x_box);tb.addWidget(self.sym_y_box)
        self.fill_box=QCheckBox('Solid')
        self.fill_box.setToolTip('Fill rectangles and ellipses')
        tb.addWidget(self.fill_box)
        self.contiguous_box=QCheckBox('Region')
        self.contiguous_box.setChecked(True)
        self.contiguous_box.toggled.connect(lambda v:setattr(self,'contiguous',v))
        self.contiguous_box.setToolTip('Flood fill connected area; unchecked = replace throughout cel')
        tb.addWidget(self.contiguous_box)
        self.set_tool('pencil')

    def build_dock(self,title,objectname,widget,area):
        dock=QDockWidget(title,self)
        dock.setObjectName(objectname)
        dock.setWidget(widget)
        dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.addDockWidget(area,dock)
        self.menuBar().findChild(QMenu,'View') if False else None
        self._view_docks = getattr(self,'_view_docks',[])
        self._view_docks.append(dock)
        return dock

    def build_layers(self):
        root=QWidget();v=QVBoxLayout(root)
        self.layer_list=QListWidget()
        self.layer_list.setMinimumWidth(200)
        self.layer_list.currentRowChanged.connect(self.layer_selected)
        self.layer_list.itemChanged.connect(self.layer_item_changed)
        v.addWidget(self.layer_list)
        controls=QHBoxLayout()
        for label,fn,tip in [('+',self.add_layer,'Add layer'),('−',self.delete_layer,'Delete layer'),
                             ('↑',lambda:self.move_layer(1),'Move higher'),('↓',lambda:self.move_layer(-1),'Move lower'),
                             ('Rename',self.rename_layer,'Rename layer')]:
            b=QPushButton(label);b.setToolTip(tip);b.clicked.connect(fn);controls.addWidget(b)
        v.addLayout(controls)
        opacity=QHBoxLayout()
        opacity.addWidget(QLabel('Opacity'))
        self.opacity_slider=QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(0,255);self.opacity_slider.setValue(255)
        self.opacity_slider.sliderReleased.connect(self.commit_layer_opacity)
        self.opacity_slider.sliderPressed.connect(lambda:self.history.begin(self.doc))
        self.opacity_slider.valueChanged.connect(self.opacity_changed)
        opacity.addWidget(self.opacity_slider)
        self.opacity_value=QLabel('100%')
        opacity.addWidget(self.opacity_value)
        v.addLayout(opacity)
        self.layer_lock=QCheckBox('Lock current layer')
        self.layer_lock.toggled.connect(self.layer_locked)
        v.addWidget(self.layer_lock)
        self.layer_dock=self.build_dock('Layers','LayersDock',root,Qt.DockWidgetArea.RightDockWidgetArea)

    def build_palette(self):
        root=QWidget();v=QVBoxLayout(root)
        top=QHBoxLayout()
        self.fg_button=QPushButton('FG')
        self.bg_button=QPushButton('BG')
        self.fg_button.setToolTip('Click to pick foreground color')
        self.bg_button.setToolTip('Click to pick secondary/right-click color')
        self.fg_button.clicked.connect(lambda:self.pick_color(False))
        self.bg_button.clicked.connect(lambda:self.pick_color(True))
        top.addWidget(self.fg_button);top.addWidget(self.bg_button)
        v.addLayout(top)
        self.color_grid=QGridLayout();self.color_grid.setSpacing(4)
        v.addLayout(self.color_grid)
        a=QPushButton('+ Add FG to palette')
        a.clicked.connect(self.add_palette_color)
        v.addWidget(a)
        v.addStretch()
        self.palette_dock=self.build_dock('Palette','PaletteDock',root,Qt.DockWidgetArea.RightDockWidgetArea)
        self.tabifyDockWidget(self.layer_dock,self.palette_dock)
        self.layer_dock.raise_()

    def build_timeline(self):
        root=QWidget();v=QVBoxLayout(root)
        top=QHBoxLayout()
        for label,fn,tip in [('|◀',self.previous_frame,'Previous frame'),
                             ('▶ / ❚❚',self.toggle_play,'Play/pause'),
                             ('▶|',self.next_frame,'Next frame'),
                             ('+ Blank',self.add_frame,'Insert blank after current'),
                             ('⧉ Duplicate',self.duplicate_frame,'Duplicate selected frames (Ctrl+D)'),
                             ('⇄ Hold',self.insert_holds,'Insert linked holds of active pose'),
                             ('− Delete',self.delete_frame,'Delete current frame')]:
            b=QPushButton(label);b.clicked.connect(fn);b.setToolTip(tip);top.addWidget(b)
        for label, fn, tip in [ ('←',lambda:self.move_selected_frames(-1),'Move selected frames left'),
                               ('→',lambda:self.move_selected_frames(1),'Move selected frames right'),
                               ('Link',self.link_selected_cels,'Link selected cels on current layer'),
                               ('Unlink',self.unlink_selected_cels,'Unlink selected cels on current layer')]:
            b=QPushButton(label); b.clicked.connect(fn); b.setToolTip(tip); top.addWidget(b)
        top.addStretch()
        top.addWidget(QLabel('Duration of selected frames (ms)'))
        self.duration=QSpinBox();self.duration.setRange(16,10000);self.duration.setSingleStep(25)
        self.duration.setValue(100)
        self.duration.valueChanged.connect(self.duration_changed)
        top.addWidget(self.duration)
        v.addLayout(top)
        self.timeline=FrameTimeline()
        self.timeline.setViewMode(QListWidget.ViewMode.IconMode)
        self.timeline.setFlow(QListWidget.Flow.LeftToRight)
        self.timeline.setWrapping(False)
        self.timeline.setMovement(QListWidget.Movement.Static)
        self.timeline.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.timeline.setToolTip('Ctrl-click / Shift-click frames to select a block. Ctrl+D duplicates the selected block.')
        self.timeline.setIconSize(QSize(76,76))
        self.timeline.setGridSize(QSize(96,110))
        self.timeline.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.timeline.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.timeline.setMaximumHeight(136)
        self.timeline.setMinimumHeight(118)
        self.timeline.currentRowChanged.connect(self.frame_selected)
        self.timeline.frameDropRequested.connect(self.reorder_selected_frames)
        v.addWidget(self.timeline)
        self.timeline_dock=self.build_dock('Animation timeline','TimelineDock',root,
                                          Qt.DockWidgetArea.BottomDockWidgetArea)

    def build_preview(self):
        root=QWidget();v=QVBoxLayout(root)
        self.preview=QLabel()
        self.preview.setMinimumSize(175,180)
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setStyleSheet('background:#303847; border:1px solid #586176;')
        v.addWidget(self.preview)
        v.addWidget(QLabel('Native-pixel playback · per-frame timing'))
        self.preview_dock=self.build_dock('Live preview','PreviewDock',root,
                                         Qt.DockWidgetArea.RightDockWidgetArea)

    def set_tool(self,tool):
        if tool not in ('move', 'marquee') and hasattr(self, 'canvas'):
            self.commit_floating()
        self.tool=tool
        for name,b in self.tool_buttons.items():
            b.setChecked(name==tool)
        if hasattr(self,'statusBar'):
            self.statusBar().showMessage('Tool: '+tool.title(),1400)

    def keyPressEvent(self,event):
        # Do not steal letter keys from layer names, dialogs, or numeric controls.
        from PySide6.QtWidgets import QLineEdit, QTextEdit, QAbstractSpinBox
        focus=QApplication.focusWidget()
        if isinstance(focus,(QLineEdit,QTextEdit,QAbstractSpinBox)):
            super().keyPressEvent(event);return
        if event.modifiers() in (Qt.KeyboardModifier.NoModifier, Qt.KeyboardModifier.ShiftModifier):
            key=event.key()
            mapping={Qt.Key.Key_B:'pencil',Qt.Key.Key_D:'dither',Qt.Key.Key_E:'eraser',Qt.Key.Key_F:'bucket',
                     Qt.Key.Key_I:'picker',Qt.Key.Key_L:'line',Qt.Key.Key_R:'rectangle',
                     Qt.Key.Key_O:'ellipse',Qt.Key.Key_M:'marquee',Qt.Key.Key_V:'move',
                     Qt.Key.Key_H:'pan'}
            if key in mapping and not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                self.set_tool(mapping[key]);event.accept();return
            if key==Qt.Key.Key_Escape:
                if self.canvas.floating is not None:
                    self.cancel_floating()
                else:
                    self.deselect()
                event.accept();return
            if key in [Qt.Key.Key_BracketLeft, Qt.Key.Key_BracketRight]:
                self.brush_spin.setValue(self.brush_size+(1 if key==Qt.Key.Key_BracketRight else -1))
                event.accept();return
            arrow={Qt.Key.Key_Left:(-1,0),Qt.Key.Key_Right:(1,0),
                   Qt.Key.Key_Up:(0,-1),Qt.Key.Key_Down:(0,1)}
            if key in arrow and (self.canvas.selection or self.canvas.floating):
                dx,dy=arrow[key]
                mul=10 if event.modifiers() & Qt.KeyboardModifier.ShiftModifier else 1
                self.nudge_selection(dx*mul,dy*mul)
                event.accept();return
        super().keyPressEvent(event)

    def keyReleaseEvent(self,event):
        super().keyReleaseEvent(event)

    def show_pixel(self,x,y):
        if self.canvas.floating:
            c = self.doc.composite(cel_override=self.canvas.floating.render()).getpixel((x,y))
        else:
            q = self.composite_qimage(self.doc.active_frame)
            c = tuple(q.pixelColor(x, y).getRgb())
        self.status.setText(f'Cell ({x}, {y}) · RGBA {c} · {self.doc.width}×{self.doc.height}')

    def show_zoom(self,zoom):
        self.zoom_label.setText(f'{zoom}×')

    def zoom_fit(self):
        size=self.scroller.viewport().size()
        self.canvas.set_zoom(max(2,min(64,size.width()//self.doc.width,
                                           size.height()//self.doc.height)))

    def invalidate_render(self, indices=None):
        if indices is None:
            self._composite_cache.clear()
            self._thumb_cache.clear()
        else:
            for i in indices:
                self._composite_cache.pop(i, None)
                for key in list(self._thumb_cache):
                    if key[0] == i:
                        self._thumb_cache.pop(key, None)

    def composite_qimage(self, index: int) -> QImage:
        if index not in self._composite_cache:
            self._composite_cache[index] = qimage_from_pil(self.doc.composite(index))
        return self._composite_cache[index]

    def thumbnail(self, index: int, size: int) -> QPixmap:
        key = (index, size)
        if key not in self._thumb_cache:
            self._thumb_cache[key] = QPixmap.fromImage(self.composite_qimage(index)).scaled(
                size, size, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.FastTransformation)
        return self._thumb_cache[key]

    def on_canvas_changed(self):
        indices = self.doc.linked_frames()
        self._canvas_dirty_frames.update(indices)
        self.invalidate_render(indices)
        self.canvas.update()

    def refresh_all(self):
        self.invalidate_render()
        self._canvas_dirty_frames.clear()
        self._refreshing=True
        try:
            self.canvas.adjust_size()
            self.refresh_timeline()
            self.refresh_layers()
            self.refresh_palette()
            self.refresh_preview()
            self.update_title()
            self.sym_x_box.toggled.connect(lambda v:setattr(self.canvas,'sym_x',v)) if not getattr(self,'_sym_connected',False) else None
            self.sym_y_box.toggled.connect(lambda v:setattr(self.canvas,'sym_y',v)) if not getattr(self,'_sym_connected',False) else None
            self.fill_box.toggled.connect(lambda v:setattr(self.canvas,'filled_shapes',v)) if not getattr(self,'_sym_connected',False) else None
            self._sym_connected=True
        finally:
            self._refreshing=False

    def selected_frame_indices(self):
        if self._frame_selection_override is not None:
            return list(self._frame_selection_override)
        if not hasattr(self, 'timeline'):
            return [self.doc.active_frame]
        selected = sorted(self.timeline.row(item) for item in self.timeline.selectedItems())
        return selected or [self.doc.active_frame]

    def select_frame_indices(self, indices):
        self._frame_selection_override = sorted(set(indices))
        self.refresh_timeline()

    def refresh_timeline(self):
        selected = self.selected_frame_indices()
        # Count linked references once: O(frames), not O(frames²).
        from collections import Counter
        aliases = Counter(id(f.cels[self.doc.active_layer]) for f in self.doc.frames)
        self.timeline.blockSignals(True)
        self.timeline.clear()
        for i,frame in enumerate(self.doc.frames):
            linked = aliases[id(frame.cels[self.doc.active_layer])] > 1
            icon = ' ↔' if linked else ''
            item=QListWidgetItem(QIcon(self.thumbnail(i,76)),
                                 f'#{i+1:02d}{icon} · {frame.duration_ms} ms')
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setSizeHint(QSize(95,105))
            self.timeline.addItem(item)
        self.timeline.setCurrentRow(self.doc.active_frame)
        for i in range(self.timeline.count()):
            self.timeline.item(i).setSelected(i in selected)
        self._frame_selection_override = None
        self.duration.blockSignals(True)
        self.duration.setValue(self.doc.frames[self.doc.active_frame].duration_ms)
        self.duration.blockSignals(False)
        self.timeline.blockSignals(False)

    def refresh_layers(self):
        self.layer_list.blockSignals(True)
        self.layer_list.clear()
        ordered=list(reversed(self.doc.layers))
        for layer in ordered:
            item=QListWidgetItem(layer.name + ('  🔒' if layer.locked else ''))
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if layer.visible else Qt.CheckState.Unchecked)
            item.setData(Qt.ItemDataRole.UserRole,layer.id)
            self.layer_list.addItem(item)
            if layer.id==self.doc.active_layer:
                self.layer_list.setCurrentItem(item)
        self.layer_list.blockSignals(False)
        self.layer_lock.blockSignals(True)
        self.layer_lock.setChecked(self.doc.layer.locked)
        self.layer_lock.blockSignals(False)
        self.opacity_slider.blockSignals(True)
        self.opacity_slider.setValue(self.doc.layer.opacity)
        self.opacity_slider.blockSignals(False)
        self.opacity_value.setText(f'{round(self.doc.layer.opacity*100/255)}%')

    def refresh_palette(self):
        while self.color_grid.count():
            w=self.color_grid.takeAt(0).widget()
            if w:w.deleteLater()
        for i,hexcode in enumerate(self.doc.palette):
            sw=Swatch(hexcode,self.set_foreground_hex,self.set_secondary_hex)
            self.color_grid.addWidget(sw,i//6,i%6)
        self.fg_button.setStyleSheet('background:'+self.to_hex(self.foreground)+'; color:#fff; font-weight:bold;')
        self.bg_button.setStyleSheet('background:'+self.to_hex(self.secondary)+'; color:#151923; font-weight:bold;')

    @staticmethod
    def to_hex(c):
        return '#%02x%02x%02x' % c[:3]

    def set_foreground_hex(self,hexcode):
        c=QColor(hexcode)
        self.foreground=(c.red(),c.green(),c.blue(),255)
        self.refresh_palette()

    def set_secondary_hex(self,hexcode):
        c=QColor(hexcode)
        self.secondary=(c.red(),c.green(),c.blue(),255)
        self.refresh_palette()

    def pick_color(self,secondary):
        original=QColor.fromRgb(*(self.secondary if secondary else self.foreground))
        c=QColorDialog.getColor(original,self,'Pick pixel color')
        if c.isValid():
            if secondary:self.set_secondary_hex(c.name())
            else:self.set_foreground_hex(c.name())

    def add_palette_color(self):
        c=self.to_hex(self.foreground)
        if c not in self.doc.palette:
            self.begin_edit();self.doc.palette.append(c);self.finish_edit()
            self.refresh_palette()

    def sample_color(self,c):
        if c[3] == 0:return
        self.foreground=tuple(c)
        self.refresh_palette()
        self.set_tool('pencil')

    def refresh_preview(self):
        self.preview.setPixmap(self.thumbnail(self.doc.active_frame,175))
        self.canvas.update()

    def refresh_changed_thumbnails(self, indices):
        if self.timeline.count() != len(self.doc.frames):
            self.refresh_timeline()
            return
        for i in indices:
            if 0 <= i < self.timeline.count():
                item = self.timeline.item(i)
                item.setIcon(QIcon(self.thumbnail(i,76)))
        self.refresh_preview()


    def lightweight_refresh(self):
        self.refresh_timeline()
        self.refresh_preview()
        self.update_title()

    def begin_edit(self):
        self.commit_floating()
        self.history.begin(self.doc)

    def finish_edit(self):
        frames = set(self._canvas_dirty_frames)
        self._canvas_dirty_frames.clear()
        if self.history.commit(self.doc):
            self.dirty=True
            if frames:
                self.refresh_changed_thumbnails(frames)
                self.update_title()
            else:
                self.invalidate_render()
                self.lightweight_refresh()

    def undo(self):
        if self.canvas.floating is not None:
            self.cancel_floating()
            return
        if not self.history.undo:return
        self.doc=self.history.back(self.doc)
        self.canvas.selection=None
        self.dirty=True
        self.refresh_all()

    def redo(self):
        if self.canvas.floating is not None:
            self.cancel_floating()
            return
        if not self.history.redo:return
        self.doc=self.history.forward(self.doc)
        self.canvas.selection=None
        self.dirty=True
        self.refresh_all()

    def frame_selected(self,index):
        if self._refreshing or index<0 or index>=len(self.doc.frames):return
        if self.doc.active_frame != index:
            self.commit_floating()
        self.doc.active_frame=index
        self.duration.blockSignals(True)
        self.duration.setValue(self.doc.frames[index].duration_ms)
        self.duration.blockSignals(False)
        self.refresh_preview()

    def duration_changed(self,value):
        if self._refreshing:return
        self.begin_edit()
        self.doc.set_frame_durations(self.selected_frame_indices(), value)
        self.finish_edit()
        if self.preview_playing:
            self.play_timer.setInterval(value)

    def set_frame_fast(self, index):
        if index % len(self.doc.frames) != self.doc.active_frame:
            self.commit_floating()
        self.doc.active_frame=index % len(self.doc.frames)
        self.timeline.blockSignals(True)
        self.timeline.setCurrentRow(self.doc.active_frame)
        self.timeline.blockSignals(False)
        self.duration.blockSignals(True)
        self.duration.setValue(self.doc.frames[self.doc.active_frame].duration_ms)
        self.duration.blockSignals(False)
        self.refresh_preview()

    def previous_frame(self):
        self.set_frame_fast(self.doc.active_frame-1)

    def next_frame(self):
        self.set_frame_fast(self.doc.active_frame+1)

    def duplicate_frame(self):
        selected = self.selected_frame_indices()
        self.begin_edit()
        new_indices = self.doc.duplicate_frames(selected)
        self._frame_selection_override = new_indices
        self.finish_edit()
        self.canvas.selection=None
        self.refresh_all()

    def duplicate_linked(self):
        selected = self.selected_frame_indices()
        self.begin_edit()
        new_indices = self.doc.duplicate_frames(selected, linked=True)
        self._frame_selection_override = new_indices
        self.finish_edit()
        self.canvas.selection=None
        self.refresh_all()

    def insert_holds(self):
        count,ok=QInputDialog.getInt(self,'Insert linked holds',
            'Number of linked exposure frames:',3,1,100)
        if not ok:return
        try:
            self.begin_edit()
            new_indices=self.doc.insert_hold(count)
            self._frame_selection_override=new_indices
            self.finish_edit()
            self.refresh_all()
        except ValueError as exc:
            self.history.cancel()
            QMessageBox.warning(self,'Cannot insert holds',str(exc))

    def copy_frame_block(self):
        chosen=self.selected_frame_indices()
        self.frames_clipboard=self.doc.copy_frames(chosen)
        self.statusBar().showMessage(f'Copied {len(chosen)} animation frames. Ctrl+Alt+V pastes.',3500)

    def paste_frame_block(self):
        if not self.frames_clipboard:return
        try:
            indices=self.selected_frame_indices()
            self.begin_edit()
            newly=self.doc.paste_frames(self.frames_clipboard,after=max(indices))
            self._frame_selection_override=newly
            self.finish_edit()
            self.refresh_all()
        except (ValueError,KeyError) as exc:
            self.history.cancel()
            QMessageBox.warning(self,'Paste frames failed',str(exc))

    def move_selected_frames(self,direction):
        indices=self.selected_frame_indices()
        self.begin_edit()
        new_indices=self.doc.move_frames(indices,direction)
        self._frame_selection_override=new_indices
        self.finish_edit()
        self.refresh_all()

    def reorder_selected_frames(self, insertion):
        indices = self.selected_frame_indices()
        self.begin_edit()
        new_indices = self.doc.reorder_frames(indices, insertion)
        self._frame_selection_override = new_indices
        self.finish_edit()
        self.refresh_all()
        self.statusBar().showMessage(f'Moved {len(indices)} frame(s) to position {new_indices[0]+1}', 2000)

    def link_selected_cels(self):
        indices=self.selected_frame_indices()
        if len(indices)<2:
            self.statusBar().showMessage('Select two or more frames (Ctrl-click/Shift-click), then Link.',3500)
            return
        if self.doc.layer.locked:return
        self.begin_edit()
        source=indices[0]
        for target in indices[1:]:
            self.doc.link_cel(source,target)
        self._frame_selection_override=indices
        self.finish_edit()
        self.refresh_all()

    def unlink_selected_cels(self):
        if self.doc.layer.locked:return
        indices=self.selected_frame_indices()
        self.begin_edit()
        for i in indices:
            self.doc.unlink_cel(i)
        self._frame_selection_override=indices
        self.finish_edit()
        self.refresh_all()

    def add_frame(self):
        self.begin_edit();new_idx=self.doc.add_frame()
        self._frame_selection_override=[new_idx]
        self.finish_edit()
        self.canvas.selection=None
        self.refresh_all()

    def delete_frame(self):
        chosen=self.selected_frame_indices()
        if len(chosen)==len(self.doc.frames):
            self.statusBar().showMessage('Cannot delete the last animation frame.',2000)
            return
        self.begin_edit()
        self.doc.delete_frames(chosen)
        self._frame_selection_override=[self.doc.active_frame]
        self.finish_edit()
        self.canvas.selection=None
        self.refresh_all()

    def toggle_play(self):
        if self.preview_playing:
            self.play_timer.stop()
            self.preview_playing=False
        else:
            self.preview_playing=True
            self.play_timer.setInterval(self.doc.frames[self.doc.active_frame].duration_ms)
            self.play_timer.start()
        self.statusBar().showMessage('Playing' if self.preview_playing else 'Paused',1500)

    def next_playback_frame(self):
        self.next_frame()
        self.play_timer.setInterval(self.doc.frames[self.doc.active_frame].duration_ms)

    def layer_selected(self,index):
        if self._refreshing or index<0:return
        item=self.layer_list.item(index)
        if item is None:return
        self.doc.active_layer=item.data(Qt.ItemDataRole.UserRole)
        self.refresh_layers()

    def layer_item_changed(self,item):
        if self._refreshing:return
        layer=next((x for x in self.doc.layers if x.id==item.data(Qt.ItemDataRole.UserRole)),None)
        if layer:
            self.begin_edit()
            layer.visible=item.checkState()==Qt.CheckState.Checked
            self.finish_edit()

    def layer_locked(self,value):
        if self._refreshing:return
        self.begin_edit();self.doc.layer.locked=value;self.finish_edit();self.refresh_layers()

    def opacity_changed(self,value):
        if self._refreshing:return
        self.doc.layer.opacity=value
        self.opacity_value.setText(f'{round(value*100/255)}%')
        self.refresh_preview()

    def commit_layer_opacity(self):
        self.finish_edit()

    def add_layer(self):
        name,ok=QInputDialog.getText(self,'Add layer','Layer name:',text=f'Layer {len(self.doc.layers)+1}')
        if ok:
            self.begin_edit();self.doc.add_layer(name or 'Layer');self.finish_edit();self.refresh_all()

    def delete_layer(self):
        if len(self.doc.layers)<2:return
        self.begin_edit();self.doc.remove_layer();self.finish_edit();self.refresh_all()

    def move_layer(self,step):
        self.begin_edit();self.doc.shift_layer(step);self.finish_edit();self.refresh_all()

    def rename_layer(self):
        name,ok=QInputDialog.getText(self,'Rename layer','Layer name:',text=self.doc.layer.name)
        if ok and name.strip():
            self.begin_edit();self.doc.layer.name=name.strip();self.finish_edit();self.refresh_layers()

    def toggle_grid(self):
        self.canvas.show_grid=self.action_grid.isChecked();self.canvas.update()

    def toggle_onion(self):
        self.canvas.onion=self.action_onion.isChecked();self.canvas.update()

    def toggle_guides(self):
        self.canvas.show_guides=self.action_guides.isChecked();self.canvas.update()

    def commit_floating(self):
        floating = self.canvas.floating
        if floating is None:
            return False
        self.history.begin(self.doc)
        self.doc.replace_cel(floating.render())
        self.canvas.floating = None
        self.canvas.selection = None
        self.finish_edit()
        self.canvas.update()
        return True

    def cancel_floating(self):
        if self.canvas.floating is None:
            return
        self.canvas.floating = None
        self.canvas.selection = None
        self.canvas.update()
        self.statusBar().showMessage('Floating selection cancelled; pixels unchanged.', 2000)

    def select_all(self):
        self.commit_floating()
        self.canvas.selection=(0,0,self.doc.width,self.doc.height);self.canvas.update()

    def deselect(self):
        self.commit_floating()
        self.canvas.selection=None;self.canvas.update()

    def copy_selection(self):
        if self.canvas.floating is not None:
            selection = self.canvas.floating.pixels.copy()
            x,y = self.canvas.floating.x,self.canvas.floating.y
        else:
            rect=self.canvas.selection or (0,0,self.doc.width,self.doc.height)
            selection=self.doc.cel.crop(rect)
            x,y=rect[:2]
        self.copied=(selection,x,y)
        QApplication.clipboard().setImage(qimage_from_pil(selection))
        self.statusBar().showMessage(f'Copied {selection.width}×{selection.height} logical pixels',1800)

    def cut_selection(self):
        if self.doc.layer.locked:return
        self.commit_floating()
        self.copy_selection()
        rect=self.canvas.selection or (0,0,self.doc.width,self.doc.height)
        self.begin_edit()
        from PIL import ImageDraw
        x0,y0,x1,y1=rect
        ImageDraw.Draw(self.doc.cel).rectangle((x0,y0,x1-1,y1-1),fill=(0,0,0,0))
        self.finish_edit()

    def paste_selection(self):
        if self.doc.layer.locked or not self.doc.layer.visible:return
        self.commit_floating()
        if self.copied:
            img,x,y=self.copied
        else:
            q=QApplication.clipboard().image()
            if q.isNull():return
            img=pil_from_qimage(q)
            x=max(0,(self.doc.width-img.width)//2)
            y=max(0,(self.doc.height-img.height)//2)
        self.canvas.floating=FloatingSelection.pasted(self.doc.cel,img,(x,y))
        self.canvas.selection=None
        self.set_tool('move')
        self.canvas.update()
        self.statusBar().showMessage('Floating paste: drag / arrows to position · Ctrl+Enter commit · Esc cancel',5000)

    def nudge_selection(self,dx,dy):
        if self.doc.layer.locked or not self.doc.layer.visible:return
        if self.canvas.floating is None:
            if self.canvas.selection is None:return
            self.canvas.floating=FloatingSelection.from_cel(self.doc.cel,self.canvas.selection)
        self.canvas.floating.shift(dx,dy)
        self.canvas.update()

    def flip_cel(self,horizontal):
        if self.doc.layer.locked:return
        self.begin_edit()
        self.doc.replace_cel(flip_cel(self.doc.cel,horizontal))
        self.finish_edit()

    def clear_cel(self):
        if self.doc.layer.locked:return
        self.begin_edit();self.doc.cel.paste(blank(self.doc.width,self.doc.height));self.finish_edit()

    def resize_canvas(self):
        w,ok=QInputDialog.getInt(self,'Resize canvas','New logical width:',self.doc.width,1,2048)
        if not ok:return
        h,ok=QInputDialog.getInt(self,'Resize canvas','New logical height:',self.doc.height,1,2048)
        if not ok:return
        self.begin_edit();self.doc.resized(w,h);self.finish_edit()
        self.canvas.selection=None;self.refresh_all()

    def confirm_discard(self):
        if not self.dirty and self.canvas.floating is None:return True
        result=QMessageBox.question(self,'Unsaved work',
          'Save changes to the current project?',
          QMessageBox.StandardButton.Save|QMessageBox.StandardButton.Discard|QMessageBox.StandardButton.Cancel,
          QMessageBox.StandardButton.Save)
        if result==QMessageBox.StandardButton.Cancel:return False
        if result==QMessageBox.StandardButton.Save:return self.save_project()
        # Explicit discard must not reappear as a recovery offer next launch.
        self.recovery.discard_token(self.recovery.token_for(
            self.file_path, self._recovery_session))
        if self._recovered_entry is not None:
            self.recovery.discard(self._recovered_entry)
            self._recovered_entry = None
        return True

    def new_project(self):
        if not self.confirm_discard():return
        dialog=NewDocumentDialog(self)
        if dialog.exec()!=QDialog.DialogCode.Accepted:return
        self.set_document(Document(dialog.w.value(),dialog.h.value(),dialog.name.text() or 'Untitled'))

    def open_project(self):
        if not self.confirm_discard():return
        path,_=QFileDialog.getOpenFileName(self,'Open Mellow Studio project','','Mellow projects (*.mellowzip)')
        if not path:return
        try:
            self.set_document(project_load(path),Path(path))
        except Exception as exc:
            QMessageBox.critical(self,'Project could not be opened',str(exc))

    def open_mellow(self):
        if self.confirm_discard():
            self.set_document(mellow_document())

    def import_measured_sequence(self):
        """Calibrate once, then convert an entire screenshot sequence to true pixels."""
        import re
        paths,_=QFileDialog.getOpenFileNames(self,'Choose reference frames (same measured grid)',
                     '', 'Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)')
        if not paths:return
        paths=sorted(paths,key=lambda p:[int(t) if t.isdigit() else t.lower()
                                 for t in re.split(r'(\d+)',Path(p).name)])
        try:
            with Image.open(paths[0]) as im:
                first=im.convert('RGBA')
            dialog=ImportDialog(self,first,(self.doc.width,self.doc.height))
            if dialog.exec()!=QDialog.DialogCode.Accepted:return
            cfg=dialog.cfg
            frames=[dialog.result_image]
            for path in paths[1:]:
                with Image.open(path) as im:src=im.convert('RGBA')
                if src.size != first.size:
                    raise ValueError(f'{Path(path).name}: reference size differs. All frames must use the same calibrated screen pixel grid.')
                frames.append(cfg.extract(src,['median','center','dominant'][dialog.sampling.currentIndex()]))
            if not self.confirm_discard():return
            doc=Document(cfg.cols,cfg.rows,Path(paths[0]).stem+' · measured animation')
            doc.cel.paste(frames[0])
            for image in frames[1:]:
                doc.add_frame()
                doc.cel.paste(image)
            doc.active_frame=0
            doc.guides=[{'name':'Shared measured reference grid',
                         'pitch_x':cfg.pitch_x,'pitch_y':cfg.pitch_y,
                         'origin_x':cfg.origin_x,'origin_y':cfg.origin_y}]
            self.set_document(doc)
            self.statusBar().showMessage(f'{len(frames)} measured reference images converted into editable native-pixel frames.',5000)
        except Exception as exc:
            QMessageBox.warning(self,'Measured sequence import failed',str(exc))

    def import_spritesheet(self):
        path,_=QFileDialog.getOpenFileName(self,'Choose native-pixel spritesheet','',
                                           'Images (*.png *.bmp *.gif *.webp)')
        if not path:return
        try:
            with Image.open(path) as im:sheet=im.convert('RGBA')
            w,ok=QInputDialog.getInt(self,'Split spritesheet','Width of one frame in TRUE pixels:',
                       min(64,sheet.width),1,sheet.width)
            if not ok:return
            h,ok=QInputDialog.getInt(self,'Split spritesheet','Height of one frame in TRUE pixels:',
                       min(64,sheet.height),1,sheet.height)
            if not ok:return
            cols,rows=sheet.width//w,sheet.height//h
            if cols*rows>2000 or cols*rows<1:
                raise ValueError('Frame count must be between 1 and 2000.')
            if sheet.width%w or sheet.height%h:
                answer=QMessageBox.question(self,'Uneven spritesheet',
                   'Image dimensions are not exact multiples of the frame size. Discard the incomplete right/bottom edges?',
                   QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.Cancel)
                if answer!=QMessageBox.StandardButton.Yes:return
            if not self.confirm_discard():return
            doc=Document(w,h,Path(path).stem+' · sliced')
            for index in range(cols*rows):
                if index:doc.add_frame()
                x,y=(index%cols)*w,(index//cols)*h
                doc.cel.paste(sheet.crop((x,y,x+w,y+h)))
            doc.active_frame=0
            self.set_document(doc)
            self.statusBar().showMessage(f'Imported {cols*rows} editable frames in row-major order.',5000)
        except Exception as exc:
            QMessageBox.warning(self,'Spritesheet import failed',str(exc))

    def import_raw_png(self):
        if not self.confirm_discard():return
        path,_=QFileDialog.getOpenFileName(self,'Import native-resolution image','','Images (*.png *.bmp *.gif *.webp)')
        if not path:return
        try:
            with Image.open(path) as im:
                src=im.convert('RGBA')
            self.set_document(Document(src.width,src.height,Path(path).stem))
            self.doc.cel.paste(src)
            self.refresh_all()
        except Exception as exc:QMessageBox.warning(self,'Image import failed',str(exc))

    def import_reference(self):
        path,_=QFileDialog.getOpenFileName(self,'Choose image to measure','','Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)')
        if not path:return
        try:
            with Image.open(path) as im:source=im.convert('RGBA')
            dialog=ImportDialog(self,source,(self.doc.width,self.doc.height))
            if dialog.exec()!=QDialog.DialogCode.Accepted:return
            if not self.confirm_discard():return
            src=dialog.result_image
            self.set_document(Document(src.width,src.height,Path(path).stem+' · measured'))
            self.doc.cel.paste(src)
            self.doc.guides=[{'name':'Reference calibration','pitch_x':dialog.cfg.pitch_x,
                'pitch_y':dialog.cfg.pitch_y,'origin_x':dialog.cfg.origin_x,
                'origin_y':dialog.cfg.origin_y,'source_size':[source.width,source.height]}]
            self.refresh_all()
        except Exception as exc:QMessageBox.warning(self,'Reference import failed',str(exc))

    def set_document(self,doc,file_path=None):
        if self.preview_playing:self.toggle_play()
        self.doc=doc
        self.file_path=file_path
        self.dirty=(file_path is None)
        self.history=History()
        self._recovery_session = uuid4().hex
        self._recovered_entry = None
        self.invalidate_render()
        self._canvas_dirty_frames.clear()
        self.canvas.selection=None
        self.canvas.floating=None
        self.copied=None
        self.frames_clipboard=[]
        self._frame_selection_override=[doc.active_frame]
        self.refresh_all()
        self.zoom_fit()

    def update_title(self):
        self.setWindowTitle(('* ' if self.dirty else '')+self.doc.name+' — '+APP_TITLE)

    def _save_to_path(self, path: Path) -> bool:
        self.commit_floating()
        previous_path = self.file_path
        previous_token = self.recovery.token_for(previous_path, self._recovery_session)
        try:
            project_save(self.doc, path)
        except Exception as exc:
            # Never switch project identity or clear the dirty flag on failed save.
            QMessageBox.critical(self, 'Save failed', str(exc))
            return False
        self.file_path = path
        self.dirty = False
        self.recovery.discard_token(previous_token)
        if self._recovered_entry is not None:
            self.recovery.discard(self._recovered_entry)
            self._recovered_entry = None
        self.update_title()
        self.statusBar().showMessage('Project saved · ' + str(path),3500)
        return True

    def save_project(self):
        if self.file_path is None:
            return self.save_project_as()
        return self._save_to_path(self.file_path)

    def save_project_as(self):
        path,_=QFileDialog.getSaveFileName(self,'Save Mellow Studio project',
                    (self.doc.name.replace('·','-').replace('×','x')+'.mellowzip'),
                    'Mellow Studio project (*.mellowzip)')
        if not path:return False
        p=Path(path)
        if p.suffix.lower()!='.mellowzip':p=p.with_suffix('.mellowzip')
        return self._save_to_path(p)

    def export_png(self):
        path,_=QFileDialog.getSaveFileName(self,'Export current frame',self.doc.name+'.png','PNG image (*.png)')
        if path:
            self.doc.composite().save(path)
            self.statusBar().showMessage('Exported actual native-resolution PNG.',3000)

    def export_sheet(self):
        if not self.doc.frames:return
        path,_=QFileDialog.getSaveFileName(self,'Export horizontal spritesheet',self.doc.name+'_sheet.png','PNG image (*.png)')
        if not path:return
        horizontal=QMessageBox.question(self,'Spritesheet layout','Arrange frames horizontally? (No = vertical)',
                             QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)==QMessageBox.StandardButton.Yes
        w,h=self.doc.width,self.doc.height
        sheet=blank(w*len(self.doc.frames) if horizontal else w,
                    h if horizontal else h*len(self.doc.frames))
        for i in range(len(self.doc.frames)):
            sheet.paste(self.doc.composite(i),(w*i if horizontal else 0,h*i if not horizontal else 0))
        sheet.save(path)
        metadata={'frame_width':w,'frame_height':h,'frame_count':len(self.doc.frames),
                  'layout':'horizontal' if horizontal else 'vertical',
                  'durations_ms':[f.duration_ms for f in self.doc.frames]}
        Path(path).with_suffix('.json').write_text(json.dumps(metadata,indent=2),encoding='utf8')
        self.statusBar().showMessage('Saved spritesheet PNG + frame metadata JSON.',3400)

    def export_gif(self):
        path,_=QFileDialog.getSaveFileName(self,'Export animation GIF',self.doc.name+'.gif','GIF animation (*.gif)')
        if not path:return
        frames=[self.doc.composite(i) for i in range(len(self.doc.frames))]
        frames[0].save(path,save_all=True,append_images=frames[1:],
                       duration=[f.duration_ms for f in self.doc.frames],loop=0,disposal=2)
        self.statusBar().showMessage('Animated GIF saved.',2500)

    def export_frames(self):
        folder=QFileDialog.getExistingDirectory(self,'Choose export folder')
        if not folder:return
        d=Path(folder)
        for i in range(len(self.doc.frames)):
            self.doc.composite(i).save(d/f'{self.doc.name}_frame_{i+1:04d}.png')
        self.statusBar().showMessage(f'Exported {len(self.doc.frames)} PNG frames.',3500)

    def autosave(self):
        if not self.dirty and self.canvas.floating is None:
            return
        try:
            if self.canvas.floating is not None:
                recovered = self.doc.copy()
                recovered.replace_cel(self.canvas.floating.render())
            else:
                recovered = self.doc
            self.recovery.write(recovered, self.file_path, self._recovery_session)
            self.statusBar().showMessage('Project-specific recovery snapshot saved.',1500)
        except Exception:
            self.statusBar().showMessage('Recovery snapshot unavailable — check disk.',3000)

    def recover_autosave(self):
        entries = self.recovery.entries()
        if not entries:
            # Upgrade path for pre-0.2.2 single-slot crash recovery.
            legacy = self.recovery.root.parent / 'mellow_autorecover.mellowzip'
            if not legacy.is_file():
                self.statusBar().showMessage('No recovery snapshots found.',3000)
                return
            choice = QMessageBox.question(self,'Legacy recovery found',
                'A recovery from Mellow Studio 0.2.1 is available. Open it?',
                QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
            if choice == QMessageBox.StandardButton.Yes:
                try:
                    recovered = project_load(legacy)
                    if self.confirm_discard():
                        self.set_document(recovered)
                        self.dirty = True
                        self.update_title()
                except Exception as exc:
                    QMessageBox.warning(self,'Recovery failed',str(exc))
            return
        options = [f'{datetime.fromtimestamp(e.created_at):%Y-%m-%d %H:%M}  ·  '
                   f'{e.project_name}  ·  {e.project_path or "Unsaved session"}'
                   for e in entries]
        selected, ok = QInputDialog.getItem(self, 'Restore recovery snapshot',
            'Choose a project-specific snapshot to reopen:',options,0,False)
        if not ok:
            return
        entry = entries[options.index(selected)]
        try:
            recovered = project_load(entry.archive)
        except Exception as exc:
            QMessageBox.warning(self,'Recovery failed',str(exc))
            return
        if not self.confirm_discard():
            return
        self.set_document(recovered, Path(entry.project_path) if entry.project_path else None)
        self._recovered_entry = entry
        self.dirty = True
        self.update_title()
        self.statusBar().showMessage('Recovery opened. Save to keep recovered changes.',5000)

    def restore_workspace(self):
        geometry=self.settings.value('window/geometry')
        state=self.settings.value('window/state')
        if geometry:self.restoreGeometry(geometry)
        if state:self.restoreState(state)

    def reset_layout(self):
        for dock in self._view_docks:dock.show()
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea,self.timeline_dock)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea,self.layer_dock)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea,self.palette_dock)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea,self.preview_dock)
        self.tabifyDockWidget(self.layer_dock,self.palette_dock)
        self.layer_dock.raise_()

    def closeEvent(self,event):
        if not self.confirm_discard():
            event.ignore();return
        self.settings.setValue('window/geometry',self.saveGeometry())
        self.settings.setValue('window/state',self.saveState())
        if not self.dirty and self.canvas.floating is None:
            self.recovery.discard_token(self.recovery.token_for(
                self.file_path, self._recovery_session))
        super().closeEvent(event)

    def show_shortcuts(self):
        QMessageBox.information(self,'Keyboard shortcuts',
          'Tools: B pencil, D 2-color dither, E eraser, F bucket, I eyedropper, L line, R rectangle, '
          'O ellipse, M selection, V move, H pan.\n\n'
          'Ctrl+D duplicate selected frames · Ctrl+Shift+D linked exposures · Ctrl+Alt+H linked holds.\n'
          'Ctrl/Shift-click multiple timeline frames · Ctrl+Alt+C/V copy/paste frame blocks.\n'
          'Drag selected timeline frames to reorder · Ctrl+Alt+Left/Right moves one slot.\n'
          'Alt+N blank frame · Space playback.\n'
          'Ctrl+Z/Y undo/redo · Ctrl+C/X/V copy/cut/paste · Ctrl+A select all · '
          'Ctrl+Shift+A deselect · Arrow keys position a floating selection (Shift = 10).\n'
          'Ctrl+Enter commits floating pixels · Esc cancels the uncommitted float.\n'
          'Ctrl+N/O/S new/open/save · Ctrl+I measured import · Ctrl+E export PNG.\n'
          'G show grid · Shift+O onion skin · Ctrl+mouse wheel zoom · middle drag pan · '
          '[ and ] brush size · right mouse secondary color.\n\n'
          'Controls and panels are dockable and stored between sessions.')

    def about(self):
        QMessageBox.about(self,'About Mellow Studio',
          f'Mellow Studio v{VERSION}\nNative Python / Qt desktop sprite art & animation workstation.\n'
          'Built around measured logical pixels and rapid frame-to-frame work.')


def main():
    app=QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)
    app.setOrganizationName('MellowStudio')
    app.setStyle('Fusion')
    app.setStyleSheet('''
      QMainWindow, QDialog, QWidget { background-color:#252d3b; color:#ebf0f7; }
      QMenuBar, QMenu, QStatusBar, QToolBar, QDockWidget { background-color:#202735; color:#ebf0f7; }
      QMenuBar::item:selected, QMenu::item:selected {background:#455371;}
      QDockWidget::title {background:#333e52; padding:7px 8px; font-weight:bold;}
      QPushButton, QToolButton {background:#39465b; border:1px solid #52617c; border-radius:4px; padding:5px;}
      QPushButton:hover, QToolButton:hover {background:#4d5e7a;}
      QToolButton:checked {background:#466f9c; border:1px solid #9bcdf7;}
      QLineEdit,QSpinBox,QDoubleSpinBox,QComboBox,QListWidget {background:#202735; border:1px solid #52617c; border-radius:3px; color:#edf2fc; padding:3px;}
      QListWidget::item:selected {background:#466f9c;}
      QLabel, QCheckBox {color:#edf1f8;}
      QScrollBar {background:#1d2634;}
      QScrollBar::handle {background:#536781; border-radius:3px;}
    ''')
    window=Editor()
    window.show()
    sys.exit(app.exec())


if __name__=='__main__':
    main()
