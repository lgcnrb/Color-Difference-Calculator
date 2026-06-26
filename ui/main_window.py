# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QByteArray, QBuffer, QIODevice
from PyQt6.QtGui import QImage, QPixmap, QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QTabWidget, QPushButton, QComboBox, QSpinBox, QCheckBox, QLabel,
    QTableWidget, QTableWidgetItem, QGroupBox, QFrame, QLineEdit,
    QFileDialog, QMessageBox, QStatusBar, QHeaderView, QSplitter,
    QAbstractItemView, QScrollArea, QSizePolicy, QDialog,
    QDialogButtonBox, QFormLayout, QTextEdit, QTreeWidget, QTreeWidgetItem,
)

from config.settings import UI, CAMERA, COLOR_ENGINE, DELTA_METHODS, COLOR_SPACES, EXPORT_DIR
from core.camera.manager import CameraManager
from core.color_engine.engine import ColorEngine
from core.spectrophotometer.parser import SpectrophotometerParser
from core.spectrophotometer.cxf3_parser import CxF3Parser, CxF3Measurement
from core.spectrophotometer.watcher import FileWatcher
from core.lotting.engine import DeltaECalculator, LottingEngine
from core.models.color_data import (
    LabColor, LCHColor, RGBColor, SpectralReading, CameraAnalysis,
    DeltaEResult, LottingResult, LotDecision, MeasurementSource,
    MeasurementRecord, MasterColor,
)
from core.job.manager import JobManager, Job, Master, Sample, DynamicField
from core.analysis.spectral_graph import SpectralGraph
from core.analysis.color_plot import ColorPlot
from core.analysis.metamerism import MetamerismChecker, MetamerismReport
from core.analysis.tolerance import ToleranceEngine
from core.export.excel_report import ExcelReport
from core.export.barcode import BarcodeGenerator

logger = logging.getLogger(__name__)


class ColorSwatch(QLabel):
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


class StatCard(QFrame):
    def __init__(self, title: str, value: str = "---", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setFixedHeight(48)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(2)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(
            "color: #999999; font-size: 7pt; border: none; background: transparent;"
        )
        self.title_label.setFixedHeight(14)

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(
            "color: #FFFFFF; font-size: 12pt; font-weight: bold; "
            "border: none; background: transparent;"
        )
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.value_label.setFixedHeight(22)

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)

    def set_value(self, value: str, color: str = "#FFFFFF"):
        self.value_label.setText(value)
        self.value_label.setStyleSheet(
            f"color: {color}; font-size: 12pt; font-weight: bold; "
            f"border: none; background: transparent;"
        )


