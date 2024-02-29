import os.path
import sys

import yaml
from yaml.parser import ParserError

# from checkin.air import Air
# from checkin.yuchen import YuChen
from utils.logger import log

PATH = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
config_PATH = os.path.join(PATH, 'config.yaml')


class Config(object):
    """配置类"""

    Account: dict = {
        "YuChen": list,
        "AirPort": list,
    }
    Push: dict = {}

    def __init__(self, file_path):
        self.file_path = file_path

    def read_config(self):
        """读取配置文件"""
        log.info('读取配置文件')
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = f.read()
                config = yaml.safe_load(data)
                self.Account = config["Account"]
                self.Push = config["Push"]
        except ParserError:
            log.info("配置文件填写错误")
            sys.exit()
        except KeyError:
            log.info("未找到的配置项")

    def write_config(self):
        """写入配置文件"""
        config_dict = {
            'Account': {
                'YuChen': [
                    {
                        "username": '',
                        "password": '',
                        "user_agent": '',
                    },
                    {
                        "username": '',
                        "password": '',
                        "user_agent": '',
                    },
                ],
                'AirPort': [
                    {
                        "base_url": "",
                        "email": "",
                        "password": "",
                    },
                    {
                        "base_url": "",
                        "email": "",
                        "password": "",
                    },
                ]
            },
            'Push': '',
        }
        with open(self.file_path, 'w') as file:
            file.write(yaml.dump(config_dict, allow_unicode=True, sort_keys=False))
        log.info("生成配置文件成功")


Conf = Config(config_PATH)
if os.path.exists(config_PATH):
    Conf.read_config()
    # config_YuChen = Conf.Account["YuChen"]
    # config_Air = Conf.Account["Air"]
    # config_Push = Conf.Push
else:
    log.info("配置文件不存在")
    Conf.write_config()
    log.info("请填写配置文件后重新启动")
if __name__ == '__main__':
    print(Conf.Push["onepush"])
