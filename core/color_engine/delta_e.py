# -*- coding: utf-8 -*-
from __future__ import annotations

import math
from typing import Literal

import numpy as np


def _lab_to_xyz(L: float, a: float, b: float) -> tuple[float, float, float]:
    """L*a*b* -> XYZ (D65)."""
    fy = (L + 16.0) / 116.0
    fx = a / 500.0 + fy
    fz = fy - b / 200.0

    epsilon = 0.008856
    kappa = 903.3

    x = fx ** 3 if fx ** 3 > epsilon else (116.0 * fx - 16.0) / kappa
    y = ((L + 16.0) / 116.0) ** 3 if L > kappa * epsilon else L / kappa
    z = fz ** 3 if fz ** 3 > epsilon else (116.0 * fz - 16.0) / kappa

    ref_x, ref_y, ref_z = 0.95047, 1.00000, 1.08883
    return x * ref_x, y * ref_y, z * ref_z


def _delta_hue(h1: float, h2: float) -> float:
    """Iki aci arasindaki farki hesapla (derece)."""
    diff = h2 - h1
    if abs(diff) <= 180.0:
        return diff
    elif diff > 180.0:
        return diff - 360.0
    else:
        return diff + 360.0


def delta_e_cie1976(L1: float, a1: float, b1: float,
                     L2: float, a2: float, b2: float) -> float:
    """CIE 1976 Delta E (basit öklid mesafesi)."""
    return math.sqrt((L2 - L1) ** 2 + (a2 - a1) ** 2 + (b2 - b1) ** 2)


def delta_e_cie1994(L1: float, a1: float, b1: float,
                     L2: float, a2: float, b2: float,
                     textiles: bool = True) -> float:
    """CIE 1994 Delta E."""
    C1 = math.sqrt(a1 ** 2 + b1 ** 2)
    C2 = math.sqrt(a2 ** 2 + b2 ** 2)
    dL = L1 - L2
    dC = C1 - C2
    dH = math.sqrt(max(0, (a2 - a1) ** 2 + (b2 - b1) ** 2 - dC ** 2))

    if textiles:
        kL, kC, kH = 2.0, 1.0, 1.0
        SL = 1.0
    else:
        kL, kC, kH = 1.0, 1.0, 1.0
        SL = 0.045 * C1 if C1 != 0 else 1.0

    SC = 1.0 + 0.045 * C1 if C1 != 0 else 1.0
    SH = 1.0 + 0.015 * C1 if C1 != 0 else 1.0

    return math.sqrt(
        (dL / kL / SL) ** 2 +
        (dC / kC / SC) ** 2 +
        (dH / kH / SH) ** 2
    )


def delta_e_cie2000(L1: float, a1: float, b1: float,
                     L2: float, a2: float, b2: float) -> float:
    """
    CIEDE2000 Delta E - tam implementasyon.
    Referans: CIE 224:2007
    """
    # Adim 1: LAB'yi L'C'h' donusumu
    C1 = math.sqrt(a1 ** 2 + b1 ** 2)
    C2 = math.sqrt(a2 ** 2 + b2 ** 2)
    C_avg = (C1 + C2) / 2.0
    C_avg_7 = C_avg ** 7
    G = 0.5 * (1.0 - math.sqrt(C_avg_7 / (C_avg_7 + 25.0 ** 7)))

    a1p = a1 * (1.0 + G)
    a2p = a2 * (1.0 + G)
    C1p = math.sqrt(a1p ** 2 + b1 ** 2)
    C2p = math.sqrt(a2p ** 2 + b2 ** 2)

    h1p = math.degrees(math.atan2(b1, a1p))
    if h1p < 0:
        h1p += 360.0
    h2p = math.degrees(math.atan2(b2, a2p))
    if h2p < 0:
        h2p += 360.0

    # Adim 2: L*, C', h' farklari
    dLp = L2 - L1
    dCp = C2p - C1p

    if C1p * C2p == 0:
        dhp = 0.0
    elif abs(h2p - h1p) <= 180.0:
        dhp = h2p - h1p
    elif h2p - h1p > 180.0:
        dhp = h2p - h1p - 360.0
    else:
        dhp = h2p - h1p + 360.0

    dHp = 2.0 * math.sqrt(C1p * C2p) * math.sin(math.radians(dhp / 2.0))

    # Adim 3: Ortalamalar
    Lp_avg = (L1 + L2) / 2.0
    Cp_avg = (C1p + C2p) / 2.0

    if C1p * C2p == 0:
        hp_avg = h1p + h2p
    elif abs(h1p - h2p) <= 180.0:
        hp_avg = (h1p + h2p) / 2.0
    elif h1p + h2p < 360.0:
        hp_avg = (h1p + h2p + 360.0) / 2.0
    else:
        hp_avg = (h1p + h2p - 360.0) / 2.0

    T = (1.0
         - 0.17 * math.cos(math.radians(hp_avg - 30.0))
         + 0.24 * math.cos(math.radians(2.0 * hp_avg))
         + 0.32 * math.cos(math.radians(3.0 * hp_avg + 6.0))
         - 0.20 * math.cos(math.radians(4.0 * hp_avg - 63.0)))

    SL = 1.0 + 0.015 * (Lp_avg - 50.0) ** 2 / math.sqrt(20.0 + (Lp_avg - 50.0) ** 2)
    SC = 1.0 + 0.045 * Cp_avg
    SH = 1.0 + 0.015 * Cp_avg * T

    Cp_avg_7 = Cp_avg ** 7
    RT = (-math.sin(2.0 * math.radians(
        60.0 * math.exp(-((hp_avg - 275.0) / 25.0) ** 2)
    ))
         * math.sqrt(Cp_avg_7 / (Cp_avg_7 + 25.0 ** 7)))

    # Agirlikli katsayilar (CIE standardi)
    kL, kC, kH = 1.0, 1.0, 1.0

    return math.sqrt(
        (dLp / kL / SL) ** 2 +
        (dCp / kC / SC) ** 2 +
        (dHp / kH / SH) ** 2 +
        RT * (dCp / kC / SC) * (dHp / kH / SH)
    )


