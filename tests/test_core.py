# -*- coding: utf-8 -*-
import os
import sys
import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.models.color_data import LabColor, LCHColor, RGBColor, SpectralReading, DeltaEResult, LotDecision
from core.color_engine.engine import ColorEngine
from core.lotting.engine import DeltaECalculator, LottingEngine
from core.spectrophotometer.parser import SpectrophotometerParser


class TestLabColor:
    def test_creation(self):
        lab = LabColor(L=50.0, a=-15.0, b=-20.0)
        assert lab.L == 50.0
        assert lab.a == -15.0
        assert lab.b == -20.0

    def test_to_array(self):
        lab = LabColor(L=50.0, a=-15.0, b=-20.0)
        arr = lab.to_array()
        assert arr[0] == 50.0
        assert arr[1] == -15.0
        assert arr[2] == -20.0

    def test_from_array(self):
        arr = np.array([50.0, -15.0, -20.0])
        lab = LabColor.from_array(arr)
        assert lab.L == 50.0
        assert lab.a == -15.0
        assert lab.b == -20.0


class TestColorEngine:
    def test_rgb_from_frame(self):
        frame = np.zeros((10, 10, 3), dtype=np.uint8)
        frame[:, :] = [128, 64, 32]
        rgb = ColorEngine.rgb_from_frame(frame)
        assert rgb.R == pytest.approx(128.0)
        assert rgb.G == pytest.approx(64.0)
        assert rgb.B == pytest.approx(32.0)

    def test_lab_from_frame(self):
        frame = np.ones((10, 10, 3), dtype=np.uint8) * 128
        lab, lch = ColorEngine.lab_from_frame(frame)
        assert 0 <= lab.L <= 100
        assert -128 <= lab.a <= 128
        assert -128 <= lab.b <= 128

    def test_rgb_difference(self):
        ref = RGBColor(R=100, G=100, B=100)
        meas = RGBColor(R=110, G=90, B=105)
        dr, dg, db = ColorEngine.rgb_difference(ref, meas)
        assert dr == pytest.approx(10.0)
        assert dg == pytest.approx(-10.0)
        assert db == pytest.approx(5.0)

    def test_analyze_surface_homogeneous(self):
        frame = np.ones((50, 50, 3), dtype=np.uint8) * 128
        analysis = ColorEngine.analyze_surface(frame)
        assert analysis.is_homogeneous
        assert analysis.overall_std < 0.1


class TestDeltaECalculator:
    def test_identical_colors(self):
        lab = LabColor(L=50.0, a=-15.0, b=-20.0)
        result = DeltaECalculator.calculate(lab, lab)
        assert result.de_1976 == pytest.approx(0.0, abs=0.01)
        assert result.de_2000 == pytest.approx(0.0, abs=0.01)

    def test_different_colors(self):
        ref = LabColor(L=50.0, a=-15.0, b=-20.0)
        sample = LabColor(L=55.0, a=-10.0, b=-15.0)
        result = DeltaECalculator.calculate(ref, sample)
        assert result.de_1976 > 0
        assert result.de_2000 > 0

    def test_calculate_by_method(self):
        ref = LabColor(L=50.0, a=-15.0, b=-20.0)
        sample = LabColor(L=52.0, a=-13.0, b=-18.0)
        de = DeltaECalculator.calculate_by_method(ref, sample, "delta_e_cie2000")
        assert de > 0


class TestLottingEngine:
    def test_perfect_match(self):
        master = LabColor(L=50.0, a=-15.0, b=-20.0)
        engine = LottingEngine(master, de_target=1.0)
        reading = SpectralReading(lab=LabColor(L=50.0, a=-15.0, b=-20.0))
        de = engine.evaluate_device_reading(reading)
        assert de < 0.1

    def test_lot_decision_a(self):
        master = LabColor(L=50.0, a=-15.0, b=-20.0)
        engine = LottingEngine(master, de_target=1.0)
        result = engine.make_decision(
            device_de=0.5, camera_de=0.4,
            surface_variance=0.5, is_homogeneous=True
        )
        assert result.decision == LotDecision.LOT_A

    def test_lot_decision_red_heterogeneous(self):
        master = LabColor(L=50.0, a=-15.0, b=-20.0)
        engine = LottingEngine(master, de_target=1.0)
        result = engine.make_decision(
            device_de=0.3, camera_de=0.2,
            surface_variance=5.0, is_homogeneous=False
        )
        assert result.decision == LotDecision.RED

    def test_lot_decision_red_high_de(self):
        master = LabColor(L=50.0, a=-15.0, b=-20.0)
        engine = LottingEngine(master, de_target=1.0)
        result = engine.make_decision(
            device_de=2.0, camera_de=2.5,
            surface_variance=1.0, is_homogeneous=True
        )
        assert result.decision == LotDecision.RED


class TestSpectrophotometerParser:
    def test_parse_csv_line(self):
        lab = SpectrophotometerParser.parse_csv_line("50.0,-15.0,-20.0")
        assert lab is not None
        assert lab.L == 50.0

    def test_parse_invalid_line(self):
        lab = SpectrophotometerParser.parse_csv_line("invalid,data")
        assert lab is None

    def test_parse_tab_line(self):
        lab = SpectrophotometerParser.parse_tab_line("50.0\t-15.0\t-20.0")
        assert lab is not None
        assert lab.L == 50.0

    def test_extract_lab_from_text(self):
        lab = SpectrophotometerParser._extract_lab_from_text("L=50.0 a=-15.0 b=-20.0")
        assert lab is not None
        assert lab.L == 50.0
