# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)

_TORCH_AVAILABLE = False
try:
    import torch
    import torchvision.models as models
    import torchvision.transforms as transforms
    _TORCH_AVAILABLE = True
except ImportError:
    logger.warning("PyTorch not found. CNN features disabled.")


class FeatureExtractor:
    FEATURE_DIM = 1101  # LAB(3) + CNN(960) + Doku(138)

    def __init__(self, use_gpu: bool = True):
        self.device = None
        self.cnn_model = None
        self.cnn_transform = None
        self._use_gpu = use_gpu
        self._initialized = False

    def initialize(self):
        if self._initialized:
            return
        if _TORCH_AVAILABLE:
            self._init_cnn()
        else:
            logger.warning("CNN disabled. Only LAB + Texture will be used.")
        self._initialized = True

    def _init_cnn(self):
        if not _TORCH_AVAILABLE:
            return
        self.device = torch.device(
            "cuda" if torch.cuda.is_available() and self._use_gpu else "cpu"
        )
        logger.info("CNN device: %s", self.device)

        model = models.mobilenet_v3_large(weights=models.MobileNet_V3_Large_Weights.DEFAULT)
        features = list(model.children())[:-1]
        self.cnn_model = torch.nn.Sequential(*features)
        self.cnn_model.to(self.device)
        self.cnn_model.eval()

        self.cnn_transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ])
        logger.info("MobileNetV3-Large loaded. Feature dim: 960")

    def extract(self, frame_rgb: np.ndarray) -> np.ndarray:
        self.initialize()
        lab_feat = self._extract_lab(frame_rgb)
        cnn_feat = self._extract_cnn(frame_rgb)
        tex_feat = self._extract_texture(frame_rgb)
        return np.concatenate([lab_feat, cnn_feat, tex_feat]).astype(np.float32)

    def _extract_lab(self, frame_rgb: np.ndarray) -> np.ndarray:
        if frame_rgb.dtype == np.uint8:
            img = frame_rgb.astype(np.float64) / 255.0
        else:
            img = frame_rgb.astype(np.float64)

        img_rgb = np.clip(img, 0, 1)
        img_lab = cv2.cvtColor((img_rgb * 255).astype(np.uint8), cv2.COLOR_RGB2LAB)
        img_lab_f = img_lab.astype(np.float64)

        mean_lab = np.mean(img_lab_f, axis=(0, 1))
        std_lab = np.std(img_lab_f, axis=(0, 1))

        return np.array([
            mean_lab[0] / 100.0,
            (mean_lab[1] + 128.0) / 255.0,
            (mean_lab[2] + 128.0) / 255.0,
        ])

    def _extract_cnn(self, frame_rgb: np.ndarray) -> np.ndarray:
        if not _TORCH_AVAILABLE or self.cnn_model is None:
            return np.zeros(960, dtype=np.float32)

        try:
            img = frame_rgb.copy()
            if img.dtype == np.uint8:
                img = img.astype(np.float32) / 255.0

            tensor = self.cnn_transform((img * 255).astype(np.uint8))
            tensor = tensor.unsqueeze(0).to(self.device)

            with torch.no_grad():
                features = self.cnn_model(tensor)

            feat = features.squeeze().cpu().numpy().flatten()
            feat = feat[:960]
            if len(feat) < 960:
                feat = np.pad(feat, (0, 960 - len(feat)))
            return feat.astype(np.float32)
        except Exception as e:
            logger.error("CNN feature extraction error: %s", e)
            return np.zeros(960, dtype=np.float32)

    def _extract_texture(self, frame_rgb: np.ndarray) -> np.ndarray:
        if len(frame_rgb.shape) == 3:
            gray = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2GRAY)
        else:
            gray = frame_rgb
        gray = gray.astype(np.uint8)

        hist_feat = self._histogram_features(gray)
        gabor_feat = self._gabor_features(gray)
        lbp_feat = self._lbp_features(gray)

        return np.concatenate([hist_feat, gabor_feat, lbp_feat]).astype(np.float32)

    def _histogram_features(self, gray: np.ndarray) -> np.ndarray:
        hist = cv2.calcHist([gray], [0], None, [32], [0, 256])
        hist = hist.flatten()
        hist = hist / (hist.sum() + 1e-7)
        return hist.astype(np.float32)

    def _gabor_features(self, gray: np.ndarray) -> np.ndarray:
        features = []
        orientations = [0, np.pi / 4, np.pi / 2, 3 * np.pi / 4]
        scales = [3, 5, 7, 11]

        for theta in orientations:
            for sigma in scales:
                kernel_size = max(3, sigma * 2 + 1)
                kernel = cv2.getGaborKernel(
                    (int(kernel_size), int(kernel_size)),
                    sigma, theta, 10, 0.5, 0,
                )
                filtered = cv2.filter2D(gray, cv2.CV_64F, kernel)
                features.append(np.mean(filtered))
                features.append(np.std(filtered))

        features = np.array(features)
        max_val = np.max(np.abs(features))
        if max_val > 0:
            features = features / max_val
        return features.astype(np.float32)

    def _lbp_features(self, gray: np.ndarray) -> np.ndarray:
        h, w = gray.shape
        lbp = np.zeros((h, w), dtype=np.uint8)

        for i in range(1, h - 1):
            for j in range(1, w - 1):
                center = gray[i, j]
                code = 0
                code |= (1 << 7) if gray[i - 1, j - 1] >= center else 0
                code |= (1 << 6) if gray[i - 1, j] >= center else 0
                code |= (1 << 5) if gray[i - 1, j + 1] >= center else 0
                code |= (1 << 4) if gray[i, j + 1] >= center else 0
                code |= (1 << 3) if gray[i + 1, j + 1] >= center else 0
                code |= (1 << 2) if gray[i + 1, j] >= center else 0
                code |= (1 << 1) if gray[i + 1, j - 1] >= center else 0
                code |= (1 << 0) if gray[i, j - 1] >= center else 0
                lbp[i, j] = code

        hist, _ = np.histogram(lbp.ravel(), bins=26, range=(0, 256))
        hist = hist.astype(np.float64)
        hist = hist / (hist.sum() + 1e-7)
        return hist.astype(np.float32)


_feature_extractor: Optional[FeatureExtractor] = None


def get_feature_extractor() -> FeatureExtractor:
    global _feature_extractor
    if _feature_extractor is None:
        _feature_extractor = FeatureExtractor(use_gpu=True)
    return _feature_extractor
