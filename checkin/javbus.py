import requests
from lxml import etree

from utils.config import ACCOUNT, USER_AGENT
from utils.logger import log
from utils.util import sleep_random

config_JavBus = ACCOUNT["JavBus"]
name = "JavBus"


class JavBus(object):
    def __init__(self, **kwargs):
        self.url: str = ""
        self.cookies: str = ""
        self.user_agent: str = ""
        self.__dict__.update(kwargs)
        if 'user_agent' not in kwargs:
            self.user_agent: str = USER_AGENT
        self.session = requests.Session()

    def checkin(self):
        url = self.url + "/forum/home.php?mod=spacecp&ac=credit&op=log&suboperation=creditrulelog"
        headers = {
            'authority': self.url,
            'method': 'GET',
            'path': '/forum/home.php?mod=spacecp&ac=credit',
            'scheme': 'https',
            'User-Agent': self.user_agent,
            # 'Connection' : 'keep-alive',
            # 'Host' : 'www.right.com.cn',
            'Upgrade-Insecure-Requests': '1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Accept-Encoding': 'gzip, deflate',
            'Cookie': self.cookies,
            'referer': self.url + '/forum/home.php?mod=spacecp'
        }
        response = self.session.get(url, headers=headers, timeout=60)
        if '每天登录' in response.text or '每天登錄' in response.text:
            h = etree.HTML(response.text)
            data = h.xpath('//tr/td[6]/text()')
            log.info(f'签到成功或今日已签到,最后签到时间:{data[0]}')
        else:
            log.info('签到失败,可能是cookie失效了!')

    def complete(self):
        if self.url == "" and self.cookies == "":
            log.info("账号信息不完整,跳过此账号")
            return False
        return True


def main():
    log.info(f"{name}检测到{len(config_JavBus)}个账号")
    for i in range(len(config_JavBus)):
        log.info(f"账号{i + 1}签到开始执行")
        account = JavBus(**config_JavBus[i])
        if account.complete():
            try:
                account.checkin()
            except Exception as e:
                log.info(f"账号{i + 1}签到失败,更换网络环境或者使用防屏蔽网址")
                log.debug(e)
                continue
            sleep_random()
        continue


if __name__ == '__main__':
    main()
