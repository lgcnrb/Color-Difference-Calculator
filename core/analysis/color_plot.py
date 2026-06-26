# -*- coding: utf-8 -*-
from __future__ import annotations

import io
import logging
from typing import List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class ColorPlot:
    @staticmethod
    def create_target_board(
        measurements: List[Tuple[float, float, str]],
        tolerance: float = 1.0,
        title: str = "Color Deviation Graph (Target Board)",
    ) -> Optional[bytes]:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(1, 1, figsize=(7, 7), dpi=100)
            fig.patch.set_facecolor("#202020")
            ax.set_facecolor("#1A1A1A")

            circle1 = plt.Circle((0, 0), tolerance, color="#107C10", fill=False, linestyle="--", linewidth=1.5, label=f"Tolerance (DE={tolerance})")
            circle2 = plt.Circle((0, 0), tolerance * 1.5, color="#C19C00", fill=False, linestyle=":", linewidth=1.0, label=f"Warning (DE={tolerance*1.5:.1f})")
            circle3 = plt.Circle((0, 0), tolerance * 2.0, color="#C42B1C", fill=False, linestyle="-.", linewidth=1.0, label=f"Reject (DE={tolerance*2:.1f})")
            ax.add_artist(circle1)
            ax.add_artist(circle2)
            ax.add_artist(circle3)

            ax.axhline(y=0, color="#555555", linewidth=0.8)
            ax.axvline(x=0, color="#555555", linewidth=0.8)

            for da, db, name in measurements:
                de = np.sqrt(da**2 + db**2)
                if de <= tolerance:
                    color = "#107C10"
                elif de <= tolerance * 1.5:
                    color = "#C19C00"
                else:
                    color = "#C42B1C"
                ax.plot(da, db, "o", color=color, markersize=8, markeredgecolor="#FFFFFF", markeredgewidth=0.5)
                ax.annotate(name, (da, db), textcoords="offset points", xytext=(5, 5),
                           fontsize=7, color="#AAAAAA")

            ax.set_xlabel("Delta a* (Red-Green)", color="#AAAAAA", fontsize=9)
            ax.set_ylabel("Delta b* (Yellow-Blue)", color="#AAAAAA", fontsize=9)
            ax.set_title(title, color="#FFFFFF", fontsize=11, fontweight="bold")
            ax.set_aspect("equal")
            ax.grid(True, alpha=0.15, color="#555555")
            ax.legend(loc="upper left", fontsize=8, facecolor="#2D2D2D", edgecolor="#454545", labelcolor="#CCCCCC")

            for spine in ax.spines.values():
                spine.set_color("#454545")

            limit = tolerance * 2.5
            ax.set_xlim(-limit, limit)
            ax.set_ylim(-limit, limit)

            ax.text(0.7, 0.95, "+Red / +Yellow", transform=ax.transAxes, fontsize=7, color="#888888", ha="center")
            ax.text(0.7, 0.02, "+Red / -Blue", transform=ax.transAxes, fontsize=7, color="#888888", ha="center")
            ax.text(0.0, 0.95, "-Green / +Yellow", transform=ax.transAxes, fontsize=7, color="#888888", ha="center")
            ax.text(0.0, 0.02, "-Green / -Blue", transform=ax.transAxes, fontsize=7, color="#888888", ha="center")

            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight", facecolor=fig.get_facecolor())
            plt.close(fig)
            buf.seek(0)
            return buf.getvalue()

        except ImportError:
            logger.warning("matplotlib not available")
            return None
        except Exception as e:
            logger.error("Target board graph error: %s", e)
            return None

    @staticmethod
    def create_de_bar_chart(
        measurements: List[Tuple[str, float, str]],
        tolerance: float = 1.0,
        title: str = "Delta E Values",
    ) -> Optional[bytes]:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            names = [m[0] for m in measurements]
            des = [m[1] for m in measurements]
            colors = ["#107C10" if de <= tolerance else ("#C19C00" if de <= tolerance * 1.5 else "#C42B1C") for de in des]

            fig, ax = plt.subplots(1, 1, figsize=(max(6, len(names) * 0.8), 4), dpi=100)
            fig.patch.set_facecolor("#202020")
            ax.set_facecolor("#1A1A1A")

            bars = ax.bar(names, des, color=colors, edgecolor="#454545", linewidth=0.5)
            ax.axhline(y=tolerance, color="#C42B1C", linestyle="--", linewidth=1.0, label=f"Tolerance ({tolerance})")

            ax.set_ylabel("Delta E", color="#AAAAAA", fontsize=9)
            ax.set_title(title, color="#FFFFFF", fontsize=11, fontweight="bold")
            ax.tick_params(colors="#888888", labelsize=8)
            ax.legend(facecolor="#2D2D2D", edgecolor="#454545", labelcolor="#CCCCCC", fontsize=8)

            for bar, de in zip(bars, des):
                ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.02,
                       f"{de:.2f}", ha="center", va="bottom", color="#CCCCCC", fontsize=7)

            for spine in ax.spines.values():
                spine.set_color("#454545")

            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight", facecolor=fig.get_facecolor())
            plt.close(fig)
            buf.seek(0)
            return buf.getvalue()

        except Exception as e:
            logger.error("DE bar graph error: %s", e)
            return None
