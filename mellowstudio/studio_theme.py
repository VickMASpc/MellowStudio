"""Native Qt presentation tokens for Mellow's artist-first workspace."""

STUDIO_QSS = """
QWidget { background-color: #171b23; color: #e8edf5; font-family: 'Segoe UI'; font-size: 10pt; }
QMainWindow, QDialog { background-color: #171b23; }
QMenuBar, QMenu, QStatusBar { background: #141820; color: #c4cfdf; }
QMenuBar::item { padding: 7px 12px; }
QMenuBar::item:selected, QMenu::item:selected { background: #303f51; color: white; }
QMenu::item { padding: 7px 25px; }
QToolBar { background: #202631; border: none; spacing: 5px; padding: 5px; }
QToolBar#StudioControlBar { background: #181e28; border-bottom: 1px solid #333d4e; }
QToolBar#ToolOptionsBar { background: #202631; border-bottom: 1px solid #384456; padding: 5px 10px; }
QToolBar#DrawingTools { background: #202630; border-right: 1px solid #333d4e; padding: 7px 4px; spacing: 4px; }
QDockWidget { border: none; color: #c2cddd; }
QDockWidget::title { background: #242c39; padding: 9px 12px; border-top: 1px solid #354153; font-weight: 600; }
QLabel#StudioWordmark { color: #ffcc9c; font-weight: 800; font-size: 13pt; background: #181e28; }
QLabel#StudioKicker, QLabel#SectionEyebrow { color: #90acbf; font-size: 9pt; font-weight: 700; }
QLabel#ToolTitle { color: #f7dec1; font-size: 10pt; font-weight: 700; }
QLabel#ToolHint { color: #9aafc1; font-size: 9pt; }
QLabel#TimelineInfo { color: #9bb1c3; font-size: 9pt; }
QLabel#ReferencePreview { background: #121823; border: 1px solid #445268; border-radius: 7px; padding: 4px; }
QPushButton, QToolButton { background: #303b4d; color: #eaf0f7; border: 1px solid #485a70; border-radius: 7px; padding: 7px 11px; }
QPushButton:hover, QToolButton:hover { background: #41546b; border-color: #a2c7d8; }
QPushButton:pressed, QToolButton:pressed { background: #26384a; }
QPushButton#PrimaryAction, QToolButton#PrimaryAction, QPushButton#AccentAction, QToolButton#AccentAction { background: #bd785a; color: #fffaf7; border: 1px solid #d99574; font-weight: 700; }
QPushButton#PrimaryAction:hover, QToolButton#PrimaryAction:hover, QPushButton#AccentAction:hover, QToolButton#AccentAction:hover { background: #d38a6c; }
QToolButton#ToolGlyph { background: transparent; border: 1px solid transparent; border-radius: 9px; padding: 5px; }
QToolButton#ToolGlyph:hover { background: #344357; border-color: #4c6278; }
QToolButton#ToolGlyph:checked { background: #485a70; border-color: #e4ad8c; }
QToolButton:checked { background: #42556b; border: 1px solid #daa486; }
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QListWidget, QTableWidget { background: #222b39; border: 1px solid #465369; color: #eef3f7; border-radius: 6px; padding: 5px; selection-background-color: #4d7089; }
QListWidget::item:selected, QTableWidget::item:selected { background: #3c596f; color: #fff; }
QListWidget::item:hover { background: #313f52; }
QHeaderView::section { background: #293647; color: #dbe5ef; border: none; border-right: 1px solid #3e4a5b; padding: 6px; }
QLabel, QCheckBox { color: #d4dfeb; }
QScrollBar { background: #1a2230; width: 11px; height: 11px; }
QScrollBar::handle { background: #526980; border-radius: 4px; }
QSlider::groove:horizontal { background: #39485b; height: 5px; border-radius: 3px; }
QSlider::handle:horizontal { background: #e4ac88; width: 15px; margin: -5px 0; border-radius: 7px; }
QTabBar::tab { background: #253141; color: #b0c1d2; padding: 9px 14px; }
QTabBar::tab:selected { background: #40566b; color: white; border-top: 2px solid #e3ac8b; }
QDialog#WelcomeDialog { background: #171d27; }
QLabel#WelcomeKicker { color: #e4ae87; font-weight: 800; font-size: 10pt; }
QLabel#WelcomeTitle { color: #fff4e9; font-size: 29pt; font-weight: 700; }
QLabel#WelcomeTagline { color: #b7c8d7; font-size: 11pt; }
QFrame#WelcomeCard { background: #252f3d; border: 1px solid #3d4d60; border-radius: 12px; }
QLabel#WelcomeCardTitle { background: transparent; color: #f5ebdf; font-size: 14pt; font-weight: 700; }
QLabel#WelcomeCardDescription { background: transparent; color: #b9c8d7; font-size: 10pt; }
QListWidget#WelcomeRecents { background: #1e2733; border-radius: 9px; }
QLabel#ExportTitle { color: #fff4e9; font-size: 22pt; font-weight: 700; }
QLabel#ExportSubtitle { color: #a7b9cc; }
"""
