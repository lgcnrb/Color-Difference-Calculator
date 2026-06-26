# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
import os as _os
_os.environ.setdefault("OMP_NUM_THREADS", "1")

from config.settings import LOTTING, DELTA_METHODS, EXPORT_DIR
from core.models.color_data import LabColor, DeltaEResult
from core.color_engine.delta_e_lib import calculate_all_delta_e

logger = logging.getLogger(__name__)


class DeltaECalculator:
    @classmethod
    def calculate(cls, reference: LabColor, sample: LabColor) -> DeltaEResult:
        all_de = calculate_all_delta_e(
            reference.L, reference.a, reference.b,
            sample.L, sample.a, sample.b,
        )
        dL = sample.L - reference.L
        da = sample.a - reference.a
        db = sample.b - reference.b
        dC = (sample.a ** 2 + sample.b ** 2) ** 0.5 - (reference.a ** 2 + reference.b ** 2) ** 0.5

        return DeltaEResult(
            de_1976=all_de["cie1976"],
            de_1994=all_de["cie1994"],
            de_2000=all_de["cie2000"],
            de_cmc=all_de["cmc"],
            dL=float(dL),
            da=float(da),
            db=float(db),
            dC=float(dC),
            dH=0.0,
        )

    @classmethod
    def calculate_by_method(cls, reference: LabColor, sample: LabColor, method: str) -> float:
        result = cls.calculate(reference, sample)
        return result.get_by_method(method)

    @classmethod
    def pairwise_de(cls, labs: List[LabColor]) -> Dict[str, float]:
        if len(labs) < 2:
            return {"mean": 0.0, "min": 0.0, "max": 0.0, "std": 0.0}
        pairwise = []
        for i in range(len(labs)):
            for j in range(i + 1, len(labs)):
                de = cls.calculate_by_method(labs[i], labs[j], DELTA_METHODS.CIE2000)
                pairwise.append(de)
        if not pairwise:
            return {"mean": 0.0, "min": 0.0, "max": 0.0, "std": 0.0}
        arr = np.array(pairwise)
        return {
            "mean": float(np.mean(arr)),
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
            "std": float(np.std(arr)) if len(arr) > 1 else 0.0,
        }


@dataclass
class MeasurementRecord:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8].upper())
    image_path: str = ""
    lab: Optional[LabColor] = None
    feature_vector: Optional[np.ndarray] = None
    delta_e: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    lot_group: str = ""
    lot_color: str = ""


