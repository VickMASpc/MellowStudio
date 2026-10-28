"""Measured screenshot import dialog with live calibrated grid overlay."""
from __future__ import annotations
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QPen, QColor
from PySide6.QtWidgets import (QDialog, QWidget, QSpinBox, QDoubleSpinBox, QGridLayout,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QComboBox,
    QGroupBox, QMessageBox, QInputDialog)
from PIL import Image
from .canvas import qimage_from_pil
from .calibration import (GridCalibration, default_calibration, align_to_edges,
                          MELLOW_EXACT, suggest_grids)


class ReferencePreview(QWidget):
    clicked = Signal(float, float)
    hovered = Signal(float, float)
    shifted = Signal(float, float)
    shiftEnded = Signal()

    def __init__(self, image, cfg):
        super().__init__()
        self.image = image
        self.cfg = cfg
        self.zoom = 2
        self._right_drag = None
        self.setMouseTracking(True)
        self.resize_view()

    def resize_view(self):
        self.setFixedSize(self.image.width*self.zoom, self.image.height*self.zoom)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self._right_drag = event.position()
            self.shifted.emit(0.0, 0.0)
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(event.position().x()/self.zoom, event.position().y()/self.zoom)

    def mouseMoveEvent(self, event):
        self.hovered.emit(event.position().x()/self.zoom, event.position().y()/self.zoom)
        if self._right_drag is not None:
            delta = event.position() - self._right_drag
            self.shifted.emit(delta.x()/self.zoom, delta.y()/self.zoom)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self._right_drag = None
            self.shiftEnded.emit()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        p.drawImage(self.rect(), qimage_from_pil(self.image))
        p.setPen(QPen(QColor(0, 220, 255, 175), 1))
        xs, ys = self.cfg.bounds_x(), self.cfg.bounds_y()
        for x in xs:
            ix = round(x * self.zoom)
            p.drawLine(ix, 0, ix, self.height())
        for y in ys:
            iy = round(y * self.zoom)
            p.drawLine(0, iy, self.width(), iy)
        p.setPen(QPen(QColor('#fdd073'), 2))
        p.drawLine(round(self.cfg.origin_x*self.zoom), 0,
                   round(self.cfg.origin_x*self.zoom), self.height())
        p.drawLine(0, round(self.cfg.origin_y*self.zoom),
                   self.width(), round(self.cfg.origin_y*self.zoom))
        p.end()


