# -*- coding: utf-8 -*-
import os
from dataclasses import dataclass, field
from typing import List, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
EXPORT_DIR = os.path.join(DATA_DIR, "exports")
LOG_DIR = os.path.join(DATA_DIR, "logs")
SAMPLE_DIR = os.path.join(DATA_DIR, "samples")

for _dir in (EXPORT_DIR, LOG_DIR, SAMPLE_DIR):
    os.makedirs(_dir, exist_ok=True)


@dataclass(frozen=True)
class CameraConfig:
    device_id: int = 0
    width: int = 640
    height: int = 480
    preview_width: int = 320
    preview_height: int = 240
    fps_target: int = 30


@dataclass(frozen=True)
class ColorEngineConfig:
    delta_e_target: float = 1.0
    delta_e_warning: float = 0.8
    delta_e_critical: float = 1.5
    spatial_variance_target: float = 2.0
    illuminant: str = "D65"
    observer_angle: str = "2"
    illuminant_name: str = "D65 (6500K Daylight)"


@dataclass(frozen=True)
class LottingConfig:
    default_eps: float = 1.0
    min_eps: float = 0.1
    max_eps: float = 5.0
    min_samples: int = 2
    use_cnn: bool = True
    auto_eps_factor: float = 0.4
    lot_a_threshold: float = 0.5
    lot_b_threshold: float = 1.0
    lot_c_threshold: float = 2.0
    lot_d_threshold: float = 3.5


@dataclass(frozen=True)
class CNNConfig:
    model_name: str = "mobilenet_v3_large"
    feature_dim: int = 960
    use_gpu: bool = True
    texture_bins: int = 32
    gabor_orientations: int = 4
    gabor_scales: int = 4
    input_size: int = 224


@dataclass(frozen=True)
class UIConfig:
    window_title: str = "ColorIQ"
    window_min_width: int = 1200
    window_min_height: int = 720
    theme: str = "dark"
    font_family: str = "Segoe UI"
    font_size: int = 10
    accent_color: str = "#0078D4"
    success_color: str = "#107C10"
    warning_color: str = "#C19C00"
    danger_color: str = "#C42B1C"
    bg_primary: str = "#202020"
    bg_secondary: str = "#2D2D2D"
    bg_card: str = "#303030"
    text_primary: str = "#FFFFFF"
    text_secondary: str = "#9A9A9A"
    border_color: str = "#454545"


@dataclass(frozen=True)
class DeltaEmethods:
    CIE1976: str = "delta_e_cie1976"
    CIE1994: str = "delta_e_cie1994"
    CIE2000: str = "delta_e_cie2000"
    CMC: str = "delta_e_cmc"

    @classmethod
    def all_methods(cls) -> List[str]:
        return [cls.CIE1976, cls.CIE1994, cls.CIE2000, cls.CMC]

    @classmethod
    def display_names(cls) -> dict:
        return {
            cls.CIE1976: "CIE 1976",
            cls.CIE1994: "CIE 1994",
            cls.CIE2000: "CIEDE 2000",
            cls.CMC: "CMC (l:c)",
        }


@dataclass(frozen=True)
class ColorSpaces:
    CIE_LAB: str = "CIE-Lab/LCH"
    RGB: str = "RGB"

    @classmethod
    def all(cls) -> List[str]:
        return [cls.CIE_LAB, cls.RGB]


CAMERA = CameraConfig()
COLOR_ENGINE = ColorEngineConfig()
LOTTING = LottingConfig()
CNN = CNNConfig()
UI = UIConfig()
DELTA_METHODS = DeltaEmethods()
COLOR_SPACES = ColorSpaces()
