from __future__ import annotations

import tkinter as tk
from collections import deque
from typing import Deque, Optional

import numpy as np

from .audio_capture import AudioCapture, AudioConfig
from .device_manager import DeviceManager
from .models import AppState, SegmentResult
from .playback_monitor import PlaybackMonitor
from .text_processor import TextProcessor
from .ui import AppUI
from .whisper_transcriber import WhisperTranscriber


class AppController:
    def __init__(self, root: tk.Tk) -> None:
        self.ui = AppUI(root)
        self.device_manager = DeviceManager()
        self.audio_capture = AudioCapture()
        self.playback = PlaybackMonitor()
        self.text_processor = TextProcessor()

        self.transcriber: Optional[WhisperTranscriber] = None
        self.state = AppState.IDLE

        self.segment_seconds = 2
        self.silence_threshold = 0.015
        self.silence_hold_s = 0.6
        self.trailing_padding_s = 0.2

        self._buffers: Deque[np.ndarray] = deque()
        self._buffer_samples = 0
        self._silence_s = 0.0
        self._samplerate = 16000

        self._bind_events()
        self.refresh_devices()

    def _bind_events(self) -> None:
        self.ui.on_refresh(self.refresh_devices)
        self.ui.on_start(self.start)
        self.ui.on_stop(self.stop)
        self.ui.on_clear(self.clear_text)
        self.ui.on_copy_all(self.copy_all)

    def set_state(self, state: AppState, extra: str = "") -> None:
        self.state = state
        label = state.value if not extra else f"{state.value} ({extra})"
        self.ui.set_state(label)

    def refresh_devices(self) -> None:
        inputs = self.device_manager.list_input_devices()
        outputs = self.device_manager.list_output_devices()
        self.ui.set_devices(inputs, outputs)
        self.ui.append_log(f"已加载输入设备：{len(inputs)} 个")
        self.ui.append_log(f"已加载输出设备：{len(outputs)} 个")

    def start(self) -> None:
        if self.state in {AppState.LISTENING, AppState.TRANSCRIBING, AppState.INITIALIZING}:
            return
        self.set_state(AppState.INITIALIZING)
        try:
            input_dev = self.ui.get_selected_input()
            output_dev = self.ui.get_selected_output()
            self.segment_seconds = int(self.ui.segment_var.get())
            self._samplerate = input_dev.samplerate
            language = self.ui.language_var.get()

            self.text_processor.auto_copy = self.ui.auto_copy_var.get()
            self.text_processor.append_history = self.ui.append_var.get()

            self.transcriber = WhisperTranscriber(model_name="small", language=language)
            self.transcriber.start(self._on_segment_result)
            self.ui.append_log("Whisper 模型已加载：small")

            if self.ui.monitor_var.get():
                self.playback.start(output_dev.device_id, input_dev.samplerate, min(input_dev.channels, output_dev.channels))
                self.ui.append_log("监听回放：开启")
            else:
                self.ui.append_log("监听回放：关闭")

            self.audio_capture.start(
                AudioConfig(
                    input_device_id=input_dev.device_id,
                    samplerate=input_dev.samplerate,
                    channels=input_dev.channels,
                    block_duration_s=0.1,
                ),
                self._on_audio,
            )
            self.ui.append_log("音频输入流已启动")
            self.set_state(AppState.LISTENING)
        except Exception as exc:
            self.set_state(AppState.ERROR, str(exc))
            self.ui.append_log(f"错误：{exc}")
            self.stop()

    def stop(self) -> None:
        self.audio_capture.stop()
        self.playback.stop()
        if self.transcriber is not None:
            self.transcriber.stop()
            self.transcriber = None
        self._buffers.clear()
        self._buffer_samples = 0
        self._silence_s = 0
        self.set_state(AppState.STOPPED)
        self.ui.append_log("已停止并释放资源")

    def _on_audio(self, chunk: np.ndarray) -> None:
        mono = chunk[:, 0] if chunk.ndim > 1 else chunk
        level = float(np.sqrt(np.mean(np.square(mono))))
        self.ui.root.after(0, lambda: self.ui.set_level(level * 6))

        if self.ui.monitor_var.get():
            self.playback.push(chunk)

        self._buffers.append(mono)
        self._buffer_samples += len(mono)

        duration = len(mono) / self._samplerate
        if level < self.silence_threshold:
            self._silence_s += duration
        else:
            self._silence_s = 0

        collected_s = self._buffer_samples / self._samplerate
        should_flush = collected_s >= self.segment_seconds
        if self._silence_s >= self.silence_hold_s and collected_s >= 1.0:
            should_flush = True

        if should_flush:
            self._flush_segment(with_tail=True)

    def _flush_segment(self, with_tail: bool) -> None:
        if self.transcriber is None or self._buffer_samples <= 0:
            return
        audio = np.concatenate(list(self._buffers), axis=0)
        if with_tail:
            tail = int(self.trailing_padding_s * self._samplerate)
            if tail > 0:
                audio = np.concatenate([audio, np.zeros(tail, dtype=np.float32)], axis=0)
        self._buffers.clear()
        self._buffer_samples = 0
        self._silence_s = 0
        self.set_state(AppState.TRANSCRIBING)
        self.ui.root.after(0, lambda: self.ui.append_log(f"已收到 {len(audio) / self._samplerate:.1f} 秒音频"))
        self.transcriber.submit(audio)
        self.set_state(AppState.LISTENING)

    def _on_segment_result(self, result: SegmentResult) -> None:
        processed = self.text_processor.process(result.text)

        def ui_update() -> None:
            self.ui.set_elapsed(result.elapsed_s)
            self.ui.append_log(f"Whisper 识别完成：{result.text}")
            if processed.latest:
                self.ui.update_latest(processed.latest)
                self.ui.update_history(processed.history)
                if processed.should_copy:
                    self.ui.root.clipboard_clear()
                    self.ui.root.clipboard_append(processed.latest)
                    self.ui.set_clipboard_status("已复制")
                    self.ui.append_log("剪贴板已更新")

        self.ui.root.after(0, ui_update)

    def clear_text(self) -> None:
        self.text_processor.clear()
        self.ui.clear_texts()
        self.ui.append_log("文本已清空")

    def copy_all(self) -> None:
        all_text = self.ui.get_history_content()
        if not all_text.strip():
            self.ui.set_clipboard_status("空文本，未复制")
            return
        self.ui.root.clipboard_clear()
        self.ui.root.clipboard_append(all_text)
        self.ui.set_clipboard_status("已复制全部")
        self.ui.append_log("已复制全部文本")
