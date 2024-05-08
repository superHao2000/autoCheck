import os
import sys

from loguru import logger

log_messages = ""


def record_to_string(record):
    global log_messages
    log_messages.join(record)


def LogFilter(record):
    # global message
    message = ""
    if record["level"].no >= 20:
        message += f"{record.get('message')}\n"
    return True


log_PATH = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), "logs")
path_log = os.path.join(log_PATH, '日志文件.log')
log = logger
log.remove()

log.add(sys.stdout, level="INFO", colorize=True,
        format="<cyan>{time:HH:mm:ss}</cyan>"
               " - <level>{message}</level>", filter=LogFilter)
# log.add(sys.stdout, level="INFO", colorize=True,
#         format="<cyan>{module}</cyan>.<cyan>{function}</cyan>"
#                ":<cyan>{line}</cyan> - "
#                "<level>{message}</level>", filter=LogFilter)

log.add(path_log, level="DEBUG",
        format="{time:HH:mm:ss} - "
               "{level}\t| "
               "{module}.{function}:{line} - {message}",
        rotation="1 days", enqueue=True, serialize=False, encoding="utf-8", retention="10 days")

logger.add(record_to_string, level="INFO", colorize=True,
           format="<cyan>{time:HH:mm:ss}</cyan>"
                  " - <level>{message}</level>", )
