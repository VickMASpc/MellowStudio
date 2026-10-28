"""One destination-oriented export dialog for artwork and animations."""
from __future__ import annotations

from pathlib import Path
from PySide6.QtWidgets import (
    QComboBox, QDialog, QFileDialog, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QVBoxLayout, QWidget,
)


KINDS = (
    ('Spritesheet PNG + timing JSON', 'sheet'),
    ('Animated GIF', 'gif'),
    ('Current frame PNG', 'png'),
    ('All frames as PNGs + timing JSON', 'frames'),
)


class ExportDialog(QDialog):
    def __init__(self, doc, initial_folder: str = '', parent=None):
        super().__init__(parent)
        self.setWindowTitle('Export artwork')
        self.setMinimumWidth(480)
        self.doc = doc
        self.folder = Path(initial_folder).expanduser() if initial_folder else Path.home()
        self.setObjectName('ExportDialog')
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 23, 24, 22)
        root.setSpacing(13)
        title = QLabel('Ready to share.')
        title.setObjectName('ExportTitle')
        subtitle = QLabel(f'{doc.name}  ·  {doc.width}×{doc.height} actual pixels  ·  {len(doc.frames)} frame(s)')
        subtitle.setObjectName('ExportSubtitle')
        root.addWidget(title)
        root.addWidget(subtitle)
        form = QFormLayout()
        form.setSpacing(12)
        self.format = QComboBox()
        for title, kind in KINDS:
            self.format.addItem(title, kind)
        self.format.currentIndexChanged.connect(self._update_format)
        form.addRow('Format', self.format)
        self.layout_kind = QComboBox()
        self.layout_kind.addItem('Horizontal strip', 'horizontal')
        self.layout_kind.addItem('Vertical strip', 'vertical')
        form.addRow('Sheet layout', self.layout_kind)
        root.addLayout(form)
        self.description = QLabel('')
        self.description.setWordWrap(True)
        self.description.setObjectName('ExportSubtitle')
        root.addWidget(self.description)
        dest_row = QHBoxLayout()
        self.destination = QLineEdit()
        self.destination.setPlaceholderText('Choose where to export…')
        self.browse = QPushButton('Browse…')
        self.browse.clicked.connect(self.choose_destination)
        dest_row.addWidget(self.destination, 1)
        dest_row.addWidget(self.browse)
        root.addWidget(QLabel('DESTINATION'))
        root.addLayout(dest_row)
        footer = QHBoxLayout()
        footer.addStretch()
        cancel = QPushButton('Cancel')
        cancel.clicked.connect(self.reject)
        self.export_button = QPushButton('Export')
        self.export_button.setObjectName('PrimaryAction')
        self.export_button.clicked.connect(self._export_clicked)
        footer.addWidget(cancel)
        footer.addWidget(self.export_button)
        root.addLayout(footer)
        self._update_format()

    @property
    def kind(self) -> str:
        return self.format.currentData()

    def suggested_path(self) -> Path:
        name = ''.join(c if c.isalnum() or c in '-_ ' else '_' for c in self.doc.name).strip() or 'Mellow'
        suffix = {'sheet':'_sheet.png','png':'.png','gif':'.gif','frames':'_frames'}[self.kind]
        return self.folder / (name + suffix)

    def _update_format(self, *_):
        self.layout_kind.setEnabled(self.kind == 'sheet')
        self.description.setText({
            'sheet': 'Lossless sprite strip plus JSON frame timings for game engines.',
            'gif': 'A looping animation preview. GIF may reduce colors; keep the PNG artwork as your master.',
            'png': 'A single lossless image of the current frame at native resolution.',
            'frames': 'A numbered PNG sequence plus a timing manifest.'
        }[self.kind])
        self.destination.setText(str(self.suggested_path()))

    def choose_destination(self):
        if self.kind == 'frames':
            path = QFileDialog.getExistingDirectory(self, 'Choose destination folder', str(self.folder))
        else:
            extension = 'GIF files (*.gif)' if self.kind == 'gif' else 'PNG files (*.png)'
            path, _ = QFileDialog.getSaveFileName(self, 'Export artwork', self.destination.text(), extension)
        if path:
            self.destination.setText(path)
            self.folder = Path(path).expanduser().parent

    def _export_clicked(self):
        if not self.destination.text().strip():
            self.choose_destination()
        if self.destination.text().strip():
            self.accept()
