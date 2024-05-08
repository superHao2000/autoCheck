import json

import requests

from utils.config import Conf
from utils.logger import log
from utils.util import sleep_random

config_GlaDos = Conf.ACCOUNT.GlADOS
name = "GlaDos"


class GlaDos(object):
    referer = "https://glados.rocks/console/checkin"
    origin = "https://glados.rocks"

    def __init__(self, glados):
        self.cookies = glados.cookies
        self.user_agent = glados.user_agent
        self.session = requests.session()

    def checkin(self):
        url = "https://glados.rocks/api/user/checkin"
        headers = {"cookie": self.cookies,
                   "referer": self.referer,
                   "origin": self.origin,
                   "user-agent": self.user_agent,
                   "content-type": 'application/json;charset=UTF-8'}
        payload = {
            'token': 'glados.one'
        }
        checkin = self.session.post(url, headers=headers, data=json.dumps(payload))
        if checkin.status_code == 200:
            result = checkin.json()
            # 获取签到结果
            message = result.get('message')
            points = result.get("points")
            if message == 'Checkin Repeats! Please Try Tomorrow':
                message = "今日已签到"
            elif "Checkin! Got" in message:
                message = f"签到成功，points+{points}"
            else:
                message = "签到失败，请检查..."
            log.info(message)

    def state(self):
        url = "https://glados.rocks/api/user/status"
        headers = {
            'cookie': self.cookies,
            "referer": self.referer,
            "origin": self.origin,
            "user-agent": self.user_agent,
        }
        state = self.session.get(url=url, headers=headers)
        days = state.json()["data"]["days"]
        left_days = int(float(state.json()["data"]["leftDays"]))
        log.info(f"当前point{days}点,剩余天数{left_days}天")

    def complete(self):
        """判断账号信息是否完整"""
        if self.cookies == "" or self.user_agent == "":
            log.info("账号信息不完整，跳过此账号")
            return False
        return True


def main():
    log.info(f"{name}签到开始执行")
    log.info(f"{name}检测到{len(config_GlaDos)}个账号")
    for i in range(len(config_GlaDos)):
        glados = GlaDos(config_GlaDos[i])
        if glados.complete():
            try:
                glados.checkin()
                glados.state()
                sleep_random()
            except Exception as e:
                log.info(f"账号{i + 1}签到失败")

        continue


if __name__ == '__main__':
    main()
    # glados = GlaDos(config_GlaDos[0])
    # glados.checkin()
