"""Integer-zoom, pixel-exact Qt canvas with tools and animation onion skins."""
from __future__ import annotations

from PIL import Image
from PySide6.QtCore import Qt, Signal, QPoint, QRect, QSize
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget, QAbstractScrollArea

from .model import draw_stroke, draw_shape, bucket_fill, FloatingSelection


def qimage_from_pil(image: Image.Image) -> QImage:
    im = image.convert('RGBA')
    bits = im.tobytes()
    return QImage(bits, im.width, im.height, im.width * 4, QImage.Format.Format_RGBA8888).copy()


def pil_from_qimage(image: QImage) -> Image.Image:
    img = image.convertToFormat(QImage.Format.Format_RGBA8888)
    return Image.frombytes('RGBA', (img.width(), img.height()), bytes(img.bits()))


class PixelCanvas(QWidget):
    changed = Signal()
    cursorMoved = Signal(int, int)
    sampled = Signal(tuple)
    zoomChanged = Signal(int)

    def __init__(self, editor):
        super().__init__()
        self.editor = editor
        self.zoom = 12
        self.show_grid = True
        self.show_guides = True
        self.onion = True
        self.sym_x = False
        self.sym_y = False
        self.filled_shapes = False
        self.selection: tuple[int, int, int, int] | None = None
        self.floating: FloatingSelection | None = None
        self._floating_drag_origin = (0, 0)
        self.dragging = False
        self.drag_origin = (0, 0)
        self.last_point = (0, 0)
        self.before_cel: Image.Image | None = None
        self._pan_start = None
        self._pan_bar_start = None
        self._tool_override = None
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.adjust_size()

    @property
    def doc(self):
        return self.editor.doc

    def adjust_size(self):
        self.setFixedSize(self.doc.width * self.zoom, self.doc.height * self.zoom)
        self.update()

    def set_zoom(self, value: int):
        self.zoom = max(1, min(64, int(value)))
        self.adjust_size()
        self.zoomChanged.emit(self.zoom)

    def pixel_at(self, pos: QPoint) -> tuple[int, int]:
        return (max(0, min(self.doc.width - 1, int(pos.x() // self.zoom))),
                max(0, min(self.doc.height - 1, int(pos.y() // self.zoom))))

    def scroll_area(self):
        w = self.parentWidget()
        while w is not None:
            if isinstance(w, QAbstractScrollArea):
                return w
            w = w.parentWidget()
        return None

    def paintEvent(self, event):
        d, s = self.doc, self.zoom
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        p.fillRect(self.rect(), QColor('#313746'))
        cell = max(1, 8 * s)
        for y in range(0, self.height(), cell):
            for x in range(0, self.width(), cell):
                if ((x // cell) + (y // cell)) % 2 == 0:
                    p.fillRect(x, y, cell, cell, QColor('#404859'))
        if self.onion and len(d.frames) > 1:
            for delta, opacity in [(-1, .20), (1, .15)]:
                f = d.active_frame + delta
                if 0 <= f < len(d.frames):
                    image = qimage_from_pil(d.composite(f))
                    p.setOpacity(opacity)
                    p.drawImage(QRect(0, 0, self.width(), self.height()), image)
            p.setOpacity(1.0)
        preview_cel = self.floating.render() if self.floating is not None else None
        p.drawImage(QRect(0, 0, self.width(), self.height()),
                    qimage_from_pil(d.composite(cel_override=preview_cel)))
        if self.show_grid and s >= 6:
            p.setPen(QPen(QColor(13, 23, 37, 100), 1))
            for x in range(d.width + 1):
                px = x * s
                p.drawLine(px, 0, px, self.height())
            for y in range(d.height + 1):
                py = y * s
                p.drawLine(0, py, self.width(), py)
        if self.show_guides:
            for guide in d.guides:
                if 'points' not in guide:
                    continue
                p.setPen(QPen(QColor('#f6d37b'), 2))
                for x, y in guide['points']:
                    p.drawRect(x*s+1, y*s+1, max(1, s-2), max(1, s-2))
        outline = self.floating.rect if self.floating is not None else self.selection
        if outline:
            x0, y0, x1, y1 = outline
            p.setPen(QPen(QColor('#ffe18e'), 2, Qt.PenStyle.DashLine))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRect(QRect(x0*s, y0*s, (x1-x0)*s, (y1-y0)*s))
        p.end()

    def _start_pan(self, event):
        scroll = self.scroll_area()
        if scroll:
            self._pan_start = event.globalPosition().toPoint()
            self._pan_bar_start = (scroll.horizontalScrollBar().value(),
                                   scroll.verticalScrollBar().value())
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mousePressEvent(self, event):
        self.setFocus()
        if event.button() == Qt.MouseButton.MiddleButton or self.editor.space_pan or self.editor.tool == 'pan':
            self._start_pan(event)
            return
        if event.button() not in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):
            return
        point = self.pixel_at(event.position().toPoint())
        self.cursorMoved.emit(*point)
        tool = self.editor.tool
        if tool == 'picker':
            self.sampled.emit(tuple(self.doc.composite().getpixel(point)))
            return
        if tool == 'marquee':
            self.editor.commit_floating()
            self.dragging = True
            self.drag_origin = point
            self.selection = (*point, point[0]+1, point[1]+1)
            self.update()
            return
        if self.doc.layer.locked or not self.doc.layer.visible:
            self.editor.statusBar().showMessage('Unlock/show this layer to paint.', 2800)
            return
        if tool == 'move':
            if self.floating is None and self.selection is not None:
                self.floating = FloatingSelection.from_cel(self.doc.cel, self.selection)
            if self.floating is None:
                return
            self.dragging = True
            self.drag_origin = point
            self.last_point = point
            self._floating_drag_origin = (self.floating.x, self.floating.y)
            self.update()
            return
        if self.floating is not None:
            self.editor.commit_floating()
            self.selection = None
        self.editor.history.begin(self.doc)
        self.dragging = True
        self.drag_origin = point
        self.last_point = point
        self.before_cel = self.doc.cel.copy()
        self._tool_override = tool
        if event.button() == Qt.MouseButton.RightButton:
            self._tool_override = 'eraser' if tool == 'eraser' else 'secondary-pencil'
        self._apply(point)

    def _paint_color(self):
        if self._tool_override == 'eraser':
            return (0, 0, 0, 0)
        return self.editor.secondary if self._tool_override == 'secondary-pencil' else self.editor.foreground

    def _apply(self, point):
        tool = self._tool_override
        img = self.doc.cel
        color = self._paint_color()
        if tool in ('pencil', 'secondary-pencil', 'eraser'):
            draw_stroke(img, [self.last_point, point], color,
                        self.editor.brush_size, self.sym_x, self.sym_y)
        elif tool == 'bucket':
            bucket_fill(img, point, color, self.editor.contiguous)
        elif tool in ('line', 'rectangle', 'ellipse'):
            img.paste(self.before_cel)
            draw_shape(img, tool, self.drag_origin, point, color, self.filled_shapes)
        self.last_point = point
        self.update()
        self.changed.emit()

    def mouseMoveEvent(self, event):
        if self._pan_start is not None:
            scroll = self.scroll_area()
            if scroll:
                dp = event.globalPosition().toPoint() - self._pan_start
                scroll.horizontalScrollBar().setValue(self._pan_bar_start[0] - dp.x())
                scroll.verticalScrollBar().setValue(self._pan_bar_start[1] - dp.y())
            return
        pt = self.pixel_at(event.position().toPoint())
        self.cursorMoved.emit(*pt)
        if not self.dragging:
            return
        if self.editor.tool == 'marquee':
            x0, x1 = sorted([self.drag_origin[0], pt[0]])
            y0, y1 = sorted([self.drag_origin[1], pt[1]])
            self.selection = (x0, y0, x1+1, y1+1)
            self.update()
        elif self.editor.tool == 'move' and self.floating is not None:
            self.floating.move_to(self._floating_drag_origin[0] + pt[0] - self.drag_origin[0],
                                  self._floating_drag_origin[1] + pt[1] - self.drag_origin[1])
            self.update()
        elif self._tool_override != 'bucket':
            self._apply(pt)

    def mouseReleaseEvent(self, event):
        if self._pan_start is not None:
            self._pan_start = None
            self.setCursor(Qt.CursorShape.CrossCursor)
            return
        if not self.dragging:
            return
        self.dragging = False
        if self.editor.tool not in ('marquee', 'move'):
            self.editor.finish_edit()
        self.before_cel = None
        self._tool_override = None
        self.update()

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.set_zoom(self.zoom + (1 if event.angleDelta().y() > 0 else -1))
            event.accept()
            return
        super().wheelEvent(event)
