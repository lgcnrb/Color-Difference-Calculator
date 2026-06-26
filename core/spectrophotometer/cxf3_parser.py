# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
import os
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from core.models.color_data import LabColor, SpectralReading, MeasurementSource

logger = logging.getLogger(__name__)

NM_RANGE = list(range(380, 781, 10))

ILLUMINANTS = {
    "D50": "D50 (5003K)",
    "D65": "D65 (6500K)",
    "D75": "D75 (7500K)",
    "A": "A (2856K)",
    "F2": "F2 (4100K)",
    "F7": "F7 (6500K)",
    "F11": "F11 (4000K)",
    "TL84": "TL84 (4000K)",
    "CWF": "CWF (4150K)",
}

OBSERVER_ANGLES = {"2": "2 Aci (CIE 1931)", "10": "10 Aci (CIE 1964)"}


@dataclass
class CxF3Measurement:
    sample_name: str
    illuminant: str
    observer_angle: str
    wavelengths: List[int] = field(default_factory=list)
    reflectances: List[float] = field(default_factory=list)
    lab: Optional[LabColor] = None
    lch: Optional[Tuple[float, float, float]] = None
    metadata: Dict[str, str] = field(default_factory=dict)

    @property
    def has_spectral_data(self) -> bool:
        return len(self.wavelengths) > 0 and len(self.reflectances) > 0

    def interpolate_to_380_780(self) -> List[float]:
        if not self.has_spectral_data:
            return []
        result = []
        for nm in NM_RANGE:
            if nm in self.wavelengths:
                idx = self.wavelengths.index(nm)
                result.append(self.reflectances[idx])
            else:
                nearest = min(self.wavelengths, key=lambda x: abs(x - nm))
                idx = self.wavelengths.index(nearest)
                result.append(self.reflectances[idx])
        return result


