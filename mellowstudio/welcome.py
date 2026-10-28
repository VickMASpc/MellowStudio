"""Project-first Mellow Studio home screen. Pure Qt; no browser or web dependencies."""
from __future__ import annotations

from pathlib import Path
from .recent import tidy_recent

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QDialog, QFrame, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPushButton, QVBoxLayout, QWidget,
)


def _action_card(title: str, description: str, action: str, callback, primary=False) -> QFrame:
    card = QFrame()
    card.setObjectName('WelcomeCard')
    layout = QVBoxLayout(card)
    layout.setContentsMargins(18, 17, 18, 16)
    layout.setSpacing(8)
    heading = QLabel(title)
    heading.setObjectName('WelcomeCardTitle')
    detail = QLabel(description)
    detail.setObjectName('WelcomeCardDescription')
    detail.setWordWrap(True)
    button = QPushButton(action)
    button.setMinimumHeight(38)
    if primary:
        button.setObjectName('PrimaryAction')
    button.clicked.connect(callback)
    layout.addWidget(heading)
    layout.addWidget(detail)
    layout.addStretch()
    layout.addWidget(button)
    return card


class WelcomeDialog(QDialog):
    """Returns a chosen project action without mutating the live editor."""

    def __init__(self, parent=None, recent: list[str] | None = None, show_at_startup=True, recovery_available=False):
        super().__init__(parent)
        self.setObjectName('WelcomeDialog')
        self.setWindowTitle('Welcome to Mellow Studio')
        self.setMinimumSize(740, 510)
        self.resize(820, 570)
        self.choice = 'continue'
        self.selected_path: str | None = None
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 25, 28, 22)
        root.setSpacing(17)
        kicker = QLabel('M E L L O W   S T U D I O')
        kicker.setObjectName('WelcomeKicker')
        title = QLabel('Make something move.')
        title.setObjectName('WelcomeTitle')
        tagline = QLabel('Pixel art, animation, and the tools you need — all in one studio.')
        tagline.setObjectName('WelcomeTagline')
        root.addWidget(kicker)
        root.addWidget(title)
        root.addWidget(tagline)

        cards = QHBoxLayout()
        cards.setSpacing(11)
        cards.addWidget(_action_card('New canvas',
            'Create a crisp pixel-art canvas. Pick a size and start drawing.',
            'Create project', lambda: self._choose('new'), True), 1)
        cards.addWidget(_action_card('Open project',
            'Return to a saved animation, palette, or layered artwork.',
            'Browse files', lambda: self._choose('open')), 1)
        cards.addWidget(_action_card('Explore Mellow',
            'Open the included 41×55 example and try frame-by-frame animation.',
            'Open sample', lambda: self._choose('sample')), 1)
        root.addLayout(cards, 2)

        recent_heading = QLabel('RECENT PROJECTS')
        recent_heading.setObjectName('SectionEyebrow')
        root.addWidget(recent_heading)
        self.recent_list = QListWidget()
        self.recent_list.setObjectName('WelcomeRecents')
        self.recent_list.setMinimumHeight(100)
        self.recent_list.setMaximumHeight(148)
        for item_path in tidy_recent(recent):
            path = Path(item_path)
            item = QListWidgetItem(f'{path.stem}    ·    {path.parent}')
            item.setData(Qt.ItemDataRole.UserRole, item_path)
            item.setToolTip(item_path)
            self.recent_list.addItem(item)
        if not self.recent_list.count():
            placeholder = QListWidgetItem('Your saved projects will appear here.')
            placeholder.setFlags(Qt.ItemFlag.NoItemFlags)
            self.recent_list.addItem(placeholder)
        self.recent_list.itemDoubleClicked.connect(self._open_recent)
        root.addWidget(self.recent_list)
        footer = QHBoxLayout()
        self.show_on_startup = QCheckBox('Show this screen when Mellow starts')
        self.show_on_startup.setChecked(bool(show_at_startup))
        footer.addWidget(self.show_on_startup)
        footer.addStretch()
        if recovery_available:
            recovery = QPushButton('Recover unsaved work…')
            recovery.setToolTip('Open a recovery snapshot from an interrupted session')
            recovery.clicked.connect(lambda: self._choose('recover'))
            footer.addWidget(recovery)
        continue_button = QPushButton('Continue editing')
        continue_button.setObjectName('SubtleAction')
        continue_button.clicked.connect(lambda: self._choose('continue'))
        footer.addWidget(continue_button)
        root.addLayout(footer)

    def _choose(self, choice: str):
        self.choice = choice
        self.accept()

    def _open_recent(self, item: QListWidgetItem):
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self.selected_path = str(path)
            self._choose('recent')
