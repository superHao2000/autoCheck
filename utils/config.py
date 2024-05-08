import os.path
import sys
from json import JSONDecodeError
from typing import List

import yaml
from pydantic import BaseModel, ValidationError
from utils.logger import log

ROOT_PATH = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
"""主目录"""
CONFIG_PATH = os.path.join(ROOT_PATH, 'config.yaml')
"""数据文件目录"""


class YuChen(BaseModel):
    username: str = ""
    '''账号'''
    password: str = ""
    '''密码'''
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0"
    '''浏览器头'''


class AirPort(BaseModel):
    base_url: str = ""
    '''网址'''
    email: str = ""
    '''邮箱'''
    password: str = ""
    '''密码'''
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0"
    '''浏览器头'''


class GlaDos(BaseModel):
    cookies: str = ""
    '''cookies'''
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0"
    '''浏览器头'''


class Account(BaseModel):
    YUCHEN: List[YuChen] = [YuChen()]
    GLADOS: List[GlaDos] = [GlaDos()]
    AIRPORT: List[AirPort] = [AirPort()]


class Push(BaseModel):
    pass


class Config(BaseModel):
    ACCOUNT: Account = Account()
    PUSH: Push = Push()


def write_data():
    try:
        data = Config()
        str_data = yaml.dump(data.model_dump(), indent=4, allow_unicode=True, sort_keys=False)
        with open(CONFIG_PATH, "w", encoding="utf-8") as file:
            file.write(str_data)
        log.info("生成配置文件成功")
    except:
        print("出现意外")
        raise


def read_data():
    try:
        with open(CONFIG_PATH, 'r', encoding="utf-8") as file:
            data = yaml.safe_load(file)
            new_model = Config.model_validate(data)
            for attr in new_model.model_fields:
                # Config.data_obj.__setattr__(attr, new_model.__getattribute__(attr))
                setattr(Config, attr, getattr(new_model, attr))
            return new_model
    except (ValidationError, JSONDecodeError):
        log.exception(f"读取数据文件失败，请检查数据文件 {CONFIG_PATH} 格式是否正确")
        raise
    except Exception:
        log.exception(
            f"读取数据文件失败，请检查数据文件 {CONFIG_PATH} 是否存在且有权限读取和写入")
        raise


if os.path.exists(CONFIG_PATH):
    Conf = read_data()
    # config_YuChen = Conf.Account["YuChen"]
    # config_Air = Conf.Account["Air"]
    # config_Push = Conf.Push
else:
    log.info("配置文件不存在")
    write_data()
    log.info("请填写配置文件后重新启动")
    sys.exit()
if __name__ == '__main__':
    print(Conf)