class LottingEngine:
    LOT_COLORS = [
        "#107C10", "#0078D4", "#C19C00", "#C42B1C",
        "#8764B8", "#00B294", "#E3008C", "#767676",
        "#00CC6A", "#FF8C00", "#68217A", "#00188F",
    ]

    CLUSTERING_METHODS = {
        "kmeans": {
            "name": "K-Means",
            "description": "Determines optimal k using silhouette score. Fast and general purpose.",
            "params": {"auto_k": True, "fixed_k": 3},
        },
        "dbscan": {
            "name": "DBSCAN",
            "description": "Clusters by density. Good for noisy data. Adjust precision with eps.",
            "params": {"eps": 1.0, "min_samples": 2},
        },
        "agglomerative": {
            "name": "Agglomerative",
            "description": "Hierarchical clustering. k can be visualized with dendrogram.",
            "params": {"auto_k": True, "fixed_k": 3, "linkage": "ward"},
        },
    }

    def __init__(self):
        self.measurements: List[MeasurementRecord] = []
        self.job_folder: str = ""
        self.tolerance_eps: float = LOTTING.default_eps
        self.clustering_method: str = "kmeans"
        self.method_params: Dict = {"auto_k": True, "fixed_k": 3, "eps": 1.0, "min_samples": 2, "linkage": "ward"}
        self._feature_extractor = None

    def _get_feature_extractor(self):
        if self._feature_extractor is None:
            from core.color_engine.feature_extractor import get_feature_extractor
            self._feature_extractor = get_feature_extractor()
        return self._feature_extractor

    def set_tolerance(self, eps: float):
        self.tolerance_eps = max(LOTTING.min_eps, min(LOTTING.max_eps, eps))

    def set_clustering_method(self, method: str):
        if method in self.CLUSTERING_METHODS:
            self.clustering_method = method

    def set_method_param(self, key: str, value):
        self.method_params[key] = value

    def get_method_info(self) -> Dict:
        info = self.CLUSTERING_METHODS.get(self.clustering_method, {})
        return {
            "name": info.get("name", ""),
            "description": info.get("description", ""),
            "params": self.method_params.copy(),
        }

    def set_job_folder(self, folder: str):
        self.job_folder = folder
        os.makedirs(folder, exist_ok=True)
        os.makedirs(os.path.join(folder, "images"), exist_ok=True)

    def _ensure_folder(self):
        if not self.job_folder:
            self.set_job_folder(os.path.join(EXPORT_DIR, "auto_measurements"))

    def save_measurement(self, frame: np.ndarray, lab: LabColor) -> MeasurementRecord:
        self._ensure_folder()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"measurement_{timestamp}_{uuid.uuid4().hex[:4]}.png"
        filepath = os.path.join(self.job_folder, "images", filename)
        cv2.imwrite(filepath, frame)

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) if len(frame.shape) == 3 else frame
        feature_extractor = self._get_feature_extractor()
        feature_vector = feature_extractor.extract(frame_rgb)

        record = MeasurementRecord(
            image_path=filepath,
            lab=lab,
            feature_vector=feature_vector,
        )
        self.measurements.append(record)
        return record

    def analyze_image(self, image_path: str) -> Optional[Tuple[LabColor, np.ndarray]]:
        try:
            frame = cv2.imread(image_path)
            if frame is None:
                return None
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            from core.color_engine.color_convert import rgb_to_lab
            lab_img = rgb_to_lab(frame_rgb)
            mean_lab = np.mean(lab_img, axis=(0, 1))
            lab = LabColor(L=float(mean_lab[0]), a=float(mean_lab[1]), b=float(mean_lab[2]))

            feature_extractor = self._get_feature_extractor()
            feature_vector = feature_extractor.extract(frame_rgb)
            return lab, feature_vector
        except Exception as e:
            logger.error("Image analysis error (%s): %s", image_path, e)
            return None

    def batch_analyze(self) -> List[MeasurementRecord]:
        for record in self.measurements:
            if record.lab is None and record.image_path:
                result = self.analyze_image(record.image_path)
                if result:
                    record.lab, record.feature_vector = result
        return self.measurements

    def assign_lot_for_new(self, record: MeasurementRecord) -> str:
        if len(self.measurements) <= 1:
            record.lot_group = "LOT-A"
            record.lot_color = self.LOT_COLORS[0]
            return record.lot_group

        existing = [m for m in self.measurements if m.id != record.id and m.lab is not None]
        if not existing or record.lab is None:
            record.lot_group = "LOT-A"
            record.lot_color = self.LOT_COLORS[0]
            return record.lot_group

        labs = [m.lab for m in existing] + [record.lab]
        n = len(labs)

        if n < 3:
            closest_dist = float("inf")
            closest_lot = "LOT-A"
            for m in existing:
                dist = np.linalg.norm(record.lab.to_array() - m.lab.to_array())
                if dist < closest_dist:
                    closest_dist = dist
                    closest_lot = m.lot_group
            record.lot_group = closest_lot
            record.lot_color = self.LOT_COLORS[0]
            return record.lot_group

        try:
            from sklearn.cluster import KMeans
            from sklearn.preprocessing import StandardScaler
            from sklearn.metrics import silhouette_score

            X = np.array([[l.L, l.a, l.b] for l in labs])
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            best_k = 2
            best_score = -1
            max_k = min(n - 1, 8)

            for k in range(2, max_k + 1):
                km = KMeans(n_clusters=k, random_state=42, n_init=10)
                labels = km.fit_predict(X_scaled)
                if len(set(labels)) < 2:
                    continue
                score = silhouette_score(X_scaled, labels)
                if score > best_score:
                    best_score = score
                    best_k = k

            km = KMeans(n_clusters=best_k, random_state=42, n_init=10)
            labels = km.fit_predict(X_scaled)
            new_label = labels[-1]

            lot_map = {}
            for idx in range(best_k):
                lot_name = f"LOT-{chr(65 + min(idx, 25))}"
                lot_map[idx] = lot_name

            record.lot_group = lot_map[new_label]
            record.lot_color = self.LOT_COLORS[new_label % len(self.LOT_COLORS)]

            for i, m in enumerate(existing):
                m.lot_group = lot_map[labels[i]]
                m.lot_color = self.LOT_COLORS[labels[i] % len(self.LOT_COLORS)]

        except ImportError:
            closest_dist = float("inf")
            closest_lot = "LOT-A"
            for m in existing:
                dist = np.linalg.norm(record.lab.to_array() - m.lab.to_array())
                if dist < closest_dist:
                    closest_dist = dist
                    closest_lot = m.lot_group
            record.lot_group = closest_lot

        return record.lot_group

    def cluster_lots(self, measurements: Optional[List[MeasurementRecord]] = None) -> Dict[str, List[MeasurementRecord]]:
        if measurements is None:
            measurements = self.measurements

        valid = [m for m in measurements if m.lab is not None]
        if not valid:
            return {}
        if len(valid) == 1:
            valid[0].lot_group = "LOT-A"
            valid[0].lot_color = self.LOT_COLORS[0]
            return {"LOT-A": valid}
        if len(valid) == 2:
            lab0 = valid[0].lab
            lab1 = valid[1].lab
            de = DeltaECalculator.calculate_by_method(lab0, lab1, DELTA_METHODS.CIE2000)
            if de <= self.tolerance_eps:
                valid[0].lot_group = "LOT-A"
                valid[0].lot_color = self.LOT_COLORS[0]
                valid[1].lot_group = "LOT-A"
                valid[1].lot_color = self.LOT_COLORS[0]
                return {"LOT-A": valid}
            else:
                valid[0].lot_group = "LOT-A"
                valid[0].lot_color = self.LOT_COLORS[0]
                valid[1].lot_group = "LOT-B"
                valid[1].lot_color = self.LOT_COLORS[1]
                return {"LOT-A": [valid[0]], "LOT-B": [valid[1]]}

        X = np.array([[m.lab.L, m.lab.a, m.lab.b] for m in valid])

        try:
            from sklearn.preprocessing import StandardScaler
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            if self.clustering_method == "dbscan":
                labels = self._cluster_dbscan(X_scaled)
            elif self.clustering_method == "agglomerative":
                labels = self._cluster_agglomerative(X_scaled)
            else:
                labels = self._cluster_kmeans(X_scaled)

            groups: Dict[str, List[MeasurementRecord]] = {}
            unique_labels = sorted(set(labels))

            for idx, label in enumerate(unique_labels):
                lot_name = f"LOT-{chr(65 + min(idx, 25))}"
                members = [valid[i] for i in range(len(valid)) if labels[i] == label]
                groups[lot_name] = members
                color = self.LOT_COLORS[idx % len(self.LOT_COLORS)]
                for m in members:
                    m.lot_group = lot_name
                    m.lot_color = color

            method_name = self.CLUSTERING_METHODS.get(self.clustering_method, {}).get("name", self.clustering_method)
            logger.info("%s lotting: %d groups, %d samples", method_name, len(groups), len(valid))
            return groups

        except ImportError:
            logger.warning("sklearn not available, falling back to LAB distance clustering")
            return self._lab_distance_clustering(valid)

    def _cluster_kmeans(self, X_scaled: np.ndarray) -> np.ndarray:
        from sklearn.cluster import KMeans
        from sklearn.metrics import silhouette_score

        n = len(X_scaled)
        if self.method_params.get("auto_k", True):
            best_k = 2
            best_score = -1
            max_k = min(n - 1, 8)
            for k in range(2, max_k + 1):
                km = KMeans(n_clusters=k, random_state=42, n_init=10)
                labels = km.fit_predict(X_scaled)
                if len(set(labels)) < 2:
                    continue
                score = silhouette_score(X_scaled, labels)
                if score > best_score:
                    best_score = score
                    best_k = k
            k = best_k
        else:
            k = max(2, min(self.method_params.get("fixed_k", 3), n - 1))

        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        return km.fit_predict(X_scaled)

    def _cluster_dbscan(self, X_scaled: np.ndarray) -> np.ndarray:
        from sklearn.cluster import DBSCAN

        eps = self.method_params.get("eps", 1.0)
        min_samples = self.method_params.get("min_samples", 2)
        clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(X_scaled)
        labels = clustering.labels_

        if len(set(labels)) < 2 or (labels == -1).all():
            from sklearn.cluster import KMeans
            km = KMeans(n_clusters=2, random_state=42, n_init=10)
            labels = km.fit_predict(X_scaled)

        return labels

    def _cluster_agglomerative(self, X_scaled: np.ndarray) -> np.ndarray:
        from sklearn.cluster import AgglomerativeClustering
        from sklearn.metrics import silhouette_score

        n = len(X_scaled)
        linkage = self.method_params.get("linkage", "ward")

        if self.method_params.get("auto_k", True):
            best_k = 2
            best_score = -1
            max_k = min(n - 1, 8)
            for k in range(2, max_k + 1):
                agg = AgglomerativeClustering(n_clusters=k, linkage=linkage)
                labels = agg.fit_predict(X_scaled)
                if len(set(labels)) < 2:
                    continue
                score = silhouette_score(X_scaled, labels)
                if score > best_score:
                    best_score = score
                    best_k = k
            k = best_k
        else:
            k = max(2, min(self.method_params.get("fixed_k", 3), n - 1))

        agg = AgglomerativeClustering(n_clusters=k, linkage=linkage)
        return agg.fit_predict(X_scaled)

    def _lab_distance_clustering(self, measurements: List[MeasurementRecord]) -> Dict[str, List[MeasurementRecord]]:
        if not measurements:
            return {}

        groups: Dict[str, List[MeasurementRecord]] = {}
        lot_idx = 0

        for m in measurements:
            assigned = False
            for lot_name, members in groups.items():
                center_labs = [x.lab for x in members if x.lab]
                if center_labs and m.lab:
                    center = LabColor(
                        L=np.mean([l.L for l in center_labs]),
                        a=np.mean([l.a for l in center_labs]),
                        b=np.mean([l.b for l in center_labs]),
                    )
                    de = DeltaECalculator.calculate_by_method(center, m.lab, DELTA_METHODS.CIE2000)
                    if de <= self.tolerance_eps:
                        groups[lot_name].append(m)
                        m.lot_group = lot_name
                        assigned = True
                        break

            if not assigned:
                lot_name = f"LOT-{chr(65 + min(lot_idx, 25))}"
                groups[lot_name] = [m]
                m.lot_group = lot_name
                m.lot_color = self.LOT_COLORS[lot_idx % len(self.LOT_COLORS)]
                lot_idx += 1

        return groups

    def compute_lot_statistics(self, groups: Dict[str, List[MeasurementRecord]]) -> List[Dict]:
        stats = []
        for lot_name, members in sorted(groups.items()):
            labs = [m.lab for m in members if m.lab]
            intra = DeltaECalculator.pairwise_de(labs) if len(labs) >= 2 else {"mean": 0.0, "min": 0.0, "max": 0.0, "std": 0.0}

            mean_lab = None
            if labs:
                mean_lab = LabColor(
                    L=float(np.mean([l.L for l in labs])),
                    a=float(np.mean([l.a for l in labs])),
                    b=float(np.mean([l.b for l in labs])),
                )

            color = members[0].lot_color if members else self.LOT_COLORS[0]
            stat = {
                "lot": lot_name,
                "count": len(members),
                "de_mean": intra["mean"],
                "de_min": intra["min"],
                "de_max": intra["max"],
                "de_std": intra["std"],
                "mean_lab": mean_lab,
                "status": self._lot_status(intra["max"]),
                "members": members,
                "color": color,
            }
            stats.append(stat)
        return stats

    @staticmethod
    def _lot_status(worst_de: float) -> str:
        if worst_de <= LOTTING.lot_a_threshold:
            return "Perfect"
        elif worst_de <= LOTTING.lot_b_threshold:
            return "Good"
        elif worst_de <= LOTTING.lot_c_threshold:
            return "Acceptable"
        elif worst_de <= LOTTING.lot_d_threshold:
            return "Borderline"
        else:
            return "REJECTED"

    def generate_report(self) -> Dict:
        groups = self.cluster_lots()
        stats = self.compute_lot_statistics(groups)
        total = len(self.measurements)
        passed = sum(s["count"] for s in stats if s["status"] in ("Perfect", "Good", "Acceptable"))
        return {
            "total_measurements": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": (passed / total * 100) if total > 0 else 0,
            "lot_groups": groups,
            "lot_statistics": stats,
            "tolerance_eps": self.tolerance_eps,
            "timestamp": datetime.now().isoformat(),
        }
