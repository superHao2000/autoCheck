import requests
from bs4 import BeautifulSoup

from utils.config import ACCOUNT, USER_AGENT
from utils.logger import log
from utils.util import LoginResultHandler
from utils.util import sleep_random

config_YuChen: dict = ACCOUNT["YuChen"]
name = "雨晨ios资源"


class YuChen:
    """处理账号信息"""

    def __init__(self, **kwargs):
        self.username = None
        self.password = None
        self.__dict__.update(kwargs)
        self.url = "yc.yuchengyouxi.com"
        if 'user_agent' not in kwargs:
            self.user_agent = USER_AGENT
        self.session = requests.session()
        log.debug(self.__str__())

    def __str__(self):
        return f'username={self.username},password={self.password},user_agent={self.user_agent}'

    def headers(self):
        return {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Host": self.url,
            "Origin": "https://" + self.url,
            "User-Agent": self.user_agent
        }

    def get_token(self) -> str:
        """
        获取登录所需token \n
        无token不能通过安全效验
        :return: token
        """
        url = "https://" + self.url + "/login"
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0"
        }
        response = self.session.get(url=url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        token = soup.find('input', {'name': 'token'}).get('value')
        log.debug(f"token:{token}")
        return token

    def yu_chen_login(self) -> bool:
        """
        登录网站
        """
        # log.info("开始登录")
        url = "https://" + self.url + "/wp-admin/admin-ajax.php"
        data = {
            "user_login": self.username,
            "password": self.password,
            "rememberme": "1",
            "redirect": "https://" + self.url + "/",
            "action": "userlogin_form",
            "token": self.get_token()
        }
        headers = self.headers()
        response = self.session.post(url=url, data=data, headers=headers)
        log.debug(response.json())
        message = LoginResultHandler(response.json())
        if message.success == "error":
            log.info("登录失败")
            log.info(message.msg)
            return False
        return True

    def yu_chen_check(self) -> None:
        """
        签到 \n
        地址:yc.yuchengyouxi.com
        :return:
        """
        # log.info("开始签到")
        url = "https://" + self.url + "/wp-admin/admin-ajax.php"
        data = {
            "action": "daily_sign"
        }
        headers = self.headers()
        response = self.session.post(url=url, data=data, headers=headers)
        log.debug(response.json())
        message = LoginResultHandler(response.json())
        log.info(message.msg)

    def yu_chen_info(self) -> None:
        """
        获取积分总值
        :return:
        """
        url = "https://" + self.url + "/users?tab=credit"
        headers = self.headers()
        response = self.session.get(url=url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.find('div', {'class': 'header_tips'}).text
        log.info(text.replace("", ""))

    def complete(self) -> bool:
        """判断账号信息是否完整"""
        if self.user_agent == "" or self.username == "" or self.password == "":
            log.info("账号信息不完整，跳过此账号")
            return False
        return True

    def run(self):
        """运行"""
        if self.yu_chen_login():
            self.yu_chen_check()
            self.yu_chen_info()


def main():
    log.info(f"{name}检测到{len(config_YuChen)}个账号")
    for i in range(len(config_YuChen)):
        try:
            log.info(f"账号{i + 1}签到开始执行")
            yuchen = YuChen(**config_YuChen[i])
            if yuchen.complete():
                try:
                    yuchen.run()
                except Exception as e:
                    log.info(f"账号{i + 1}签到失败")
                    log.debug(e)
                sleep_random()
            continue
        except Exception as e:
            log.info("出现错误了，请查看日志文件")
            log.debug(e)


if __name__ == '__main__':
    main()
