# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import logging
import os
import re
from typing import List, Optional

from core.models.color_data import LabColor, SpectralReading, MeasurementSource

logger = logging.getLogger(__name__)


class SpectrophotometerParser:
    SUPPORTED_EXTENSIONS = (".csv", ".txt", ".cxf", ".xml")

    @staticmethod
    def parse_csv_line(line: str) -> Optional[LabColor]:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 3:
            try:
                L, a, b = float(parts[0]), float(parts[1]), float(parts[2])
                return LabColor(L=L, a=a, b=b)
            except ValueError:
                pass
        return None

    @staticmethod
    def parse_tab_line(line: str) -> Optional[LabColor]:
        parts = [p.strip() for p in line.split("\t")]
        if len(parts) >= 3:
            try:
                L, a, b = float(parts[0]), float(parts[1]), float(parts[2])
                return LabColor(L=L, a=a, b=b)
            except ValueError:
                pass
        return None

    @classmethod
    def parse_file(cls, filepath: str) -> List[SpectralReading]:
        if not os.path.isfile(filepath):
            logger.error("Dosya bulunamadı: %s", filepath)
            return []

        ext = os.path.splitext(filepath)[1].lower()
        if ext not in cls.SUPPORTED_EXTENSIONS:
            logger.warning("Desteklenmeyen dosya formatı: %s", ext)

        readings: List[SpectralReading] = []
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                for line_no, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith("#") or line.startswith("Color"):
                        continue
                    lab = None
                    if ext == ".csv":
                        lab = cls.parse_csv_line(line)
                    elif ext in (".txt", ".cxf"):
                        lab = cls.parse_tab_line(line) or cls.parse_csv_line(line)
                    elif ext == ".xml":
                        lab = cls._parse_xml_line(line)
                    if lab is None:
                        lab = cls._extract_lab_from_text(line)
                    if lab is not None:
                        readings.append(SpectralReading(
                            lab=lab,
                            source=MeasurementSource.SPECTROPHOTOMETER,
                            sample_id=f"SAT-{line_no:04d}",
                        ))
        except Exception as e:
            logger.error("Dosya okuma hatası (%s): %s", filepath, e)

        logger.info("%d okuma yüklendi: %s", len(readings), filepath)
        return readings

    @staticmethod
    def _parse_xml_line(line: str) -> Optional[LabColor]:
        l_match = re.search(r"L[*\"=:\s]+([-\d.]+)", line)
        a_match = re.search(r"a[*\"=:\s]+([-\d.]+)", line)
        b_match = re.search(r"b[*\"=:\s]+([-\d.]+)", line)
        if l_match and a_match and b_match:
            try:
                return LabColor(
                    L=float(l_match.group(1)),
                    a=float(a_match.group(1)),
                    b=float(b_match.group(1)),
                )
            except ValueError:
                pass
        return None

    @staticmethod
    def _extract_lab_from_text(line: str) -> Optional[LabColor]:
        numbers = re.findall(r"[-]?\d+\.?\d*", line)
        if len(numbers) >= 3:
            try:
                L, a, b = float(numbers[0]), float(numbers[1]), float(numbers[2])
                if 0 <= L <= 100 and -128 <= a <= 128 and -128 <= b <= 128:
                    return LabColor(L=L, a=a, b=b)
            except ValueError:
                pass
        return None

    @staticmethod
    def create_reading(lab: LabColor, sample_id: str = "") -> SpectralReading:
        return SpectralReading(
            lab=lab,
            source=MeasurementSource.SPECTROPHOTOMETER,
            sample_id=sample_id,
        )
