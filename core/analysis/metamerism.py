# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from core.models.color_data import LabColor
from core.lotting.engine import DeltaECalculator

logger = logging.getLogger(__name__)


@dataclass
class MetamerismResult:
    illuminant: str
    de_value: float
    passed: bool
    delta_L: float = 0.0
    delta_a: float = 0.0
    delta_b: float = 0.0


@dataclass
class MetamerismReport:
    reference_name: str
    sample_name: str
    results: List[MetamerismResult] = field(default_factory=list)
    has_metamerism_risk: bool = False
    risk_illuminants: List[str] = field(default_factory=list)

    @property
    def overall_passed(self) -> bool:
        return all(r.passed for r in self.results)

    @property
    def worst_de(self) -> float:
        if not self.results:
            return 0.0
        return max(r.de_value for r in self.results)

    @property
    def summary(self) -> str:
        if self.overall_passed:
            return "GECTI - Tum isik kaynaklarinda uyumlu"
        return f"RED - Metamerik risk: {', '.join(self.risk_illuminants)}"


class MetamerismChecker:
    ILLUMINANT_KEYS = {
        "D65": "D65 (Gun Isigi)",
        "D50": "D50 ( baski )",
        "A": "A ( Ev Isigi )",
        "F2": "F2 (Ofis Isigi)",
        "F7": "F7 (Fluoresan)",
        "F11": "F11 (Fluoresan)",
        "TL84": "TL84 (Magaza)",
        "CWF": "CWF (Magaza)",
    }

    def __init__(self, method: str = "delta_e_cie2000"):
        self.method = method

    def check(
        self,
        reference: LabColor,
        sample: LabColor,
        illuminants: Optional[List[str]] = None,
        tolerans_de: float = 1.0,
    ) -> MetamerismReport:
        if illuminants is None:
            illuminants = ["D65", "A", "TL84"]

        report = MetamerismReport(
            reference_name="Referans",
            sample_name="Numune",
        )

        for illum in illuminants:
            de = DeltaECalculator.calculate(reference, sample, self.method)
            dL = sample.L - reference.L
            da = sample.a - reference.a
            db = sample.b - reference.b

            passed = de <= tolerans_de

            result = MetamerismResult(
                illuminant=illum,
                de_value=de,
                passed=passed,
                delta_L=dL,
                delta_a=da,
                delta_b=db,
            )
            report.results.append(result)

            if not passed:
                report.has_metamerism_risk = True
                display = self.ILLUMINANT_KEYS.get(illum, illum)
                report.risk_illuminants.append(display)

        return report

    def check_multi_sample(
        self,
        reference: LabColor,
        samples: List[Tuple[str, LabColor]],
        illuminants: Optional[List[str]] = None,
        tolerans_de: float = 1.0,
    ) -> List[Tuple[str, MetamerismReport]]:
        results = []
        for name, sample in samples:
            report = self.check(reference, sample, illuminants, tolerans_de)
            report.reference_name = "Referans"
            report.sample_name = name
            results.append((name, report))
        return results

    @staticmethod
    def calculate_metamerism_index(
        lab_d65: LabColor,
        lab_A: LabColor,
    ) -> float:
        dL = lab_d65.L - lab_A.L
        da = lab_d65.a - lab_A.a
        db = lab_d65.b - lab_A.b
        return (dL**2 + da**2 + db**2) ** 0.5
