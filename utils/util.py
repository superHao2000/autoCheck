import platform
import random
import time
from urllib.request import getproxies

from utils.logger import log


class LoginResultHandler:
    """
    处理返回的信息
    """

    def __init__(self, consent: dict):
        self.success = consent["success"]
        self.msg = consent["msg"]


def show_info(tip, info):
    return "{}: {}".format(tip, info)


def systesm_info():
    """
    输出系统信息
    :return:
    """
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
    time.sleep(random.randint(min, max))


class ObjDictTool:
    @staticmethod
    def to_obj(obj: object, **data):
        obj.__dict__.update(data)
