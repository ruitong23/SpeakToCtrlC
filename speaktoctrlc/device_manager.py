from __future__ import annotations

from typing import List

import sounddevice as sd

from .models import DeviceInfo


class DeviceManager:
    """设备枚举与设备信息查询。"""

    def list_input_devices(self) -> List[DeviceInfo]:
        devices = sd.query_devices()
        results: List[DeviceInfo] = []
        for idx, raw in enumerate(devices):
            channels = int(raw.get("max_input_channels", 0))
            if channels <= 0:
                continue
            results.append(
                DeviceInfo(
                    device_id=idx,
                    name=str(raw.get("name", f"Input-{idx}")),
                    samplerate=int(raw.get("default_samplerate", 16000)),
                    channels=channels,
                )
            )
        return results

    def list_output_devices(self) -> List[DeviceInfo]:
        devices = sd.query_devices()
        results: List[DeviceInfo] = []
        for idx, raw in enumerate(devices):
            channels = int(raw.get("max_output_channels", 0))
            if channels <= 0:
                continue
            results.append(
                DeviceInfo(
                    device_id=idx,
                    name=str(raw.get("name", f"Output-{idx}")),
                    samplerate=int(raw.get("default_samplerate", 16000)),
                    channels=channels,
                )
            )
        return results
