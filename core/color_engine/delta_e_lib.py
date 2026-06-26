# -*- coding: utf-8 -*-
from __future__ import annotations

import numpy as np

# colormath library is incompatible with numpy 2.x (numpy.asscalar removed)
# We re-add the asscalar function to fix this.
if not hasattr(np, "asscalar"):
    np.asscalar = lambda x: x.item()

from colormath.color_diff import delta_e_cie1976, delta_e_cie1994, delta_e_cie2000, delta_e_cmc
from colormath.color_objects import LabColor as ColormathLab
from typing import Literal


DeltaEMethod = Literal["cie1976", "cie1994", "cie2000", "cmc"]


def _to_colormath(L: float, a: float, b: float) -> ColormathLab:
    return ColormathLab(lab_l=L, lab_a=a, lab_b=b)


def delta_e_cie1976_val(L1: float, a1: float, b1: float,
                         L2: float, a2: float, b2: float) -> float:
    return float(delta_e_cie1976(_to_colormath(L2, a2, b2), _to_colormath(L1, a1, b1)))


def delta_e_cie1994_val(L1: float, a1: float, b1: float,
                         L2: float, a2: float, b2: float) -> float:
    return float(delta_e_cie1994(_to_colormath(L2, a2, b2), _to_colormath(L1, a1, b1)))


def delta_e_cie2000_val(L1: float, a1: float, b1: float,
                         L2: float, a2: float, b2: float) -> float:
    return float(delta_e_cie2000(_to_colormath(L2, a2, b2), _to_colormath(L1, a1, b1)))


def delta_e_cmc_val(L1: float, a1: float, b1: float,
                     L2: float, a2: float, b2: float) -> float:
    return float(delta_e_cmc(_to_colormath(L2, a2, b2), _to_colormath(L1, a1, b1)))


DELTA_E_FUNCTIONS = {
    "cie1976": delta_e_cie1976_val,
    "cie1994": delta_e_cie1994_val,
    "cie2000": delta_e_cie2000_val,
    "cmc": delta_e_cmc_val,
}


def calculate_delta_e(L1: float, a1: float, b1: float,
                      L2: float, a2: float, b2: float,
                      method: DeltaEMethod = "cie2000") -> float:
    func = DELTA_E_FUNCTIONS[method]
    return func(L1, a1, b1, L2, a2, b2)


def calculate_all_delta_e(L1: float, a1: float, b1: float,
                          L2: float, a2: float, b2: float) -> dict[str, float]:
    return {name: func(L1, a1, b1, L2, a2, b2)
            for name, func in DELTA_E_FUNCTIONS.items()}
