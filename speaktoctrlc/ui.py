from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Iterable

from .models import DeviceInfo


class AppUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("SpeakToCtrlC - Whisper 实时转写")
        self.root.geometry("1080x760")

        self.input_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.segment_var = tk.StringVar(value="2")
        self.language_var = tk.StringVar(value="auto")
        self.monitor_var = tk.BooleanVar(value=False)
        self.auto_copy_var = tk.BooleanVar(value=True)
        self.append_var = tk.BooleanVar(value=True)

        self.status_var = tk.StringVar(value="状态：未启动")
        self.level_var = tk.IntVar(value=0)
        self.latency_var = tk.StringVar(value="识别耗时：-")
        self.clipboard_var = tk.StringVar(value="剪贴板：-")

        self.latest_var = tk.StringVar(value="")

        self._build()

    def _build(self) -> None:
        top = ttk.LabelFrame(self.root, text="设备区")
        top.pack(fill="x", padx=10, pady=8)

        ttk.Label(top, text="输入设备").grid(row=0, column=0, padx=6, pady=6)
        self.input_combo = ttk.Combobox(top, textvariable=self.input_var, width=46, state="readonly")
        self.input_combo.grid(row=0, column=1, padx=6, pady=6)

        ttk.Label(top, text="监听输出").grid(row=0, column=2, padx=6, pady=6)
        self.output_combo = ttk.Combobox(top, textvariable=self.output_var, width=46, state="readonly")
        self.output_combo.grid(row=0, column=3, padx=6, pady=6)

        self.refresh_button = ttk.Button(top, text="刷新设备")
        self.refresh_button.grid(row=0, column=4, padx=8, pady=6)

        controls = ttk.LabelFrame(self.root, text="控制区")
        controls.pack(fill="x", padx=10, pady=8)

        self.start_button = ttk.Button(controls, text="开始")
        self.start_button.grid(row=0, column=0, padx=6, pady=6)
        self.stop_button = ttk.Button(controls, text="停止")
        self.stop_button.grid(row=0, column=1, padx=6, pady=6)

        ttk.Checkbutton(controls, text="监听回放", variable=self.monitor_var).grid(row=0, column=2, padx=8)
        ttk.Checkbutton(controls, text="自动复制到剪贴板", variable=self.auto_copy_var).grid(row=0, column=3, padx=8)
        ttk.Checkbutton(controls, text="追加到历史文本", variable=self.append_var).grid(row=0, column=4, padx=8)

        ttk.Label(controls, text="分段秒数").grid(row=1, column=0, padx=6)
        self.segment_combo = ttk.Combobox(controls, textvariable=self.segment_var, values=["2", "3", "5"], width=8, state="readonly")
        self.segment_combo.grid(row=1, column=1, padx=6)

        ttk.Label(controls, text="语言").grid(row=1, column=2, padx=6)
        self.language_combo = ttk.Combobox(controls, textvariable=self.language_var, values=["auto", "zh", "en"], width=10, state="readonly")
        self.language_combo.grid(row=1, column=3, padx=6)

        status = ttk.LabelFrame(self.root, text="状态区")
        status.pack(fill="x", padx=10, pady=8)

        ttk.Label(status, textvariable=self.status_var).grid(row=0, column=0, padx=8, pady=6, sticky="w")
        self.level_bar = ttk.Progressbar(status, maximum=100, variable=self.level_var, length=220)
        self.level_bar.grid(row=0, column=1, padx=8)
        ttk.Label(status, textvariable=self.latency_var).grid(row=0, column=2, padx=8)
        ttk.Label(status, textvariable=self.clipboard_var).grid(row=0, column=3, padx=8)

        text_frame = ttk.LabelFrame(self.root, text="文本区")
        text_frame.pack(fill="both", expand=True, padx=10, pady=8)

        ttk.Label(text_frame, text="最新一句").pack(anchor="w", padx=8, pady=(8, 0))
        ttk.Entry(text_frame, textvariable=self.latest_var).pack(fill="x", padx=8, pady=6)

        ttk.Label(text_frame, text="累计文本").pack(anchor="w", padx=8, pady=(8, 0))
        self.history_text = tk.Text(text_frame, height=12, wrap="word")
        self.history_text.pack(fill="both", expand=True, padx=8, pady=6)

        bottom = ttk.Frame(text_frame)
        bottom.pack(fill="x", padx=8, pady=6)
        self.clear_button = ttk.Button(bottom, text="清空文本")
        self.clear_button.pack(side="left", padx=4)
        self.copy_all_button = ttk.Button(bottom, text="复制全部")
        self.copy_all_button.pack(side="left", padx=4)

        logs = ttk.LabelFrame(self.root, text="日志区")
        logs.pack(fill="both", expand=True, padx=10, pady=8)
        self.log_text = tk.Text(logs, height=10, wrap="word")
        self.log_text.pack(fill="both", expand=True, padx=8, pady=8)

    def set_devices(self, inputs: Iterable[DeviceInfo], outputs: Iterable[DeviceInfo]) -> None:
        self._inputs = {self._device_label(d): d for d in inputs}
        self._outputs = {self._device_label(d): d for d in outputs}
        self.input_combo["values"] = list(self._inputs.keys())
        self.output_combo["values"] = list(self._outputs.keys())
        if self._inputs and not self.input_var.get():
            self.input_var.set(next(iter(self._inputs.keys())))
        if self._outputs and not self.output_var.get():
            self.output_var.set(next(iter(self._outputs.keys())))

    def get_selected_input(self) -> DeviceInfo:
        return self._inputs[self.input_var.get()]

    def get_selected_output(self) -> DeviceInfo:
        return self._outputs[self.output_var.get()]

    def on_refresh(self, fn: Callable[[], None]) -> None:
        self.refresh_button.configure(command=fn)

    def on_start(self, fn: Callable[[], None]) -> None:
        self.start_button.configure(command=fn)

    def on_stop(self, fn: Callable[[], None]) -> None:
        self.stop_button.configure(command=fn)

    def on_clear(self, fn: Callable[[], None]) -> None:
        self.clear_button.configure(command=fn)

    def on_copy_all(self, fn: Callable[[], None]) -> None:
        self.copy_all_button.configure(command=fn)

    def set_state(self, text: str) -> None:
        self.status_var.set(f"状态：{text}")

    def set_level(self, level_0_to_1: float) -> None:
        self.level_var.set(int(max(0.0, min(1.0, level_0_to_1)) * 100))

    def set_elapsed(self, elapsed_s: float) -> None:
        self.latency_var.set(f"识别耗时：{elapsed_s:.2f}s")

    def set_clipboard_status(self, text: str) -> None:
        self.clipboard_var.set(f"剪贴板：{text}")

    def update_latest(self, text: str) -> None:
        self.latest_var.set(text)

    def update_history(self, text: str) -> None:
        self.history_text.delete("1.0", tk.END)
        self.history_text.insert(tk.END, text)

    def clear_texts(self) -> None:
        self.latest_var.set("")
        self.history_text.delete("1.0", tk.END)

    def append_log(self, line: str) -> None:
        self.log_text.insert(tk.END, f"{line}\n")
        self.log_text.see(tk.END)

    def get_history_content(self) -> str:
        return self.history_text.get("1.0", tk.END).strip()

    @staticmethod
    def _device_label(d: DeviceInfo) -> str:
        return f"{d.name} | {d.samplerate}Hz | {d.channels}ch | id={d.device_id}"
