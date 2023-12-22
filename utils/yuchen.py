import requests
from bs4 import BeautifulSoup

from utils.logger import log
from utils.util import LoginResultHandler


class Account:
    """处理账号信息"""
    # user_agent: str = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0"

    def __init__(self, account):
        self.username = account["username"]
        self.password = account["password"]
        self.user_agent = account["user_agent"]
        self.cookie = None
        self.token = self.get_token()
        log.debug(self.__str__())

    def __str__(self):
        return f'username={self.username},password={self.password},user_agent={self.user_agent}'

    @staticmethod
    def get_token() -> str:
        """
        获取登录所需token \n
        无token不能通过安全效验
        :return: token
        """
        url = "https://yuchen.tonghuaios.com/login"
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0"
        }
        response = requests.get(url=url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        token = soup.find('input', {'name': 'token'}).get('value')
        log.debug(f"token:{token}")
        return token

    def yuchen_login(self):
        """
        登录网站获取cookie
        """
        log.info("开始登录")
        url = "https://yuchen.tonghuaios.com/wp-admin/admin-ajax.php"
        data = {
            "user_login": self.username,
            "password": self.password,
            "rememberme": "1",
            "redirect": "https://yuchen.tonghuaios.com/",
            "action": "userlogin_form",
            "token": self.token
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Host": "yuchen.tonghuaios.com",
            "Origin": "https://yuchen.tonghuaios.com",
            # "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0"
            "User-Agent": self.user_agent
        }
        response = requests.post(url=url, data=data, headers=headers)
        log.debug(response.json())
        message = LoginResultHandler(response.json())
        if message.success == "error":
            log.info("登录失败")
            log.info(message.msg)
            return False
        self.cookie = response.cookies
        return True

    def yuchen_check(self):
        """
        签到 \n
        yuchen.tonghuaios.com
        :return:
        """
        log.info("开始签到")
        url = "https://yuchen.tonghuaios.com/wp-admin/admin-ajax.php"
        data = {
            "action": "daily_sign"
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Host": "yuchen.tonghuaios.com",
            "Origin": "https://yuchen.tonghuaios.com",
            "User-Agent": self.user_agent,
            # "Cookie": cookies
        }
        response = requests.post(url=url, data=data, headers=headers, cookies=self.cookie)
        log.debug(response.json())
        message = LoginResultHandler(response.json())
        log.info(message.msg)

    def yuchen_info(self):
        """
        获取积分总值
        :return:
        """
        url = "https://yuchen.tonghuaios.com/users?tab=credit"
        headers = {
            "Hosts": "yuchen.tonghuaios.com"
        }
        response = requests.get(url=url)
        print(response.text)


if __name__ == '__main__':
    pass
