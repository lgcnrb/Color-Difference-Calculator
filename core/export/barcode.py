# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class BarcodeGenerator:
    @staticmethod
    def generate_codebar(
        lot_name: str,
        pantone: str = "",
        customer: str = "",
    ) -> str:
        parts = [lot_name.replace(" ", "-")]
        if pantone:
            parts.append(pantone.replace(" ", ""))
        if customer:
            parts.append(customer.replace(" ", "-")[:15])
        return "-".join(parts)

    @staticmethod
    def create_barcode_image(
        code: str,
        width: int = 300,
        height: int = 100,
    ) -> Optional[bytes]:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import matplotlib.patches as patches
            import io

            fig, ax = plt.subplots(1, 1, figsize=(width/100, height/100), dpi=100)
            fig.patch.set_facecolor("white")
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis("off")

            import hashlib
            code_hash = hashlib.md5(code.encode()).hexdigest()
            bits = bin(int(code_hash[:8], 16))[2:].zfill(32)

            x_start = 0.05
            x_end = 0.95
            bar_width = (x_end - x_start) / len(bits)

            for i, bit in enumerate(bits):
                if bit == "1":
                    x = x_start + i * bar_width
                    ax.add_patch(patches.Rectangle((x, 0.15), bar_width * 0.8, 0.55, color="black"))

            ax.text(0.5, 0.85, code, ha="center", va="center", fontsize=7, fontfamily="monospace", color="black")
            ax.text(0.5, 0.05, "ColorIQ", ha="center", va="center", fontsize=5, color="#888888")

            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight", dpi=100, facecolor="white")
            plt.close(fig)
            buf.seek(0)
            return buf.getvalue()

        except Exception as e:
            logger.error("Barcode creation error: %s", e)
            return None

    @staticmethod
    def create_label_text(
        lot_name: str,
        batch_id: str = "",
        pantone: str = "",
        de_value: float = 0.0,
        status: str = "",
        customer: str = "",
    ) -> str:
        lines = [
            "=" * 40,
            "  ColorIQ - COLOR QUALITY LABEL",
            "=" * 40,
            f"  Lot:        {lot_name}",
        ]
        if batch_id:
            lines.append(f"  Batch:      {batch_id}")
        if pantone:
            lines.append(f"  Pantone:    {pantone}")
        if customer:
            lines.append(f"  Customer:   {customer}")
        lines.extend([
            f"  Delta E:    {de_value:.3f}",
            f"  Status:     {status}",
            "=" * 40,
        ])
        return "\n".join(lines)
