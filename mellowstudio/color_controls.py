"""Compact, immediately usable pixel-art color field (no modal dialog needed)."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QColor, QImage, QPainter, QPen
from PySide6.QtWidgets import QWidget, QSizePolicy


class SaturationValueField(QWidget):
    """Click/drag horizontally for saturation, vertically for brightness."""
    colorChanged = Signal(QColor)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._hue = 0
        self._saturation = 255
        self._value = 255
        self._gradient: QImage | None = None
        self._gradient_key = None
        self.setObjectName("SaturationValueField")
        self.setMinimumSize(170, 120)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(140)
        self.setAccessibleName("Color saturation and brightness")
        self.setToolTip("Move left/right for saturation; up/down for brightness.")

    def set_color(self, color: QColor, keep_hue=False):
        if not color.isValid():
            return
        hue = color.hsvHue()
        if hue >= 0 and not keep_hue:
            self.set_hue(hue)
        self._saturation = color.hsvSaturation()
        self._value = color.value()
        self.update()

    def set_hue(self, hue: int):
        hue = max(0, min(359, int(hue)))
        if hue != self._hue:
            self._hue = hue
            self._gradient_key = None
            self.update()

    def current_color(self) -> QColor:
        return QColor.fromHsv(self._hue, self._saturation, self._value)

    def _select_point(self, point: QPoint):
        self._saturation = round(255 * max(0, min(self.width()-1, point.x())) / max(1,self.width()-1))
        self._value = round(255 * (1 - max(0, min(self.height()-1, point.y())) / max(1,self.height()-1)))
        self.update()
        self.colorChanged.emit(self.current_color())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._select_point(event.position().toPoint())
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._select_point(event.position().toPoint())
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def paintEvent(self, event):
        w, h = max(1,self.width()), max(1,self.height())
        key=(w,h,self._hue)
        if self._gradient_key != key:
            image = QImage(w,h,QImage.Format.Format_RGB32)
            for y in range(h):
                val=round(255*(1-y/max(1,h-1)))
                for x in range(w):
                    sat=round(255*x/max(1,w-1))
                    image.setPixelColor(x,y,QColor.fromHsv(self._hue,sat,val))
            self._gradient=image
            self._gradient_key=key
        painter=QPainter(self)
        painter.drawImage(0,0,self._gradient)
        cx=round(self._saturation*max(0,w-1)/255)
        cy=round((255-self._value)*max(0,h-1)/255)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QPen(QColor("#202c35"), 3))
        painter.drawEllipse(QPoint(cx,cy),6,6)
        painter.setPen(QPen(QColor("#ffffff"), 2))
        painter.drawEllipse(QPoint(cx,cy),6,6)
        painter.end()
