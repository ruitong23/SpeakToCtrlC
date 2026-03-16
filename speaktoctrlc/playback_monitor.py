from __future__ import annotations

import queue
from typing import Optional

import numpy as np
import sounddevice as sd


class PlaybackMonitor:
    """将输入音频回放到输出设备用于监听。"""

    def __init__(self) -> None:
        self._stream: Optional[sd.OutputStream] = None
        self._queue: "queue.Queue[np.ndarray]" = queue.Queue(maxsize=60)

    def start(self, device_id: int, samplerate: int, channels: int) -> None:
        self.stop()

        def callback(outdata, frames, time_info, status):
            del time_info
            if status:
                pass
            try:
                chunk = self._queue.get_nowait()
            except queue.Empty:
                outdata.fill(0)
                return
            if chunk.shape[0] < frames:
                padded = np.zeros((frames, channels), dtype=np.float32)
                padded[: chunk.shape[0], : chunk.shape[1]] = chunk
                outdata[:] = padded
            else:
                outdata[:] = chunk[:frames, :channels]

        self._stream = sd.OutputStream(
            samplerate=samplerate,
            device=device_id,
            channels=channels,
            dtype="float32",
            callback=callback,
            blocksize=0,
        )
        self._stream.start()

    def push(self, chunk: np.ndarray) -> None:
        if self._stream is None:
            return
        try:
            self._queue.put_nowait(chunk.copy())
        except queue.Full:
            _ = self._queue.get_nowait()
            self._queue.put_nowait(chunk.copy())

    def stop(self) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        while not self._queue.empty():
            self._queue.get_nowait()
