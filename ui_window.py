import os
import shutil
import keyboard
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QComboBox, QCheckBox, QMessageBox, QFileDialog, QProgressBar)
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from core_recorder import AudioRecorderEngine
from utils import check_ffmpeg, convert_audio, logger

class ModernRecorderUI(QMainWindow):
    hotkey_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.engine = AudioRecorderEngine()
        self.has_ffmpeg = check_ffmpeg()
        
        self.init_ui()
        self.check_environment()
        self.setup_hotkeys()
        
        logger.info("UI 初始化完成。")

    def init_ui(self):
        self.setWindowTitle("系统音频捕捉引擎")
        self.setFixedSize(450, 300)
        
        # 修正的事实：必须加上 CustomizeWindowHint，底层才会真正禁用最大化按钮
        self.setWindowFlags(
            Qt.WindowType.CustomizeWindowHint | 
            Qt.WindowType.WindowTitleHint | 
            Qt.WindowType.WindowMinimizeButtonHint | 
            Qt.WindowType.WindowCloseButtonHint
        )
        
        self.setStyleSheet("""
            QMainWindow { background-color: #f7f7f7; color: #333333; }
            QLabel { color: #333333; font-family: 'Segoe UI', Arial; font-weight: 500;}
            QPushButton { 
                background-color: #ffffff; color: #333333; 
                border: 1px solid #dcdcdc; padding: 10px; border-radius: 6px; 
                font-family: 'Segoe UI'; font-weight: bold;
            }
            QPushButton:hover { background-color: #f0f0f0; }
            QPushButton:disabled { background-color: #e0e0e0; color: #a0a0a0; border: none; }
            QPushButton#btn_start { background-color: #2CC985; color: white; border: none; }
            QPushButton#btn_start:hover { background-color: #25a86f; }
            QPushButton#btn_stop { background-color: #E84C3D; color: white; border: none; }
            QPushButton#btn_stop:hover { background-color: #c0392b; }
            QPushButton#btn_pause { background-color: #F1C40F; color: white; border: none; }
            QPushButton#btn_pause:hover { background-color: #f39c12; }
            QComboBox { 
                background-color: #ffffff; color: #333333; 
                border: 1px solid #dcdcdc; padding: 4px; border-radius: 4px;
            }
            QProgressBar {
                border: 1px solid #dcdcdc; border-radius: 3px; background-color: #e8e8e8; text-align: center; color: transparent; 
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2CC985, stop:0.7 #F1C40F, stop:1 #E84C3D);
                width: 4px; margin: 1px;
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        top_layout = QHBoxLayout()
        self.format_combo = QComboBox()
        self.format_combo.addItems(["wav", "mp3", "flac"])
        top_layout.addWidget(QLabel("格式:"))
        top_layout.addWidget(self.format_combo)

        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems(["320k", "192k", "128k"])
        top_layout.addWidget(QLabel("比特率:"))
        top_layout.addWidget(self.bitrate_combo)

        self.topmost_check = QCheckBox("窗口置顶")
        self.topmost_check.stateChanged.connect(self.toggle_topmost)
        self.topmost_check.setStyleSheet("color: #333333;")
        top_layout.addWidget(self.topmost_check)
        top_layout.addStretch()
        layout.addLayout(top_layout)

        self.timer_label = QLabel("00:00:00")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setStyleSheet("font-size: 52px; font-family: 'Consolas'; font-weight: bold; margin: 10px 0;")
        layout.addWidget(self.timer_label)

        self.vu_meter = QProgressBar()
        self.vu_meter.setRange(0, 100)
        self.vu_meter.setValue(0)
        self.vu_meter.setFixedHeight(12)
        layout.addWidget(self.vu_meter)
        
        layout.addSpacing(15)

        control_layout = QHBoxLayout()
        control_layout.addStretch() 
        
        self.btn_start = QPushButton("开始录制 (F9)")
        self.btn_start.setObjectName("btn_start")
        self.btn_start.setMinimumWidth(120)
        self.btn_start.clicked.connect(self.start_recording)
        
        self.btn_pause = QPushButton("暂停 (F9)")
        self.btn_pause.setObjectName("btn_pause")
        self.btn_pause.setMinimumWidth(100)
        self.btn_pause.clicked.connect(self.pause_recording)
        self.btn_pause.hide()
        
        self.btn_stop = QPushButton("停止并保存 (F10)")
        self.btn_stop.setObjectName("btn_stop")
        self.btn_stop.setMinimumWidth(120)
        self.btn_stop.clicked.connect(self.stop_recording)
        self.btn_stop.hide() 

        control_layout.addWidget(self.btn_start)
        control_layout.addWidget(self.btn_pause)
        control_layout.addWidget(self.btn_stop)
        control_layout.addStretch() 
        
        layout.addLayout(control_layout)

        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self.update_ui_state)

    def setup_hotkeys(self):
        self.hotkey_signal.connect(self.handle_hotkey)
        try:
            keyboard.add_hotkey('F9', lambda: self.hotkey_signal.emit('F9'))
            keyboard.add_hotkey('F10', lambda: self.hotkey_signal.emit('F10'))
            logger.info("全局快捷键已注册 (F9, F10)。")
        except Exception as e:
            logger.error(f"快捷键注册失败 (可能是权限不足): {e}")

    def handle_hotkey(self, key):
        if key == 'F9':
            if not self.engine.is_recording:
                self.start_recording()
            else:
                self.pause_recording()
        elif key == 'F10':
            if self.engine.is_recording:
                self.stop_recording()

    def check_environment(self):
        if not self.has_ffmpeg:
            logger.warning("触发防呆设计：已禁用 MP3/FLAC 选择。")
            QMessageBox.warning(
                self, 
                "环境提示", 
                "未检测到 FFmpeg 环境变量。\n\n"
                "为了防呆保护，有关需要调用的功能已全部禁用，只允许保存为无损 WAV。\n"
                "请下载 FFmpeg 并在系统环境中配置，然后重启本软件。"
            )
            self.format_combo.setCurrentText("wav")
            self.format_combo.setEnabled(False)
            self.bitrate_combo.setEnabled(False)

    def toggle_topmost(self, state):
        if state == 2:
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        else:
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, False)
        self.show()

    def update_button_visibility(self, is_recording):
        if is_recording:
            self.btn_start.hide()
            self.btn_pause.show()
            self.btn_stop.show()
        else:
            self.btn_pause.hide()
            self.btn_stop.hide()
            self.btn_start.show()

    def start_recording(self):
        self.engine.start(self.on_recording_error)
        self.ui_timer.start(50) 
        
        self.update_button_visibility(True)
        self.format_combo.setEnabled(False)
        self.btn_pause.setText("暂停 (F9)")

    def pause_recording(self):
        is_paused = self.engine.pause_resume()
        self.btn_pause.setText("继续 (F9)" if is_paused else "暂停 (F9)")
        if is_paused:
            self.vu_meter.setValue(0)

    def stop_recording(self):
        self.engine.stop()
        self.ui_timer.stop()
        self.vu_meter.setValue(0)
        
        self.btn_pause.setEnabled(False)
        self.btn_stop.setEnabled(False)
        self.btn_stop.setText("处理中...")
        
        self.save_file()

    def save_file(self):
        fmt = self.format_combo.currentText()
        filters = f"Audio File (*.{fmt})"
        
        file_path, _ = QFileDialog.getSaveFileName(self, "保存录音", "", filters)
        
        if file_path:
            try:
                if fmt == "wav":
                    shutil.copy(self.engine.temp_filename, file_path)
                else:
                    convert_audio(self.engine.temp_filename, file_path, fmt, self.bitrate_combo.currentText())
                logger.info(f"录音已成功保存至: {file_path}")
                QMessageBox.information(self, "成功", f"文件已保存:\n{file_path}")
            except Exception as e:
                logger.error(f"UI层保存失败: {e}")
                QMessageBox.critical(self, "错误", f"保存或转换失败:\n{str(e)}")
        else:
            logger.info("用户取消了保存文件。")
        
        if os.path.exists(self.engine.temp_filename):
            try: os.remove(self.engine.temp_filename)
            except: pass
            
        self.reset_ui()

    def reset_ui(self):
        self.update_button_visibility(False)
        self.timer_label.setText("00:00:00")
        self.vu_meter.setValue(0)
        self.btn_pause.setEnabled(True)
        self.btn_stop.setEnabled(True)
        self.btn_stop.setText("停止并保存 (F10)")
        if self.has_ffmpeg:
            self.format_combo.setEnabled(True)

    def update_ui_state(self):
        self.timer_label.setText(self.engine.get_time_string())
        
        current_val = self.vu_meter.value()
        target_val = self.engine.current_volume
        if target_val > current_val:
            self.vu_meter.setValue(target_val) 
        else:
            self.vu_meter.setValue(max(0, current_val - 5))

    def on_recording_error(self, error_msg):
        logger.error(f"收到引擎抛出的错误信号: {error_msg}")
        QTimer.singleShot(0, lambda: self._handle_error_ui(error_msg))

    def _handle_error_ui(self, error_msg):
        QMessageBox.critical(self, "录制发生意外", error_msg)
        if os.path.exists(self.engine.temp_filename) and os.path.getsize(self.engine.temp_filename) > 0:
            logger.info("异常退出，尝试挽救已录制的数据...")
            self.save_file()
        else:
            self.reset_ui()

    def closeEvent(self, event):
        logger.info("正在关闭软件，清理资源...")
        keyboard.unhook_all()
        if self.engine.is_recording:
            self.engine.stop()
        event.accept()