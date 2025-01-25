import os.path
import shutil
import sys
from json import JSONDecodeError

import yaml
from pydantic import ValidationError

from utils.logger import log

ROOT_PATH = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
"""主目录"""
CONFIG_PATH = os.path.join(ROOT_PATH, 'config.yaml')
"""数据文件目录"""
CONFIG_PATH_BAK = os.path.join(ROOT_PATH, 'config.yaml.bak')


def read_data() -> dict:
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


def write_data() -> None:
    source = CONFIG_PATH_BAK
    destination = CONFIG_PATH
    try:
        # 检查源文件是否存在
        if os.path.exists(source):
            # 复制并重命名文件
            shutil.copyfile(source, destination)
            log.info(f"配置文件 {source} 已成功生成")
        else:
            log.info(f"配置文件备份 {source} 不存在。")
    except Exception as e:
        log.debug(f"发生错误: {e}")


if os.path.exists(CONFIG_PATH):
    Conf = read_data()
    ACCOUNT = Conf.get('ACCOUNT')
    PUSH = Conf.get('PUSH')
    USER_AGENT = Conf.get('USER_AGENT')
else:
    write_data()
    log.info("请填写配置文件后重新启动")
    sys.exit()

if __name__ == '__main__':
    print(Conf["ACCOUNT"]["YuChen"][0])
    print(type(Conf["ACCOUNT"]["YuChen"][0]))
