"""Qt workbench for reviewing and correcting embedded source registrations.

No automatic transform is committed: artists choose suggested offsets or type
precise fractional origins, inspect a visual difference, and apply changes.
"""
from __future__ import annotations

from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton, QDoubleSpinBox, QSplitter,
    QWidget, QFormLayout, QDialogButtonBox, QHeaderView, QMessageBox)

from .canvas import qimage_from_pil
from .model import Document
from .reference import calibration_dict, reference_difference


class ReferenceWorkbench(QDialog):
    """Edit a staging document; caller replaces live document only after accept."""

    def __init__(self, doc: Document, parent=None):
        super().__init__(parent)
        self.doc = doc.copy()
        self.setWindowTitle('Reference Lab  /  alignment & native-pixel reconstruction')
        self.resize(1130, 740)
        self.setMinimumSize(870, 520)
        self._loading = False
        self.modified = set()
        self.originals = {i: (r.config().origin_x, r.config().origin_y)
                          for i, f in enumerate(self.doc.frames)
                          if (r := self.doc.reference_for_frame(i)) is not None}
        self.frame_indices = [i for i in range(len(self.doc.frames))
                              if self.doc.reference_for_frame(i) is not None]
        self.current_index = self.frame_indices[0] if self.frame_indices else -1
        root = QVBoxLayout(self)
        banner=QLabel('REFERENCE LAB     /     NATIVE PIXEL REGISTRATION')
        banner.setObjectName('StudioKicker')
        root.addWidget(banner)
        expl=QLabel('Source screenshots are preserved inside the project. Preview an offset before rebuilding. '
                    'A moving pose is not necessarily a shifted crop; no suggestion is applied automatically.')
        expl.setWordWrap(True)
        root.addWidget(expl)

        split=QSplitter(Qt.Orientation.Horizontal)
        root.addWidget(split,1)
        left=QWidget(); lv=QVBoxLayout(left)
        lv.addWidget(QLabel('FRAME SOURCES  /  select a frame to inspect'))
        self.table=QTableWidget(len(self.frame_indices),4)
        self.table.setHorizontalHeaderLabels(['Frame','Embedded source','Suggested offset','Status'])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(1,QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0,58);self.table.setColumnWidth(2,115);self.table.setColumnWidth(3,200)
        for row,fi in enumerate(self.frame_indices):
            asset=self.doc.reference_for_frame(fi)
            candidate=asset.registration
            entries=[f'{fi+1:02d}',asset.name,
                     (f"{candidate['dx']:+d}, {candidate['dy']:+d}" if 'dx' in candidate else 'Manual'),
                     candidate.get('status','Embedded source')]
            for col,value in enumerate(entries):
                item=QTableWidgetItem(value);item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row,col,item)
        lv.addWidget(self.table,1)
        self.table.currentCellChanged.connect(self.row_changed)
        split.addWidget(left)

        right=QWidget(); rv=QVBoxLayout(right)
        self.frame_label=QLabel('FRAME  /  REFERENCE')
        self.frame_label.setObjectName('StudioKicker')
        rv.addWidget(self.frame_label)
        previews=QHBoxLayout()
        self.source_preview=QLabel('Original reference')
        self.diff_preview=QLabel('Red = base • cyan = target')
        for label in (self.source_preview,self.diff_preview):
            label.setMinimumSize(225,200)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setObjectName('ReferencePreview')
            previews.addWidget(label,1)
        rv.addLayout(previews,1)
        self.cel_preview=QLabel('Editable native-pixel reconstruction')
        self.cel_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cel_preview.setMinimumHeight(140)
        self.cel_preview.setObjectName('ReferencePreview')
        rv.addWidget(self.cel_preview)
        form=QFormLayout()
        self.ox=QDoubleSpinBox();self.oy=QDoubleSpinBox()
        for spin in (self.ox,self.oy):
            spin.setRange(-6000,6000);spin.setDecimals(4);spin.setSingleStep(1)
            spin.valueChanged.connect(self.origin_changed)
        form.addRow('Source-grid origin X',self.ox)
        form.addRow('Source-grid origin Y',self.oy)
        rv.addLayout(form)
        buttons=QHBoxLayout()
        self.suggest_button=QPushButton('Use suggested offset')
        self.suggest_button.setToolTip('Explicitly set origin relative to first reference; no automatic crop correction')
        self.suggest_button.clicked.connect(self.accept_candidate)
        buttons.addWidget(self.suggest_button)
        btn_reset=QPushButton('Reset to initial');btn_reset.clicked.connect(self.reset_current)
        buttons.addWidget(btn_reset)
        btn_rebuild=QPushButton('Reconstruct frame')
        btn_rebuild.setObjectName('AccentAction')
        btn_rebuild.clicked.connect(self.rebuild_selected)
        buttons.addWidget(btn_rebuild)
        rv.addLayout(buttons)
        self.note=QLabel('')
        self.note.setWordWrap(True)
        rv.addWidget(self.note)
        split.addWidget(right)
        split.setSizes([420,710])
        bottom=QHBoxLayout()
        self.apply_count=QLabel('No changes staged')
        bottom.addWidget(self.apply_count,1)
        dialog_buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|
                                        QDialogButtonBox.StandardButton.Cancel)
        dialog_buttons.button(QDialogButtonBox.StandardButton.Ok).setText('Apply changes to project')
        dialog_buttons.accepted.connect(self.commit_all)
        dialog_buttons.rejected.connect(self.reject)
        bottom.addWidget(dialog_buttons)
        root.addLayout(bottom)
        if self.frame_indices:
            self.table.selectRow(0)
            self.select_frame(0)
        else:
            self.note.setText('This project has no embedded reference sources.')
            self.suggest_button.setEnabled(False)

    def _asset(self):
        return self.doc.reference_for_frame(self.current_index)

    def row_changed(self,row,column,prev_row,prev_column):
        if row >= 0:
            self.select_frame(row)

    def select_frame(self,row):
        if not 0 <= row < len(self.frame_indices):
            return
        self.current_index=self.frame_indices[row]
        asset=self._asset()
        cfg=asset.config()
        self._loading=True
        self.ox.setValue(cfg.origin_x);self.oy.setValue(cfg.origin_y)
        self._loading=False
        self.frame_label.setText(f'FRAME {self.current_index+1:02d}  /  {asset.name}')
        self.suggest_button.setEnabled('dx' in asset.registration and self.current_index != self.frame_indices[0])
        self.render()

    def origin_changed(self):
        if self._loading or self.current_index < 0:
            return
        asset=self.doc.detach_reference(self.current_index)
        cfg=asset.config()
        cfg.origin_x=self.ox.value();cfg.origin_y=self.oy.value()
        asset.calibration=calibration_dict(cfg)
        self.modified.add(self.current_index)
        self.apply_count.setText(f'{len(self.modified)} frame calibration(s) pending / review before applying')
        self.render()

    def accept_candidate(self):
        if self.current_index < 0:return
        first=self.doc.reference_for_frame(self.frame_indices[0])
        candidate=self._asset().registration
        if not all(k in candidate for k in ('dx','dy')):return
        cfg=first.config()
        self.ox.setValue(cfg.origin_x+candidate['dx'])
        self.oy.setValue(cfg.origin_y+candidate['dy'])

    def reset_current(self):
        if self.current_index<0:return
        ox,oy=self.originals[self.current_index]
        self.ox.setValue(ox);self.oy.setValue(oy)

    def rebuild_selected(self):
        if self.current_index<0:return
        try:
            self.doc.rebuild_reference(self.current_index)
        except Exception as exc:
            QMessageBox.warning(self,'Reference reconstruction failed',str(exc))
            return
        self.modified.discard(self.current_index)
        self.render()
        self.note.setText('Frame rebuilt from the embedded source. Independent linked cels remain untouched. '
                          'Accept the dialog to commit the document transaction, or Cancel to revert.')

    def _scaled(self,img,label,max_w=300,max_h=245):
        if img is None:
            label.clear();return
        px=QPixmap.fromImage(qimage_from_pil(img))
        label.setPixmap(px.scaled(max_w,max_h,Qt.AspectRatioMode.KeepAspectRatio,
                                  Qt.TransformationMode.FastTransformation))

    def render(self):
        asset=self._asset()
        if asset is None:return
        src=asset.image()
        preview_scale=max(1, (max(src.size)+719)//720)
        src_small=src.resize(((src.width+preview_scale-1)//preview_scale,
                              (src.height+preview_scale-1)//preview_scale), Image.Resampling.BOX) if preview_scale>1 else src
        self._scaled(src_small,self.source_preview)
        base=self.doc.reference_for_frame(self.frame_indices[0])
        first=base.config()
        cfg=asset.config()
        delta_x=round(cfg.origin_x-first.origin_x)
        delta_y=round(cfg.origin_y-first.origin_y)
        anchor=base.image()
        if preview_scale>1:
            anchor=anchor.resize(((anchor.width+preview_scale-1)//preview_scale,
                                   (anchor.height+preview_scale-1)//preview_scale), Image.Resampling.BOX)
        self._scaled(reference_difference(anchor,src_small,round(delta_x/preview_scale),
                                          round(delta_y/preview_scale)),self.diff_preview)
        try:
            self._scaled(asset.extract(),self.cel_preview,300,190)
            self.note.setText(f'{src.width}×{src.height} source → {cfg.cols}×{cfg.rows} logical cells. '
                f'Grid origin ({cfg.origin_x:g}, {cfg.origin_y:g}) · pitch ({cfg.pitch_x:.3f}, {cfg.pitch_y:.3f}). '
                'Red/cyan disagreement can also represent legitimate pose changes.')
        except Exception as exc:
            self.note.setText(str(exc))

    def commit_all(self):
        try:
            for index in sorted(self.modified):
                self.doc.rebuild_reference(index)
        except Exception as exc:
            QMessageBox.warning(self,'Could not reconstruct reference',str(exc))
            return
        self.modified.clear()
        self.accept()
