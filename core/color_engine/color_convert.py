# -*- coding: utf-8 -*-
from __future__ import annotations

import numpy as np
from skimage.color import rgb2lab, lab2lch, lab2rgb


def rgb_to_lab(rgb: np.ndarray) -> np.ndarray:
    """
    RGB (0-255) dizisini CIE L*a*b* donusumune sokar.
    Girdi: (H, W, 3) uint8 veya float64 [0,1]
    Cikti: (H, W, 3) float64
    """
    if rgb.dtype == np.uint8:
        img = rgb.astype(np.float64) / 255.0
    else:
        img = rgb.astype(np.float64)
    return rgb2lab(img)


def lab_to_lch(lab: np.ndarray) -> np.ndarray:
    """
    CIE L*a*b* dizisini CIE L*C*h* donusumune sokar.
    scikit-image lab2lch kullanir.
    """
    return lab2lch(lab)


def lab_to_rgb(lab: np.ndarray) -> np.ndarray:
    """
    CIE L*a*b* dizisini RGB donusumune sokar.
    Cikti: (H, W, 3) uint8 [0-255]
    """
    rgb_float = lab2rgb(lab)
    return (np.clip(rgb_float, 0, 1) * 255).astype(np.uint8)


def rgb_to_lab_single(r: float, g: float, b: float) -> tuple[float, float, float]:
    """Tek bir RGB degerini L*a*b* donusumune sokar."""
    rgb = np.array([[[r, g, b]]], dtype=np.uint8)
    lab = rgb_to_lab(rgb)
    return float(lab[0, 0, 0]), float(lab[0, 0, 1]), float(lab[0, 0, 2])


def lab_to_lch_single(L: float, a: float, b: float) -> tuple[float, float, float]:
    """Tek bir L*a*b* degerini L*C*h* donusumune sokar."""
    lab = np.array([[[L, a, b]]], dtype=np.float64)
    lch = lab_to_lch(lab)
    return float(lch[0, 0, 0]), float(lch[0, 0, 1]), float(lch[0, 0, 2])


def lab_to_rgb_single(L: float, a: float, b: float) -> tuple[int, int, int]:
    """Tek bir L*a*b* degerini RGB'ye donusturur (0-255)."""
    lab = np.array([[[L, a, b]]], dtype=np.float64)
    rgb = lab_to_rgb(lab)
    return int(rgb[0, 0, 0]), int(rgb[0, 0, 1]), int(rgb[0, 0, 2])
