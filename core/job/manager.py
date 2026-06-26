# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.models.color_data import LabColor, SpectralReading, MeasurementSource

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "jobs.json")


@dataclass
class DynamicField:
    key: str
    label: str
    value: str
    field_type: str = "text"

    def to_dict(self) -> dict:
        return {"key": self.key, "label": self.label, "value": self.value, "type": self.field_type}


@dataclass
class Sample:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8].upper())
    name: str = ""
    batch_id: str = ""
    readings: List[Dict] = field(default_factory=list)
    lab: Optional[LabColor] = None
    delta_e: float = 0.0
    lot_decision: str = ""
    status: str = "Beklemede"
    dynamic_fields: List[DynamicField] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "batch_id": self.batch_id,
            "readings": self.readings,
            "lab": {"L": self.lab.L, "a": self.lab.a, "b": self.lab.b} if self.lab else None,
            "delta_e": self.delta_e,
            "lot_decision": self.lot_decision,
            "status": self.status,
            "dynamic_fields": [f.to_dict() for f in self.dynamic_fields],
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Sample:
        lab = None
        if d.get("lab"):
            lab = LabColor(L=d["lab"]["L"], a=d["lab"]["a"], b=d["lab"]["b"])
        return cls(
            id=d["id"],
            name=d["name"],
            batch_id=d.get("batch_id", ""),
            readings=d.get("readings", []),
            lab=lab,
            delta_e=d.get("delta_e", 0.0),
            lot_decision=d.get("lot_decision", ""),
            status=d.get("status", "Beklemede"),
            dynamic_fields=[DynamicField(**f) for f in d.get("dynamic_fields", [])],
            created_at=d.get("created_at", datetime.now().isoformat()),
        )


@dataclass
class Master:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8].upper())
    name: str = ""
    lab: Optional[LabColor] = None
    tolerans_de: float = 1.0
    illuminants: List[str] = field(default_factory=lambda: ["D65"])
    fabric_type: str = ""
    pantone: str = ""
    dynamic_fields: List[DynamicField] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "lab": {"L": self.lab.L, "a": self.lab.a, "b": self.lab.b} if self.lab else None,
            "tolerans_de": self.tolerans_de,
            "illuminants": self.illuminants,
            "fabric_type": self.fabric_type,
            "pantone": self.pantone,
            "dynamic_fields": [f.to_dict() for f in self.dynamic_fields],
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Master:
        lab = None
        if d.get("lab"):
            lab = LabColor(L=d["lab"]["L"], a=d["lab"]["a"], b=d["lab"]["b"])
        return cls(
            id=d["id"],
            name=d["name"],
            lab=lab,
            tolerans_de=d.get("tolerans_de", 1.0),
            illuminants=d.get("illuminants", ["D65"]),
            fabric_type=d.get("fabric_type", ""),
            pantone=d.get("pantone", ""),
            dynamic_fields=[DynamicField(**f) for f in d.get("dynamic_fields", [])],
            created_at=d.get("created_at", datetime.now().isoformat()),
        )


@dataclass
class Job:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8].upper())
    name: str = ""
    customer: str = ""
    season: str = ""
    description: str = ""
    masters: List[Master] = field(default_factory=list)
    samples: List[Sample] = field(default_factory=list)
    dynamic_fields: List[DynamicField] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "customer": self.customer,
            "season": self.season,
            "description": self.description,
            "masters": [m.to_dict() for m in self.masters],
            "samples": [s.to_dict() for s in self.samples],
            "dynamic_fields": [f.to_dict() for f in self.dynamic_fields],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Job:
        return cls(
            id=d["id"],
            name=d["name"],
            customer=d.get("customer", ""),
            season=d.get("season", ""),
            description=d.get("description", ""),
            masters=[Master.from_dict(m) for m in d.get("masters", [])],
            samples=[Sample.from_dict(s) for s in d.get("samples", [])],
            dynamic_fields=[DynamicField(**f) for f in d.get("dynamic_fields", [])],
            created_at=d.get("created_at", datetime.now().isoformat()),
            updated_at=d.get("updated_at", datetime.now().isoformat()),
        )

    @property
    def total_samples(self) -> int:
        return len(self.samples)

    @property
    def passed_samples(self) -> int:
        return sum(1 for s in self.samples if s.status == "Gecti")

    @property
    def failed_samples(self) -> int:
        return sum(1 for s in self.samples if s.status == "Reddedildi")

    @property
    def pass_rate(self) -> float:
        if self.total_samples == 0:
            return 0.0
        return (self.passed_samples / self.total_samples) * 100


class JobManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.jobs: List[Job] = []
        self._load()

    def _load(self):
        if os.path.isfile(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.jobs = [Job.from_dict(j) for j in data.get("jobs", [])]
                logger.info("%d job yuklendi", len(self.jobs))
            except Exception as e:
                logger.error("Veritabani yukleme hatasi: %s", e)
                self.jobs = []
        else:
            self.jobs = []

    def _save(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        data = {"jobs": [j.to_dict() for j in self.jobs], "updated_at": datetime.now().isoformat()}
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def create_job(self, name: str, customer: str = "", season: str = "", description: str = "") -> Job:
        job = Job(name=name, customer=customer, season=season, description=description)
        self.jobs.append(job)
        self._save()
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        for j in self.jobs:
            if j.id == job_id:
                return j
        return None

    def delete_job(self, job_id: str) -> bool:
        for i, j in enumerate(self.jobs):
            if j.id == job_id:
                self.jobs.pop(i)
                self._save()
                return True
        return False

    def add_master(self, job_id: str, master: Master) -> bool:
        job = self.get_job(job_id)
        if job:
            job.masters.append(master)
            job.updated_at = datetime.now().isoformat()
            self._save()
            return True
        return False

    def add_sample(self, job_id: str, sample: Sample) -> bool:
        job = self.get_job(job_id)
        if job:
            job.samples.append(sample)
            job.updated_at = datetime.now().isoformat()
            self._save()
            return True
        return False

    def add_dynamic_field_def(self, job_id: str, key: str, label: str, field_type: str = "text"):
        job = self.get_job(job_id)
        if job:
            existing = [f.key for f in job.dynamic_fields]
            if key not in existing:
                job.dynamic_fields.append(DynamicField(key=key, label=label, value="", field_type=field_type))
                self._save()

    def set_sample_field(self, job_id: str, sample_id: str, key: str, value: str):
        job = self.get_job(job_id)
        if not job:
            return
        for s in job.samples:
            if s.id == sample_id:
                for f in s.dynamic_fields:
                    if f.key == key:
                        f.value = value
                        self._save()
                        return
                s.dynamic_fields.append(DynamicField(key=key, label=key, value=value))
                self._save()
                return

    def filter_samples(self, job_id: str, filters: Dict[str, str]) -> List[Sample]:
        job = self.get_job(job_id)
        if not job:
            return []
        result = job.samples
        for key, value in filters.items():
            result = [
                s for s in result
                if any(f.key == key and f.value == value for f in s.dynamic_fields)
            ]
        return result

    def get_all_jobs(self) -> List[Job]:
        return self.jobs
