# -*- coding: utf-8 -*-
from config.settings import UI


def get_dark_stylesheet() -> str:
    c = UI
    return f"""
    /* ===== GLOBAL ===== */
    QWidget {{
        background-color: {c.bg_primary};
        color: {c.text_primary};
        font-family: {c.font_family};
        font-size: {c.font_size}pt;
        selection-background-color: {c.accent_color};
        selection-color: white;
    }}

    /* ===== MAIN WINDOW ===== */
    QMainWindow {{
        background-color: {c.bg_primary};
    }}

    /* ===== MENU BAR ===== */
    QMenuBar {{
        background-color: {c.bg_secondary};
        color: {c.text_primary};
        border-bottom: 1px solid {c.border_color};
        padding: 2px 4px;
        font-size: 9pt;
    }}
    QMenuBar::item {{
        padding: 4px 10px;
        border-radius: 4px;
    }}
    QMenuBar::item:selected {{
        background-color: #404040;
    }}
    QMenu {{
        background-color: {c.bg_secondary};
        color: {c.text_primary};
        border: 1px solid {c.border_color};
        border-radius: 8px;
        padding: 4px;
    }}
    QMenu::item {{
        padding: 6px 24px;
        border-radius: 4px;
    }}
    QMenu::item:selected {{
        background-color: #404040;
    }}

    /* ===== TAB WIDGET ===== */
    QTabWidget::pane {{
        border: 1px solid {c.border_color};
        border-radius: 8px;
        background-color: {c.bg_primary};
        top: -1px;
    }}
    QTabBar::tab {{
        background-color: {c.bg_secondary};
        color: {c.text_secondary};
        border: 1px solid {c.border_color};
        border-bottom: none;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        padding: 8px 20px;
        margin-right: 2px;
        font-size: 9pt;
    }}
    QTabBar::tab:selected {{
        background-color: {c.bg_primary};
        color: {c.accent_color};
        font-weight: bold;
    }}
    QTabBar::tab:hover:!selected {{
        background-color: #383838;
        color: {c.text_primary};
    }}

    /* ===== BUTTONS ===== */
    QPushButton {{
        background-color: #353535;
        color: {c.text_primary};
        border: 1px solid #454545;
        border-radius: 6px;
        padding: 7px 14px;
        font-weight: bold;
        font-size: 9pt;
        min-height: 18px;
    }}
    QPushButton:hover {{
        background-color: #404040;
        border-color: #555555;
    }}
    QPushButton:pressed {{
        background-color: #2A2A2A;
    }}
    QPushButton:disabled {{
        background-color: #2A2A2A;
        color: #555555;
        border-color: #353535;
    }}

    QPushButton#btn_capture {{
        background-color: {c.accent_color};
        color: white;
        font-size: 13pt;
        font-weight: bold;
        min-height: 36px;
        border: none;
        border-radius: 8px;
        letter-spacing: 2px;
    }}
    QPushButton#btn_capture:hover {{
        background-color: #1A8AE8;
    }}
    QPushButton#btn_capture:pressed {{
        background-color: #005A9E;
    }}

    QPushButton#btn_setref {{
        background-color: {c.success_color};
        color: white;
        border: none;
        border-radius: 6px;
        font-size: 10pt;
        min-height: 28px;
    }}
    QPushButton#btn_setref:hover {{
        background-color: #138E13;
    }}

    QPushButton#btn_reset {{
        background-color: {c.danger_color};
        color: white;
        border: none;
        border-radius: 6px;
    }}
    QPushButton#btn_reset:hover {{
        background-color: #E04834;
    }}

    QPushButton#btn_save {{
        background-color: {c.warning_color};
        color: #1A1A1A;
        border: none;
        border-radius: 6px;
    }}
    QPushButton#btn_save:hover {{
        background-color: #D1AD00;
    }}

    QPushButton#btn_import {{
        background-color: #3A3A3A;
        color: {c.text_primary};
        border: 1px solid #505050;
        border-radius: 6px;
    }}
    QPushButton#btn_import:hover {{
        background-color: #454545;
    }}

    QPushButton#btn_open_cam {{
        background-color: #2A5A2A;
        color: #90EE90;
        border: 1px solid #3A7A3A;
        border-radius: 6px;
    }}
    QPushButton#btn_open_cam:hover {{
        background-color: #306030;
    }}

    /* ===== COMBO BOX ===== */
    QComboBox {{
        background-color: #353535;
        color: {c.text_primary};
        border: 1px solid #454545;
        border-radius: 6px;
        padding: 5px 10px;
        min-height: 18px;
        font-size: 9pt;
    }}
    QComboBox:hover {{
        border-color: #555555;
    }}
    QComboBox:focus {{
        border-color: {c.accent_color};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}
    QComboBox::down-arrow {{
        image: none;
        border: none;
    }}
    QComboBox QAbstractItemView {{
        background-color: {c.bg_secondary};
        color: {c.text_primary};
        border: 1px solid {c.border_color};
        border-radius: 4px;
        selection-background-color: #404040;
        outline: none;
        font-size: 9pt;
    }}

    /* ===== SPIN BOX ===== */
    QSpinBox {{
        background-color: #353535;
        color: {c.text_primary};
        border: 1px solid #454545;
        border-radius: 6px;
        padding: 5px 8px;
        font-size: 9pt;
    }}
    QSpinBox:hover {{
        border-color: #555555;
    }}
    QSpinBox:focus {{
        border-color: {c.accent_color};
    }}

    /* ===== LINE EDIT ===== */
    QLineEdit {{
        background-color: #353535;
        color: {c.text_primary};
        border: 1px solid #454545;
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 9pt;
    }}
    QLineEdit:hover {{
        border-color: #555555;
    }}
    QLineEdit:focus {{
        border-color: {c.accent_color};
    }}
    QLineEdit::placeholder {{
        color: #666666;
    }}

    /* ===== TABLE WIDGET ===== */
    QTableWidget {{
        background-color: #252525;
        color: {c.text_primary};
        border: 1px solid {c.border_color};
        border-radius: 6px;
        gridline-color: #353535;
        selection-background-color: #404040;
        selection-color: white;
        font-size: 9pt;
    }}
    QTableWidget::item {{
        padding: 3px 6px;
    }}
    QTableWidget::item:selected {{
        background-color: #404040;
    }}
    QHeaderView::section {{
        background-color: #2A2A2A;
        color: {c.text_secondary};
        border: none;
        border-bottom: 2px solid {c.border_color};
        border-right: 1px solid #353535;
        padding: 5px 6px;
        font-weight: bold;
        font-size: 8pt;
        text-transform: uppercase;
    }}
    QTableCornerButton::section {{
        background-color: #2A2A2A;
        border: none;
    }}

    /* ===== LABELS ===== */
    QLabel {{
        color: {c.text_primary};
    }}
    QLabel#label_title {{
        font-size: 11pt;
        font-weight: bold;
        color: {c.text_primary};
        padding: 4px 0;
        letter-spacing: 1px;
    }}
    QLabel#label_section {{
        font-size: 9pt;
        font-weight: bold;
        color: {c.text_secondary};
        padding: 2px 0;
        border-bottom: 1px solid {c.border_color};
    }}
    QLabel#label_lot_result {{
        font-size: 13pt;
        font-weight: bold;
        padding: 8px;
        border-radius: 8px;
        text-align: center;
    }}

    /* ===== GROUP BOX ===== */
    QGroupBox {{
        border: 1px solid {c.border_color};
        border-radius: 8px;
        margin-top: 10px;
        padding: 12px 8px 8px 8px;
        font-weight: bold;
        font-size: 9pt;
        color: {c.accent_color};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 10px;
        padding: 0 6px;
    }}

    /* ===== CHECK BOX ===== */
    QCheckBox {{
        spacing: 6px;
        color: {c.text_primary};
        font-size: 9pt;
    }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border: 1px solid #555555;
        border-radius: 3px;
        background-color: #353535;
    }}
    QCheckBox::indicator:checked {{
        background-color: {c.accent_color};
        border-color: {c.accent_color};
    }}
    QCheckBox::indicator:hover {{
        border-color: #666666;
    }}

    /* ===== SCROLL BAR ===== */
    QScrollBar:vertical {{
        background-color: transparent;
        width: 8px;
        border-radius: 4px;
        margin: 2px;
    }}
    QScrollBar::handle:vertical {{
        background-color: #555555;
        border-radius: 4px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: #666666;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar:horizontal {{
        background-color: transparent;
        height: 8px;
        border-radius: 4px;
        margin: 2px;
    }}
    QScrollBar::handle:horizontal {{
        background-color: #555555;
        border-radius: 4px;
        min-width: 30px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background-color: #666666;
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}

    /* ===== FRAME (CARD STYLE) ===== */
    QFrame#card {{
        background-color: {c.bg_card};
        border: 1px solid {c.border_color};
        border-radius: 10px;
        padding: 10px;
    }}

    /* ===== SPLITTER ===== */
    QSplitter::handle {{
        background-color: {c.border_color};
        width: 1px;
        margin: 4px 2px;
    }}

    /* ===== STATUS BAR ===== */
    QStatusBar {{
        background-color: {c.bg_secondary};
        color: {c.text_secondary};
        border-top: 1px solid {c.border_color};
        font-size: 8pt;
        padding: 2px 8px;
    }}

    /* ===== TOOLTIP ===== */
    QToolTip {{
        background-color: #3A3A3A;
        color: {c.text_primary};
        border: 1px solid #555555;
        border-radius: 4px;
        padding: 4px 8px;
        font-size: 9pt;
    }}
    """
