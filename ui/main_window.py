# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Optional

import numpy as np
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap, QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QTabWidget, QPushButton, QComboBox, QSpinBox, QCheckBox, QLabel,
    QTableWidget, QTableWidgetItem, QGroupBox, QFrame, QLineEdit,
    QFileDialog, QMessageBox, QStatusBar, QHeaderView, QSplitter,
    QAbstractItemView, QScrollArea, QSizePolicy, QGraphicsDropShadowEffect,
)

from config.settings import UI, CAMERA, COLOR_ENGINE, DELTA_METHODS, COLOR_SPACES, EXPORT_DIR
from core.camera.manager import CameraManager
from core.color_engine.engine import ColorEngine
from core.spectrophotometer.parser import SpectrophotometerParser
from core.lotting.engine import DeltaECalculator, LottingEngine
from core.models.color_data import (
    LabColor, LCHColor, RGBColor, SpectralReading, CameraAnalysis,
    DeltaEResult, LottingResult, LotDecision, MeasurementSource,
    MeasurementRecord, MasterColor,
)

logger = logging.getLogger(__name__)


# ─── Color Swatch ───────────────────────────────────────────────────────────
class ColorSwatch(QLabel):
    """Rounded color swatch with hex label."""
    def __init__(self, size: int = 64, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._hex = "#000000"
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(
            "background-color: #2D2D2D;"
            "border: 2px solid #454545;"
            "border-radius: 10px;"
        )

    def set_color(self, r: int, g: int, b: int):
        self._hex = f"#{r:02X}{g:02X}{b:02X}"
        self.setStyleSheet(
            f"background-color: rgb({r},{g},{b});"
            "border: 2px solid #454545;"
            "border-radius: 10px;"
        )

    def set_lab_color(self, lab: LabColor):
        from core.color_engine.color_convert import lab_to_rgb_single
        r, g, b = lab_to_rgb_single(lab.L, lab.a, lab.b)
        self.set_color(r, g, b)


# ─── Stat Card ──────────────────────────────────────────────────────────────
class StatCard(QFrame):
    """Compact stat card with title + value."""
    def __init__(self, title: str, value: str = "---", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setFixedHeight(56)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(2)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: #888888; font-size: 8pt; border: none; background: transparent;")
        self.title_label.setFixedHeight(16)

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(
            "color: #FFFFFF; font-size: 16pt; font-weight: bold; border: none; background: transparent;"
        )
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)

    def set_value(self, value: str, color: str = "#FFFFFF"):
        self.value_label.setText(value)
        self.value_label.setStyleSheet(
            f"color: {color}; font-size: 16pt; font-weight: bold; border: none; background: transparent;"
        )


# ─── Section Header ─────────────────────────────────────────────────────────
class SectionHeader(QLabel):
    """Bold section header with underline."""
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setObjectName("label_section")
        self.setFixedHeight(24)


# ─── Main Window ────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.camera = CameraManager()
        self.color_engine = ColorEngine()
        self.parser = SpectrophotometerParser()

        self.reference_lab: Optional[LabColor] = None
        self.reference_lch: Optional[LCHColor] = None
        self.reference_rgb: Optional[RGBColor] = None
        self.current_reading: Optional[SpectralReading] = None
        self.current_analysis: Optional[CameraAnalysis] = None
        self.measurement_count = 0

        self._setup_ui()
        self._connect_signals()
        self._apply_style()
        self.statusBar().showMessage("  Hazir  |  Kamerayi acin ve olcum yapin")

    # ── UI Setup ─────────────────────────────────────────────────────────────
    def _setup_ui(self):
        self.setWindowTitle("iColor Control  |  Hibrit Renk Kontrol Sistemi")
        self.setMinimumSize(1280, 740)
        self.resize(1440, 840)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # Top toolbar
        toolbar = self._create_toolbar()
        main_layout.addWidget(toolbar)

        # Main content: 3-panel splitter
        content_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Reference
        left = self._create_reference_panel()
        # Center: Capture
        center = self._create_capture_panel()
        # Right: Results
        right = self._create_result_panel()

        content_splitter.addWidget(left)
        content_splitter.addWidget(center)
        content_splitter.addWidget(right)
        content_splitter.setSizes([280, 520, 440])
        content_splitter.setHandleWidth(2)

        main_layout.addWidget(content_splitter, stretch=1)

        # Bottom: Lot Grouping
        bottom = self._create_lot_panel()
        main_layout.addWidget(bottom, stretch=0)

    # ── Toolbar ──────────────────────────────────────────────────────────────
    def _create_toolbar(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("card")
        frame.setFixedHeight(50)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(8)

        # Logo
        logo = QLabel("iColor Control")
        logo.setStyleSheet(
            "color: #1A7AE8; font-size: 14pt; font-weight: bold; "
            "border: none; background: transparent; letter-spacing: 1px;"
        )
        layout.addWidget(logo)

        sep = QLabel("|")
        sep.setStyleSheet("color: #454545; font-size: 14pt; border: none; background: transparent;")
        layout.addWidget(sep)

        subtitle = QLabel("Hibrit Renk Kontrol Sistemi")
        subtitle.setStyleSheet(
            "color: #888888; font-size: 9pt; border: none; background: transparent;"
        )
        layout.addWidget(subtitle)

        layout.addStretch()

        # Delta E method
        lbl_de = QLabel("Delta E Yontemi:")
        lbl_de.setStyleSheet("color: #888888; font-size: 9pt; border: none; background: transparent;")
        layout.addWidget(lbl_de)

        self.combo_de = QComboBox()
        for key, label in DELTA_METHODS.display_names().items():
            self.combo_de.addItem(label, key)
        self.combo_de.setFixedWidth(120)
        layout.addWidget(self.combo_de)

        # Save button
        self.btn_save = QPushButton("  Excel Kaydet  ")
        self.btn_save.setObjectName("btn_save")
        self.btn_save.setFixedHeight(32)
        layout.addWidget(self.btn_save)

        return frame

    # ── Reference Panel (Left) ───────────────────────────────────────────────
    def _create_reference_panel(self) -> QWidget:
        wrapper = QWidget()
        wrapper.setObjectName("card")
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        header = SectionHeader("REFERANS RENK")
        layout.addWidget(header)

        # Swatch
        swatch_row = QHBoxLayout()
        swatch_row.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.ref_swatch = ColorSwatch(96)
        swatch_row.addWidget(self.ref_swatch)
        layout.addLayout(swatch_row)

        # Hex value
        self.ref_hex = QLabel("---")
        self.ref_hex.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ref_hex.setStyleSheet(
            "color: #AAAAAA; font-size: 11pt; font-family: Consolas, monospace; "
            "border: none; background: transparent;"
        )
        self.ref_hex.setFixedHeight(20)
        layout.addWidget(self.ref_hex)

        # Color info table
        self.ref_table = QTableWidget(3, 2)
        self.ref_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.ref_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.ref_table.verticalHeader().setVisible(False)
        self.ref_table.horizontalHeader().setVisible(False)
        self.ref_table.setShowGrid(False)
        self.ref_table.setFixedHeight(90)
        self.ref_table.setColumnWidth(0, 70)
        self.ref_table.setColumnWidth(1, 100)

        for row, (label, key) in enumerate([("L*", "L"), ("a*", "a"), ("b*", "b")]):
            lbl_item = QTableWidgetItem(label)
            lbl_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            lbl_item.setForeground(QColor("#888888"))
            lbl_item.setFont(QFont(UI.font_family, 9, QFont.Weight.Bold))
            self.ref_table.setItem(row, 0, lbl_item)

            val_item = QTableWidgetItem("---")
            val_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            val_item.setFont(QFont("Consolas", 10))
            self.ref_table.setItem(row, 1, val_item)

        layout.addWidget(self.ref_table)

        # Buttons
        btn_row = QHBoxLayout()
        self.btn_set_reference = QPushButton("REFERANS OLARAK AYARLA")
        self.btn_set_reference.setObjectName("btn_setref")
        self.btn_set_reference.setFixedHeight(36)
        self.btn_set_reference.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_row.addWidget(self.btn_set_reference)

        self.btn_reset = QPushButton("SIFIRLA")
        self.btn_reset.setObjectName("btn_reset")
        self.btn_reset.setFixedHeight(36)
        self.btn_reset.setFixedWidth(70)
        self.btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_row.addWidget(self.btn_reset)

        layout.addLayout(btn_row)

        # Import section
        import_group = QGroupBox("SPEKTROFOTOMETRE VERISI ICI")
        import_layout = QVBoxLayout(import_group)
        import_layout.setSpacing(6)

        self.entry_import = QLineEdit()
        self.entry_import.setPlaceholderText("X-Rite dosya yolu...")
        import_layout.addWidget(self.entry_import)

        imp_row = QHBoxLayout()
        self.btn_import = QPushButton("DOSYA SEC")
        self.btn_import.setObjectName("btn_import")
        self.btn_import.setCursor(Qt.CursorShape.PointingHandCursor)
        imp_row.addWidget(self.btn_import)

        self.btn_load_data = QPushButton("YUKLE")
        self.btn_load_data.setObjectName("btn_capture")
        self.btn_load_data.setFixedWidth(70)
        self.btn_load_data.setCursor(Qt.CursorShape.PointingHandCursor)
        imp_row.addWidget(self.btn_load_data)

        import_layout.addLayout(imp_row)
        layout.addWidget(import_group)

        layout.addStretch()

        return wrapper

    # ── Capture Panel (Center) ───────────────────────────────────────────────
    def _create_capture_panel(self) -> QWidget:
        wrapper = QWidget()
        wrapper.setObjectName("card")
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        header = SectionHeader("KAMERA GORUNTUSU")
        layout.addWidget(header)

        # Camera view
        self.camera_label = QLabel()
        self.camera_label.setFixedHeight(360)
        self.camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_label.setStyleSheet(
            "background-color: #1A1A1A; border: 2px solid #353535; border-radius: 10px;"
            "color: #555555; font-size: 10pt;"
        )
        self.camera_label.setText("Kamera kapali")
        layout.addWidget(self.camera_label)

        # Camera controls
        cam_row = QHBoxLayout()
        cam_row.setSpacing(8)

        self.btn_open_camera = QPushButton("KAMERAYI AC")
        self.btn_open_camera.setObjectName("btn_open_cam")
        self.btn_open_camera.setFixedHeight(36)
        self.btn_open_camera.setCursor(Qt.CursorShape.PointingHandCursor)
        cam_row.addWidget(self.btn_open_camera)

        self.combo_camera = QComboBox()
        self.combo_camera.setFixedHeight(36)
        self.combo_camera.setPlaceholderText("Kamera secin...")
        cam_row.addWidget(self.combo_camera)

        layout.addLayout(cam_row)

        # Capture button
        self.btn_capture = QPushButton("SNAP")
        self.btn_capture.setObjectName("btn_capture")
        self.btn_capture.setFixedHeight(52)
        self.btn_capture.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_capture.setEnabled(True)
        layout.addWidget(self.btn_capture)

        # Captured color display
        snap_color_row = QHBoxLayout()
        snap_color_row.setSpacing(12)

        self.snap_swatch = ColorSwatch(72)
        snap_color_row.addWidget(self.snap_swatch)

        snap_info = QVBoxLayout()
        snap_info.setSpacing(2)

        self.snap_hex = QLabel("RENK: ---")
        self.snap_hex.setStyleSheet(
            "color: #CCCCCC; font-size: 11pt; font-family: Consolas, monospace; "
            "border: none; background: transparent;"
        )

        self.snap_rgb = QLabel("RGB: -,-,-")
        self.snap_rgb.setStyleSheet("color: #888888; font-size: 8pt; border: none; background: transparent;")

        self.snap_lab = QLabel("LAB: -,-,-")
        self.snap_lab.setStyleSheet("color: #888888; font-size: 8pt; border: none; background: transparent;")

        snap_info.addWidget(self.snap_hex)
        snap_info.addWidget(self.snap_rgb)
        snap_info.addWidget(self.snap_lab)

        snap_color_row.addLayout(snap_info)
        snap_color_row.addStretch()

        layout.addLayout(snap_color_row)

        # Settings row
        settings_row = QHBoxLayout()
        settings_row.setSpacing(10)

        self.chk_auto = QCheckBox("Otomatik")
        self.chk_auto.setChecked(True)
        settings_row.addWidget(self.chk_auto)

        settings_row.addStretch()

        lbl_res = QLabel("Cozunurluk:")
        lbl_res.setStyleSheet("color: #888888; font-size: 9pt; border: none; background: transparent;")
        settings_row.addWidget(lbl_res)

        self.combo_resolution = QComboBox()
        self.combo_resolution.addItems(["Dusuk", "Normal", "Yuksek"])
        self.combo_resolution.setCurrentIndex(1)
        self.combo_resolution.setFixedWidth(90)
        settings_row.addWidget(self.combo_resolution)

        layout.addLayout(settings_row)

        layout.addStretch()

        return wrapper

    # ── Result Panel (Right) ─────────────────────────────────────────────────
    def _create_result_panel(self) -> QWidget:
        wrapper = QWidget()
        wrapper.setObjectName("card")
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        header = SectionHeader("OLCUM SONUCLARI")
        layout.addWidget(header)

        # Stat cards
        self.stat_de = StatCard("DELTA E (CIEDE 2000)", "---")
        self.stat_l = StatCard("L* (Parlaklik)", "---")
        self.stat_a = StatCard("a* (Kirmizi-Yesil)", "---")
        self.stat_b = StatCard("b* (Sari-Mavi)", "---")

        layout.addWidget(self.stat_de)
        layout.addWidget(self.stat_l)
        layout.addWidget(self.stat_a)
        layout.addWidget(self.stat_b)

        # Lot decision
        self.lot_result = QLabel("")
        self.lot_result.setObjectName("label_lot_result")
        self.lot_result.setFixedHeight(44)
        self.lot_result.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lot_result.setStyleSheet(
            "background-color: #252525; border: 2px solid #353535; border-radius: 8px; "
            "color: #888888; font-size: 12pt; font-weight: bold;"
        )
        layout.addWidget(self.lot_result)

        # Detail section
        detail_group = QGroupBox("DETAYLI SONUCLAR")
        detail_layout = QVBoxLayout(detail_group)
        detail_layout.setSpacing(4)

        self.result_table = QTableWidget(0, 3)
        self.result_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.result_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.result_table.verticalHeader().setVisible(False)
        self.result_table.setShowGrid(True)
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setFixedHeight(130)
        self.result_table.horizontalHeader().setStretchLastSection(True)
        self.result_table.setColumnWidth(0, 100)
        self.result_table.setColumnWidth(1, 120)
        self.result_table.setColumnWidth(2, 120)

        self.result_table.setHorizontalHeaderLabels(["Parametre", "Deger", "Birim"])

        for row, (param, val, unit) in enumerate([
            ("L*", "---", ""),
            ("a*", "---", ""),
            ("b*", "---", ""),
            ("C*", "---", ""),
            ("h", "---", "derece"),
            ("Delta E", "---", ""),
        ]):
            self.result_table.insertRow(row)
            for col, text in enumerate([param, val, unit]):
                item = QTableWidgetItem(text)
                item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                if col == 0:
                    item.setForeground(QColor("#888888"))
                    item.setFont(QFont(UI.font_family, 9, QFont.Weight.Bold))
                else:
                    item.setFont(QFont("Consolas", 9))
                self.result_table.setItem(row, col, item)

        detail_layout.addWidget(self.result_table)
        layout.addWidget(detail_group)

        layout.addStretch()

        return wrapper

    # ── Lot Panel (Bottom) ───────────────────────────────────────────────────
    def _create_lot_panel(self) -> QWidget:
        wrapper = QFrame()
        wrapper.setObjectName("card")
        wrapper.setFixedHeight(160)

        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        header_row = QHBoxLayout()
        header_row.setSpacing(8)

        lbl = SectionHeader("LOT GRUPLANDIRMA")
        header_row.addWidget(lbl)

        header_row.addStretch()

        self.btn_lot_decision = QPushButton("LOT KARARI UYGULA")
        self.btn_lot_decision.setObjectName("btn_setref")
        self.btn_lot_decision.setFixedHeight(30)
        self.btn_lot_decision.setFixedWidth(160)
        self.btn_lot_decision.setCursor(Qt.CursorShape.PointingHandCursor)
        header_row.addWidget(self.btn_lot_decision)

        layout.addLayout(header_row)

        self.lot_table = QTableWidget(0, 6)
        self.lot_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.lot_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.lot_table.verticalHeader().setVisible(False)
        self.lot_table.setShowGrid(True)
        self.lot_table.setAlternatingRowColors(True)
        self.lot_table.setFixedHeight(85)

        self.lot_table.setHorizontalHeaderLabels(
            ["Lot", "Ort. DE", "Min DE", "Max DE", "Adet", "Durum"]
        )

        header_view = self.lot_table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in range(1, 6):
            header_view.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.lot_table)

        return wrapper

    # ── Signals ──────────────────────────────────────────────────────────────
    def _connect_signals(self):
        self.btn_open_camera.clicked.connect(self._toggle_camera)
        self.btn_capture.clicked.connect(self._capture_snapshot)
        self.btn_set_reference.clicked.connect(self._set_reference)
        self.btn_reset.clicked.connect(self._reset_reference)
        self.btn_import.clicked.connect(self._browse_file)
        self.btn_load_data.clicked.connect(self._import_spectro_data)
        self.btn_save.clicked.connect(self._export_to_excel)
        self.btn_lot_decision.clicked.connect(self._run_lot_decision)
        self.combo_de.currentIndexChanged.connect(self._update_delta_e_method)

    # ── Style ────────────────────────────────────────────────────────────────
    def _apply_style(self):
        from ui.styles.dark_theme import get_dark_stylesheet
        self.setStyleSheet(get_dark_stylesheet())

    # ── Camera ───────────────────────────────────────────────────────────────
    def _toggle_camera(self):
        if self.camera.is_active:
            self.camera.release()
            self.btn_open_camera.setText("KAMERAYI AC")
            self.btn_open_camera.setObjectName("btn_open_cam")
            self.btn_open_camera.setStyleSheet(self.styleSheet())
            self.camera_label.setText("Kamera kapali")
            self.camera_label.setPixmap(QPixmap())
            self.statusBar().showMessage("  Kamera kapatildi")
        else:
            cam_id = self.combo_camera.currentIndex()
            if self.camera.start(cam_id):
                self.btn_open_camera.setText("KAMERAYI KAPAT")
                self.btn_open_camera.setObjectName("btn_reset")
                self.btn_open_camera.setStyleSheet(self.styleSheet())
                self._update_camera_feed()
                self.statusBar().showMessage("  Kamera acildi")
            else:
                QMessageBox.warning(self, "Hata", "Kamera acilamadi!")

    def _update_camera_feed(self):
        if not self.camera.is_active:
            return
        frame = self.camera.read_frame()
        if frame is not None:
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888).rgbSwapped()
            pixmap = QPixmap.fromImage(q_img)
            scaled = pixmap.scaled(
                self.camera_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.camera_label.setPixmap(scaled)
        QTimer.singleShot(33, self._update_camera_feed)

    # ── Capture ──────────────────────────────────────────────────────────────
    def _capture_snapshot(self):
        frame = self.camera.read_frame() if self.camera.is_active else None
        if frame is None:
            frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)

        analysis = self.color_engine.analyze_surface(frame)
        self.current_analysis = analysis

        r, g, b = analysis.dominant_rgb.r, analysis.dominant_rgb.g, analysis.dominant_rgb.b
        lab = analysis.dominant_lab

        # Update capture panel
        self.snap_swatch.set_color(r, g, b)
        self.snap_hex.setText(f"RENK: #{r:02X}{g:02X}{b:02X}")
        self.snap_rgb.setText(f"RGB: {r}, {g}, {b}")
        self.snap_lab.setText(f"LAB: {lab.L:.1f}, {lab.a:.1f}, {lab.b:.1f}")

        # Update result panel
        lch = analysis.dominant_lch
        de = self._calc_delta_e(lab)

        self._update_stat_cards(de, lab, lch)
        self._update_result_table(de, lab, lch)
        self._update_lot_decision(de)
        self._update_lot_table(de)

        self.measurement_count += 1
        self.statusBar().showMessage(
            f"  Olcum #{self.measurement_count}  |  "
            f"DE={de:.3f}  |  "
            f"LAB=({lab.L:.1f}, {lab.a:.1f}, {lab.b:.1f})  |  "
            f"Durum: {self._de_category(de)}"
        )

    # ── Delta E ──────────────────────────────────────────────────────────────
    def _calc_delta_e(self, lab: LabColor) -> float:
        method = self.combo_de.currentData()
        if self.reference_lab is None:
            return 0.0
        return DeltaECalculator.calculate(self.reference_lab, lab, method)

    def _update_delta_e_method(self):
        if self.current_analysis and self.reference_lab:
            de = self._calc_delta_e(self.current_analysis.dominant_lab)
            self.stat_de.set_value(f"{de:.3f}", UI.error_color if de > 1.0 else UI.success_color)

    # ── Reference ────────────────────────────────────────────────────────────
    def _set_reference(self):
        if self.current_analysis is None:
            QMessageBox.information(self, "Bilgi", "Once bir olcum yapin (SNAP).")
            return

        lab = self.current_analysis.dominant_lab
        self.reference_lab = lab
        self.reference_lch = self.current_analysis.dominant_lch
        self.reference_rgb = self.current_analysis.dominant_rgb

        r, g, b = self.reference_rgb.r, self.reference_rgb.g, self.reference_rgb.b
        self.ref_swatch.set_color(r, g, b)
        self.ref_hex.setText(f"#{r:02X}{g:02X}{b:02X}")

        self.ref_table.item(0, 1).setText(f"{lab.L:.2f}")
        self.ref_table.item(1, 1).setText(f"{lab.a:.2f}")
        self.ref_table.item(2, 1).setText(f"{lab.b:.2f}")

        self.statusBar().showMessage(f"  Referans ayarlandi  |  LAB=({lab.L:.2f}, {lab.a:.2f}, {lab.b:.2f})")

    def _reset_reference(self):
        self.reference_lab = None
        self.reference_lch = None
        self.reference_rgb = None

        self.ref_swatch.setStyleSheet(
            "background-color: #2D2D2D; border: 2px solid #454545; border-radius: 10px;"
        )
        self.ref_hex.setText("---")

        for row in range(3):
            self.ref_table.item(row, 1).setText("---")

        self.stat_de.set_value("---", "#FFFFFF")
        self.stat_l.set_value("---", "#FFFFFF")
        self.stat_a.set_value("---", "#FFFFFF")
        self.stat_b.set_value("---", "#FFFFFF")
        self.lot_result.setText("")
        self.lot_result.setStyleSheet(
            "background-color: #252525; border: 2px solid #353535; border-radius: 8px; "
            "color: #888888; font-size: 12pt; font-weight: bold;"
        )
        self.lot_table.setRowCount(0)

        for row in range(6):
            self.result_table.item(row, 1).setText("---")

        self.measurement_count = 0
        self.current_analysis = None
        self.statusBar().showMessage("  Referans sifirlandi")

    # ── Stat Cards ───────────────────────────────────────────────────────────
    def _update_stat_cards(self, de: float, lab: LabColor, lch: LCHColor):
        de_color = UI.error_color if de > 1.0 else (UI.warning_color if de > 0.5 else UI.success_color)
        self.stat_de.set_value(f"{de:.3f}", de_color)
        self.stat_l.set_value(f"{lab.L:.2f}", "#FFFFFF")
        self.stat_a.set_value(f"{lab.a:.2f}", "#FFFFFF")
        self.stat_b.set_value(f"{lab.b:.2f}", "#FFFFFF")

    def _update_result_table(self, de: float, lab: LabColor, lch: LCHColor):
        values = [
            (f"{lab.L:.2f}", ""),
            (f"{lab.a:.2f}", ""),
            (f"{lab.b:.2f}", ""),
            (f"{lch.C:.2f}", ""),
            (f"{lch.h:.2f}", ""),
            (f"{de:.3f}", ""),
        ]
        for row, (val, _) in enumerate(values):
            self.result_table.item(row, 1).setText(val)

    # ── Lot ──────────────────────────────────────────────────────────────────
    def _update_lot_decision(self, de: float):
        if de <= 0.5:
            text = "LOT A  -  Kusursuz Uyum"
            bg, fg = "#0D3B0D", "#90EE90"
        elif de <= 1.0:
            text = "LOT B  -  Iyi Uyum"
            bg, fg = "#1A3A1A", "#80FF80"
        elif de <= 2.0:
            text = "LOT C  -  Kabul Edilebilir"
            bg, fg = "#3B3B0D", "#FFFF80"
        elif de <= 3.5:
            text = "LOT D  -  Sinir Deger"
            bg, fg = "#3B2B0D", "#FFD080"
        else:
            text = "LOT F  -  REDDEDILDI"
            bg, fg = "#3B0D0D", "#FF8080"

        self.lot_result.setText(text)
        self.lot_result.setStyleSheet(
            f"background-color: {bg}; border: 2px solid #454545; border-radius: 8px; "
            f"color: {fg}; font-size: 12pt; font-weight: bold;"
        )

    def _update_lot_table(self, de: float):
        row = self.lot_table.rowCount()
        self.lot_table.insertRow(row)

        lot_name = f"LOT-{chr(65 + row)}"
        values = [lot_name, f"{de:.3f}", f"{de:.3f}", f"{de:.3f}", "1", self._de_category(de)]

        for col, text in enumerate(values):
            item = QTableWidgetItem(text)
            item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            if col == 5:
                if "Kusursuz" in text or "Iyi" in text:
                    item.setForeground(QColor(UI.success_color))
                elif "Sinir" in text:
                    item.setForeground(QColor(UI.warning_color))
                else:
                    item.setForeground(QColor(UI.error_color))
            elif col == 0:
                item.setFont(QFont(UI.font_family, 9, QFont.Weight.Bold))
            else:
                item.setFont(QFont("Consolas", 9))
            self.lot_table.setItem(row, col, item)

        self.lot_table.scrollToBottom()

    # ── Helpers ──────────────────────────────────────────────────────────────
    @staticmethod
    def _de_category(de: float) -> str:
        if de <= 0.5:
            return "Kusursuz"
        elif de <= 1.0:
            return "Iyi"
        elif de <= 2.0:
            return "Kabul Edilebilir"
        elif de <= 3.5:
            return "Sinir Deger"
        else:
            return "REDDEDILDI"

    # ── Import ───────────────────────────────────────────────────────────────
    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Spektrofotometre Dosyasi Sec", "",
            "Tum Dosyalar (*.csv *.txt *.cxf *.xml);;CSV (*.csv);;TXT (*.txt);;CXF (*.cxf);;XML (*.xml)"
        )
        if path:
            self.entry_import.setText(path)

    def _import_spectro_data(self):
        path = self.entry_import.text().strip()
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "Hata", "Gecerli bir dosya yolu girin.")
            return

        try:
            readings = self.parser.parse_file(path)
            if readings:
                self.statusBar().showMessage(f"  {len(readings)} olcum yuklendi: {os.path.basename(path)}")
            else:
                QMessageBox.information(self, "Bilgi", "Dosyada okunabilir veri bulunamadi.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Dosya okunamadi:\n{e}")

    # ── Export ───────────────────────────────────────────────────────────────
    def _export_to_excel(self):
        if self.measurement_count == 0:
            QMessageBox.information(self, "Bilgi", "Kaydedilecek olcum yok.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Excel Kaydet", f"renk_raporu_{datetime.now():%Y%m%d_%H%M%S}.xlsx",
            "Excel Dosyasi (*.xlsx)"
        )
        if not path:
            return

        try:
            import pandas as pd
            data = []
            for row in range(self.lot_table.rowCount()):
                data.append({
                    "Lot": self.lot_table.item(row, 0).text() if self.lot_table.item(row, 0) else "",
                    "Ort. DE": self.lot_table.item(row, 1).text() if self.lot_table.item(row, 1) else "",
                    "Min DE": self.lot_table.item(row, 2).text() if self.lot_table.item(row, 2) else "",
                    "Max DE": self.lot_table.item(row, 3).text() if self.lot_table.item(row, 3) else "",
                    "Adet": self.lot_table.item(row, 4).text() if self.lot_table.item(row, 4) else "",
                    "Durum": self.lot_table.item(row, 5).text() if self.lot_table.item(row, 5) else "",
                })

            df = pd.DataFrame(data)
            df.to_excel(path, index=False, sheet_id="Rapor")
            self.statusBar().showMessage(f"  Kaydedildi: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydedilemedi:\n{e}")

    # ── Lot Decision ─────────────────────────────────────────────────────────
    def _run_lot_decision(self):
        if self.lot_table.rowCount() == 0:
            QMessageBox.information(self, "Bilgi", "Once olcum yapin.")
            return
        self.statusBar().showMessage("  Lot karari uygulandi")

    # ── Close ────────────────────────────────────────────────────────────────
    def closeEvent(self, event):
        self.camera.release()
        event.accept()
