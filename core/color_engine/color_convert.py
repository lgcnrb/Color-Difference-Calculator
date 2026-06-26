# -*- coding: utf-8 -*-
from __future__ import annotations

import numpy as np
from skimage.color import rgb2lab, lab2lch, lab2rgb


def rgb_to_lab(rgb: np.ndarray) -> np.ndarray:
    """
    Converts RGB (0-255) array to CIE L*a*b*.
    Input: (H, W, 3) uint8 or float64 [0,1]
    Output: (H, W, 3) float64
    """
    if rgb.dtype == np.uint8:
        img = rgb.astype(np.float64) / 255.0
    else:
        img = rgb.astype(np.float64)
    return rgb2lab(img)


def lab_to_lch(lab: np.ndarray) -> np.ndarray:
    """
    Converts CIE L*a*b* array to CIE L*C*h*.
    Uses scikit-image lab2lch.
    """
    return lab2lch(lab)


def lab_to_rgb(lab: np.ndarray) -> np.ndarray:
    """
    Converts CIE L*a*b* array to RGB.
    Output: (H, W, 3) uint8 [0-255]
    """
    rgb_float = lab2rgb(lab)
    return (np.clip(rgb_float, 0, 1) * 255).astype(np.uint8)


def rgb_to_lab_single(r: float, g: float, b: float) -> tuple[float, float, float]:
    """Converts a single RGB value to L*a*b*."""
    rgb = np.array([[[r, g, b]]], dtype=np.uint8)
    lab = rgb_to_lab(rgb)
    return float(lab[0, 0, 0]), float(lab[0, 0, 1]), float(lab[0, 0, 2])


def lab_to_lch_single(L: float, a: float, b: float) -> tuple[float, float, float]:
    """Converts a single L*a*b* value to L*C*h*."""
    lab = np.array([[[L, a, b]]], dtype=np.float64)
    lch = lab_to_lch(lab)
    return float(lch[0, 0, 0]), float(lch[0, 0, 1]), float(lch[0, 0, 2])


def lab_to_rgb_single(L: float, a: float, b: float) -> tuple[int, int, int]:
    """Converts a single L*a*b* value to RGB (0-255)."""
    lab = np.array([[[L, a, b]]], dtype=np.float64)
    rgb = lab_to_rgb(lab)
    return int(rgb[0, 0, 0]), int(rgb[0, 0, 1]), int(rgb[0, 0, 2])
