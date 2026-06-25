# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Generator, Optional, Tuple

import cv2
import numpy as np

from config.settings import CAMERA

logger = logging.getLogger(__name__)


@dataclass
class CameraFrame:
    raw_bgr: np.ndarray
    preview_rgb: np.ndarray
    width: int
    height: int
    timestamp: float


class CameraManager:
    _instance: Optional[CameraManager] = None
    _capture: Optional[cv2.VideoCapture] = None

    def __new__(cls) -> CameraManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def open(self, device_id: Optional[int] = None) -> bool:
        dev = device_id if device_id is not None else CAMERA.device_id
        if self._capture is not None and self._capture.isOpened():
            return True
        self._capture = cv2.VideoCapture(dev)
        if not self._capture.isOpened():
            logger.error("Kamera açılamadı: device_id=%d", dev)
            return False
        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA.width)
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA.height)
        self._capture.set(cv2.CAP_PROP_FPS, CAMERA.fps_target)
        logger.info("Kamera açıldı: device_id=%d", dev)
        return True

    def release(self) -> None:
        if self._capture is not None:
            self._capture.release()
            self._capture = None
            logger.info("Kamera serbest bırakıldı.")

    @property
    def is_opened(self) -> bool:
        return self._capture is not None and self._capture.isOpened()

    def read_frame(self) -> Optional[CameraFrame]:
        if not self.is_opened:
            logger.warning("Kamera açık değil, okunamaz.")
            return None
        ret, frame = self._capture.read()
        if not ret or frame is None:
            logger.error("Kare okunamadı.")
            return None
        preview = cv2.resize(frame, (CAMERA.preview_width, CAMERA.preview_height))
        preview_rgb = cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)
        h, w = preview_rgb.shape[:2]
        return CameraFrame(
            raw_bgr=frame,
            preview_rgb=preview_rgb,
            width=w,
            height=h,
            timestamp=time.time(),
        )

    def capture_single(self) -> Optional[CameraFrame]:
        if not self.is_opened:
            if not self.open():
                return None
        time.sleep(0.1)
        return self.read_frame()

    @contextmanager
    def session(self) -> Generator[CameraManager, None, None]:
        opened = self.is_opened
        if not opened:
            self.open()
        try:
            yield self
        finally:
            if not opened:
                self.release()

    def list_devices(self) -> list[int]:
        available = []
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available.append(i)
                cap.release()
        return available
