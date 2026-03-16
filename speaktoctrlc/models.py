from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AppState(str, Enum):
    IDLE = "未启动"
    INITIALIZING = "正在初始化"
    LISTENING = "正在监听"
    TRANSCRIBING = "正在识别"
    STOPPED = "已停止"
    ERROR = "错误"


@dataclass(slots=True)
class DeviceInfo:
    device_id: int
    name: str
    samplerate: int
    channels: int


@dataclass(slots=True)
class SegmentResult:
    text: str
    elapsed_s: float
