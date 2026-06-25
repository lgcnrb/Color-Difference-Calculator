# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

# 1. Test color_convert (scikit-image)
from core.color_engine.color_convert import rgb_to_lab, lab_to_lch, lab_to_rgb, rgb_to_lab_single, lab_to_lch_single, lab_to_rgb_single

test_img = np.ones((10, 10, 3), dtype=np.uint8) * 128
lab = rgb_to_lab(test_img)
lch = lab_to_lch(lab)
print(f"[1] color_convert OK: L={lab[0,0,0]:.2f} a={lab[0,0,1]:.2f} b={lab[0,0,2]:.2f}")
print(f"    LCH: L={lch[0,0,0]:.2f} C={lch[0,0,1]:.2f} H={lch[0,0,2]:.2f}")

# Lab -> RGB test
L, a, b = lab_to_rgb_single(53.59, 0.0, 0.0)
print(f"    lab_to_rgb_single: R={L} G={a} B={b}")

# 2. Test delta_e_lib (colormath)
from core.color_engine.delta_e_lib import calculate_all_delta_e, calculate_delta_e

de = calculate_all_delta_e(50.0, -15.0, -20.0, 52.0, -13.0, -18.0)
print(f"[2] delta_e_lib OK:")
print(f"    CIE1976={de['cie1976']:.4f}")
print(f"    CIE1994={de['cie1994']:.4f}")
print(f"    CIE2000={de['cie2000']:.4f}")
print(f"    CMC={de['cmc']:.4f}")

# 3. Test models
from core.models.color_data import LabColor, LotDecision
lab1 = LabColor(L=50.0, a=-15.0, b=-20.0)
print(f"[3] models OK: {lab1}")

# 4. Test ColorEngine
from core.color_engine.engine import ColorEngine
rgb_frame = np.ones((20, 20, 3), dtype=np.uint8) * 128
rgb = ColorEngine.rgb_from_frame(rgb_frame)
print(f"[4] ColorEngine OK: R={rgb.R:.0f} G={rgb.G:.0f} B={rgb.B:.0f}")

# 5. Test DeltaECalculator (lotting)
from core.lotting.engine import DeltaECalculator
sample = LabColor(L=52.0, a=-13.0, b=-18.0)
result = DeltaECalculator.calculate(lab1, sample)
print(f"[5] DeltaECalculator OK: DE2000={result.de_2000:.4f} DE1976={result.de_1976:.4f}")

# 6. Test LottingEngine
from core.lotting.engine import LottingEngine
engine = LottingEngine(lab1)
lot = engine.make_decision(device_de=0.5, camera_de=0.4, surface_variance=0.5, is_homogeneous=True)
print(f"[6] LottingEngine OK: {lot.decision.value} DE={lot.final_de:.4f}")

lot_red = engine.make_decision(device_de=0.3, camera_de=0.2, surface_variance=5.0, is_homogeneous=False)
print(f"    Heterojen test: {lot_red.decision.value}")

# 7. Test Parser
from core.spectrophotometer.parser import SpectrophotometerParser
parser = SpectrophotometerParser()
sample_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "samples", "sample_xrite.csv")
readings = parser.parse_file(sample_path)
print(f"[7] Parser OK: {len(readings)} readings loaded")
if readings:
    print(f"    Ilk okuma: L={readings[0].lab.L:.4f} a={readings[0].lab.a:.4f} b={readings[0].lab.b:.4f}")

# 8. Test Surface Analysis
analysis = ColorEngine.analyze_surface(rgb_frame)
print(f"[8] Surface analysis OK: std={analysis.overall_std:.4f} homogeneous={analysis.is_homogeneous}")

# 9. Test CameraManager
from core.camera.manager import CameraManager
mgr = CameraManager()
print(f"[9] CameraManager OK: singleton={mgr is CameraManager()}")

# 10. Test pandas import
import pandas as pd
import xlsxwriter
print(f"[10] pandas OK: {pd.__version__}")
print(f"     xlsxwriter OK: {xlsxwriter.__version__}")

# 11. Test all delta E identical
de_same = calculate_all_delta_e(50.0, -15.0, -20.0, 50.0, -15.0, -20.0)
print(f"[11] Identical color DE: CIE1976={de_same['cie1976']:.4f} CIE2000={de_same['cie2000']:.4f}")
assert de_same['cie1976'] < 0.01, "CIE1976 should be ~0 for identical colors"
assert de_same['cie2000'] < 0.01, "CIE2000 should be ~0 for identical colors"

print()
print("=" * 50)
print("ALL TESTS PASSED!")
print("=" * 50)
