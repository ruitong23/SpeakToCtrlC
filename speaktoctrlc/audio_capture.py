from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

import numpy as np
import sounddevice as sd


@dataclass(slots=True)
class AudioConfig:
    input_device_id: int
    samplerate: int
    channels: int
    block_duration_s: float = 0.1


class AudioCapture:
    """持续采集音频并回调上层。"""

    def __init__(self) -> None:
        self._stream: Optional[sd.InputStream] = None

    def start(self, config: AudioConfig, on_audio: Callable[[np.ndarray], None]) -> None:
        self.stop()
        blocksize = int(config.samplerate * config.block_duration_s)

        def callback(indata, frames, time_info, status):
            del frames, time_info
            if status:
                pass
            on_audio(indata.copy())

        self._stream = sd.InputStream(
            samplerate=config.samplerate,
            device=config.input_device_id,
            channels=config.channels,
            dtype="float32",
            callback=callback,
            blocksize=blocksize,
        )
        self._stream.start()

    def stop(self) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
