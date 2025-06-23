import logging
import sys
from PyQt6.QtWidgets import QApplication
from whatsapp_warmer.utils.logger import setup_logger, get_logger
from whatsapp_warmer.gui.window import MainWindow

logger = get_logger(__name__)

def main():
    """Точка входа в приложение"""
    try:
        # 1. Настройка логгера
        setup_logger(
            log_file='logs/app.log',
            level=logging.DEBUG if '--debug' in sys.argv else logging.INFO
        )
        logger.info("Starting WhatsApp Account Warmer PRO")

        # 2. Создание приложения
        app = QApplication(sys.argv)
        app.setApplicationName("WhatsApp Warmer PRO")
        app.setApplicationVersion("1.0.0")

        # 3. Создание и отображение главного окна
        window = MainWindow()
        window.show()

        # 4. Запуск основного цикла
        ret = app.exec()
        logger.info("Application shutdown")
        return ret

    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())