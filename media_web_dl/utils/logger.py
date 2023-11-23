import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from colorlog import ColoredFormatter

from media_web_dl.utils.paths import logs_path

LOGFORMAT = "%(asctime)s - %(levelname)s - %(message)s"
DATEFORMAT = "%H:%M:%S"


class Logger:
    logger: logging.Logger
    log_file_path: Path

    def __init__(self, name: str = "default"):
        self.log_file_path = logs_path / f"{name}.log"
        self._int_logger(name)

    def _int_logger(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # 设置颜色
        stream_handler = logging.StreamHandler()
        colored_formatter = ColoredFormatter(
            "%(log_color)s" + LOGFORMAT, datefmt=DATEFORMAT
        )
        stream_handler.setFormatter(colored_formatter)
        self.logger.addHandler(stream_handler)

        # 设置文件处理器
        file_handler = RotatingFileHandler(
            self.log_file_path, maxBytes=5 * 1024 * 1024, backupCount=5
        )
        file_handler.setFormatter(
            logging.Formatter(LOGFORMAT, datefmt=DATEFORMAT)
        )
        self.logger.addHandler(file_handler)

    def debug(self, msg: str):
        self.logger.debug(msg)

    def info(self, msg: str):
        self.logger.info(msg)

    def error(self, msg: str):
        self.logger.error(msg)

    def critical(self, msg: str):
        self.logger.critical(msg)


log = Logger()
