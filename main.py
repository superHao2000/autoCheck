import requests
from bs4 import BeautifulSoup
from requests.cookies import RequestsCookieJar

from utils.config import config
from utils.logger import log
from utils.utils import systesm_info, LoginResultHandler

acc = object


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
    log.info(token)
    return token


def yuchen_login() -> RequestsCookieJar:
    """
    登录网站获取cookie
    :return:
    """
    log.info("登录yuchen.com")
    url = "https://yuchen.tonghuaios.com/wp-admin/admin-ajax.php"
    data = {
        "user_login": acc.user_login,
        "password": acc.password,
        "rememberme": "1",
        "redirect": "https://yuchen.tonghuaios.com/",
        "action": "userlogin_form",
        "token": get_token()
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Host": "yuchen.tonghuaios.com",
        "Origin": "https://yuchen.tonghuaios.com",
        # "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0"
        "User-Agent": acc.user_agent
    }
    response = requests.post(url=url, data=data, headers=headers)
    log.debug(response.json())
    message = LoginResultHandler(response.json())
    if message.success == "error":
        log.info("登录失败")
        log.info(message.msg)
        return ""
    return response.cookies


def yuchen_check(cookies):
    """
    签到
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
        "User-Agent": acc.user_agent,
        # "Cookie": cookies
    }
    response = requests.post(url=url, data=data, headers=headers, cookies=cookies)
    log.debug(response.json())
    message = LoginResultHandler(response.json())
    log.info(message.msg)


def yuchen_info():
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


def main():
    systesm_info()
    global acc
    acc = config('config.yaml')
    ck = yuchen_login()
    if ck == "":
        return
    yuchen_check(ck)


if __name__ == '__main__':
    main()
