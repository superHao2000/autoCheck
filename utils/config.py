import os.path
import sys
from json import JSONDecodeError

import yaml
from pydantic import ValidationError

from utils.logger import log

ROOT_PATH = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
"""主目录"""
CONFIG_PATH = os.path.join(ROOT_PATH, 'config.yaml')
"""数据文件目录"""


def read_data():
    try:
        with open(CONFIG_PATH, 'r') as file:
            config = yaml.safe_load(file)
        return config
    except (ValidationError, JSONDecodeError):
        log.exception(f"读取数据文件失败，请检查数据文件 {CONFIG_PATH} 格式是否正确")
        raise
    except Exception:
        log.exception(
            f"读取数据文件失败，请检查数据文件 {CONFIG_PATH} 是否存在且有权限读取和写入")
        raise


if os.path.exists(CONFIG_PATH):
    Conf = read_data()
    ACCOUNT = Conf.get('ACCOUNT')
    PUSH = Conf.get('PUSH')
    USER_AGENT = Conf.get('USER_AGENT')
else:
    log.info("配置文件不存在")
    log.info("请填写配置文件后重新启动")
    sys.exit()

if __name__ == '__main__':
    print(Conf["ACCOUNT"]["YuChen"][0])
    print(type(Conf["ACCOUNT"]["YuChen"][0]))
