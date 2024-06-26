import os
import sys

from loguru import logger


class InterceptHandler:
    """拦截器"""

    message = ""
    """消息"""

    def __init__(self, record: dict):
        self.write(record)

    def write(self, record: dict):
        """写入"""
        InterceptHandler.message += f"{record.get('message')}\n"


log_PATH = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), "logs")
path_log = os.path.join(log_PATH, '日志文件.log')
log = logger
log.remove()


log.add(sys.stdout, level="INFO", colorize=True,
        format="<cyan>{time:HH:mm:ss}</cyan>"
               " - <level>{message}</level>", filter=InterceptHandler)

# log.add(sys.stdout, level="INFO", colorize=True,
#         format="<cyan>{module}</cyan>.<cyan>{function}</cyan>"
#                ":<cyan>{line}</cyan> - "
#                "<level>{message}</level>", filter=LogFilter)

log.add(path_log, level="DEBUG",
        format="{time:HH:mm:ss} - "
               "{level}\t| "
               "{module}.{function}:{line} - {message}",
        rotation="1 days", enqueue=True, serialize=False, encoding="utf-8", retention="10 days")