class SectionHeader(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setObjectName("label_section")
        self.setFixedHeight(24)


class JobDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Yeni Is (Job) Olustur")
        self.setMinimumWidth(400)
        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.customer_edit = QLineEdit()
        self.season_edit = QLineEdit()
        self.desc_edit = QTextEdit()
        self.desc_edit.setFixedHeight(60)

        layout.addRow("Is Adi:", self.name_edit)
        layout.addRow("Musteri:", self.customer_edit)
        layout.addRow("Sezon:", self.season_edit)
        layout.addRow("Aciklama:", self.desc_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)


class MasterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Master Renk Ekle")
        self.setMinimumWidth(400)
        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.l_edit = QLineEdit("50.0")
        self.a_edit = QLineEdit("0.0")
        self.b_edit = QLineEdit("0.0")
        self.tolerans_edit = QLineEdit("1.0")
        self.pantone_edit = QLineEdit()
        self.fabric_edit = QLineEdit()

        layout.addRow("Master Adi:", self.name_edit)
        layout.addRow("L*:", self.l_edit)
        layout.addRow("a*:", self.a_edit)
        layout.addRow("b*:", self.b_edit)
        layout.addRow("Tolerans DE:", self.tolerans_edit)
        layout.addRow("Pantone:", self.pantone_edit)
        layout.addRow("Kumas Tipi:", self.fabric_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)


class DynamicFieldDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dinamik Alan Ekle")
        self.setMinimumWidth(350)
        layout = QFormLayout(self)

        self.key_edit = QLineEdit()
        self.label_edit = QLineEdit()
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Metin", "Sayi", "Tarih", "Secim"])

        layout.addRow("Anahtar:", self.key_edit)
        layout.addRow("Gosterim Adi:", self.label_edit)
        layout.addRow("Tip:", self.type_combo)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.camera = CameraManager()
        self.color_engine = ColorEngine()
        self.parser = SpectrophotometerParser()
        self.job_manager = JobManager()
        self.file_watcher: Optional[FileWatcher] = None
        self.metamerism_checker = MetamerismChecker()

        self.reference_lab: Optional[LabColor] = None
        self.reference_lch: Optional[LCHColor] = None
        self.reference_rgb: Optional[RGBColor] = None
        self.current_reading: Optional[SpectralReading] = None
        self.current_analysis: Optional[CameraAnalysis] = None
        self.current_cxf_measurements: List[CxF3Measurement] = []
        self.measurement_count = 0
        self.lot_data_list: List[Dict] = []

        self._setup_ui()
        self._connect_signals()
        self._apply_style()
        self._refresh_job_tree()
        self._scan_cameras()
        self.statusBar().showMessage("  Hazir  |  Kamerayi acin veya X-Rite dosyasi ekleyin")
        logger.info("iColor Control baslatildi")

    def _setup_ui(self):
        self.setWindowTitle("iColor Control  |  Endustriyel Renk Kontrol Sistemi")
        self.setMinimumSize(1400, 800)
        self.resize(1600, 900)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(6)

        toolbar = self._create_toolbar()
        main_layout.addWidget(toolbar)

        content_splitter = QSplitter(Qt.Orientation.Horizontal)

        left = self._create_job_panel()
        center = self._create_capture_panel()
        right = self._create_result_panel()

        content_splitter.addWidget(left)
        content_splitter.addWidget(center)
        content_splitter.addWidget(right)
        content_splitter.setSizes([240, 500, 380])
        content_splitter.setHandleWidth(1)

        main_layout.addWidget(content_splitter, stretch=3)

        bottom = self._create_lot_panel()
        main_layout.addWidget(bottom, stretch=1)

    def _create_toolbar(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("card")
        frame.setFixedHeight(50)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(8)

        logo = QLabel("iColor Control")
        logo.setStyleSheet(
            "color: #1A7AE8; font-size: 14pt; font-weight: bold; "
            "border: none; background: transparent; letter-spacing: 1px;"
        )
        layout.addWidget(logo)

        sep = QLabel("|")
        sep.setStyleSheet("color: #454545; font-size: 14pt; border: none; background: transparent;")
        layout.addWidget(sep)

        subtitle = QLabel("Endustriyel Renk Kontrol Sistemi  v2.0")
        subtitle.setStyleSheet("color: #888888; font-size: 9pt; border: none; background: transparent;")
        layout.addWidget(subtitle)

        layout.addStretch()

        lbl_de = QLabel("Delta E:")
        lbl_de.setStyleSheet("color: #888888; font-size: 9pt; border: none; background: transparent;")
        layout.addWidget(lbl_de)

        self.combo_de = QComboBox()
        for key, label in DELTA_METHODS.display_names().items():
            self.combo_de.addItem(label, key)
        self.combo_de.setFixedWidth(110)
        layout.addWidget(self.combo_de)

        self.btn_watch_dir = QPushButton("  Watch Klasoru Sec  ")
        self.btn_watch_dir.setObjectName("btn_import")
        self.btn_watch_dir.setFixedHeight(32)
        layout.addWidget(self.btn_watch_dir)

        self.btn_save = QPushButton("  Excel Kaydet  ")
        self.btn_save.setObjectName("btn_save")
        self.btn_save.setFixedHeight(32)
        layout.addWidget(self.btn_save)

        return frame

    def _create_job_panel(self) -> QWidget:
        wrapper = QWidget()
        wrapper.setObjectName("card")
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        header = SectionHeader("IS YONETIMI")
        layout.addWidget(header)

        btn_row = QHBoxLayout()
        self.btn_new_job = QPushButton("+ YENI IS")
        self.btn_new_job.setObjectName("btn_setref")
        self.btn_new_job.setFixedHeight(30)
        btn_row.addWidget(self.btn_new_job)

        self.btn_new_master = QPushButton("+ MASTER")
        self.btn_new_master.setObjectName("btn_open_cam")
        self.btn_new_master.setFixedHeight(30)
        btn_row.addWidget(self.btn_new_master)
        layout.addLayout(btn_row)

        self.btn_add_dynamic = QPushButton("+ DINAMIK ALAN")
        self.btn_add_dynamic.setObjectName("btn_import")
        self.btn_add_dynamic.setFixedHeight(28)
        layout.addWidget(self.btn_add_dynamic)

        self.job_tree = QTreeWidget()
        self.job_tree.setHeaderLabels(["Is / Master / Numune"])
        self.job_tree.setRootIsDecorated(True)
        self.job_tree.setAlternatingRowColors(True)
        self.job_tree.setMinimumHeight(120)
        layout.addWidget(self.job_tree, stretch=1)

        info_group = QGroupBox("SECILI DETAY")
        info_layout = QVBoxLayout(info_group)
        info_layout.setContentsMargins(4, 10, 4, 4)
        info_layout.setSpacing(1)

        self.info_table = QTableWidget(6, 2)
        self.info_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.info_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.info_table.verticalHeader().setVisible(False)
        self.info_table.horizontalHeader().setVisible(False)
        self.info_table.setShowGrid(False)
        self.info_table.verticalHeader().setDefaultSectionSize(16)
        self.info_table.setColumnWidth(0, 70)
        self.info_table.setColumnWidth(1, 100)

        info_labels = ["Tip", "Adi", "Musteri", "L*", "a*", "b*"]
        for row, label in enumerate(info_labels):
            lbl_item = QTableWidgetItem(label)
            lbl_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            lbl_item.setForeground(QColor("#888888"))
            lbl_item.setFont(QFont(UI.font_family, 8, QFont.Weight.Bold))
            self.info_table.setItem(row, 0, lbl_item)
            val_item = QTableWidgetItem("---")
            val_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            val_item.setFont(QFont("Consolas", 8))
            self.info_table.setItem(row, 1, val_item)

        info_layout.addWidget(self.info_table)
        layout.addWidget(info_group)

        stats_row = QHBoxLayout()
        self.stat_jobs = StatCard("Is", "0")
        self.stat_jobs.setFixedHeight(36)
        self.stat_samples = StatCard("Numune", "0")
        self.stat_samples.setFixedHeight(36)
        stats_row.addWidget(self.stat_jobs)
        stats_row.addWidget(self.stat_samples)
        layout.addLayout(stats_row)
        return wrapper

    def _create_capture_panel(self) -> QWidget:
        wrapper = QWidget()
        wrapper.setObjectName("card")
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        tabs = QTabWidget()

        camera_tab = QWidget()
        cam_layout = QVBoxLayout(camera_tab)
        cam_layout.setContentsMargins(4, 4, 4, 4)
        cam_layout.setSpacing(4)

        self.camera_label = QLabel()
        self.camera_label.setMinimumHeight(280)
        self.camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_label.setStyleSheet(
            "background-color: #1A1A1A; border: 2px solid #353535; border-radius: 8px;"
            "color: #555555; font-size: 10pt;"
        )
        self.camera_label.setText("Kamera kapali")
        cam_layout.addWidget(self.camera_label, stretch=1)

        cam_row = QHBoxLayout()
        cam_row.setSpacing(4)
        self.btn_open_camera = QPushButton("KAMERAYI AC")
        self.btn_open_camera.setObjectName("btn_open_cam")
        self.btn_open_camera.setFixedHeight(32)
        self.btn_open_camera.setCursor(Qt.CursorShape.PointingHandCursor)
        cam_row.addWidget(self.btn_open_camera)

        self.combo_camera = QComboBox()
        self.combo_camera.setFixedHeight(32)
        cam_row.addWidget(self.combo_camera)
        cam_layout.addLayout(cam_row)

        self.btn_capture = QPushButton("SNAP")
        self.btn_capture.setObjectName("btn_capture")
        self.btn_capture.setFixedHeight(44)
        self.btn_capture.setCursor(Qt.CursorShape.PointingHandCursor)
        cam_layout.addWidget(self.btn_capture)

        snap_row = QHBoxLayout()
        snap_row.setSpacing(8)
        self.snap_swatch = ColorSwatch(56)
        snap_row.addWidget(self.snap_swatch)
        snap_info = QVBoxLayout()
        snap_info.setSpacing(1)
        self.snap_hex = QLabel("RENK: ---")
        self.snap_hex.setStyleSheet("color: #CCCCCC; font-size: 9pt; font-family: Consolas; border: none; background: transparent;")
        self.snap_rgb = QLabel("RGB: -,-,-")
        self.snap_rgb.setStyleSheet("color: #888888; font-size: 7pt; border: none; background: transparent;")
        self.snap_lab = QLabel("LAB: -,-,-")
        self.snap_lab.setStyleSheet("color: #888888; font-size: 7pt; border: none; background: transparent;")
        snap_info.addWidget(self.snap_hex)
        snap_info.addWidget(self.snap_rgb)
        snap_info.addWidget(self.snap_lab)
        snap_row.addLayout(snap_info)
        snap_row.addStretch()
        cam_layout.addLayout(snap_row)

        tabs.addTab(camera_tab, "Kamera")

        import_tab = QWidget()
        imp_layout = QVBoxLayout(import_tab)
        imp_layout.setSpacing(6)

        self.entry_import = QLineEdit()
        self.entry_import.setPlaceholderText("X-Rite dosya yolu (.cxf, .csv, .txt, .xml)...")
        imp_layout.addWidget(self.entry_import)

        imp_btn_row = QHBoxLayout()
        self.btn_import = QPushButton("DOSYA SEC")
        self.btn_import.setObjectName("btn_import")
        imp_btn_row.addWidget(self.btn_import)
        self.btn_load_data = QPushButton("YUKLE")
        self.btn_load_data.setObjectName("btn_capture")
        self.btn_load_data.setFixedWidth(80)
        imp_btn_row.addWidget(self.btn_load_data)
        imp_layout.addLayout(imp_btn_row)

        self.cxf_info = QLabel("CxF3 Dosya Bilgisi: -")
        self.cxf_info.setStyleSheet("color: #888888; font-size: 8pt; border: none; background: transparent;")
        imp_layout.addWidget(self.cxf_info)

        self.watch_status = QLabel("Watch: Kapali")
        self.watch_status.setStyleSheet("color: #888888; font-size: 8pt; border: none; background: transparent;")
        imp_layout.addWidget(self.watch_status)

        imp_layout.addStretch()
        tabs.addTab(import_tab, "Spektrofotometre")

        spectral_tab = QWidget()
        spec_layout = QVBoxLayout(spectral_tab)
        self.spectral_plot_label = QLabel("Spektral egriler yuklenmedi")
        self.spectral_plot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spectral_plot_label.setStyleSheet(
            "background-color: #1A1A1A; border: 2px solid #353535; border-radius: 8px; "
            "color: #555555; font-size: 9pt;"
        )
        self.spectral_plot_label.setMinimumHeight(280)
        spec_layout.addWidget(self.spectral_plot_label)
        tabs.addTab(spectral_tab, "Spektral Egriler")

        colorplot_tab = QWidget()
        cp_layout = QVBoxLayout(colorplot_tab)
        self.color_plot_label = QLabel("Renk sapma grafigi yuklenmedi")
        self.color_plot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.color_plot_label.setStyleSheet(
            "background-color: #1A1A1A; border: 2px solid #353535; border-radius: 8px; "
            "color: #555555; font-size: 9pt;"
        )
        self.color_plot_label.setMinimumHeight(280)
        cp_layout.addWidget(self.color_plot_label)
        tabs.addTab(colorplot_tab, "Target Board")

        metamerism_tab = QWidget()
        met_layout = QVBoxLayout(metamerism_tab)
        self.metamerism_table = QTableWidget(0, 4)
        self.metamerism_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.metamerism_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.metamerism_table.verticalHeader().setVisible(False)
        self.metamerism_table.setHorizontalHeaderLabels(["Isik Kaynagi", "Delta E", "Durum", "Uyari"])
        self.metamerism_table.horizontalHeader().setStretchLastSection(True)
        met_layout.addWidget(self.metamerism_table)
        tabs.addTab(metamerism_tab, "Metamerizm")

        layout.addWidget(tabs)
        return wrapper

    def _create_result_panel(self) -> QWidget:
        wrapper = QWidget()
        wrapper.setObjectName("card")
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        header = SectionHeader("OLCUM SONUCLARI")
        layout.addWidget(header)

        self.stat_de = StatCard("DELTA E (CIEDE 2000)", "---")
        self.stat_l = StatCard("L* (Parlaklik)", "---")
        self.stat_a = StatCard("a* (Kirmizi-Yesil)", "---")
        self.stat_b = StatCard("b* (Sari-Mavi)", "---")

        layout.addWidget(self.stat_de)
        layout.addWidget(self.stat_l)
        layout.addWidget(self.stat_a)
        layout.addWidget(self.stat_b)

        layout.addSpacing(4)

        self.lot_result = QLabel("")
        self.lot_result.setObjectName("label_lot_result")
        self.lot_result.setFixedHeight(40)
        self.lot_result.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lot_result.setStyleSheet(
            "background-color: #252525; border: 2px solid #353535; border-radius: 8px; "
            "color: #888888; font-size: 11pt; font-weight: bold;"
        )
        layout.addWidget(self.lot_result)

        layout.addSpacing(2)

        barcode_frame = QFrame()
        barcode_frame.setStyleSheet(
            "background-color: #FFFFFF; border-radius: 6px;"
        )
        barcode_frame.setFixedHeight(36)
        barcode_layout = QVBoxLayout(barcode_frame)
        barcode_layout.setContentsMargins(8, 2, 8, 2)
        self.barcode_label = QLabel("Barkod: Olcum yapin")
        self.barcode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.barcode_label.setStyleSheet(
            "color: #333333; font-size: 8pt; font-family: Consolas; "
            "background: transparent; border: none;"
        )
        barcode_layout.addWidget(self.barcode_label)
        layout.addWidget(barcode_frame)

        layout.addSpacing(4)

        detail_group = QGroupBox("DETAYLI SONUCLAR")
        detail_group.setStyleSheet(
            "QGroupBox { font-size: 8pt; padding-top: 12px; } "
            "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 6px; }"
        )
        detail_layout = QVBoxLayout(detail_group)
        detail_layout.setContentsMargins(4, 8, 4, 4)
        detail_layout.setSpacing(2)

        self.result_table = QTableWidget(0, 3)
        self.result_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.result_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.result_table.verticalHeader().setVisible(False)
        self.result_table.setShowGrid(True)
        self.result_table.setAlternatingRowColors(True)
        self.result_table.verticalHeader().setDefaultSectionSize(16)
        self.result_table.horizontalHeader().setStretchLastSection(True)
        self.result_table.setColumnWidth(0, 70)
        self.result_table.setColumnWidth(1, 80)
        self.result_table.setColumnWidth(2, 60)
        self.result_table.setHorizontalHeaderLabels(["Parametre", "Deger", "Birim"])

        for row, (param, val, unit) in enumerate([
            ("L*", "---", ""), ("a*", "---", ""), ("b*", "---", ""),
            ("C*", "---", ""), ("h", "---", "derece"), ("Delta E", "---", ""),
        ]):
            self.result_table.insertRow(row)
            for col, text in enumerate([param, val, unit]):
                item = QTableWidgetItem(text)
                item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                if col == 0:
                    item.setForeground(QColor("#888888"))
                    item.setFont(QFont(UI.font_family, 8, QFont.Weight.Bold))
                else:
                    item.setFont(QFont("Consolas", 8))
                self.result_table.setItem(row, col, item)

        detail_layout.addWidget(self.result_table)
        layout.addWidget(detail_group)

        layout.addStretch()
        return wrapper

    def _create_lot_panel(self) -> QWidget:
        wrapper = QFrame()
        wrapper.setObjectName("card")
        wrapper.setMinimumHeight(180)

        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        header_row = QHBoxLayout()
        lbl = SectionHeader("LOT GRUPLANDIRMA")
        header_row.addWidget(lbl)
        header_row.addStretch()

        self.btn_lot_decision = QPushButton("LOT KARARI UYGULA")
        self.btn_lot_decision.setObjectName("btn_setref")
        self.btn_lot_decision.setFixedHeight(32)
        self.btn_lot_decision.setFixedWidth(170)
        header_row.addWidget(self.btn_lot_decision)
        layout.addLayout(header_row)

        self.lot_table = QTableWidget(0, 6)
        self.lot_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.lot_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.lot_table.verticalHeader().setVisible(False)
        self.lot_table.setShowGrid(True)
        self.lot_table.setAlternatingRowColors(True)
        self.lot_table.verticalHeader().setDefaultSectionSize(22)
        self.lot_table.setHorizontalHeaderLabels(["Lot", "Ort. DE", "Min DE", "Max DE", "Adet", "Durum"])
        header_view = self.lot_table.horizontalHeader()
        header_view.setDefaultSectionSize(90)
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.lot_table, stretch=1)

        return wrapper

    def _connect_signals(self):
        self.btn_open_camera.clicked.connect(self._toggle_camera)
        self.btn_capture.clicked.connect(self._capture_snapshot)
        self.btn_import.clicked.connect(self._browse_file)
        self.btn_load_data.clicked.connect(self._import_spectro_data)
        self.btn_save.clicked.connect(self._export_to_excel)
        self.btn_lot_decision.clicked.connect(self._run_lot_decision)
        self.combo_de.currentIndexChanged.connect(self._update_delta_e_method)
        self.btn_new_job.clicked.connect(self._create_new_job)
        self.btn_new_master.clicked.connect(self._add_master)
        self.btn_add_dynamic.clicked.connect(self._add_dynamic_field)
        self.btn_watch_dir.clicked.connect(self._select_watch_dir)
        self.job_tree.itemClicked.connect(self._on_tree_item_clicked)

    def _apply_style(self):
        from ui.styles.dark_theme import get_dark_stylesheet
        self.setStyleSheet(get_dark_stylesheet())

    def _scan_cameras(self):
        self.combo_camera.clear()
        try:
            available = self.camera.list_devices()
            if available:
                for dev_id in available:
                    self.combo_camera.addItem(f"Kamera {dev_id}", dev_id)
                logger.info("Kameralar tarandi: %s", available)
            else:
                self.combo_camera.addItem("Kamera bulunamadi", -1)
                logger.warning("Kamera bulunamadi")
        except Exception as e:
            self.combo_camera.addItem("Kamera tarama hatasi", -1)
            logger.error("Kamera tarama hatasi: %s", e)

    def _toggle_camera(self):
        if self.camera.is_opened:
            self.camera.release()
            self.btn_open_camera.setText("KAMERAYI AC")
            self.btn_open_camera.setObjectName("btn_open_cam")
            self.btn_open_camera.setStyleSheet(self.styleSheet())
            self.camera_label.setText("Kamera kapali")
            self.camera_label.setPixmap(QPixmap())
            self.statusBar().showMessage("  Kamera kapatildi")
            logger.info("Kamera kapatildi")
        else:
            cam_id = self.combo_camera.currentData()
            if cam_id is None or cam_id < 0:
                cam_id = 0
                logger.info("Kamera secilmemis, varsayilan device_id=0 kullaniliyor")

            logger.info("Kamera aciliyor: device_id=%d", cam_id)
            if self.camera.open(cam_id):
                self.btn_open_camera.setText("KAMERAYI KAPAT")
                self.btn_open_camera.setObjectName("btn_reset")
                self.btn_open_camera.setStyleSheet(self.styleSheet())
                self._update_camera_feed()
                self.statusBar().showMessage(f"  Kamera acildi (device_id={cam_id})")
                logger.info("Kamera basariyla acildi: device_id=%d", cam_id)
            else:
                QMessageBox.warning(
                    self, "Kamera Hata",
                    f"Kamera acilamadi!\n\n"
                    f"Device ID: {cam_id}\n"
                    f"Kontrol edin:\n"
                    f"- Kamera takili mi?\n"
                    f"- Baska bir uygulama kullaniyor mu?\n"
                    f"- Surucu yuklu mu?"
                )
                self.statusBar().showMessage(f"  Kamera acilamadi (device_id={cam_id})")
                logger.error("Kamera acilamadi: device_id=%d", cam_id)

    def _update_camera_feed(self):
        if not self.camera.is_opened:
            return
        cam_frame = self.camera.read_frame()
        if cam_frame is not None:
            frame = cam_frame.raw_bgr
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

    def _capture_snapshot(self):
        cam_frame = self.camera.read_frame() if self.camera.is_opened else None
        frame = cam_frame.raw_bgr if cam_frame is not None else None
        if frame is None:
            frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)

        analysis = self.color_engine.analyze_surface(frame)
        self.current_analysis = analysis

        lab = analysis.mean_lab
        from core.color_engine.color_convert import lab_to_rgb_single
        r, g, b = lab_to_rgb_single(lab.L, lab.a, lab.b)

        self.snap_swatch.set_color(r, g, b)
        self.snap_hex.setText(f"RENK: #{r:02X}{g:02X}{b:02X}")
        self.snap_rgb.setText(f"RGB: {r}, {g}, {b}")
        self.snap_lab.setText(f"LAB: {lab.L:.1f}, {lab.a:.1f}, {lab.b:.1f}")

        lch = LCHColor(
            L=lab.L,
            C=(lab.a**2 + lab.b**2)**0.5,
            H=np.degrees(np.arctan2(lab.b, lab.a)) % 360,
        )

        if self.reference_lab is None:
            self._set_reference_from_lab(lab, "Otomatik Referans")
            self.statusBar().showMessage(
                f"  Ilk olcum referans olarak ayarlandi  |  "
                f"LAB=({lab.L:.1f}, {lab.a:.1f}, {lab.b:.1f})"
            )
            return

        de = self._calc_delta_e(lab)

        self._update_stat_cards(de, lab, lch)
        self._update_result_table(de, lab, lch)
        self._update_lot_decision(de)
        self._update_lot_table(de)
        self._update_target_board(de, lab)
        self._generate_barcode(de)

        self.measurement_count += 1
        self.statusBar().showMessage(
            f"  Olcum #{self.measurement_count}  |  DE={de:.3f}  |  "
            f"LAB=({lab.L:.1f}, {lab.a:.1f}, {lab.b:.1f})  |  {self._de_category(de)}"
        )

    def _calc_delta_e(self, lab: LabColor) -> float:
        method = self.combo_de.currentData()
        if self.reference_lab is None:
            return -1.0
        return DeltaECalculator.calculate(self.reference_lab, lab, method)

    def _update_delta_e_method(self):
        if self.current_analysis and self.reference_lab:
            de = self._calc_delta_e(self.current_analysis.dominant_lab)
            self.stat_de.set_value(f"{de:.3f}", UI.error_color if de > 1.0 else UI.success_color)

    def _set_reference_from_lab(self, lab: LabColor, name: str = "Referans"):
        self.reference_lab = lab
        self.reference_lch = LCHColor(
            L=lab.L,
            C=(lab.a**2 + lab.b**2)**0.5,
            H=np.degrees(np.arctan2(lab.b, lab.a)) % 360,
        )
        from core.color_engine.color_convert import lab_to_rgb_single
        r, g, b = lab_to_rgb_single(lab.L, lab.a, lab.b)
        self.reference_rgb = RGBColor(R=r, G=g, B=b)

        self.info_table.item(0, 1).setText("Master")
        self.info_table.item(1, 1).setText(name)
        self.info_table.item(3, 1).setText(f"{lab.L:.2f}")
        self.info_table.item(4, 1).setText(f"{lab.a:.2f}")
        self.info_table.item(5, 1).setText(f"{lab.b:.2f}")

    def _set_reference(self):
        if self.current_analysis is None:
            QMessageBox.information(self, "Bilgi", "Once bir olcum yapin (SNAP).")
            return
        lab = self.current_analysis.dominant_lab
        self._set_reference_from_lab(lab, "Kamera Referansi")

    def _reset_reference(self):
        self.reference_lab = None
        self.reference_lch = None
        self.reference_rgb = None

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
        self.lot_data_list = []
        self.barcode_label.clear()

        for row in range(6):
            self.result_table.item(row, 1).setText("---")

        self.measurement_count = 0
        self.current_analysis = None

    def _update_stat_cards(self, de: float, lab: LabColor, lch: LCHColor):
        de_color = UI.error_color if de > 1.0 else (UI.warning_color if de > 0.5 else UI.success_color)
        self.stat_de.set_value(f"{de:.3f}", de_color)
        self.stat_l.set_value(f"{lab.L:.2f}", "#FFFFFF")
        self.stat_a.set_value(f"{lab.a:.2f}", "#FFFFFF")
        self.stat_b.set_value(f"{lab.b:.2f}", "#FFFFFF")

    def _update_result_table(self, de: float, lab: LabColor, lch: LCHColor):
        values = [
            (f"{lab.L:.2f}", ""), (f"{lab.a:.2f}", ""), (f"{lab.b:.2f}", ""),
            (f"{lch.C:.2f}", ""), (f"{lch.H:.2f}", ""), (f"{de:.3f}", ""),
        ]
        for row, (val, _) in enumerate(values):
            self.result_table.item(row, 1).setText(val)

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
        self.lot_data_list.append({
            "de": de,
            "lab": self.current_analysis.mean_lab if self.current_analysis else None,
        })

        self.lot_table.setRowCount(0)
        for i, entry in enumerate(self.lot_data_list):
            row = self.lot_table.rowCount()
            self.lot_table.insertRow(row)

            letter = chr(65 + (i % 26))
            if i >= 26:
                letter = f"A{chr(65 + (i - 26) % 26)}"
            lot_name = f"LOT-{letter}"

            de_val = entry["de"]
            lab = entry["lab"]
            values = [
                lot_name,
                f"{de_val:.3f}",
                f"{de_val:.3f}",
                f"{de_val:.3f}",
                "1",
                self._de_category(de_val),
            ]
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

    def _update_target_board(self, de: float, lab: LabColor):
        if self.reference_lab is None:
            return
        da = lab.a - self.reference_lab.a
        db = lab.b - self.reference_lab.b
        tolerans = 1.0

        measurements = [(da, db, f"#{self.measurement_count+1:03d}")]
        img_bytes = ColorPlot.create_target_board(measurements, tolerans)
        if img_bytes:
            pixmap = QPixmap()
            pixmap.loadFromData(QByteArray(img_bytes))
            scaled = pixmap.scaled(
                self.color_plot_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.color_plot_label.setPixmap(scaled)

    def _generate_barcode(self, de: float):
        if self.reference_lab is None:
            return
        lot = self._de_category(de)
        code = BarcodeGenerator.generate_codebar(lot, customer="iColor")
        de_str = f"{de:.3f}"
        self.barcode_label.setText(f"||| {code} |||  DE: {de_str}")

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

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Spektrofotometre Dosyasi Sec", "",
            "Tum Desteklenen (*.cxf *.csv *.txt *.xml);;CxF3 (*.cxf);;CSV (*.csv);;TXT (*.txt);;XML (*.xml)"
        )
        if path:
            self.entry_import.setText(path)

    def _import_spectro_data(self):
        path = self.entry_import.text().strip()
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "Hata", "Gecerli bir dosya yolu girin.")
            return

        ext = os.path.splitext(path)[1].lower()
        try:
            if ext == ".cxf":
                measurements = CxF3Parser.parse_file(path)
                self.current_cxf_measurements = measurements
                if measurements:
                    self.cxf_info.setText(
                        f"CxF3: {len(measurements)} olcum  |  "
                        f"Illuminant: {measurements[0].illuminant}  |  "
                        f"Observer: {measurements[0].observer_angle}"
                    )
                    if measurements[0].lab:
                        self._set_reference_from_lab(measurements[0].lab, measurements[0].sample_name)
                    if measurements[0].has_spectral_data:
                        self._update_spectral_graph(measurements)
            else:
                readings = self.parser.parse_file(path)
                if readings:
                    self.cxf_info.setText(f"Yuklendi: {len(readings)} olcum")
                    if readings[0].lab:
                        self._set_reference_from_lab(readings[0].lab, readings[0].sample_id)

            self.statusBar().showMessage(f"  Dosya yuklendi: {os.path.basename(path)}")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Dosya okunamadi:\n{e}")

    def _update_spectral_graph(self, measurements: List[CxF3Measurement]):
        if len(measurements) < 1:
            return
        curves = []
        colors = ["#1A7AE8", "#E85D1A", "#107C10", "#FFD700", "#C42B1C"]
        for i, m in enumerate(measurements):
            if m.has_spectral_data:
                refl = m.interpolate_to_380_780()
                curves.append((m.sample_name, refl, colors[i % len(colors)]))

        if curves:
            img_bytes = SpectralGraph.create_multi_plot(curves)
            if img_bytes:
                pixmap = QPixmap()
                pixmap.loadFromData(QByteArray(img_bytes))
                scaled = pixmap.scaled(
                    self.spectral_plot_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.spectral_plot_label.setPixmap(scaled)

    def _select_watch_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Watch Klasoru Sec")
        if dir_path:
            self._start_watcher(dir_path)

    def _start_watcher(self, dir_path: str):
        if self.file_watcher:
            self.file_watcher.stop()

        self.file_watcher = FileWatcher(dir_path, self._on_watcher_file)
        if self.file_watcher.start():
            self.watch_status.setText(f"Watch: Aktif  |  {dir_path}")
            self.watch_status.setStyleSheet("color: #107C10; font-size: 8pt; border: none; background: transparent;")
            self.statusBar().showMessage(f"  Watch baslatildi: {dir_path}")
        else:
            self.watch_status.setText("Watch: HATA")

    def _on_watcher_file(self, filepath: str, measurements: List[CxF3Measurement]):
        self.current_cxf_measurements = measurements
        if measurements and measurements[0].lab:
            self._set_reference_from_lab(measurements[0].lab, measurements[0].sample_name)
        if measurements and measurements[0].has_spectral_data:
            self._update_spectral_graph(measurements)
        QTimer.singleShot(0, lambda: self.statusBar().showMessage(
            f"  Yeni dosya: {os.path.basename(filepath)} ({len(measurements)} olcum)"
        ))

    def _export_to_excel(self):
        if not self.lot_data_list:
            QMessageBox.information(self, "Bilgi", "Kaydedilecek olcum yok.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Excel Kaydet",
            f"renk_raporu_{datetime.now():%Y%m%d_%H%M%S}.xlsx",
            "Excel Dosyasi (*.xlsx)"
        )
        if not path:
            return

        try:
            master_info = {}
            if self.reference_lab:
                master_info = {"L": self.reference_lab.L, "a": self.reference_lab.a, "b": self.reference_lab.b}

            samples = []
            for i, entry in enumerate(self.lot_data_list):
                de_val = entry["de"]
                lab = entry["lab"]
                letter = chr(65 + (i % 26))
                if i >= 26:
                    letter = f"A{chr(65 + (i - 26) % 26)}"
                samples.append({
                    "name": f"LOT-{letter}",
                    "delta_e": de_val,
                    "status": self._de_category(de_val),
                    "L": lab.L if lab else 0,
                    "a": lab.a if lab else 0,
                    "b": lab.b if lab else 0,
                })

            report = ExcelReport()
            success = report.create_report(
                filepath=path,
                job_name="iColor Control Raporu",
                customer="Genel",
                master_info=master_info,
                samples=samples,
            )

            if success:
                self.statusBar().showMessage(f"  Kaydedildi: {path}")
            else:
                QMessageBox.warning(self, "Hata", "Excel raporu olusturulamadi.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydedilemedi:\n{e}")

    def _run_lot_decision(self):
        if self.lot_table.rowCount() == 0:
            QMessageBox.information(self, "Bilgi", "Once olcum yapin.")
            return
        self.statusBar().showMessage("  Lot karari uygulandi")

    def _create_new_job(self):
        dialog = JobDialog(self)
        if dialog.exec():
            job = self.job_manager.create_job(
                name=dialog.name_edit.text(),
                customer=dialog.customer_edit.text(),
                season=dialog.season_edit.text(),
                description=dialog.desc_edit.toPlainText(),
            )
            self._refresh_job_tree()
            self.stat_jobs.set_value(str(len(self.job_manager.jobs)))
            self.statusBar().showMessage(f"  Yeni is olusturuldu: {job.name}")

    def _add_master(self):
        job_id = self._get_selected_job_id()
        if not job_id:
            QMessageBox.information(self, "Bilgi", "Once bir is secin.")
            return

        dialog = MasterDialog(self)
        if dialog.exec():
            lab = LabColor(
                L=float(dialog.l_edit.text()),
                a=float(dialog.a_edit.text()),
                b=float(dialog.b_edit.text()),
            )
            master = Master(
                name=dialog.name_edit.text(),
                lab=lab,
                tolerans_de=float(dialog.tolerans_edit.text()),
                pantone=dialog.pantone_edit.text(),
                fabric_type=dialog.fabric_edit.text(),
            )
            self.job_manager.add_master(job_id, master)
            self._set_reference_from_lab(lab, master.name)
            self._refresh_job_tree()
            self.statusBar().showMessage(f"  Master eklendi: {master.name}")

    def _add_dynamic_field(self):
        job_id = self._get_selected_job_id()
        if not job_id:
            QMessageBox.information(self, "Bilgi", "Once bir is secin.")
            return

        dialog = DynamicFieldDialog(self)
        if dialog.exec():
            type_map = {"Metin": "text", "Sayi": "number", "Tarih": "date", "Secim": "select"}
            self.job_manager.add_dynamic_field_def(
                job_id,
                key=dialog.key_edit.text(),
                label=dialog.label_edit.text(),
                field_type=type_map.get(dialog.type_combo.currentText(), "text"),
            )
            self.statusBar().showMessage(f"  Dinamik alan eklendi: {dialog.label_edit.text()}")

    def _refresh_job_tree(self):
        self.job_tree.clear()
        for job in self.job_manager.jobs:
            job_item = QTreeWidgetItem(self.job_tree)
            job_item.setText(0, f"[{job.customer}] {job.name}")
            job_item.setData(0, Qt.ItemDataRole.UserRole, ("job", job.id))

            for master in job.masters:
                master_item = QTreeWidgetItem(job_item)
                master_item.setText(0, f"Master: {master.name}")
                master_item.setData(0, Qt.ItemDataRole.UserRole, ("master", master.id))

                for sample in job.samples:
                    sample_item = QTreeWidgetItem(master_item)
                    status_icon = "+" if sample.status == "Gecti" else "X"
                    sample_item.setText(0, f"{status_icon} {sample.name} (DE={sample.delta_e:.2f})")
                    sample_item.setData(0, Qt.ItemDataRole.UserRole, ("sample", sample.id))

        self.stat_jobs.set_value(str(len(self.job_manager.jobs)))
        total_samples = sum(j.total_samples for j in self.job_manager.jobs)
        self.stat_samples.set_value(str(total_samples))

    def _get_selected_job_id(self) -> Optional[str]:
        item = self.job_tree.currentItem()
        if item:
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if data:
                return data[1]
        if self.job_manager.jobs:
            return self.job_manager.jobs[-1].id
        return None

    def _on_tree_item_clicked(self, item, column):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return

        item_type, item_id = data
        if item_type == "job":
            job = self.job_manager.get_job(item_id)
            if job:
                self.info_table.item(0, 1).setText("Is")
                self.info_table.item(1, 1).setText(job.name)
                self.info_table.item(2, 1).setText(job.customer)
        elif item_type == "master":
            for job in self.job_manager.jobs:
                for m in job.masters:
                    if m.id == item_id:
                        self.info_table.item(0, 1).setText("Master")
                        self.info_table.item(1, 1).setText(m.name)
                        if m.lab:
                            self._set_reference_from_lab(m.lab, m.name)
                            self.info_table.item(3, 1).setText(f"{m.lab.L:.2f}")
                            self.info_table.item(4, 1).setText(f"{m.lab.a:.2f}")
                            self.info_table.item(5, 1).setText(f"{m.lab.b:.2f}")

    def closeEvent(self, event):
        if self.file_watcher:
            self.file_watcher.stop()
        self.camera.release()
        event.accept()
