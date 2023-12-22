import sys

import yaml
from yaml.parser import ParserError

from utils.logger import log
from utils.yuchen import Account


# def account_init(accounts):
#     account_list = []
#     for account in accounts:
#         account = Account(account['username'], account['password'], account['user_agent'])
#         account_list.append(account)
#     return account_list


class Config(object):
    """配置类"""

    Accounts: list = [Account]
    mail_host: str = ''
    mail_user: str = ''
    mail_pass: str = ''

    def __init__(self, file_path):
        self.file_path = file_path

    # def is_config(self):
    #     """判断文件是否存在"""
    #     if os.path.exists(self.file_path):
    #         log.info("检测到配置文件")
    #         return True
    #     else:
    #         log.info("配置文件不存在")
    #         self.write_config()
    #         return False

    def read_config(self):
        """读取配置文件"""
        log.info('读取配置文件')
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = f.read()
                configsss = yaml.safe_load(data)
                self.Accounts = configsss["Account"]
                self.mail_host = configsss["mail_host"]
                self.mail_user = configsss["mail_user"]
                self.mail_pass = configsss["mail_pass"]
        except ParserError:
            log.info("配置文件填写错误")
            sys.exit()
        except KeyError:
            log.info("未找到的配置项")

    def write_config(self):
        """写入配置文件"""
        config_json = {
            'Account': [
                {
                    "username": '',
                    "password": '',
                    "user_agent": ''
                },
                {
                    "username": '',
                    "password": '',
                    "user_agent": ''
                },
            ],
            'mail_host': '',
            'mail_user': '',
            'mail_pass': ''
        }
        with open(self.file_path, 'w') as file:
            file.writelines(yaml.safe_dump(config_json))
        log.info("生成配置文件成功")


if __name__ == '__main__':
    config = Config('../config.yaml')
    config.read_config()
    print(config.Accounts)
