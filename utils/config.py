from pprint import pprint

import yaml

from utils.logger import log


def config(file_path):
    log.info('读取配置文件')
    with open(file_path, 'r', encoding='utf-8') as f:
        data = f.read()
        result = yaml.load(data, Loader=yaml.FullLoader)
        account = Account(result['user_login'], result['password'], result['user_agent'])
        return account


class Account:
    user_agent: str = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0"

    def __init__(self, user_login=None, password=None, user_agent=user_agent):
        self.user_login = user_login
        self.password = password
        self.user_agent = user_agent

    def __str__(self):
        return f'user_login={self.user_login},password={self.password},user_agent={self.user_agent}'


if __name__ == '__main__':
    a = config('../config.yaml')
    print(a)
