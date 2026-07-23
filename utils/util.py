"""轻量通用辅助函数，供签到模块在需要时复用。"""

import platform
import random
import time
from urllib.request import getproxies

from utils.logger import log


class LoginResultHandler:
    """将包含 success/msg 的响应字典转换为属性访问形式。"""

    def __init__(self, consent: dict):
        self.success = consent["success"]
        self.msg = consent["msg"]


def show_info(tip, info):
    """将系统信息标签和值格式化为统一日志文本。"""
    return "{}: {}".format(tip, info)


def systesm_info():
    """输出运行环境和系统代理信息，便于排查环境差异。"""
    log.info(show_info('操作系统平台', platform.platform()))
    log.info(show_info('操作系统版本', platform.version()))
    log.info(show_info('操作系统名称', platform.system()))
    log.info(show_info('操作系统位元', platform.architecture()))
    log.info(show_info('操作系统类型', platform.machine()))
    log.info(show_info('处理器信息', platform.processor()))
    log.info(show_info('Python 版本', str(platform.python_version()) + ' ' + str(platform.python_build())))
    if getproxies():
        log.info(show_info('系统代理', getproxies()))


def sleep_random(min=1, max=10):
    """在给定秒数范围内随机等待，用于降低连续请求频率。"""
    time.sleep(random.randint(min, max))


class ObjDictTool:
    """为已有对象批量写入属性的兼容工具。"""

    @staticmethod
    def to_obj(obj: object, **data):
        """将关键字参数直接更新到对象的属性字典。"""
        obj.__dict__.update(data)
