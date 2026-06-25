# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
from typing import Tuple

import numpy as np

from core.models.color_data import LabColor, LCHColor, RGBColor, CameraAnalysis
from core.color_engine.color_convert import rgb_to_lab, lab_to_lch

logger = logging.getLogger(__name__)

DEGREE_TO_RADIAN = 57.29981045


class ColorEngine:
    @staticmethod
    def rgb_from_frame(frame_rgb: np.ndarray) -> RGBColor:
        mean_vals = np.mean(frame_rgb, axis=(0, 1))
        return RGBColor(R=float(mean_vals[0]), G=float(mean_vals[1]), B=float(mean_vals[2]))

    @staticmethod
    def lab_from_frame(frame_rgb: np.ndarray) -> Tuple[LabColor, LCHColor]:
        img_lab = rgb_to_lab(frame_rgb)
        img_lch = lab_to_lch(img_lab)
        mean_lab = np.mean(img_lab, axis=(0, 1))
        mean_lch = np.mean(img_lch, axis=(0, 1))
        lab = LabColor(L=float(mean_lab[0]), a=float(mean_lab[1]), b=float(mean_lab[2]))
        lch = LCHColor(
            L=float(mean_lch[0]),
            C=float(mean_lch[1]),
            H=float(mean_lch[2]),
        )
        return lab, lch

    @staticmethod
    def analyze_surface(frame_rgb: np.ndarray) -> CameraAnalysis:
        img_lab = rgb_to_lab(frame_rgb)
        mean_lab = np.mean(img_lab, axis=(0, 1))
        std_lab = np.std(img_lab, axis=(0, 1))
        overall_std = float(np.mean(std_lab))
        pixel_count = img_lab.shape[0] * img_lab.shape[1]
        return CameraAnalysis(
            mean_lab=LabColor(L=float(mean_lab[0]), a=float(mean_lab[1]), b=float(mean_lab[2])),
            spatial_variance_L=float(std_lab[0]),
            spatial_variance_a=float(std_lab[1]),
            spatial_variance_b=float(std_lab[2]),
            overall_std=overall_std,
            pixel_count=pixel_count,
        )

    @staticmethod
    def rgb_difference(ref: RGBColor, meas: RGBColor) -> Tuple[float, float, float]:
        return (meas.R - ref.R, meas.G - ref.G, meas.B - ref.B)

    @staticmethod
    def lab_difference(ref: LabColor, meas: LabColor) -> Tuple[float, float, float, float, float]:
        dL = meas.L - ref.L
        da = meas.a - ref.a
        db = meas.b - ref.b
        dC = np.sqrt(meas.a ** 2 + meas.b ** 2) - np.sqrt(ref.a ** 2 + ref.b ** 2)
        h_ref = np.arctan2(ref.b, ref.a) * DEGREE_TO_RADIAN
        h_meas = np.arctan2(meas.b, meas.a) * DEGREE_TO_RADIAN
        dH = 2 * np.sqrt(
            np.sqrt(ref.a ** 2 + ref.b ** 2) * np.sqrt(meas.a ** 2 + meas.b ** 2)
        ) * np.sin(np.radians((h_meas - h_ref) / 2))
        return dL, da, db, dC, dH
