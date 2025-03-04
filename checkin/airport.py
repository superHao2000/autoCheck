import json

import requests
import urllib3

from utils.config import ACCOUNT, USER_AGENT
from utils.logger import log
from utils.util import sleep_random

urllib3.disable_warnings()

config_AirPort = ACCOUNT["AirPort"]
name = "飞机场"


class AirPort(object):
    def __init__(self, **kwargs):
        self.base_url: str = ""
        self.email: str = ""
        self.password: str = ""
        self.user_agent: str = ""
        self.__dict__.update(kwargs)
        if 'user_agent' not in kwargs:
            self.user_agent: str = USER_AGENT
        self.session = requests.session()

    def checkin(self):
        """
        主程序：实现登录和签到操作
        :return:
        """
        user_agent = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        # 获取主页面
        self.session.get(self.base_url, verify=False)
        # 登录
        login_url = self.base_url + '/auth/login'
        headers = {
            'User-Agent': user_agent,
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        }
        login_data = {
            'email': self.email,
            'passwd': self.password,
            'code': ''
        }
        self.session.post(url=login_url, headers=headers, data=login_data, verify=False)
        # 签到
        check_url = self.base_url + '/user/checkin'
        headers = {
            'User-Agent': user_agent,
            'Referer': self.base_url + '/user',
        }
        response = self.session.post(url=check_url, headers=headers, verify=False)
        response = json.loads(response.text)
        log.info(response["msg"])

    def complete(self):
        if self.base_url == "" or self.email == "" or self.password == "":
            log.info("账号信息不完整,跳过此账号")
            return False
        return True


def main():
    log.info(f"{name}检测到{len(config_AirPort)}个账号")
    for i in range(len(config_AirPort)):
        log.info(f"账号{i + 1}签到开始执行")
        account = AirPort(**config_AirPort[i])
        if account.complete():
            try:
                account.checkin()
            except Exception as e:
                log.info(f"账号{i + 1}签到失败")
                log.debug(e)
                continue
            sleep_random()
        continue


if __name__ == '__main__':
    main()
