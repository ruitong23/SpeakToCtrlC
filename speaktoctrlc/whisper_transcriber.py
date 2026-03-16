from __future__ import annotations

import queue
import threading
import time
from pathlib import Path
from typing import Callable, Optional

import numpy as np
from faster_whisper import WhisperModel

from .models import SegmentResult


class WhisperTranscriber:
    """接收音频分段并异步执行 Whisper 转写。"""

    def __init__(self, model_name: str, language: str | None = None) -> None:
        model_dir = Path.cwd() / "models"
        model_dir.mkdir(exist_ok=True)
        self._model = WhisperModel(model_name, download_root=str(model_dir), local_files_only=False)
        self._language = None if language in {None, "auto"} else language
        self._queue: "queue.Queue[np.ndarray]" = queue.Queue()
        self._thread: Optional[threading.Thread] = None
        self._running = False

    def start(self, on_result: Callable[[SegmentResult], None]) -> None:
        if self._running:
            return
        self._running = True

        def worker() -> None:
            while self._running:
                try:
                    chunk = self._queue.get(timeout=0.2)
                except queue.Empty:
                    continue
                st = time.perf_counter()
                segments, _ = self._model.transcribe(
                    chunk,
                    language=self._language,
                    beam_size=5,
                    vad_filter=False,
                )
                text = " ".join(seg.text.strip() for seg in segments).strip()
                elapsed = time.perf_counter() - st
                on_result(SegmentResult(text=text, elapsed_s=elapsed))

        self._thread = threading.Thread(target=worker, daemon=True)
        self._thread.start()

    def submit(self, audio: np.ndarray) -> None:
        if not self._running:
            return
        self._queue.put(audio.astype(np.float32, copy=False))

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None
        while not self._queue.empty():
            self._queue.get_nowait()
