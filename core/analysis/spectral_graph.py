# -*- coding: utf-8 -*-
from __future__ import annotations

import io
import logging
from typing import List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class SpectralGraph:
    @staticmethod
    def create_plot(
        master_reflectance: List[float],
        sample_reflectance: List[float],
        master_name: str = "Master",
        sample_name: str = "Numune",
        wavelengths: Optional[List[int]] = None,
        title: str = "Spektral Egriler",
    ) -> Optional[bytes]:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            if wavelengths is None:
                wavelengths = list(range(380, 781, 10))

            n = min(len(wavelengths), len(master_reflectance), len(sample_reflectance))
            wvl = wavelengths[:n]
            master = master_reflectance[:n]
            sample = sample_reflectance[:n]

            fig, ax = plt.subplots(1, 1, figsize=(8, 4), dpi=100)
            fig.patch.set_facecolor("#202020")
            ax.set_facecolor("#1A1A1A")

            ax.plot(wvl, master, color="#1A7AE8", linewidth=2.0, label=master_name, marker="o", markersize=3)
            ax.plot(wvl, sample, color="#E85D1A", linewidth=2.0, label=sample_name, marker="s", markersize=3)

            diff = np.array(master[:n]) - np.array(sample[:n])
            ax.fill_between(wvl, master, sample, alpha=0.15, color="#FFD700", label="Fark Alani")

            ax.set_xlabel("Dalga Boyu (nm)", color="#AAAAAA", fontsize=9)
            ax.set_ylabel("Yansima (%)", color="#AAAAAA", fontsize=9)
            ax.set_title(title, color="#FFFFFF", fontsize=11, fontweight="bold")
            ax.set_xlim(380, 780)
            ax.set_ylim(0, 100)
            ax.tick_params(colors="#888888")
            ax.grid(True, alpha=0.2, color="#555555")
            ax.legend(loc="upper right", fontsize=8, facecolor="#2D2D2D", edgecolor="#454545", labelcolor="#CCCCCC")

            for spine in ax.spines.values():
                spine.set_color("#454545")

            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight", facecolor=fig.get_facecolor())
            plt.close(fig)
            buf.seek(0)
            return buf.getvalue()

        except ImportError:
            logger.warning("matplotlib yok, grafik olusturulamadi")
            return None
        except Exception as e:
            logger.error("Spektral grafik hatasi: %s", e)
            return None

    @staticmethod
    def create_multi_plot(
        curves: List[Tuple[str, List[float], str]],
        wavelengths: Optional[List[int]] = None,
        title: str = "Coklu Spektral Egriler",
    ) -> Optional[bytes]:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            if wavelengths is None:
                wavelengths = list(range(380, 781, 10))

            colors = ["#1A7AE8", "#E85D1A", "#107C10", "#FFD700", "#C42B1C", "#9B59B6", "#1ABC9C"]

            fig, ax = plt.subplots(1, 1, figsize=(10, 5), dpi=100)
            fig.patch.set_facecolor("#202020")
            ax.set_facecolor("#1A1A1A")

            for i, (name, refl, color_override) in enumerate(curves):
                n = min(len(wavelengths), len(refl))
                c = color_override if color_override else colors[i % len(colors)]
                ax.plot(wavelengths[:n], refl[:n], color=c, linewidth=1.8, label=name, marker="o", markersize=2)

            ax.set_xlabel("Dalga Boyu (nm)", color="#AAAAAA", fontsize=9)
            ax.set_ylabel("Yansima (%)", color="#AAAAAA", fontsize=9)
            ax.set_title(title, color="#FFFFFF", fontsize=11, fontweight="bold")
            ax.set_xlim(380, 780)
            ax.set_ylim(0, 100)
            ax.tick_params(colors="#888888")
            ax.grid(True, alpha=0.2, color="#555555")
            ax.legend(loc="upper right", fontsize=7, facecolor="#2D2D2D", edgecolor="#454545", labelcolor="#CCCCCC")

            for spine in ax.spines.values():
                spine.set_color("#454545")

            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight", facecolor=fig.get_facecolor())
            plt.close(fig)
            buf.seek(0)
            return buf.getvalue()

        except Exception as e:
            logger.error("Coklu spektral grafik hatasi: %s", e)
            return None
