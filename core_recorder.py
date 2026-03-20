import pyaudiowpatch as pyaudio
import wave
import threading
import time
import os
import tempfile
import numpy as np
from utils import logger

class AudioRecorderEngine:
    def __init__(self):
        self.is_recording = False
        self.is_paused = False
        self.temp_filename = os.path.join(tempfile.gettempdir(), "temp_recording.wav")
        self.start_time = 0
        self.elapsed_time = 0
        self.current_volume = 0
        self._thread = None
        
        # 初始化独立于 Qt 的 PortAudio 引擎
        self.pyaudio_instance = pyaudio.PyAudio()

    def start(self, error_callback):
        self.is_recording = True
        self.is_paused = False
        self.start_time = time.time()
        self.elapsed_time = 0
        self.current_volume = 0
        
        logger.info("启动专业录音引擎 (pyaudiowpatch)...")
        self._thread = threading.Thread(target=self._record_thread, args=(error_callback,), daemon=True)
        self._thread.start()

    def _record_thread(self, error_callback):
        stream = None
        wf = None
        try:
            # 自动寻找系统默认的回环(内录)设备
            try:
                wasapi_info = self.pyaudio_instance.get_host_api_info_by_type(pyaudio.paWASAPI)
            except OSError:
                raise Exception("系统不支持 WASAPI 接口。")
                
            default_speakers = self.pyaudio_instance.get_default_wasapi_loopback()
            if not default_speakers:
                raise Exception("无法找到可用的系统混音器。")

            channels = default_speakers["maxInputChannels"]
            samplerate = int(default_speakers["defaultSampleRate"])
            
            logger.info(f"成功绑定设备: {default_speakers['name']} | 采样率: {samplerate}")

            stream = self.pyaudio_instance.open(
                format=pyaudio.paInt16,
                channels=channels,
                rate=samplerate,
                input=True,
                frames_per_buffer=1024,
                input_device_index=default_speakers["index"]
            )
            
            wf = wave.open(self.temp_filename, 'wb')
            wf.setnchannels(channels)
            wf.setsampwidth(self.pyaudio_instance.get_sample_size(pyaudio.paInt16))
            wf.setframerate(samplerate)

            while self.is_recording:
                try:
                    # exception_on_overflow=False 极为重要：防止系统卡顿时抛出异常导致中断
                    data = stream.read(1024, exception_on_overflow=False)
                    if not self.is_paused:
                        wf.writeframes(data)
                        
                        # 转换 16 位音频数据计算实时音量峰值 (最大 32768)
                        audio_data = np.frombuffer(data, dtype=np.int16)
                        peak = np.max(np.abs(audio_data))
                        self.current_volume = min(100, int((peak / 32768.0) * 100 * 1.5))
                    else:
                        self.start_time += (1024 / samplerate)
                        self.current_volume = 0
                except Exception as inner_e:
                    logger.warning(f"音频流轻微受阻，已静默处理: {inner_e}")
                    continue

        except Exception as e:
            logger.error(f"引擎崩溃: {e}")
            self.is_recording = False
            self.current_volume = 0
            error_callback(f"无法启动录音硬件层:\n{str(e)}")
        finally:
            if stream:
                stream.stop_stream()
                stream.close()
            if wf:
                wf.close()

    def pause_resume(self):
        self.is_paused = not self.is_paused
        self.current_volume = 0 if self.is_paused else self.current_volume
        return self.is_paused

    def stop(self):
        self.is_recording = False
        self.current_volume = 0
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2) # 设置安全超时防止假死

    def get_time_string(self):
        if self.is_recording and not self.is_paused:
            self.elapsed_time = int(time.time() - self.start_time)
        hrs = self.elapsed_time // 3600
        mins = (self.elapsed_time % 3600) // 60
        secs = self.elapsed_time % 60
        return f"{hrs:02}:{mins:02}:{secs:02}"