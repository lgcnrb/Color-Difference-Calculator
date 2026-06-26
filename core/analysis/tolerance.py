# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ToleranceResult:
    method: str
    cluster_count: int
    cluster_centers: List[Tuple[float, float]]
    cluster_sizes: List[int]
    suggested_de_threshold: float
    sample_labels: List[str] = field(default_factory=list)
    sample_clusters: List[int] = field(default_factory=list)


class ToleranceEngine:
    @staticmethod
    def dbscan_auto_tolerance(
        measurements: List[Tuple[float, float]],
        eps: float = 0.5,
        min_samples: int = 2,
    ) -> ToleranceResult:
        if len(measurements) < min_samples:
            return ToleranceResult(
                method="DBSCAN",
                cluster_count=0,
                cluster_centers=[],
                cluster_sizes=[],
                suggested_de_threshold=1.0,
            )

        X = np.array(measurements)

        try:
            from sklearn.cluster import DBSCAN
            clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(X)
            labels = clustering.labels_
        except ImportError:
            labels = np.zeros(len(X), dtype=int)

        unique_labels = set(labels)
        unique_labels.discard(-1)

        centers = []
        sizes = []
        for label in sorted(unique_labels):
            mask = labels == label
            cluster_points = X[mask]
            center = cluster_points.mean(axis=0)
            centers.append((float(center[0]), float(center[1])))
            sizes.append(int(mask.sum()))

        if centers:
            center_arr = np.array(centers)
            max_dist = 0
            for i in range(len(centers)):
                for j in range(i + 1, len(centers)):
                    dist = np.linalg.norm(center_arr[i] - center_arr[j])
                    max_dist = max(max_dist, dist)
            suggested_threshold = max_dist * 0.7 + 0.3
        else:
            all_de = np.sqrt(X[:, 0]**2 + X[:, 1]**2)
            suggested_threshold = float(np.percentile(all_de, 90)) if len(all_de) > 0 else 1.0

        return ToleranceResult(
            method="DBSCAN",
            cluster_count=len(centers),
            cluster_centers=centers,
            cluster_sizes=sizes,
            suggested_de_threshold=round(suggested_threshold, 3),
            sample_clusters=[int(l) for l in labels],
        )

    @staticmethod
    def kmeans_auto_tolerance(
        measurements: List[Tuple[float, float]],
        max_k: int = 5,
    ) -> ToleranceResult:
        if len(measurements) < 2:
            return ToleranceResult(
                method="K-Means",
                cluster_count=1,
                cluster_centers=[measurements[0]] if measurements else [],
                cluster_sizes=[len(measurements)],
                suggested_de_threshold=1.0,
            )

        X = np.array(measurements)

        try:
            from sklearn.cluster import KMeans
            from sklearn.metrics import silhouette_score

            best_k = 2
            best_score = -1
            for k in range(2, min(max_k + 1, len(X))):
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                labels = kmeans.fit_predict(X)
                score = silhouette_score(X, labels)
                if score > best_score:
                    best_score = score
                    best_k = k

            kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(X)
            centers = [(float(c[0]), float(c[1])) for c in kmeans.cluster_centers_]

        except ImportError:
            labels = np.zeros(len(X), dtype=int)
            centers = [(float(X[:, 0].mean()), float(X[:, 1].mean()))]

        sizes = []
        for label in range(max(labels) + 1):
            sizes.append(int((labels == label).sum()))

        if centers:
            center_arr = np.array(centers)
            max_dist = 0
            for i in range(len(centers)):
                for j in range(i + 1, len(centers)):
                    dist = np.linalg.norm(center_arr[i] - center_arr[j])
                    max_dist = max(max_dist, dist)
            suggested_threshold = max_dist * 0.7 + 0.3
        else:
            suggested_threshold = 1.0

        return ToleranceResult(
            method="K-Means",
            cluster_count=len(centers),
            cluster_centers=centers,
            cluster_sizes=sizes,
            suggested_de_threshold=round(suggested_threshold, 3),
            sample_clusters=[int(l) for l in labels],
        )

    @staticmethod
    def statistical_tolerance(
        de_values: List[float],
        confidence: float = 0.95,
    ) -> float:
        if not de_values:
            return 1.0
        arr = np.array(de_values)
        mean = arr.mean()
        std = arr.std(ddof=1) if len(arr) > 1 else 0

        from scipy import stats as scipy_stats
        n = len(arr)
        t_value = scipy_stats.t.ppf((1 + confidence) / 2, df=n-1) if n > 1 else 1.96

        threshold = mean + t_value * std
        return round(max(threshold, 0.5), 3)

    @staticmethod
    def adaptive_tolerance(
        measurements: List[Tuple[float, float]],
        method: str = "auto",
    ) -> ToleranceResult:
        if method == "dbscan":
            return ToleranceEngine.dbscan_auto_tolerance(measurements)
        elif method == "kmeans":
            return ToleranceEngine.kmeans_auto_tolerance(measurements)
        else:
            if len(measurements) < 5:
                return ToleranceEngine.kmeans_auto_tolerance(measurements)
            return ToleranceEngine.dbscan_auto_tolerance(measurements)
