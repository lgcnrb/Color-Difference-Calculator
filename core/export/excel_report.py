# -*- coding: utf-8 -*-
from __future__ import annotations

import io
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class ExcelReport:
    def __init__(self):
        self._writer = None
        self._workbook = None

    def create_report(
        self,
        filepath: str,
        job_name: str,
        customer: str,
        master_info: Dict,
        samples: List[Dict],
        spectral_graphs: Optional[List[Tuple[str, bytes]]] = None,
        color_plot: Optional[bytes] = None,
        de_bar_chart: Optional[bytes] = None,
        metamerism_data: Optional[List[Dict]] = None,
    ) -> bool:
        try:
            import pandas as pd

            with pd.ExcelWriter(filepath, engine="xlsxwriter") as writer:
                self._writer = writer
                self._workbook = writer.book

                self._write_summary_sheet(job_name, customer, master_info, samples)
                self._write_detail_sheet(samples)
                self._write_spectral_sheet(spectral_graphs)
                self._write_metamerism_sheet(metamerism_data)

                if color_plot:
                    self._embed_image(color_plot, "Renk Sapma Grafigi")
                if de_bar_chart:
                    self._embed_image(de_bar_chart, "DE Bar Grafigi")

            logger.info("Excel raporu olusturuldu: %s", filepath)
            return True

        except Exception as e:
            logger.error("Excel rapor hatasi: %s", e)
            return False

    def _write_summary_sheet(self, job_name, customer, master_info, samples):
        ws = self._workbook.add_worksheet("Ozet")
        self._writer.sheets["Ozet"] = ws

        header_fmt = self._workbook.add_format({
            "bold": True, "font_size": 14, "font_color": "#FFFFFF",
            "bg_color": "#1A7AE8", "border": 1, "text_wrap": True,
        })
        label_fmt = self._workbook.add_format({"bold": True, "font_size": 10, "bg_color": "#E8E8E8", "border": 1})
        value_fmt = self._workbook.add_format({"font_size": 10, "border": 1})
        pass_fmt = self._workbook.add_format({"font_size": 10, "bg_color": "#C6EFCE", "font_color": "#006100", "border": 1})
        fail_fmt = self._workbook.add_format({"font_size": 10, "bg_color": "#FFC7CE", "font_color": "#9C0006", "border": 1})
        warn_fmt = self._workbook.add_format({"font_size": 10, "bg_color": "#FFEB9C", "font_color": "#9C6500", "border": 1})

        ws.set_column("A:A", 20)
        ws.set_column("B:B", 25)
        ws.set_column("C:C", 20)
        ws.set_column("D:D", 15)
        ws.set_column("E:E", 15)

        ws.merge_range("A1:E1", f"RENK KALITE RAPORU  |  {job_name}", header_fmt)

        ws.write("A3", "Musteri:", label_fmt)
        ws.write("B3", customer, value_fmt)
        ws.write("A4", "Is Adi:", label_fmt)
        ws.write("B4", job_name, value_fmt)
        ws.write("A5", "Tarih:", label_fmt)
        ws.write("B5", datetime.now().strftime("%d/%m/%Y %H:%M"), value_fmt)

        ws.write("D3", "Master L*:", label_fmt)
        ws.write("E3", f"{master_info.get('L', 0):.2f}", value_fmt)
        ws.write("D4", "Master a*:", label_fmt)
        ws.write("E4", f"{master_info.get('a', 0):.2f}", value_fmt)
        ws.write("D5", "Master b*:", label_fmt)
        ws.write("E5", f"{master_info.get('b', 0):.2f}", value_fmt)

        total = len(samples)
        passed = sum(1 for s in samples if s.get("status") == "Gecti")
        failed = total - passed
        rate = (passed / total * 100) if total > 0 else 0

        ws.write("A7", "Toplam Numune:", label_fmt)
        ws.write("B7", total, value_fmt)
        ws.write("A8", "Gecen:", label_fmt)
        ws.write("B8", passed, pass_fmt)
        ws.write("A9", "Kalan:", label_fmt)
        ws.write("B9", failed, fail_fmt)
        ws.write("A10", "Basari Orani:", label_fmt)
        ws.write("B10", f"%{rate:.1f}", pass_fmt if rate >= 80 else warn_fmt)

        row = 12
        detail_header = self._workbook.add_format({
            "bold": True, "font_size": 9, "bg_color": "#2D2D2D", "font_color": "#FFFFFF", "border": 1,
        })
        headers = ["Numune", "L*", "a*", "b*", "Delta E", "Durum"]
        for col, h in enumerate(headers):
            ws.write(row, col, h, detail_header)
        row += 1

        for s in samples:
            ws.write(row, 0, s.get("name", ""), value_fmt)
            ws.write(row, 1, f"{s.get('L', 0):.2f}", value_fmt)
            ws.write(row, 2, f"{s.get('a', 0):.2f}", value_fmt)
            ws.write(row, 3, f"{s.get('b', 0):.2f}", value_fmt)
            de = s.get("delta_e", 0)
            ws.write(row, 4, f"{de:.3f}", value_fmt)
            status = s.get("status", "")
            if status == "Gecti":
                ws.write(row, 5, status, pass_fmt)
            elif status == "Reddedildi":
                ws.write(row, 5, status, fail_fmt)
            else:
                ws.write(row, 5, status, warn_fmt)
            row += 1

    def _write_detail_sheet(self, samples):
        ws = self._workbook.add_worksheet("Detay")
        self._writer.sheets["Detay"] = ws

        header_fmt = self._workbook.add_format({
            "bold": True, "font_size": 9, "bg_color": "#2D2D2D", "font_color": "#FFFFFF", "border": 1,
        })
        value_fmt = self._workbook.add_format({"font_size": 9, "border": 1})
        red_fmt = self._workbook.add_format({"font_size": 9, "bg_color": "#FFC7CE", "font_color": "#9C0006", "border": 1})

        headers = ["ID", "Numune", "Batch", "L*", "a*", "b*", "Delta E", "Lot", "Durum", "Notlar"]
        for col, h in enumerate(headers):
            ws.write(0, col, h, header_fmt)
            ws.set_column(col, col, 14)

        for row, s in enumerate(samples, 1):
            ws.write(row, 0, s.get("id", ""), value_fmt)
            ws.write(row, 1, s.get("name", ""), value_fmt)
            ws.write(row, 2, s.get("batch_id", ""), value_fmt)
            ws.write(row, 3, f"{s.get('L', 0):.2f}", value_fmt)
            ws.write(row, 4, f"{s.get('a', 0):.2f}", value_fmt)
            ws.write(row, 5, f"{s.get('b', 0):.2f}", value_fmt)

            de = s.get("delta_e", 0)
            if de > 1.5:
                ws.write(row, 6, f"{de:.3f}", red_fmt)
            else:
                ws.write(row, 6, f"{de:.3f}", value_fmt)

            ws.write(row, 7, s.get("lot_decision", ""), value_fmt)
            ws.write(row, 8, s.get("status", ""), value_fmt)
            ws.write(row, 9, s.get("notes", ""), value_fmt)

    def _write_spectral_sheet(self, spectral_graphs):
        if not spectral_graphs:
            return
        ws = self._workbook.add_worksheet("Spektral Grafikler")
        self._writer.sheets["Spektral Grafikler"] = ws
        ws.set_column("A:A", 80)

        row = 0
        for name, img_bytes in spectral_graphs:
            buf = io.BytesIO(img_bytes)
            self._workbook.add_worksheet()
            ws.insert_image(row, 0, name, {"image_data": buf, "x_scale": 0.5, "y_scale": 0.5})
            row += 30

    def _write_metamerism_sheet(self, metamerism_data):
        if not metamerism_data:
            return
        ws = self._workbook.add_worksheet("Metamerizm")
        self._writer.sheets["Metamerizm"] = ws

        header_fmt = self._workbook.add_format({
            "bold": True, "font_size": 9, "bg_color": "#2D2D2D", "font_color": "#FFFFFF", "border": 1,
        })
        value_fmt = self._workbook.add_format({"font_size": 9, "border": 1})
        pass_fmt = self._workbook.add_format({"font_size": 9, "bg_color": "#C6EFCE", "font_color": "#006100", "border": 1})
        fail_fmt = self._workbook.add_format({"font_size": 9, "bg_color": "#FFC7CE", "font_color": "#9C0006", "border": 1})

        headers = ["Numune", "Isik Kaynagi", "Delta E", "Delta L", "Delta a", "Delta b", "Durum"]
        for col, h in enumerate(headers):
            ws.write(0, col, h, header_fmt)
            ws.set_column(col, col, 16)

        for row, entry in enumerate(metamerism_data, 1):
            ws.write(row, 0, entry.get("sample", ""), value_fmt)
            ws.write(row, 1, entry.get("illuminant", ""), value_fmt)
            ws.write(row, 2, f"{entry.get('de', 0):.3f}", value_fmt)
            ws.write(row, 3, f"{entry.get('dL', 0):.3f}", value_fmt)
            ws.write(row, 4, f"{entry.get('da', 0):.3f}", value_fmt)
            ws.write(row, 5, f"{entry.get('db', 0):.3f}", value_fmt)
            status = entry.get("status", "")
            ws.write(row, 6, status, pass_fmt if status == "Gecti" else fail_fmt)

    def _embed_image(self, img_bytes: bytes, title: str):
        try:
            ws = self._workbook.add_worksheet(title[:31])
            self._writer.sheets[title[:31]] = ws
            buf = io.BytesIO(img_bytes)
            ws.insert_image("A1", title, {"image_data": buf, "x_scale": 0.6, "y_scale": 0.6})
        except Exception as e:
            logger.error("Gorsel ekleme hatasi: %s", e)