class ImportDialog(QDialog):
    def __init__(self, parent, image: Image.Image, initial_size=(32, 32)):
        super().__init__(parent)
        self.setWindowTitle('Measured-grid reference import')
        self.resize(1030, 740)
        self.image = image.convert('RGBA')
        self.cfg = default_calibration(self.image, *initial_size)
        self.measuring = ''
        self.first_point = None
        self.result_image = None
        self._building = True

        root = QHBoxLayout(self)
        left = QVBoxLayout()
        root.addLayout(left, 1)
        self.view = ReferencePreview(self.image, self.cfg)
        scroll = QScrollArea()
        scroll.setWidget(self.view)
        scroll.setWidgetResizable(False)
        scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left.addWidget(scroll, 1)
        self.hover_label = QLabel('Hover: source pixel → logical cell')
        left.addWidget(self.hover_label)
        self.view.hovered.connect(self.hovered)
        self.view.clicked.connect(self.measured_click)
        self.view.shifted.connect(self.drag_grid)
        self.view.shiftEnded.connect(lambda:setattr(self,'_drag_base',None))
        self._drag_base = None

        settings = QVBoxLayout()
        root.addLayout(settings)
        settings.setSpacing(9)
        explanation = QLabel('ONE measured cell = ONE actual sprite pixel.\n'
            'Adjust the overlay until it follows the original pixel boundaries.\n'
            'Grid changes do not modify the reference image.')
        explanation.setWordWrap(True)
        explanation.setMaximumWidth(310)
        settings.addWidget(explanation)
        g = QGroupBox('Native grid and measurement')
        grid = QGridLayout(g)
        settings.addWidget(g)

        def int_spin(value, lo, hi):
            w = QSpinBox();w.setRange(lo,hi);w.setValue(value);return w
        def dbl_spin(value, lo, hi, digits=4):
            w = QDoubleSpinBox();w.setRange(lo,hi);w.setDecimals(digits);w.setSingleStep(.1);w.setValue(value);return w

        self.cols = int_spin(self.cfg.cols, 1, 2048)
        self.rows = int_spin(self.cfg.rows, 1, 2048)
        self.pitch_x = dbl_spin(self.cfg.pitch_x, .5, 2000)
        self.pitch_y = dbl_spin(self.cfg.pitch_y, .5, 2000)
        self.origin_x = dbl_spin(0, -5000, 5000)
        self.origin_y = dbl_spin(0, -5000, 5000)
        controls = [('Columns', self.cols), ('Rows', self.rows), ('Cell pitch X', self.pitch_x),
                    ('Cell pitch Y', self.pitch_y), ('Grid origin X', self.origin_x),
                    ('Grid origin Y', self.origin_y)]
        for i,(title, w) in enumerate(controls):
            grid.addWidget(QLabel(title), i, 0)
            grid.addWidget(w, i, 1)
            w.valueChanged.connect(self.parameters_changed)

        settings.addWidget(QLabel('Manual measurement: click two boundaries, N cells apart.'))
        line = QHBoxLayout()
        settings.addLayout(line)
        self.measure_cells = int_spin(1, 1, 1000)
        self.measure_cells.setToolTip('Number of original sprite cells between clicked boundaries')
        line.addWidget(QLabel('N cells'))
        line.addWidget(self.measure_cells)
        settings.addWidget(QLabel('Logical index of FIRST boundary (0 = left/top edge):'))
        self.measure_index=int_spin(0,0,2048)
        settings.addWidget(self.measure_index)
        for axis in ('X','Y'):
            b=QPushButton('Measure '+axis)
            b.clicked.connect(lambda _, a=axis: self.start_measure(a))
            line.addWidget(b)

        detect = QPushButton('Suggest native grid size + pitch (experimental)')
        detect.setToolTip('Detect repeated screenshot cell boundaries; review confidence and verify manually')
        detect.clicked.connect(self.suggest_auto)
        settings.addWidget(detect)
        settings.addWidget(QLabel('Right-drag reference preview to align grid origin manually.'))
        a = QPushButton('Auto-align to edge contrast (keep cell counts)')
        a.clicked.connect(self.align_auto)
        settings.addWidget(a)
        b = QPushButton('Fit pitch to reference dimensions')
        b.clicked.connect(self.fit_pitch)
        settings.addWidget(b)
        c = QPushButton('Use measured Mellow 41 × 55 preset')
        c.clicked.connect(self.mellow_preset)
        settings.addWidget(c)
        zoom_line=QHBoxLayout()
        zoom_line.addWidget(QLabel('Preview zoom'))
        zv=int_spin(2,1,8);zv.valueChanged.connect(self.set_zoom);zoom_line.addWidget(zv)
        settings.addLayout(zoom_line)
        settings.addWidget(QLabel('Sampling (edges are excluded):'))
        self.sampling=QComboBox()
        self.sampling.addItems(['Median interior (scaled screenshots)', 'Center pixel (lossless reference)',
                                'Nearest real interior color (no blended color)'])
        settings.addWidget(self.sampling)
        self.status = QLabel('Ready to measure')
        self.status.setWordWrap(True)
        settings.addWidget(self.status)
        settings.addStretch()
        actions=QHBoxLayout()
        btn_cancel=QPushButton('Cancel');btn_cancel.clicked.connect(self.reject)
        btn_ok=QPushButton('Import exactly measured grid');btn_ok.setDefault(True)
        btn_ok.clicked.connect(self.accept_checked)
        actions.addWidget(btn_cancel);actions.addWidget(btn_ok)
        settings.addLayout(actions)
        self._building = False
        self.parameters_changed()

    def parameters_changed(self):
        if self._building:
            return
        self.cfg = GridCalibration(self.cols.value(), self.rows.value(),
            self.pitch_x.value(), self.pitch_y.value(),
            self.origin_x.value(), self.origin_y.value())
        self.view.cfg = self.cfg
        self.view.update()
        self.status.setText(f'Logical grid: {self.cfg.cols} × {self.cfg.rows} cells; '
                            f'pitch {self.cfg.pitch_x:g} × {self.cfg.pitch_y:g} source pixels')

    def update_controls(self, cfg):
        widgets = [self.cols, self.rows, self.pitch_x, self.pitch_y, self.origin_x, self.origin_y]
        for w in widgets:
            w.blockSignals(True)
        for w, value in zip(widgets, [cfg.cols, cfg.rows, cfg.pitch_x,
                                     cfg.pitch_y, cfg.origin_x, cfg.origin_y]):
            w.setValue(value)
        for w in widgets:
            w.blockSignals(False)
        self.parameters_changed()

    def set_zoom(self, value):
        self.view.zoom=value;self.view.resize_view()

    def drag_grid(self, dx, dy):
        # First event establishes a movement anchor, then every subsequent event
        # shifts the current on-screen grid. No automatic pixel guessing.
        if self._drag_base is None:
            self._drag_base = (self.origin_x.value()-dx, self.origin_y.value()-dy)
        ox,oy=self._drag_base
        self.update_controls(GridCalibration(self.cfg.cols,self.cfg.rows,
            self.cfg.pitch_x,self.cfg.pitch_y,ox+dx,oy+dy))

    def suggest_auto(self):
        results=suggest_grids(self.image)
        if not results:
            self.status.setText('No sufficiently periodic grid detected. Measure manually or specify native size.')
            return
        labels=[f'{r.calibration.cols} × {r.calibration.rows} · pitch {r.calibration.pitch_x:.3f} × '
                f'{r.calibration.pitch_y:.3f} · periodicity {r.confidence:.0%}' for r in results]
        answer,ok=QInputDialog.getItem(self,'Measured grid candidates',
            'Hypotheses, not guaranteed. Select one, then inspect the overlay:',labels,0,False)
        if ok:
            result=results[labels.index(answer)]
            self.update_controls(result.calibration)
            self.status.setText(f'Candidate selected ({result.confidence:.0%} boundary periodicity). '
                'Verify pixel boundaries and one-cell details before importing.')

    def fit_pitch(self):
        self.update_controls(default_calibration(self.image, self.cols.value(), self.rows.value()))

    def align_auto(self):
        self.update_controls(align_to_edges(self.image, self.cfg))
        self.status.setText('Auto-aligned. Inspect boundaries and adjust any offset manually.')

    def mellow_preset(self):
        self.update_controls(MELLOW_EXACT)

    def start_measure(self, axis):
        self.measuring=axis
        self.first_point=None
        self.status.setText(f'Measuring {axis}: click the FIRST grid boundary in the reference.')

    def measured_click(self, x, y):
        if not self.measuring:
            self.status.setText(f'Source ({x:.1f}, {y:.1f}) → logical {self.cfg.cell_at(x,y)}')
            return
        point = x if self.measuring == 'X' else y
        if self.first_point is None:
            self.first_point=point
            self.status.setText('Click SECOND boundary (the specified number of cells away).')
            return
        pitch = abs(point-self.first_point)/self.measure_cells.value()
        if pitch < .5:
            self.status.setText('Too close together to measure a cell. Try again.')
            self.first_point=None
            return
        cfg=self.cfg
        # The first clicked mark may be an interior column/row, e.g. Mellow
        # eye coordinates. Derive origin from its actual logical index.
        first = self.first_point
        delta = point - first
        pitch = abs(delta)/self.measure_cells.value()
        logical_index = self.measure_index.value()
        origin = first - logical_index*pitch
        if self.measuring=='X':
            cfg=GridCalibration(cfg.cols,cfg.rows,pitch,cfg.pitch_y,origin,cfg.origin_y)
        else:
            cfg=GridCalibration(cfg.cols,cfg.rows,cfg.pitch_x,pitch,cfg.origin_x,origin)
        self.update_controls(cfg)
        self.status.setText(f'Measured {self.measuring}: {pitch:.4f} screen pixels per cell; original boundary index {logical_index} sets grid origin to {origin:.3f}.')
        self.measuring=''
        self.first_point=None

    def hovered(self, x, y):
        cx,cy=self.cfg.cell_at(x,y)
        self.hover_label.setText(f'Source ({x:.1f}, {y:.1f})  →  logical cell ({cx}, {cy})')

    def accept_checked(self):
        if self.cfg.cols * self.cfg.rows > 2_000_000:
            QMessageBox.warning(self, 'Import', 'Native grid too large for this import.')
            return
        try:
            mode=['median','center','dominant'][self.sampling.currentIndex()]
            self.result_image=self.cfg.extract(self.image, mode)
        except Exception as exc:
            QMessageBox.warning(self, 'Import failed', str(exc))
            return
        self.accept()
