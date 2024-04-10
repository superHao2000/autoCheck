import requests
from bs4 import BeautifulSoup

from utils.config import Conf
from utils.logger import log
from utils.util import LoginResultHandler
from utils.util import sleep_random

config_YuChen = Conf.account.yuchen
name = "雨晨ios资源"


class YuChen:
    """处理账号信息"""

    # user_agent: str = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0"

    def __init__(self, yuchen):
        self.username = yuchen.username
        self.password = yuchen.password
        self.user_agent = yuchen.user_agent
        self.session = requests.session()
        self.cookie = None
        self.token = self.get_token()
        log.debug(self.__str__())

    def __str__(self):
        return f'username={self.username},password={self.password},user_agent={self.user_agent}'

    def headers(self):
        return {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Host": "yuchen.tonghuaios.com",
            "Origin": "https://yuchen.tonghuaios.com",
            # "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0"
            "User-Agent": self.user_agent
        }

    def get_token(self) -> str:
        """
        获取登录所需token \n
        无token不能通过安全效验
        :return: token
        """
        url = "https://yuchen.tonghuaios.com/login"
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0"
        }
        response = self.session.get(url=url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        token = soup.find('input', {'name': 'token'}).get('value')
        log.debug(f"token:{token}")
        return token

    def yuchen_login(self):
        """
        登录网站
        """
        # log.info("开始登录")
        url = "https://yuchen.tonghuaios.com/wp-admin/admin-ajax.php"
        data = {
            "user_login": self.username,
            "password": self.password,
            "rememberme": "1",
            "redirect": "https://yuchen.tonghuaios.com/",
            "action": "userlogin_form",
            "token": self.token
        }
        # headers = {
        #     "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        #     "Host": "yuchen.tonghuaios.com",
        #     "Origin": "https://yuchen.tonghuaios.com",
        #     # "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0"
        #     "User-Agent": self.user_agent
        # }
        headers = self.headers()
        response = self.session.post(url=url, data=data, headers=headers)
        log.debug(response.json())
        message = LoginResultHandler(response.json())
        if message.success == "error":
            log.info("登录失败")
            log.info(message.msg)
            return False
        # self.cookie = response.cookies
        return True

    def yuchen_check(self):
        """
        签到 \n
        yuchen.tonghuaios.com
        :return:
        """
        # log.info("开始签到")
        url = "https://yuchen.tonghuaios.com/wp-admin/admin-ajax.php"
        data = {
            "action": "daily_sign"
        }
        headers = self.headers()
        # response = requests.post(url=url, data=data, headers=headers, cookies=self.cookie)
        response = self.session.post(url=url, data=data, headers=headers)
        log.debug(response.json())
        message = LoginResultHandler(response.json())
        log.info(message.msg)

    def yuchen_info(self):
        """
        获取积分总值
        :return:
        """
        url = "https://yuchen.tonghuaios.com/users?tab=credit"
        headers = self.headers()
        # response = self.session.get(url=url, headers=headers, cookies=self.cookie)
        response = self.session.get(url=url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.find('div', {'class': 'header_tips'}).text
        log.info(text)

    def yuchen_sign(self):
        """判断账号信息是否完整"""
        if self.user_agent == "" or self.username == "" or self.password == "":
            log.info("账号信息不完整，跳过此账号")
            return False
        return True

    def run(self):
        """运行"""
        is_a = self.yuchen_login()
        if is_a:
            self.yuchen_check()
            self.yuchen_info()


def main():
    log.info(f"{name}签到开始执行")
    log.info(f"{name}检测到{len(config_YuChen)}个账号")
    for i in range(len(config_YuChen)):
        yuchen = YuChen(config_YuChen[i])
        if yuchen.yuchen_sign():
            try:
                yuchen.run()
            except Exception as e:
                log.info(f"账号{i + 1}签到失败")
            sleep_random()
        continue


if __name__ == '__main__':
    main()
