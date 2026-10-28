"""Crisp vector toolbar icons, rendered locally with Qt (no font glyph dependencies)."""
from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap, QPolygon


def tool_icon(tool: str, size: int = 26) -> QIcon:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.scale(size/26, size/26)
    painter.setPen(QPen(QColor('#d8e5ed'), 2.0, Qt.PenStyle.SolidLine,
                        Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    if tool == 'pencil':
        painter.translate(13,13); painter.rotate(42)
        painter.drawRect(QRect(-4,-10,8,17))
        painter.drawPolygon(QPolygon([QPoint(-4,7),QPoint(4,7),QPoint(0,12)]))
        painter.drawLine(-4,-5,4,-5)
    elif tool == 'dither':
        painter.setPen(Qt.PenStyle.NoPen)
        for y in range(4):
            for x in range(4):
                if (x+y)%2==0:
                    painter.fillRect(4+x*5,4+y*5,5,5,QColor('#d8e5ed'))
    elif tool == 'eraser':
        painter.translate(13,13); painter.rotate(-40)
        painter.drawRoundedRect(QRect(-8,-6,16,12),2,2)
        painter.drawLine(1,-6,1,6)
    elif tool == 'bucket':
        painter.translate(13,12); painter.rotate(-42)
        painter.drawRect(QRect(-7,-6,14,12))
        painter.rotate(42)
        painter.drawEllipse(QRect(6,7,3,3))
    elif tool == 'picker':
        painter.translate(13,13); painter.rotate(42)
        painter.drawRoundedRect(QRect(-3,-8,6,16),2,2)
        painter.drawLine(-6,-8,6,-8)
        painter.drawLine(-2,8,-2,11)
    elif tool == 'line':
        painter.drawLine(5,21,21,5)
        painter.drawEllipse(QRect(3,19,4,4)); painter.drawEllipse(QRect(19,3,4,4))
    elif tool == 'rectangle':
        painter.drawRect(QRect(5,6,16,14))
    elif tool == 'ellipse':
        painter.drawEllipse(QRect(4,6,18,14))
    elif tool == 'marquee':
        painter.setPen(QPen(QColor('#d8e5ed'),2,Qt.PenStyle.DashLine))
        painter.drawRect(QRect(4,4,18,18))
    elif tool == 'move':
        painter.drawLine(13,3,13,23);painter.drawLine(3,13,23,13)
        for a,b,c in [((13,3),(10,7),(16,7)),((13,23),(10,19),(16,19)),
                      ((3,13),(7,10),(7,16)),((23,13),(19,10),(19,16))]:
            painter.drawLine(*a,*b); painter.drawLine(*a,*c)
    elif tool == 'pan':
        painter.drawRoundedRect(QRect(6,10,14,12),4,4)
        painter.drawLine(8,12,8,4);painter.drawLine(12,10,12,3)
        painter.drawLine(16,10,16,5);painter.drawLine(20,12,20,9)
    else:
        painter.drawEllipse(QRect(5,5,16,16))
    painter.end()
    return QIcon(pixmap)