class CxF3Parser:
    XML_NAMESPACES = {
        "cx": "http://www.colourgroup.com/CxF3",
        "xrite": "http://www.xrite.com/CxF3",
    }

    @classmethod
    def parse_file(cls, filepath: str) -> List[CxF3Measurement]:
        if not os.path.isfile(filepath):
            logger.error("CxF3 dosyasi bulunamadi: %s", filepath)
            return []

        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
        except ET.ParseError as e:
            logger.error("XML parse hatasi (%s): %s", filepath, e)
            return cls._fallback_parse(filepath)

        measurements = []

        color_patches = root.findall(".//ColorPatch") or root.findall(".//Patch")
        if color_patches:
            for patch in color_patches:
                m = cls._parse_color_patch(patch)
                if m:
                    measurements.append(m)

        if not measurements:
            for elem in root.iter():
                if elem.tag.endswith("Measurement") or elem.tag.endswith("Sample"):
                    m = cls._parse_measurement_element(elem)
                    if m:
                        measurements.append(m)

        if not measurements:
            measurements = cls._parse_flat_xml(root)

        if not measurements:
            measurements = cls._fallback_parse(filepath)

        logger.info("CxF3: %d olcum okundu: %s", len(measurements), filepath)
        return measurements

    @classmethod
    def _parse_color_patch(cls, elem) -> Optional[CxF3Measurement]:
        name = (
            elem.get("name")
            or elem.get("Name")
            or cls._find_text(elem, ".//Name")
            or cls._find_text(elem, ".//SampleName")
            or "Bilinmeyen"
        )

        illuminant = cls._find_attribute(elem, "Illuminant") or "D65"
        observer = cls._find_attribute(elem, "Observer") or cls._find_attribute(elem, "ObserverAngle") or "2"

        wavelengths, reflectances = cls._parse_reflectance(elem)

        lab = cls._parse_lab(elem)
        lch = cls._parse_lch(elem)

        metadata = {}
        for child in elem:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag not in ("Reflectance", "Color", "Lab", "LCH", "Name", "SampleName"):
                text = child.text or child.get("value") or ""
                if text:
                    metadata[tag] = text

        if not wavelengths and reflectances:
            wavelengths = list(range(380, 781, 10))[: len(reflectances)]

        if wavelengths and reflectances and lab is None:
            lab = cls._lab_from_spectral(wavelengths, reflectances, illuminant, observer)

        if lab is None and reflectances:
            lab = cls._lab_from_spectral(NM_RANGE, reflectances[:len(NM_RANGE)], illuminant, observer)

        if lab is None and not reflectances:
            return None

        return CxF3Measurement(
            sample_name=name,
            illuminant=illuminant,
            observer_angle=observer,
            wavelengths=wavelengths,
            reflectances=reflectances,
            lab=lab,
            lch=lch,
            metadata=metadata,
        )

    @classmethod
    def _parse_measurement_element(cls, elem) -> Optional[CxF3Measurement]:
        name = elem.get("name") or elem.get("Name") or cls._find_text(elem, ".//Name") or "Olcum"

        illuminant = cls._find_attribute(elem, "Illuminant") or "D65"
        observer = cls._find_attribute(elem, "Observer") or "2"

        wavelengths, reflectances = cls._parse_reflectance(elem)
        lab = cls._parse_lab(elem)

        if lab is None and reflectances:
            lab = cls._lab_from_spectral(
                wavelengths if wavelengths else NM_RANGE,
                reflectances,
                illuminant,
                observer,
            )

        if lab is None and not reflectances:
            return None

        return CxF3Measurement(
            sample_name=name,
            illuminant=illuminant,
            observer_angle=observer,
            wavelengths=wavelengths or NM_RANGE[:len(reflectances)],
            reflectances=reflectances,
            lab=lab,
        )

    @classmethod
    def _parse_flat_xml(cls, root) -> List[CxF3Measurement]:
        measurements = []
        for elem in root.iter():
            tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
            if tag in ("Data", "Spectral", "Reflectance"):
                values_text = elem.text or ""
                values_text = values_text.strip()
                if not values_text:
                    values_text = " ".join(child.text for child in elem if child.text)
                    values_text = values_text.strip()

                numbers = re.findall(r"[-+]?\d*\.?\d+", values_text)
                if len(numbers) >= 10:
                    reflectances = [float(n) for n in numbers]
                    parent = elem.getparent() if hasattr(elem, "getparent") else root
                    name = parent.get("name") or parent.get("Name") or "Flat"
                    lab = cls._lab_from_spectral(NM_RANGE, reflectances, "D65", "2")
                    measurements.append(CxF3Measurement(
                        sample_name=name,
                        illuminant="D65",
                        observer_angle="2",
                        wavelengths=NM_RANGE,
                        reflectances=reflectances,
                        lab=lab,
                    ))
        return measurements

    @classmethod
    def _fallback_parse(cls, filepath: str) -> List[CxF3Measurement]:
        measurements = []
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            logger.error("Fallback okuma hatasi: %s", e)
            return []

        numbers = re.findall(r"[-+]?\d*\.?\d+", content)
        chunks = []
        i = 0
        while i < len(numbers):
            chunk = []
            for j in range(i, min(i + 41, len(numbers))):
                val = float(numbers[j])
                if 0 <= val <= 100:
                    chunk.append(val)
                else:
                    break
            if len(chunk) >= 10:
                chunks.append(chunk)
                i += len(chunk)
            else:
                i += 1

        for idx, chunk in enumerate(chunks):
            lab = cls._lab_from_spectral(NM_RANGE, chunk, "D65", "2")
            measurements.append(CxF3Measurement(
                sample_name=f"Olcum-{idx+1:03d}",
                illuminant="D65",
                observer_angle="2",
                wavelengths=NM_RANGE,
                reflectances=chunk,
                lab=lab,
            ))

        return measurements

    @classmethod
    def _parse_reflectance(cls, elem) -> Tuple[List[int], List[float]]:
        wavelengths = []
        reflectances = []

        for child in elem.iter():
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag in ("R", "Reflectance", "ReflectanceData", "SpectralData", "Data"):
                values_text = child.text or ""
                if not values_text.strip():
                    values_text = " ".join(c.text for c in child if c.text)
                numbers = re.findall(r"[-+]?\d*\.?\d+", values_text.strip())
                if numbers:
                    vals = [float(n) for n in numbers]
                    if len(vals) >= 10:
                        reflectances = vals
                        if len(vals) == len(NM_RANGE):
                            wavelengths = list(NM_RANGE)
                        elif len(vals) == 41:
                            wavelengths = list(range(380, 781, 10))
                        elif len(vals) == 31:
                            wavelengths = list(range(400, 701, 10))
                        else:
                            wavelengths = list(range(380, 380 + len(vals) * 10, 10))
                        break

        return wavelengths, reflectances

    @classmethod
    def _parse_lab(cls, elem) -> Optional[LabColor]:
        for child in elem.iter():
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag in ("Lab", "Color"):
                l_val = child.get("L") or child.get("l")
                a_val = child.get("a") or child.get("A")
                b_val = child.get("b") or child.get("B")
                if l_val and a_val and b_val:
                    try:
                        return LabColor(L=float(l_val), a=float(a_val), b=float(b_val))
                    except ValueError:
                        pass

                for sub in child:
                    sub_tag = sub.tag.split("}")[-1] if "}" in sub.tag else sub.tag
                    if sub_tag in ("L", "Lstar"):
                        l_val = sub.text or sub.get("value")
                    elif sub_tag in ("a", "astar"):
                        a_val = sub.text or sub.get("value")
                    elif sub_tag in ("b", "bstar"):
                        b_val = sub.text or sub.get("value")

                if l_val and a_val and b_val:
                    try:
                        return LabColor(L=float(l_val), a=float(a_val), b=float(b_val))
                    except ValueError:
                        pass

        return None

    @classmethod
    def _parse_lch(cls, elem) -> Optional[Tuple[float, float, float]]:
        for child in elem.iter():
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag == "LCH":
                l_val = child.get("L") or child.get("l")
                c_val = child.get("C") or child.get("c")
                h_val = child.get("H") or child.get("h")
                if l_val and c_val and h_val:
                    try:
                        return (float(l_val), float(c_val), float(h_val))
                    except ValueError:
                        pass
        return None

    @classmethod
    def _find_text(cls, elem, xpath: str) -> Optional[str]:
        found = elem.find(xpath)
        if found is not None and found.text:
            return found.text.strip()
        return None

    @classmethod
    def _find_attribute(cls, elem, attr: str) -> Optional[str]:
        val = elem.get(attr)
        if val:
            return val.strip()
        for child in elem.iter():
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag == attr:
                return (child.text or "").strip() or child.get("value")
        return None

    @classmethod
    def _lab_from_spectral(
        cls,
        wavelengths: List[int],
        reflectances: List[float],
        illuminant: str,
        observer: str,
    ) -> Optional[LabColor]:
        try:
            import numpy as np

            if len(wavelengths) != len(reflectances):
                return None

            wvl = np.array(wavelengths, dtype=float)
            refl = np.array(reflectances, dtype=float)

            if wvl[0] > wvl[-1]:
                wvl = wvl[::-1]
                refl = refl[::-1]

            illuminant_map = {
                "D50": 5003, "D65": 6500, "D75": 7500,
                "A": 2856, "F2": 4100, "F7": 6500, "F11": 4000,
                "TL84": 4000, "CWF": 4150,
            }
            cct = illuminant_map.get(illuminant.upper(), 6500)

            xyz = cls._spectral_to_xyz(wvl, refl, cct)
            if xyz is None:
                return None

            lab = cls._xyz_to_lab(xyz)
            return lab

        except Exception as e:
            logger.debug("Spektral->LAB donusum hatasi: %s", e)
            return None

    @staticmethod
    def _spectral_to_xyz(wvl, refl, cct):
        import numpy as np

        try:
            illuminant_data = _get_illuminant_data(cct, wvl)
            cmf_data = _get_cmf_data(wvl)

            if illuminant_data is None or cmf_data is None:
                return None

            X = float(np.trapz(refl * illuminant_data * cmf_data[:, 0], wvl))
            Y = float(np.trapz(refl * illuminant_data * cmf_data[:, 1], wvl))
            Z = float(np.trapz(refl * illuminant_data * cmf_data[:, 2], wvl))

            denom = X + Y + Z
            if denom == 0:
                return None

            return np.array([X / denom, Y / denom, Z / denom])

        except Exception:
            return None

    @staticmethod
    def _xyz_to_lab(xyz):
        import numpy as np

        ref_white = np.array([0.95047, 1.00000, 1.08883])

        xyz_norm = xyz / ref_white

        delta = 6.0 / 29.0
        f = np.where(
            xyz_norm > delta**3,
            np.cbrt(xyz_norm),
            xyz_norm / (3 * delta**2) + 4.0 / 29.0,
        )

        L = 116.0 * f[1] - 16.0
        a = 500.0 * (f[0] - f[1])
        b = 200.0 * (f[1] - f[2])

        return LabColor(L=round(L, 4), a=round(a, 4), b=round(b, 4))


def _get_illuminant_data(cct, wvl):
    import numpy as np

    if 6000 <= cct <= 7000:
        base = 100.0 * np.exp(-0.5 * ((wvl - 560) / 80) ** 2)
        blue_boost = 30.0 * np.exp(-0.5 * ((wvl - 440) / 40) ** 2)
        return base + blue_boost
    elif cct <= 4000:
        base = 80.0 * np.exp(-0.5 * ((wvl - 580) / 100) ** 2)
        red_boost = 40.0 * np.exp(-0.5 * ((wvl - 620) / 50) ** 2)
        return base + red_boost
    else:
        return 100.0 * np.exp(-0.5 * ((wvl - 570) / 90) ** 2)


def _get_cmf_data(wvl):
    import numpy as np

    x_bar = np.exp(-0.5 * ((wvl - 555) / 60) ** 2)
    y_bar = np.exp(-0.5 * ((wvl - 555) / 50) ** 2)
    z_bar = np.exp(-0.5 * ((wvl - 470) / 50) ** 2)

    data = np.column_stack([x_bar, y_bar, z_bar])
    norm = data.sum(axis=0)
    norm[norm == 0] = 1
    return data / norm
