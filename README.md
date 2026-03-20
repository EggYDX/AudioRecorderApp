# 🎧 AudioRecorderApp

这是一个基于 Python 和 PyQt6 构建的轻量级系统音频录制工具，旨在快速捕捉 Windows 系统内部声音。

<img width="580" height="421" alt="image" src="https://github.com/user-attachments/assets/f6b03f8c-4817-42a1-acb5-9c1328bca9c7" />

## ✨ 核心特性

* **极简交互**：纯白现代 UI 设计，内置动态 VU 音量条，实时反馈拾音状态。
* **稳定内录**：底层采用 `pyaudiowpatch` 直接对接 Windows WASAPI，录制过程平滑稳定。
* **全局快捷键**：支持后台无缝操作（`F9` 开始/暂停，`F10` 停止并保存）。
* **格式转换**：原生支持无损 `.wav` 导出；检测到 FFmpeg 环境时，自动解锁 `.mp3` 与 `.flac` 高级格式。

## 🛠️ 本地运行指南

1. 确保电脑已安装 Python 3.11 或以上版本。
2. 克隆或下载本仓库代码到本地。
3. 在终端中进入项目目录，安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
4. 启动程序：
   ```bash
   python main.py
   ```

## 📝 格式与环境说明

* 软件原生支持录制为无损的 `.wav` 格式。
* 如需导出 `.mp3` 或 `.flac`，系统必须配置好 **FFmpeg**。
  > **小白提示**：你可以前往 [FFmpeg 官网](https://ffmpeg.org/download.html) 下载 Windows 预编译版本，解压后将其 `bin` 文件夹路径添加至系统的“环境变量 -> Path”中。配置完成后重启本软件即可解锁全部格式。

## 📦 发行版下载

如果你不想配置 Python 环境，可以直接前往右侧的 [Releases] 页面，下载开箱即用的 `.exe` 打包版本（首次运行若遇 Windows SmartScreen 拦截，点击“更多信息 -> 仍要运行”即可）。

## 📄 许可证

本项目基于 [MIT License](https://en.wikipedia.org/wiki/MIT_License) 开源，你可以自由地使用、修改和分发。
