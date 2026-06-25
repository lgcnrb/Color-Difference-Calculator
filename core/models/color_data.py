# -*- coding: utf-8 -*-
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional

import numpy as np


class LotDecision(Enum):
    LOT_A = "LOT A"
    LOT_B = "LOT B"
    LOT_C = "LOT C"
    RED = "RED"


class MeasurementSource(Enum):
    SPECTROPHOTOMETER = "Spektrofotometre"
    CAMERA = "Kamera"
    HYBRID = "Hibrit"


@dataclass
class LabColor:
    L: float
    a: float
    b: float

    def to_array(self) -> np.ndarray:
        return np.array([self.L, self.a, self.b])

    @classmethod
    def from_array(cls, arr: np.ndarray) -> LabColor:
        return cls(L=float(arr[0]), a=float(arr[1]), b=float(arr[2]))

    def as_tuple(self) -> tuple:
        return (self.L, self.a, self.b)


@dataclass
class LCHColor:
    L: float
    C: float
    H: float

    def to_array(self) -> np.ndarray:
        return np.array([self.L, self.C, self.H])


@dataclass
class RGBColor:
    R: float
    G: float
    B: float

    def to_array(self) -> np.ndarray:
        return np.array([self.R, self.G, self.B])


@dataclass
class SpectralReading:
    lab: LabColor
    lch: Optional[LCHColor] = None
    reflectance: Optional[List[float]] = None
    timestamp: datetime = field(default_factory=datetime.now)
    source: MeasurementSource = MeasurementSource.SPECTROPHOTOMETER
    sample_id: str = ""

    def __post_init__(self):
        if not self.sample_id:
            self.sample_id = uuid.uuid4().hex[:8].upper()


@dataclass
class CameraAnalysis:
    mean_lab: LabColor
    spatial_variance_L: float
    spatial_variance_a: float
    spatial_variance_b: float
    overall_std: float
    pixel_count: int
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def is_homogeneous(self) -> bool:
        from config.settings import COLOR_ENGINE
        return self.overall_std <= COLOR_ENGINE.spatial_variance_target


@dataclass
class DeltaEResult:
    de_1976: float = 0.0
    de_1994: float = 0.0
    de_2000: float = 0.0
    de_cmc: float = 0.0
    dL: float = 0.0
    da: float = 0.0
    db: float = 0.0
    dC: float = 0.0
    dH: float = 0.0

    def get_by_method(self, method: str) -> float:
        mapping = {
            "delta_e_cie1976": self.de_1976,
            "delta_e_cie1994": self.de_1994,
            "delta_e_cie2000": self.de_2000,
            "delta_e_cmc": self.de_cmc,
        }
        return mapping.get(method, 0.0)


@dataclass
class LottingResult:
    decision: LotDecision
    final_de: float
    device_de: float
    camera_de: float
    surface_variance: float
    is_homogeneous: bool
    roll_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    notes: str = ""

    @property
    def is_accepted(self) -> bool:
        return self.decision in (LotDecision.LOT_A, LotDecision.LOT_B)


@dataclass
class MeasurementRecord:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12].upper())
    roll_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    reference: Optional[SpectralReading] = None
    reading: Optional[SpectralReading] = None
    delta_e: Optional[DeltaEResult] = None
    camera_analysis: Optional[CameraAnalysis] = None
    lotting_result: Optional[LottingResult] = None
    fabric_type: str = ""
    operator: str = ""
    notes: str = ""


@dataclass
class MasterColor:
    lab: LabColor
    name: str = "Master"
    fabric_type: str = ""
    created_at: datetime = field(default_factory=datetime.now)
