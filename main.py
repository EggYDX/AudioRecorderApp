import sys
from PyQt6.QtWidgets import QApplication
from ui_window import ModernRecorderUI
from utils import logger

if __name__ == "__main__":
    try:
        logger.info("=== 音频引擎初始化 ===")
        app = QApplication(sys.argv)
        window = ModernRecorderUI()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        logger.critical(f"发生致命系统崩溃: {e}", exc_info=True)