# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
from typing import Optional

from config.settings import COLOR_ENGINE, LOTTING, DELTA_METHODS
from core.models.color_data import (
    LabColor, SpectralReading, CameraAnalysis, DeltaEResult,
    LottingResult, LotDecision, MeasurementSource,
)
from core.color_engine.delta_e_lib import calculate_all_delta_e

logger = logging.getLogger(__name__)


class DeltaECalculator:
    @classmethod
    def calculate(cls, reference: LabColor, sample: LabColor) -> DeltaEResult:
        all_de = calculate_all_delta_e(
            reference.L, reference.a, reference.b,
            sample.L, sample.a, sample.b,
        )
        dL = sample.L - reference.L
        da = sample.a - reference.a
        db = sample.b - reference.b
        dC = (sample.a ** 2 + sample.b ** 2) ** 0.5 - (reference.a ** 2 + reference.b ** 2) ** 0.5

        return DeltaEResult(
            de_1976=all_de["cie1976"],
            de_1994=all_de["cie1994"],
            de_2000=all_de["cie2000"],
            de_cmc=all_de["cmc"],
            dL=float(dL),
            da=float(da),
            db=float(db),
            dC=float(dC),
            dH=0.0,
        )

    @classmethod
    def calculate_by_method(cls, reference: LabColor, sample: LabColor, method: str) -> float:
        result = cls.calculate(reference, sample)
        return result.get_by_method(method)


class LottingEngine:
    def __init__(
        self,
        master_lab: LabColor,
        de_target: float = COLOR_ENGINE.delta_e_target,
        spatial_variance_target: float = COLOR_ENGINE.spatial_variance_target,
    ):
        self.master_lab = master_lab
        self.de_target = de_target
        self.spatial_variance_target = spatial_variance_target

    def evaluate_device_reading(
        self, reading: SpectralReading, method: str = DELTA_METHODS.CIE2000
    ) -> float:
        return DeltaECalculator.calculate_by_method(self.master_lab, reading.lab, method)

    def evaluate_camera_analysis(self, analysis: CameraAnalysis) -> float:
        return DeltaECalculator.calculate_by_method(self.master_lab, analysis.mean_lab, DELTA_METHODS.CIE2000)

    def make_decision(
        self,
        device_de: float,
        camera_de: float,
        surface_variance: float,
        is_homogeneous: bool,
        roll_id: str = "",
    ) -> LottingResult:
        if not is_homogeneous or surface_variance > self.spatial_variance_target:
            decision = LotDecision.RED
            final_de = max(device_de, camera_de)
        else:
            final_de = (
                device_de * LOTTING.device_weight
                + camera_de * LOTTING.camera_weight
            )
            if final_de <= self.de_target * LOTTING.lot_a_multiplier:
                decision = LotDecision.LOT_A
            elif final_de <= self.de_target * LOTTING.lot_b_multiplier:
                decision = LotDecision.LOT_B
            elif final_de <= self.de_target * LOTTING.lot_c_multiplier:
                decision = LotDecision.LOT_C
            else:
                decision = LotDecision.RED

        result = LottingResult(
            decision=decision,
            final_de=float(final_de),
            device_de=float(device_de),
            camera_de=float(camera_de),
            surface_variance=float(surface_variance),
            is_homogeneous=is_homogeneous,
            roll_id=roll_id,
        )
        logger.info("Lot karari: %s (DE=%.3f)", decision.value, final_de)
        return result

    def process_hybrid(
        self,
        xrite_reading: Optional[SpectralReading],
        camera_analysis: Optional[CameraAnalysis],
        roll_id: str = "",
    ) -> LottingResult:
        device_de = 0.0
        camera_de = 0.0
        surface_variance = 0.0
        is_homogeneous = True

        if xrite_reading is not None:
            device_de = self.evaluate_device_reading(xrite_reading)
        if camera_analysis is not None:
            camera_de = self.evaluate_camera_analysis(camera_analysis)
            surface_variance = camera_analysis.overall_std
            is_homogeneous = camera_analysis.is_homogeneous

        return self.make_decision(device_de, camera_de, surface_variance, is_homogeneous, roll_id)
