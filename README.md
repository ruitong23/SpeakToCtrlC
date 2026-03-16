# SpeakToCtrlC

一个基于 Whisper 的麦克风实时转写小程序（桌面 GUI 版）。
目标：把 `Mic In` 进入电脑的声音自动转成文本，用户在任意窗口只需 `Ctrl + V` 即可粘贴最新一句（已做去重和防抖）。

## 功能覆盖（按你给的架构）

- **UI 模块（Tkinter）**
  - 输入设备下拉框
  - 输出设备下拉框
  - 刷新设备按钮
  - 开始按钮
  - 停止按钮
  - 监听回放开关
  - 自动复制到剪贴板开关
  - 追加到历史文本开关
  - 输入电平条
  - 状态栏
  - 最新一句文本框
  - 累积文本框
  - 日志框
  - 清空文本按钮
  - 复制全部按钮
- **设备管理模块**：独立枚举输入/输出设备并返回 id、名称、采样率、通道。
- **音频采集模块**：持续采集 Mic In 音频。
- **监听回放模块**：可选将采集音频实时推到输出设备（默认关闭，避免啸叫）。
- **Whisper 转写模块**：自动下载模型到 `./models`，分段识别（非字级流式）。
- **文本处理与剪贴板模块**：空白过滤、去重、防抖复制、最新一句/历史文本更新。
- **控制器模块**：统一流程编排、状态机、资源释放。

## 运行

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m speaktoctrlc.main
```

## 状态机

- 未启动
- 正在初始化
- 正在监听
- 正在识别
- 已停止
- 错误

## 分段策略（避免截断）

- 固定分段：默认每 2 秒切段（可改 3/5 秒）
- 静音切段：RMS 音量低于阈值并持续一段时间触发切段
- 切段尾部自动补一小段静音 padding，减少句尾被截断

## 结构

```text
speaktoctrlc/
  main.py
  controller.py
  ui.py
  device_manager.py
  audio_capture.py
  playback_monitor.py
  whisper_transcriber.py
  text_processor.py
  models.py
```

## 说明

- 首次运行会下载 Whisper 模型到当前目录的 `models/`。
- 若你要进一步提高中文识别准确率，可以把 `small` 换成 `medium` 或 `large-v3`（速度会变慢）。
