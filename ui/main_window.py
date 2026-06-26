# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import List, Optional, Tuple

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
    QApplication, QSlider,
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
        self.setWindowTitle("Create New Job")
        self.setMinimumWidth(400)
        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.customer_edit = QLineEdit()
        self.season_edit = QLineEdit()
        self.desc_edit = QTextEdit()
        self.desc_edit.setFixedHeight(60)

        layout.addRow("Job Name:", self.name_edit)
        layout.addRow("Customer:", self.customer_edit)
        layout.addRow("Season:", self.season_edit)
        layout.addRow("Description:", self.desc_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)


class MasterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Master Color")
        self.setMinimumWidth(400)
        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.l_edit = QLineEdit("50.0")
        self.a_edit = QLineEdit("0.0")
        self.b_edit = QLineEdit("0.0")
        self.tolerance_edit = QLineEdit("1.0")
        self.pantone_edit = QLineEdit()
        self.fabric_edit = QLineEdit()

        layout.addRow("Master Name:", self.name_edit)
        layout.addRow("L*:", self.l_edit)
        layout.addRow("a*:", self.a_edit)
        layout.addRow("b*:", self.b_edit)
        layout.addRow("Tolerance DE:", self.tolerance_edit)
        layout.addRow("Pantone:", self.pantone_edit)
        layout.addRow("Fabric Type:", self.fabric_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)


class SampleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Sample")
        self.setMinimumWidth(350)
        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.batch_edit = QLineEdit()

        layout.addRow("Sample Name:", self.name_edit)
        layout.addRow("Batch No:", self.batch_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)


class DynamicFieldDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Dynamic Field")
        self.setMinimumWidth(350)
        layout = QFormLayout(self)

        self.key_edit = QLineEdit()
        self.label_edit = QLineEdit()
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Text", "Number", "Date", "Selection"])

        layout.addRow("Key:", self.key_edit)
        layout.addRow("Display Name:", self.label_edit)
        layout.addRow("Type:", self.type_combo)

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
        self.lotting_engine = LottingEngine()
        self.file_watcher: Optional[FileWatcher] = None
        self.metamerism_checker = MetamerismChecker()

        self.reference_lab: Optional[LabColor] = None
        self.reference_lch: Optional[LCHColor] = None
        self.reference_rgb: Optional[RGBColor] = None
        self.current_reading: Optional[SpectralReading] = None
        self.current_analysis: Optional[CameraAnalysis] = None
        self.current_cxf_measurements: List[CxF3Measurement] = []
        self.measurement_count = 0
        self.current_frame: Optional[np.ndarray] = None

        self._setup_ui()
        self._connect_signals()
        self._apply_style()
        self._scan_cameras()
        self.statusBar().showMessage("  Ready  |  Open camera or add X-Rite file")
        logger.info("ColorIQ started")

    def _setup_ui(self):
        self.setWindowTitle("ColorIQ  |  Industrial Color Control System")
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

        center = self._create_capture_panel()
        right = self._create_result_panel()

        content_splitter.addWidget(center)
        content_splitter.addWidget(right)
        content_splitter.setSizes([500, 500])
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

        logo = QLabel("ColorIQ")
        logo.setStyleSheet(
            "color: #1A7AE8; font-size: 14pt; font-weight: bold; "
            "border: none; background: transparent; letter-spacing: 1px;"
        )
        layout.addWidget(logo)

        sep = QLabel("|")
        sep.setStyleSheet("color: #454545; font-size: 14pt; border: none; background: transparent;")
        layout.addWidget(sep)

        subtitle = QLabel("Industrial Color Control System  v2.1")
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

        self.btn_watch_dir = QPushButton("  Select Watch Folder  ")
        self.btn_watch_dir.setObjectName("btn_import")
        self.btn_watch_dir.setFixedHeight(32)
        layout.addWidget(self.btn_watch_dir)

        self.btn_save = QPushButton("  Save Excel  ")
        self.btn_save.setObjectName("btn_save")
        self.btn_save.setFixedHeight(32)
        layout.addWidget(self.btn_save)

        return frame

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
        self.camera_label.setText("Camera off")
        cam_layout.addWidget(self.camera_label, stretch=1)

        cam_row = QHBoxLayout()
        cam_row.setSpacing(4)
        self.btn_open_camera = QPushButton("OPEN CAMERA")
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
        self.snap_hex = QLabel("COLOR: ---")
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

        tabs.addTab(camera_tab, "Camera")

        import_tab = QWidget()
        imp_layout = QVBoxLayout(import_tab)
        imp_layout.setSpacing(6)

        self.entry_import = QLineEdit()
        self.entry_import.setPlaceholderText("X-Rite file path (.cxf, .csv, .txt, .xml)...")
        imp_layout.addWidget(self.entry_import)

        imp_btn_row = QHBoxLayout()
        self.btn_import = QPushButton("SELECT FILE")
        self.btn_import.setObjectName("btn_import")
        imp_btn_row.addWidget(self.btn_import)
        self.btn_load_data = QPushButton("LOAD")
        self.btn_load_data.setObjectName("btn_capture")
        self.btn_load_data.setFixedWidth(80)
        imp_btn_row.addWidget(self.btn_load_data)
        imp_layout.addLayout(imp_btn_row)

        self.cxf_info = QLabel("CxF3 File Info: -")
        self.cxf_info.setStyleSheet("color: #888888; font-size: 8pt; border: none; background: transparent;")
        imp_layout.addWidget(self.cxf_info)

        self.watch_status = QLabel("Watch: Off")
        self.watch_status.setStyleSheet("color: #888888; font-size: 8pt; border: none; background: transparent;")
        imp_layout.addWidget(self.watch_status)

        imp_layout.addStretch()
        tabs.addTab(import_tab, "Spectrophotometer")

        spectral_tab = QWidget()
        spec_layout = QVBoxLayout(spectral_tab)
        self.spectral_plot_label = QLabel("Spectral curves not loaded")
        self.spectral_plot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spectral_plot_label.setStyleSheet(
            "background-color: #1A1A1A; border: 2px solid #353535; border-radius: 8px; "
            "color: #555555; font-size: 9pt;"
        )
        self.spectral_plot_label.setMinimumHeight(280)
        spec_layout.addWidget(self.spectral_plot_label)
        tabs.addTab(spectral_tab, "Spectral Curves")

        colorplot_tab = QWidget()
        cp_layout = QVBoxLayout(colorplot_tab)
        self.color_plot_label = QLabel("Color deviation graph not loaded")
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
        self.metamerism_table.setHorizontalHeaderLabels(["Light Source", "Delta E", "Status", "Warning"])
        self.metamerism_table.horizontalHeader().setStretchLastSection(True)
        met_layout.addWidget(self.metamerism_table)
        tabs.addTab(metamerism_tab, "Metamerism")

        layout.addWidget(tabs)
        return wrapper

    def _create_result_panel(self) -> QWidget:
        wrapper = QWidget()
        wrapper.setObjectName("card")
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        header = SectionHeader("MEASUREMENT RESULTS")
        layout.addWidget(header)

        self.stat_de = StatCard("DELTA E (CIEDE 2000)", "---")
        self.stat_l = StatCard("L* (Lightness)", "---")
        self.stat_a = StatCard("a* (Red-Green)", "---")
        self.stat_b = StatCard("b* (Yellow-Blue)", "---")

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
        self.barcode_label = QLabel("Barcode: Take measurement")
        self.barcode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.barcode_label.setStyleSheet(
            "color: #333333; font-size: 8pt; font-family: Consolas; "
            "background: transparent; border: none;"
        )
        barcode_layout.addWidget(self.barcode_label)
        layout.addWidget(barcode_frame)

        layout.addSpacing(4)

        detail_group = QGroupBox("DETAILED RESULTS")
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
        self.result_table.setHorizontalHeaderLabels(["Parameter", "Value", "Unit"])

        for row, (param, val, unit) in enumerate([
            ("L*", "---", ""), ("a*", "---", ""), ("b*", "---", ""),
            ("C*", "---", ""), ("h", "---", "degrees"), ("Delta E", "---", ""),
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
        wrapper.setMinimumHeight(200)

        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        header_row = QHBoxLayout()
        lbl = SectionHeader("LOT GROUPING")
        header_row.addWidget(lbl)
        header_row.addStretch()

        self.btn_lot_decision = QPushButton("APPLY LOT DECISION")
        self.btn_lot_decision.setObjectName("btn_setref")
        self.btn_lot_decision.setFixedHeight(32)
        self.btn_lot_decision.setFixedWidth(170)
        header_row.addWidget(self.btn_lot_decision)
        layout.addLayout(header_row)

        method_row = QHBoxLayout()
        method_lbl = QLabel("Method:")
        method_lbl.setStyleSheet("color: #AAAAAA; font-size: 9pt;")
        method_row.addWidget(method_lbl)

        self.combo_method = QComboBox()
        self.combo_method.setFixedHeight(26)
        self.combo_method.addItem("K-Means (Automatic k)", "kmeans")
        self.combo_method.addItem("DBSCAN (Density)", "dbscan")
        self.combo_method.addItem("Agglomerative (Hierarchical)", "agglomerative")
        self.combo_method.currentIndexChanged.connect(self._on_method_changed)
        method_row.addWidget(self.combo_method, stretch=1)
        layout.addLayout(method_row)

        self.method_desc = QLabel("Determines optimal k using silhouette score. Fast and general purpose.")
        self.method_desc.setStyleSheet("color: #777777; font-size: 8pt; font-style: italic; border: none; background: transparent;")
        self.method_desc.setWordWrap(True)
        layout.addWidget(self.method_desc)

        param_row = QHBoxLayout()
        param_row.setSpacing(6)

        self.param_k_label = QLabel("k:")
        self.param_k_label.setStyleSheet("color: #AAAAAA; font-size: 9pt;")
        param_row.addWidget(self.param_k_label)

        self.spin_k = QSpinBox()
        self.spin_k.setRange(2, 20)
        self.spin_k.setValue(3)
        self.spin_k.setFixedHeight(26)
        self.spin_k.setFixedWidth(50)
        self.spin_k.valueChanged.connect(self._on_param_changed)
        param_row.addWidget(self.spin_k)

        self.param_auto_k = QCheckBox("Automatic")
        self.param_auto_k.setChecked(True)
        self.param_auto_k.setStyleSheet("color: #AAAAAA; font-size: 9pt;")
        self.param_auto_k.stateChanged.connect(self._on_param_changed)
        param_row.addWidget(self.param_auto_k)

        param_row.addSpacing(10)

        self.param_eps_label = QLabel("EPS:")
        self.param_eps_label.setStyleSheet("color: #AAAAAA; font-size: 9pt;")
        param_row.addWidget(self.param_eps_label)

        self.spin_eps = QSpinBox()
        self.spin_eps.setRange(1, 50)
        self.spin_eps.setValue(10)
        self.spin_eps.setFixedHeight(26)
        self.spin_eps.setFixedWidth(50)
        self.spin_eps.setSuffix("")
        self.spin_eps.valueChanged.connect(self._on_param_changed)
        param_row.addWidget(self.spin_eps)

        self.param_min_samples_label = QLabel("Min N:")
        self.param_min_samples_label.setStyleSheet("color: #AAAAAA; font-size: 9pt;")
        param_row.addWidget(self.param_min_samples_label)

        self.spin_min_samples = QSpinBox()
        self.spin_min_samples.setRange(1, 10)
        self.spin_min_samples.setValue(2)
        self.spin_min_samples.setFixedHeight(26)
        self.spin_min_samples.setFixedWidth(40)
        self.spin_min_samples.valueChanged.connect(self._on_param_changed)
        param_row.addWidget(self.spin_min_samples)

        param_row.addSpacing(10)

        self.param_linkage_label = QLabel("Linkage:")
        self.param_linkage_label.setStyleSheet("color: #AAAAAA; font-size: 9pt;")
        param_row.addWidget(self.param_linkage_label)

        self.combo_linkage = QComboBox()
        self.combo_linkage.setFixedHeight(26)
        self.combo_linkage.setFixedWidth(70)
        self.combo_linkage.addItems(["ward", "complete", "average", "single"])
        self.combo_linkage.currentTextChanged.connect(self._on_param_changed)
        param_row.addWidget(self.combo_linkage)

        param_row.addStretch()
        layout.addLayout(param_row)

        self._update_method_ui()

        tol_row = QHBoxLayout()
        tol_lbl = QLabel("Tolerance:")
        tol_lbl.setStyleSheet("color: #AAAAAA; font-size: 9pt;")
        tol_row.addWidget(tol_lbl)

        self.tolerance_slider = QSlider(Qt.Orientation.Horizontal)
        self.tolerance_slider.setRange(1, 50)
        self.tolerance_slider.setValue(10)
        self.tolerance_slider.setTickPosition(QSlider.TickPosition.NoTicks)
        tol_row.addWidget(self.tolerance_slider, stretch=1)

        self.tolerance_value = QLabel("1.0")
        self.tolerance_value.setStyleSheet("color: #FFFFFF; font-size: 9pt; font-weight: bold; min-width: 35px;")
        self.tolerance_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tol_row.addWidget(self.tolerance_value)
        layout.addLayout(tol_row)

        self.lot_table = QTableWidget(0, 6)
        self.lot_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.lot_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.lot_table.verticalHeader().setVisible(False)
        self.lot_table.setShowGrid(True)
        self.lot_table.setAlternatingRowColors(True)
        self.lot_table.verticalHeader().setDefaultSectionSize(22)
        self.lot_table.setHorizontalHeaderLabels(["Lot", "Avg DE", "Min DE", "Max DE", "Count", "Status"])
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
        self.tolerance_slider.valueChanged.connect(self._on_tolerance_changed)
        self.combo_de.currentIndexChanged.connect(self._update_delta_e_method)
        self.btn_watch_dir.clicked.connect(self._select_watch_dir)

    def _apply_style(self):
        from ui.styles.dark_theme import get_dark_stylesheet
        self.setStyleSheet(get_dark_stylesheet())

    def _scan_cameras(self):
        self.combo_camera.clear()
        try:
            available = self.camera.list_devices()
            if available:
                for dev_id in available:
                    self.combo_camera.addItem(f"Camera {dev_id}", dev_id)
                logger.info("Cameras scanned: %s", available)
            else:
                self.combo_camera.addItem("Camera not found", -1)
                logger.warning("Camera not found")
        except Exception as e:
            self.combo_camera.addItem("Camera scan error", -1)
            logger.error("Camera scan error: %s", e)

    def _toggle_camera(self):
        if self.camera.is_opened:
            self.camera.release()
            self.btn_open_camera.setText("OPEN CAMERA")
            self.btn_open_camera.setObjectName("btn_open_cam")
            self.btn_open_camera.setStyleSheet(self.styleSheet())
            self.camera_label.setText("Camera off")
            self.camera_label.setPixmap(QPixmap())
            self.statusBar().showMessage("  Camera closed")
            logger.info("Camera closed")
        else:
            cam_id = self.combo_camera.currentData()
            if cam_id is None or cam_id < 0:
                cam_id = 0
                logger.info("No camera selected, using default device_id=0")

            logger.info("Opening camera: device_id=%d", cam_id)
            if self.camera.open(cam_id):
                self.btn_open_camera.setText("CLOSE CAMERA")
                self.btn_open_camera.setObjectName("btn_reset")
                self.btn_open_camera.setStyleSheet(self.styleSheet())
                self._update_camera_feed()
                self.statusBar().showMessage(f"  Camera opened (device_id={cam_id})")
                logger.info("Camera opened successfully: device_id=%d", cam_id)
            else:
                QMessageBox.warning(
                    self, "Camera Error",
                    f"Camera could not be opened!\n\n"
                    f"Device ID: {cam_id}\n"
                    f"Check:\n"
                    f"- Is camera connected?\n"
                    f"- Is another application using it?\n"
                    f"- Is driver installed?"
                )
                self.statusBar().showMessage(f"  Camera could not be opened (device_id={cam_id})")
                logger.error("Camera could not be opened: device_id=%d", cam_id)

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

    def _ensure_job_folder(self):
        if not self.lotting_engine.job_folder:
            job_folder = os.path.join(EXPORT_DIR, "auto_measurements")
            self.lotting_engine.set_job_folder(job_folder)

    def _capture_snapshot(self):
        cam_frame = self.camera.read_frame() if self.camera.is_opened else None
        frame = cam_frame.raw_bgr if cam_frame is not None else None
        if frame is None:
            frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)

        self.current_frame = frame.copy()
        self._ensure_job_folder()

        analysis = self.color_engine.analyze_surface(frame)
        self.current_analysis = analysis

        lab = analysis.mean_lab
        from core.color_engine.color_convert import lab_to_rgb_single
        r, g, b = lab_to_rgb_single(lab.L, lab.a, lab.b)

        self.snap_swatch.set_color(r, g, b)
        self.snap_hex.setText(f"COLOR: #{r:02X}{g:02X}{b:02X}")
        self.snap_rgb.setText(f"RGB: {r}, {g}, {b}")
        self.snap_lab.setText(f"LAB: {lab.L:.1f}, {lab.a:.1f}, {lab.b:.1f}")

        lch = LCHColor(
            L=lab.L,
            C=(lab.a**2 + lab.b**2)**0.5,
            H=np.degrees(np.arctan2(lab.b, lab.a)) % 360,
        )

        self.lotting_engine.save_measurement(frame, lab)

        new_record = self.lotting_engine.measurements[-1]
        lot_group = self.lotting_engine.assign_lot_for_new(new_record)

        self._update_stat_cards(-1.0, lab, lch)
        self._update_result_table(-1.0, lab, lch)
        self._update_lot_decision_from_group(lot_group)
        self._update_target_board(-1.0, lab)
        self._generate_barcode(-1.0)

        if len(self.lotting_engine.measurements) >= 2:
            self._refresh_lot_table()

        self.measurement_count += 1
        self.statusBar().showMessage(
            f"  Measurement #{self.measurement_count}  |  "
            f"LAB=({lab.L:.1f}, {lab.a:.1f}, {lab.b:.1f})  |  "
            f"Lot: {lot_group}  |  "
            f"Recorded: {len(self.lotting_engine.measurements)}"
        )

    def _calc_delta_e(self, lab: LabColor) -> float:
        if self.reference_lab is None:
            return -1.0
        result = DeltaECalculator.calculate(self.reference_lab, lab)
        method = self.combo_de.currentData()
        return result.get_by_method(method)

    def _update_delta_e_method(self):
        if self.current_analysis and self.reference_lab:
            de = self._calc_delta_e(self.current_analysis.mean_lab)
            self.stat_de.set_value(f"{de:.3f}", UI.danger_color if de > 1.0 else UI.success_color)

    def _on_tolerance_changed(self, value: int):
        eps = value / 10.0
        self.tolerance_value.setText(f"{eps:.1f}")
        self.lotting_engine.set_tolerance(eps)
        if len(self.lotting_engine.measurements) >= 2:
            self._refresh_lot_table()

    def _on_method_changed(self, index):
        method = self.combo_method.currentData()
        if method:
            self.lotting_engine.set_clustering_method(method)
            self._update_method_ui()
            if len(self.lotting_engine.measurements) >= 2:
                self._refresh_lot_table()

    def _update_method_ui(self):
        method = self.combo_method.currentData()
        info = LottingEngine.CLUSTERING_METHODS.get(method, {})
        self.method_desc.setText(info.get("description", ""))

        is_kmeans = method == "kmeans"
        is_dbscan = method == "dbscan"
        is_agglo = method == "agglomerative"

        self.param_k_label.setVisible(is_kmeans or is_agglo)
        self.spin_k.setVisible(is_kmeans or is_agglo)
        self.param_auto_k.setVisible(is_kmeans or is_agglo)

        self.param_eps_label.setVisible(is_dbscan)
        self.spin_eps.setVisible(is_dbscan)
        self.param_min_samples_label.setVisible(is_dbscan)
        self.spin_min_samples.setVisible(is_dbscan)

        self.param_linkage_label.setVisible(is_agglo)
        self.combo_linkage.setVisible(is_agglo)

    def _on_param_changed(self):
        method = self.combo_method.currentData()
        if method == "kmeans":
            self.lotting_engine.set_method_param("auto_k", self.param_auto_k.isChecked())
            self.lotting_engine.set_method_param("fixed_k", self.spin_k.value())
            self.spin_k.setEnabled(not self.param_auto_k.isChecked())
        elif method == "dbscan":
            self.lotting_engine.set_method_param("eps", self.spin_eps.value() / 10.0)
            self.lotting_engine.set_method_param("min_samples", self.spin_min_samples.value())
        elif method == "agglomerative":
            self.lotting_engine.set_method_param("auto_k", self.param_auto_k.isChecked())
            self.lotting_engine.set_method_param("fixed_k", self.spin_k.value())
            self.lotting_engine.set_method_param("linkage", self.combo_linkage.currentText())
            self.spin_k.setEnabled(not self.param_auto_k.isChecked())

        if len(self.lotting_engine.measurements) >= 2:
            self._refresh_lot_table()

    def _refresh_lot_table(self):
        if not self.lotting_engine.measurements:
            return
        report = self.lotting_engine.generate_report()
        stats = report["lot_statistics"]
        self.lot_table.setRowCount(0)
        for stat in stats:
            row = self.lot_table.rowCount()
            self.lot_table.insertRow(row)
            values = [
                stat["lot"],
                f"{stat['de_mean']:.3f}",
                f"{stat['de_min']:.3f}",
                f"{stat['de_max']:.3f}",
                str(stat["count"]),
                stat["status"],
            ]
            for col, text in enumerate(values):
                item = QTableWidgetItem(text)
                item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                if col == 5:
                    if "Perfect" in text or "Good" in text:
                        item.setForeground(QColor(UI.success_color))
                    elif "Borderline" in text:
                        item.setForeground(QColor(UI.warning_color))
                    else:
                        item.setForeground(QColor(UI.danger_color))
                elif col == 0:
                    item.setFont(QFont(UI.font_family, 9, QFont.Weight.Bold))
                else:
                    item.setFont(QFont("Consolas", 9))
                self.lot_table.setItem(row, col, item)

    def _set_reference_from_lab(self, lab: LabColor, name: str = "Reference"):
        self.reference_lab = lab
        self.reference_lch = LCHColor(
            L=lab.L,
            C=(lab.a**2 + lab.b**2)**0.5,
            H=np.degrees(np.arctan2(lab.b, lab.a)) % 360,
        )
        from core.color_engine.color_convert import lab_to_rgb_single
        r, g, b = lab_to_rgb_single(lab.L, lab.a, lab.b)
        self.reference_rgb = RGBColor(R=r, G=g, B=b)

    def _set_reference(self):
        if self.current_analysis is None:
            QMessageBox.information(self, "Info", "Take a measurement first (SNAP).")
            return
        lab = self.current_analysis.mean_lab
        self._set_reference_from_lab(lab, "Camera Reference")

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
        self.barcode_label.clear()

        for row in range(6):
            self.result_table.item(row, 1).setText("---")

        self.measurement_count = 0
        self.current_analysis = None

    def _update_stat_cards(self, de: float, lab: LabColor, lch: LCHColor):
        de_color = UI.danger_color if de > 1.0 else (UI.warning_color if de > 0.5 else UI.success_color)
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
            text = "LOT A  -  Perfect Match"
            bg, fg = "#0D3B0D", "#90EE90"
        elif de <= 1.0:
            text = "LOT B  -  Good Match"
            bg, fg = "#1A3A1A", "#80FF80"
        elif de <= 2.0:
            text = "LOT C  -  Acceptable"
            bg, fg = "#3B3B0D", "#FFFF80"
        elif de <= 3.5:
            text = "LOT D  -  Borderline"
            bg, fg = "#3B2B0D", "#FFD080"
        else:
            text = "LOT F  -  REJECTED"
            bg, fg = "#3B0D0D", "#FF8080"

        self.lot_result.setText(text)
        self.lot_result.setStyleSheet(
            f"background-color: {bg}; border: 2px solid #454545; border-radius: 8px; "
            f"color: {fg}; font-size: 12pt; font-weight: bold;"
        )

    def _update_lot_decision_from_group(self, lot_group: str):
        lot_colors = {
            "LOT-A": ("LOT A  -  Perfect Match", "#0D3B0D", "#90EE90"),
            "LOT-B": ("LOT B  -  Good Match", "#1A3A1A", "#80FF80"),
            "LOT-C": ("LOT C  -  Acceptable", "#3B3B0D", "#FFFF80"),
            "LOT-D": ("LOT D  -  Borderline", "#3B2B0D", "#FFD080"),
            "LOT-F": ("LOT F  -  REJECTED", "#3B0D0D", "#FF8080"),
        }
        text, bg, fg = lot_colors.get(lot_group, (f"{lot_group}", "#252525", "#FFFFFF"))

        self.lot_result.setText(text)
        self.lot_result.setStyleSheet(
            f"background-color: {bg}; border: 2px solid #454545; border-radius: 8px; "
            f"color: {fg}; font-size: 12pt; font-weight: bold;"
        )

    def _update_target_board(self, de: float, lab: LabColor):
        measurements = []
        for i, m in enumerate(self.lotting_engine.measurements):
            if m.lab:
                da = m.lab.a
                db = m.lab.b
                measurements.append((da, db, f"#{i+1:03d}"))

        if not measurements:
            return

        tolerance = self.lotting_engine.tolerance_eps
        img_bytes = ColorPlot.create_target_board(measurements, tolerance)
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
        lot = "Unknown"
        if self.lotting_engine.measurements:
            last = self.lotting_engine.measurements[-1]
            if last.lot_group:
                lot = last.lot_group.replace("LOT-", "LOT ")
        code = BarcodeGenerator.generate_codebar(lot, customer="ColorIQ")
        de_str = f"{de:.3f}" if de >= 0 else "---"
        self.barcode_label.setText(f"||| {code} |||  DE: {de_str}")

    @staticmethod
    def _de_category(de: float) -> str:
        if de <= 0.5:
            return "Perfect"
        elif de <= 1.0:
            return "Good"
        elif de <= 2.0:
            return "Acceptable"
        elif de <= 3.5:
            return "Borderline"
        else:
            return "REJECTED"

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Spectrophotometer File", "",
            "All Supported (*.cxf *.csv *.txt *.xml);;CxF3 (*.cxf);;CSV (*.csv);;TXT (*.txt);;XML (*.xml)"
        )
        if path:
            self.entry_import.setText(path)

    def _import_spectro_data(self):
        path = self.entry_import.text().strip()
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "Error", "Enter a valid file path.")
            return

        ext = os.path.splitext(path)[1].lower()
        try:
            if ext == ".cxf":
                measurements = CxF3Parser.parse_file(path)
                self.current_cxf_measurements = measurements
                if measurements:
                    self.cxf_info.setText(
                        f"CxF3: {len(measurements)} measurements  |  "
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
                    self.cxf_info.setText(f"Loaded: {len(readings)} measurements")
                    if readings[0].lab:
                        self._set_reference_from_lab(readings[0].lab, readings[0].sample_id)

            self.statusBar().showMessage(f"  File loaded: {os.path.basename(path)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"File could not be read:\n{e}")

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
        dir_path = QFileDialog.getExistingDirectory(self, "Select Watch Folder")
        if dir_path:
            self._start_watcher(dir_path)

    def _start_watcher(self, dir_path: str):
        if self.file_watcher:
            self.file_watcher.stop()

        self.file_watcher = FileWatcher(dir_path, self._on_watcher_file)
        if self.file_watcher.start():
            self.watch_status.setText(f"Watch: Active  |  {dir_path}")
            self.watch_status.setStyleSheet("color: #107C10; font-size: 8pt; border: none; background: transparent;")
            self.statusBar().showMessage(f"  Watch started: {dir_path}")
        else:
            self.watch_status.setText("Watch: ERROR")

    def _on_watcher_file(self, filepath: str, measurements: List[CxF3Measurement]):
        self.current_cxf_measurements = measurements
        if measurements and measurements[0].lab:
            self._set_reference_from_lab(measurements[0].lab, measurements[0].sample_name)
        if measurements and measurements[0].has_spectral_data:
            self._update_spectral_graph(measurements)
        QTimer.singleShot(0, lambda: self.statusBar().showMessage(
            f"  New file: {os.path.basename(filepath)} ({len(measurements)} measurements)"
        ))

    def _export_to_excel(self):
        if not self.lotting_engine.measurements:
            QMessageBox.information(self, "Info", "No measurements to save.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Save Excel",
            f"color_report_{datetime.now():%Y%m%d_%H%M%S}.xlsx",
            "Excel File (*.xlsx)"
        )
        if not path:
            return

        try:
            samples = []
            for i, m in enumerate(self.lotting_engine.measurements):
                if m.lab:
                    samples.append({
                        "name": m.lot_group or f"Measurement-{i+1}",
                        "delta_e": m.delta_e,
                        "status": "Passed",
                        "L": m.lab.L,
                        "a": m.lab.a,
                        "b": m.lab.b,
                    })

            report = ExcelReport()
            success = report.create_report(
                filepath=path,
                job_name="ColorIQ Report",
                customer="General",
                master_info={},
                samples=samples,
            )

            if success:
                self.statusBar().showMessage(f"  Saved: {path}")
            else:
                QMessageBox.warning(self, "Error", "Excel report could not be created.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not be saved:\n{e}")

    def _run_lot_decision(self):
        if not self.lotting_engine.measurements:
            QMessageBox.information(self, "Info", "Take a measurement first (SNAP).")
            return

        self.statusBar().showMessage("  Computing lot decision...")
        QApplication.processEvents()

        self.lotting_engine.batch_analyze()

        report = self.lotting_engine.generate_report()
        stats = report["lot_statistics"]

        self.lot_table.setRowCount(0)
        for stat in stats:
            row = self.lot_table.rowCount()
            self.lot_table.insertRow(row)

            values = [
                stat["lot"],
                f"{stat['de_mean']:.3f}",
                f"{stat['de_min']:.3f}",
                f"{stat['de_max']:.3f}",
                str(stat["count"]),
                stat["status"],
            ]
            for col, text in enumerate(values):
                item = QTableWidgetItem(text)
                item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                if col == 5:
                    if "Perfect" in text or "Good" in text:
                        item.setForeground(QColor(UI.success_color))
                    elif "Borderline" in text:
                        item.setForeground(QColor(UI.warning_color))
                    else:
                        item.setForeground(QColor(UI.danger_color))
                elif col == 0:
                    item.setFont(QFont(UI.font_family, 9, QFont.Weight.Bold))
                else:
                    item.setFont(QFont("Consolas", 9))
                self.lot_table.setItem(row, col, item)

        total = report["total_measurements"]
        passed = report["passed"]
        rate = report["pass_rate"]

        lot_detail = "\n".join(
            f"  {s['lot']}: {s['count']} samples, Avg.DE={s['de_mean']:.3f} [{s['status']}]"
            for s in stats
        )

        self.statusBar().showMessage(
            f"  Lot decision applied  |  "
            f"Total: {total}  |  Passed: {passed}  |  "
            f"Success: %{rate:.1f}"
        )

        QMessageBox.information(
            self, "Lot Decision",
            f"Total {total} measurements processed.\n\n"
            f"Number of groups: {len(stats)}\n"
            f"Passed: {passed}\n"
            f"Success rate: %{rate:.1f}\n\n"
            f"Detail:\n{lot_detail}"
        )

    def closeEvent(self, event):
        if self.file_watcher:
            self.file_watcher.stop()
        self.camera.release()
        event.accept()