def delta_e_cmc(L1: float, a1: float, b1: float,
                L2: float, a2: float, b2: float,
                l: float = 2.0, c: float = 1.0) -> float:
    """
    CMC l:c Delta E.
    l=2.0, c=1.0 textil icin standart degerler.
    """
    C1 = math.sqrt(a1 ** 2 + b1 ** 2)
    C2 = math.sqrt(a2 ** 2 + b2 ** 2)

    dL = L1 - L2
    dC = C1 - C2
    dH_sq = max(0, (a2 - a1) ** 2 + (b2 - b1) ** 2 - dC ** 2)
    dH = math.sqrt(dH_sq)

    # SL, SC, SH katsayilari
    if L1 < 16:
        SL = 0.511
    else:
        SL = 0.040975 * L1 / (1.0 + 0.01765 * L1)

    SC = 0.0638 * C1 / (1.0 + 0.0131 * C1) + 0.638

    H1 = math.degrees(math.atan2(b1, a1))
    if H1 < 0:
        H1 += 360.0

    if C1 == 0:
        SH = 1.0
    elif 164 <= H1 <= 345:
        SH = 0.040 * C1 + 0.638
    else:
        T = (0.56 + abs(math.sin(math.radians(H1)))
             + 0.4 * abs(math.sin(math.radians(2.0 * H1))))
        SH = 0.040 * C1 * T + 0.638

    return math.sqrt(
        (dL / l / SL) ** 2 +
        (dC / c / SC) ** 2 +
        (dH / SH) ** 2
    )


DeltaEMethod = Literal["cie1976", "cie1994", "cie2000", "cmc"]

DELTA_E_FUNCTIONS = {
    "cie1976": delta_e_cie1976,
    "cie1994": delta_e_cie1994,
    "cie2000": delta_e_cie2000,
    "cmc": delta_e_cmc,
}


def calculate_delta_e(L1: float, a1: float, b1: float,
                      L2: float, a2: float, b2: float,
                      method: DeltaEMethod = "cie2000",
                      **kwargs) -> float:
    """Secilen yonteme gore Delta E hesapla."""
    func = DELTA_E_FUNCTIONS[method]
    if method == "cie1994":
        return func(L1, a1, b1, L2, a2, b2, textiles=kwargs.get("textiles", True))
    elif method == "cmc":
        return func(L1, a1, b1, L2, a2, b2,
                    l=kwargs.get("l", 2.0), c=kwargs.get("c", 1.0))
    else:
        return func(L1, a1, b1, L2, a2, b2)


def calculate_all_delta_e(L1: float, a1: float, b1: float,
                          L2: float, a2: float, b2: float) -> dict[str, float]:
    """Tum Delta E yontemlerini hesapla ve sozluk olarak dondur."""
    return {name: func(L1, a1, b1, L2, a2, b2)
            for name, func in DELTA_E_FUNCTIONS.items()}
