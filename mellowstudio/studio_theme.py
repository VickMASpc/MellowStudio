"""Mellow Studio's new integrated, light-first creative workspace.

The layout, sections, and interaction model live in main.py. This stylesheet
provides a restrained, high-contrast presentation rather than simulating docks.
"""

STUDIO_QSS = """
QWidget {
    color: #263341;
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 10pt;
}
QMainWindow, QDialog, QWidget#StudioWorkspace {
    background: #f3f5f7;
}
QMenuBar {
    background: #ffffff;
    color: #3b4655;
    padding: 3px 9px;
    border-bottom: 1px solid #e4e9ee;
}
QMenuBar::item {
    padding: 7px 13px;
    border-radius: 7px;
}
QMenuBar::item:selected, QMenu::item:selected {
    background: #e6f2f3;
    color: #126c77;
}
QMenu {
    background: white;
    color: #243441;
    border: 1px solid #d8e1e9;
    border-radius: 8px;
    padding: 6px;
}
QMenu::item {
    padding: 7px 24px;
}
QStatusBar {
    background: #f7f9fb;
    border-top: 1px solid #e3e9ef;
    color: #677786;
}
QFrame#StudioHeader {
    background: #ffffff;
    border-bottom: 1px solid #e3e8ee;
}
QFrame#ContextBar {
    background: #f8fafc;
    border-bottom: 1px solid #e2e8ef;
}
QLabel#StudioWordmark {
    color: #1e6976;
    font-size: 15pt;
    font-weight: 800;
}
QLabel#StudioKicker, QLabel#TimelineInfo {
    color: #667888;
    font-size: 9pt;
    font-weight: 600;
}
QLabel#ToolTitle {
    color: #243947;
    font-size: 10pt;
    font-weight: 700;
}
QLabel#ToolHint {
    color: #778592;
    font-size: 9pt;
}
QFrame#ToolRail {
    background: #ffffff;
    border-right: 1px solid #e1e8ee;
}
QFrame#ToolRailDivider {
    background: #e2e7ee;
    border: 0;
}
QToolButton#ToolGlyph {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 11px;
    padding: 4px;
}
QToolButton#ToolGlyph:hover {
    background: #e5eef3;
    border-color: #d6e6ec;
}
QToolButton#ToolGlyph:checked {
    background: #d7edef;
    border: 1px solid #83bac2;
}
/* Qt's original toolbars are back with the flexible docking workspace. */
QToolBar#DrawingTools {
    background: #ffffff;
    border-right: 1px solid #e1e8ee;
    padding: 8px 5px;
    spacing: 3px;
}
QToolBar#StudioControlBar {
    background: #ffffff;
    border-bottom: 1px solid #e3e8ee;
    padding: 5px 8px;
    spacing: 6px;
}
QToolBar#ToolOptionsBar {
    background: #f8fafc;
    border-bottom: 1px solid #e2e8ef;
    padding: 6px 8px;
    spacing: 6px;
}
QToolBar::separator {
    background: #e1e8ee;
    width: 1px;
    height: 1px;
    margin: 7px;
}
QMainWindow::separator {
    background: #e5ebf1;
    width: 5px;
    height: 5px;
}
QMainWindow::separator:hover {
    background: #8ebdc8;
}
QScrollArea#ColorPanelScroll {
    background: #ffffff;
    border: 0;
}
QDockWidget {
    color: #283b48;
    font-weight: 600;
    border: 1px solid #dce4eb;
    background: #ffffff;
}
QDockWidget::title {
    background: #f7f9fb;
    border-bottom: 1px solid #dfe6eb;
    padding: 8px 30px 8px 12px;
    text-align: left;
}
QDockWidget::close-button, QDockWidget::float-button {
    background: #e7eef1;
    border: 1px solid #c9d8df;
    border-radius: 3px;
}
QDockWidget::close-button:hover, QDockWidget::float-button:hover {
    background: #d3e8ec;
}
QWidget#SaturationValueField {
    border: 1px solid #cfdde4;
    border-radius: 7px;
}
QSlider#HueSlider::groove:horizontal {
    height: 12px;
    border: 1px solid #cbd6df;
    border-radius: 6px;
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
      stop:0 #ff0000, stop:0.166 #ffff00, stop:0.333 #00ff00,
      stop:0.5 #00ffff, stop:0.666 #0000ff,
      stop:0.833 #ff00ff, stop:1 #ff0000);
}
QSlider#HueSlider::handle:horizontal {
    width: 12px;
    margin: -5px 0;
    background: #ffffff;
    border: 2px solid #263b48;
    border-radius: 7px;
}
QLineEdit#ColorHexInput {
    font-family: Consolas, monospace;
    font-weight: 700;
    letter-spacing: 1px;
}
QFrame#CanvasStage {
    background: #e9edf2;
}
QScrollArea#PixelCanvasViewport, QScrollArea#PixelCanvasViewport > QWidget {
    background: #e9edf2;
    border: 0;
}
QSplitter#WorkspaceSplitter::handle, QSplitter#CanvasTimelineSplitter::handle {
    background: #e2e8ef;
}
QScrollArea#InspectorScroll, QWidget#InspectorSections {
    background: #f3f5f7;
    border: 0;
}
QFrame[studioSection="true"] {
    background: #ffffff;
    border: 1px solid #e0e6eb;
    border-radius: 13px;
}
QLabel#SectionHeader {
    color: #48606d;
    font-size: 9pt;
    font-weight: 700;
    padding: 0 0 5px 0;
}
QLabel#SectionEyebrow {
    color: #72899a;
    font-size: 9pt;
    font-weight: 600;
}
QLabel#ReferencePreview {
    background: #f0f3f6;
    border: 1px solid #dee6ed;
    border-radius: 8px;
    padding: 4px;
}
QFrame#TimelineDock {
    background: #ffffff;
    border: 1px solid #e0e6ec;
    border-radius: 0;
}
QPushButton, QToolButton {
    background: #ffffff;
    color: #334758;
    border: 1px solid #d8e0e7;
    border-radius: 8px;
    padding: 6px 10px;
    min-height: 19px;
}
QPushButton:hover, QToolButton:hover {
    background: #ecf3f6;
    border-color: #9dc6cf;
}
QPushButton:pressed, QToolButton:pressed {
    background: #d9e9ed;
}
QPushButton#PrimaryAction, QToolButton#PrimaryAction,
QPushButton#AccentAction, QToolButton#AccentAction {
    color: white;
    background: #187c89;
    border: 1px solid #187c89;
    font-weight: 700;
}
QPushButton#PrimaryAction:hover, QToolButton#PrimaryAction:hover,
QPushButton#AccentAction:hover, QToolButton#AccentAction:hover {
    background: #11636e;
    border-color: #11636e;
}
QPushButton:disabled, QToolButton:disabled {
    color: #a3acb5;
    background: #f3f5f7;
}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QListWidget, QTableWidget {
    background: #ffffff;
    color: #263744;
    border: 1px solid #d5e0e8;
    border-radius: 7px;
    padding: 4px;
    selection-background-color: #d3e9ed;
    selection-color: #1b4853;
}
QListWidget::item {
    padding: 3px;
    border-radius: 5px;
}
QListWidget::item:selected, QTableWidget::item:selected {
    color: #204c57;
    background: #d6edf0;
}
QListWidget::item:hover {
    background: #edf5f7;
}
QHeaderView::section {
    background: #f4f7f9;
    color: #5c7081;
    border: 0;
    border-bottom: 1px solid #e1e7ee;
    padding: 6px;
}
QCheckBox {
    spacing: 7px;
    color: #506476;
}
QScrollBar:vertical {
    background: #f3f6f8;
    width: 9px;
    margin: 1px;
}
QScrollBar:horizontal {
    background: #f3f6f8;
    height: 9px;
    margin: 1px;
}
QScrollBar::handle {
    background: #c3d0d9;
    border-radius: 4px;
    min-height: 20px;
    min-width: 20px;
}
QScrollBar::add-line, QScrollBar::sub-line {
    width: 0;
    height: 0;
}
QSlider::groove:horizontal {
    height: 5px;
    background: #d8e2e8;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    width: 13px;
    margin: -5px 0;
    background: #187c89;
    border-radius: 7px;
}
QFrame#WelcomeCard {
    background: #ffffff;
    border: 1px solid #dde5ec;
    border-radius: 13px;
}
QLabel#WelcomeCardTitle {
    font-size: 13pt;
    font-weight: 700;
}
QLabel#WelcomeCardDescription, QLabel#ExportSubtitle {
    color: #72818e;
}
QLabel#ExportTitle {
    font-size: 17pt;
    font-weight: 750;
}
QTabBar::tab {
    background: #ecf0f3;
    color: #526273;
    padding: 9px 15px;
}
QTabBar::tab:selected {
    background: #ffffff;
    color: #187c89;
    border-bottom: 2px solid #187c89;
}
"""
