# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
import os
import threading
import time
from typing import Callable, List, Optional

from core.spectrophotometer.cxf3_parser import CxF3Parser, CxF3Measurement
from core.spectrophotometer.parser import SpectrophotometerParser
from core.models.color_data import LabColor, SpectralReading, MeasurementSource

logger = logging.getLogger(__name__)


class XriteFileHandler:
    SUPPORTED = (".cxf", ".csv", ".txt", ".xml")

    def __init__(self, callback: Callable[[str, List[CxF3Measurement]], None]):
        self.callback = callback
        self._parser = CxF3Parser()
        self._legacy_parser = SpectrophotometerParser()

    def process_file(self, filepath: str):
        ext = os.path.splitext(filepath)[1].lower()
        if ext not in self.SUPPORTED:
            return

        try:
            time.sleep(0.5)

            if ext == ".cxf":
                measurements = CxF3Parser.parse_file(filepath)
            else:
                readings = self._legacy_parser.parse_file(filepath)
                measurements = []
                for r in readings:
                    measurements.append(CxF3Measurement(
                        sample_name=r.sample_id,
                        illuminant="D65",
                        observer_angle="2",
                        wavelengths=[],
                        reflectances=[],
                        lab=r.lab,
                    ))

            if measurements:
                self.callback(filepath, measurements)
                logger.info("File processed: %s (%d measurements)", filepath, len(measurements))

        except Exception as e:
            logger.error("File processing error (%s): %s", filepath, e)


class FileWatcher:
    def __init__(
        self,
        watch_dir: str,
        callback: Callable[[str, List[CxF3Measurement]], None],
        recursive: bool = False,
    ):
        self.watch_dir = watch_dir
        self.callback = callback
        self.recursive = recursive
        self._handler = XriteFileHandler(callback)
        self._observer = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._processed_files = set()

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> bool:
        if self._running:
            logger.warning("Watcher already running")
            return False

        if not os.path.isdir(self.watch_dir):
            try:
                os.makedirs(self.watch_dir, exist_ok=True)
                logger.info("Watcher directory created: %s", self.watch_dir)
            except OSError as e:
                logger.error("Watcher directory could not be created: %s", e)
                return False

        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler

            class Handler(FileSystemEventHandler):
                def __init__(self, watcher_ref):
                    self.watcher = watcher_ref

                def on_created(self, event):
                    if event.is_directory:
                        return
                    self.watcher._on_file_event(event.src_path)

                def on_modified(self, event):
                    if event.is_directory:
                        return
                    self.watcher._on_file_event(event.src_path)

            self._observer = Observer()
            event_handler = Handler(self)
            self._observer.schedule(event_handler, self.watch_dir, recursive=self.recursive)
            self._observer.start()
            self._running = True
            logger.info("Watcher started: %s", self.watch_dir)
            return True

        except ImportError:
            logger.warning("watchdog not found, switching to polling mode")
            self._start_polling()
            return True
        except Exception as e:
            logger.error("Watcher start error: %s", e)
            self._start_polling()
            return True

    def _start_polling(self):
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        logger.info("Polling mode started: %s", self.watch_dir)

    def _poll_loop(self):
        known = set()
        while self._running:
            try:
                current = set()
                for f in os.listdir(self.watch_dir):
                    ext = os.path.splitext(f)[1].lower()
                    if ext in XriteFileHandler.SUPPORTED:
                        full = os.path.join(self.watch_dir, f)
                        current.add(full)

                new_files = current - known - self._processed_files
                for fp in new_files:
                    self._on_file_event(fp)

                known = current
            except Exception as e:
                logger.error("Polling error: %s", e)

            time.sleep(2.0)

    def _on_file_event(self, filepath: str):
        if filepath in self._processed_files:
            return

        ext = os.path.splitext(filepath)[1].lower()
        if ext not in XriteFileHandler.SUPPORTED:
            return

        if os.path.isfile(filepath):
            self._processed_files.add(filepath)
            threading.Thread(
                target=self._handler.process_file,
                args=(filepath,),
                daemon=True,
            ).start()

    def stop(self):
        self._running = False
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=5)
            self._observer = None
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        logger.info("Watcher stopped")

    def get_recent_files(self, count: int = 10) -> List[str]:
        files = []
        try:
            for f in sorted(os.listdir(self.watch_dir), reverse=True):
                ext = os.path.splitext(f)[1].lower()
                if ext in XriteFileHandler.SUPPORTED:
                    files.append(os.path.join(self.watch_dir, f))
                    if len(files) >= count:
                        break
        except OSError:
            pass
        return files

    def clear_processed(self):
        self._processed_files.clear()
