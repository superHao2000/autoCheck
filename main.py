# new Env("auto_Check")
# cron 35 8 * * * main.py

import os

from utils import sendNotify
from utils.logger import InterceptHandler
from utils.util import sleep_random


# # 找出模块里所有的类名
def get_modules(packages="."):
    """
    获取包名下所有非__init__的模块名
    """
    __modules = []
    files = os.listdir(packages)
    for file in files:
        if not file.startswith("__"):
            name, ext = os.path.splitext(file)
            __modules.append("." + name)
    return __modules


if __name__ == '__main__':
    package = "checkin"
    modules = get_modules(package)
    for module in modules:
        try:
            # 动态导入并执行每个模块的main函数
            __import__(package + module, fromlist="main").main()
        except KeyError as e:
            pass
        except Exception as e:
            pass
        sleep_random()
    sendNotify.send("自用签到", InterceptHandler.message)
