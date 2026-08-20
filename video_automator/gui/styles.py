"""Application-wide QSS dark theme stylesheet."""

DARK_THEME = """
/* ─── Global ─────────────────────────────────────────── */
QWidget {
    background-color: #0f0f13;
    color: #e8e8f0;
    font-family: "Segoe UI", "Inter", "Roboto", Arial, sans-serif;
    font-size: 13px;
}

/* ─── Main Window ─────────────────────────────────────── */
QMainWindow {
    background-color: #0f0f13;
}

/* ─── Sidebar ─────────────────────────────────────────── */
#sidebar {
    background-color: #14141c;
    border-right: 1px solid #1e1e2e;
    min-width: 220px;
    max-width: 220px;
}

#app_title {
    color: #a78bfa;
    font-size: 18px;
    font-weight: 700;
    letter-spacing: 0.5px;
    padding: 24px 20px 16px 20px;
}

#app_subtitle {
    color: #6b7280;
    font-size: 11px;
    padding: 0 20px 20px 20px;
    letter-spacing: 1px;
    text-transform: uppercase;
}

/* ─── Wizard Header / Step Indicator ─────────────────── */
#wizard_header {
    background-color: #14141c;
    border-bottom: 1px solid #1e1e2e;
    padding: 12px 24px;
    min-height: 60px;
}

/* ─── Cards / Panels ──────────────────────────────────── */
#card {
    background-color: #1a1a27;
    border: 1px solid #252535;
    border-radius: 12px;
    padding: 20px;
}

#card_elevated {
    background-color: #1e1e2e;
    border: 1px solid #2d2d45;
    border-radius: 14px;
    padding: 24px;
}

#info_card {
    background-color: #181828;
    border: 1px solid #2a2a3e;
    border-radius: 10px;
    padding: 16px;
}

/* ─── Page Container ──────────────────────────────────── */
#page_container {
    background-color: #0f0f13;
    padding: 32px 40px;
}

/* ─── Typography ──────────────────────────────────────── */
#page_title {
    color: #f0f0f8;
    font-size: 22px;
    font-weight: 700;
    letter-spacing: -0.3px;
}

#section_label {
    color: #a78bfa;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 4px;
}

#value_label {
    color: #e8e8f0;
    font-size: 13px;
}

#hint_label {
    color: #6b7280;
    font-size: 11px;
}

#error_label {
    color: #f87171;
    font-size: 12px;
}

#success_label {
    color: #34d399;
    font-size: 12px;
}

/* ─── Buttons ─────────────────────────────────────────── */
QPushButton {
    background-color: #252535;
    color: #e8e8f0;
    border: 1px solid #2d2d45;
    border-radius: 8px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 500;
    min-height: 36px;
}

QPushButton:hover {
    background-color: #2d2d45;
    border-color: #3d3d60;
}

QPushButton:pressed {
    background-color: #1e1e30;
}

QPushButton:disabled {
    background-color: #18181f;
    color: #3f3f5f;
    border-color: #1e1e2e;
}

#btn_primary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #7c3aed, stop:1 #6d28d9);
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px 28px;
    font-size: 13px;
    font-weight: 600;
    min-height: 40px;
    min-width: 120px;
}

#btn_primary:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #8b5cf6, stop:1 #7c3aed);
}

#btn_primary:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6d28d9, stop:1 #5b21b6);
}

#btn_primary:disabled {
    background: #2d2d45;
    color: #4b4b70;
}

#btn_secondary {
    background-color: transparent;
    color: #a78bfa;
    border: 1px solid #4c1d95;
    border-radius: 8px;
    padding: 9px 24px;
    font-size: 13px;
    font-weight: 500;
    min-height: 38px;
}

#btn_secondary:hover {
    background-color: #1e1030;
    border-color: #7c3aed;
}

#btn_danger {
    background-color: transparent;
    color: #f87171;
    border: 1px solid #7f1d1d;
    border-radius: 8px;
    padding: 9px 20px;
    font-size: 13px;
    min-height: 38px;
}

#btn_danger:hover {
    background-color: #2d0f0f;
    border-color: #ef4444;
}

#btn_preset {
    background-color: #1e1e2e;
    color: #c4b5fd;
    border: 1px solid #312e81;
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 12px;
    min-height: 30px;
}

#btn_preset:hover {
    background-color: #2d2050;
    border-color: #7c3aed;
}

#btn_preset:checked, #btn_preset:pressed {
    background-color: #4c1d95;
    border-color: #a78bfa;
    color: #ede9fe;
}

/* ─── Inputs ──────────────────────────────────────────── */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #1a1a27;
    color: #e8e8f0;
    border: 1px solid #2d2d45;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
    min-height: 36px;
    selection-background-color: #5b21b6;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border-color: #7c3aed;
    background-color: #1e1e30;
}

QLineEdit:disabled, QSpinBox:disabled {
    background-color: #14141c;
    color: #3f3f5f;
}

QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    background-color: #252535;
    border: none;
    width: 20px;
    border-radius: 4px;
}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {
    background-color: #7c3aed;
}

QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #7c3aed;
}

/* ─── ComboBox ────────────────────────────────────────── */
QComboBox::drop-down {
    border: none;
    width: 28px;
}

QComboBox::down-arrow {
    image: none;
    width: 10px;
    height: 10px;
    border-left: 2px solid #6b7280;
    border-bottom: 2px solid #6b7280;
    transform: rotate(-45deg);
    margin-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #1e1e2e;
    border: 1px solid #3d3d60;
    color: #e8e8f0;
    selection-background-color: #4c1d95;
    padding: 4px;
    outline: none;
}

/* ─── Radio Buttons ───────────────────────────────────── */
QRadioButton {
    color: #d1d5db;
    font-size: 13px;
    spacing: 8px;
    padding: 4px;
}

QRadioButton:hover {
    color: #e8e8f0;
}

QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border-radius: 9px;
    border: 2px solid #4b5563;
    background-color: #1a1a27;
}

QRadioButton::indicator:hover {
    border-color: #7c3aed;
}

QRadioButton::indicator:checked {
    background-color: #7c3aed;
    border-color: #a78bfa;
}

/* ─── CheckBox ────────────────────────────────────────── */
QCheckBox {
    color: #d1d5db;
    font-size: 13px;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid #4b5563;
    background-color: #1a1a27;
}

QCheckBox::indicator:hover {
    border-color: #7c3aed;
}

QCheckBox::indicator:checked {
    background-color: #7c3aed;
    border-color: #a78bfa;
}

/* ─── Progress Bar ────────────────────────────────────── */
QProgressBar {
    background-color: #1a1a27;
    border: 1px solid #252535;
    border-radius: 8px;
    height: 14px;
    text-align: center;
    color: transparent;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #7c3aed, stop:0.5 #a855f7, stop:1 #c084fc);
    border-radius: 7px;
}

/* ─── Scroll Area ─────────────────────────────────────── */
QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollBar:vertical {
    background-color: #14141c;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background-color: #2d2d45;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #7c3aed;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* ─── List Widget ─────────────────────────────────────── */
QListWidget {
    background-color: #1a1a27;
    border: 1px solid #252535;
    border-radius: 8px;
    padding: 4px;
    color: #e8e8f0;
    outline: none;
}

QListWidget::item {
    padding: 8px 12px;
    border-radius: 6px;
}

QListWidget::item:hover {
    background-color: #252535;
}

QListWidget::item:selected {
    background-color: #4c1d95;
    color: #ede9fe;
}

/* ─── Separator / Divider ─────────────────────────────── */
QFrame[frameShape="4"] {
    color: #1e1e2e;
    background-color: #1e1e2e;
    height: 1px;
    max-height: 1px;
}

/* ─── Tooltip ─────────────────────────────────────────── */
QToolTip {
    background-color: #1e1e2e;
    color: #e8e8f0;
    border: 1px solid #3d3d60;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}

/* ─── Message Box ─────────────────────────────────────── */
QMessageBox {
    background-color: #0f0f13;
}

QMessageBox QLabel {
    color: #e8e8f0;
    font-size: 13px;
}
"""


STEP_COLORS = {
    "active": "#7c3aed",
    "completed": "#34d399",
    "inactive": "#374151",
    "text_active": "#ede9fe",
    "text_completed": "#6ee7b7",
    "text_inactive": "#6b7280",
}
