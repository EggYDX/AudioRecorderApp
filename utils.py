import os
import shutil
import logging
from logging.handlers import RotatingFileHandler
from pydub import AudioSegment

def setup_logger():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(base_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, "app_record.log")
    logger = logging.getLogger("AudioRecorder")
    logger.setLevel(logging.DEBUG)
    
    # 日志防爆满：50MB 截断，保留 1 个备份
    handler = RotatingFileHandler(log_file, maxBytes=50*1024*1024, backupCount=1, encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
    handler.setFormatter(formatter)
    
    if not logger.handlers:
        logger.addHandler(handler)
    return logger

logger = setup_logger()

def check_ffmpeg():
    has_ffmpeg = shutil.which("ffmpeg") is not None
    if not has_ffmpeg:
        logger.warning("未检测到 FFmpeg 环境变量。")
    return has_ffmpeg

def convert_audio(input_wav, output_file, format, bitrate):
    try:
        logger.info(f"开始转换: {input_wav} -> {output_file}")
        sound = AudioSegment.from_wav(input_wav)
        if format == "mp3":
            sound.export(output_file, format="mp3", bitrate=bitrate)
        elif format == "flac":
            sound.export(output_file, format="flac")
        logger.info("转换成功。")
    except Exception as e:
        logger.error(f"转换失败: {e}")
        raise e