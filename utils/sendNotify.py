import base64
import hashlib
import hmac
import json
import os
import re
import sys
import time
import urllib.parse

import requests

from utils.config import Conf
from utils.logger import log
from utils.logger import log_messages

send_Conf = Conf.PUSH
message = log_messages
# 通知服务
HITOKOTO = send_Conf.HITOKOTO  # 启用一言（随机句子）; 为空即关闭
BARK = '111'  # bark服务,自行搜索; secrets可填;
BARK_PUSH = '111'  # bark自建服务器，要填完整链接，结尾的/不要
PUSH_KEY = '111'  # Server酱的PUSH_KEY; secrets可填
TG_BOT_TOKEN = '111'  # tg机器人的TG_BOT_TOKEN; secrets可填1407203283:AAG9rt-6RDaaX0HBLZQq0laNOh898iFYaRQ
TG_USER_ID = '111'  # tg机器人的TG_USER_ID; secrets可填 1434078534
TG_API_HOST = '111'  # tg 代理api
TG_PROXY_IP = '111'  # tg机器人的TG_PROXY_IP; secrets可填
TG_PROXY_PORT = '111'  # tg机器人的TG_PROXY_PORT; secrets可填
DD_BOT_TOKEN = '111'  # 钉钉机器人的DD_BOT_TOKEN; secrets可填
DD_BOT_SECRET = '111'  # 钉钉机器人的DD_BOT_SECRET; secrets可填
QQ_SKEY = '111'  # qq机器人的QQ_SKEY; secrets可填
QQ_MODE = '111'  # qq机器人的QQ_MODE; secrets可填
QYWX_AM = '111'  # 企业微信
QYWX_KEY = '111'  # 企业微信BOT
PUSH_PLUS_TOKEN = '111'  # 微信推送Plus+
FS_KEY = '111'  # 飞书群BOT


# message_info = ''''''
# def message(str_msg):
#     global message_info
#     log.info(str_msg)
#     message_info = "{}\n{}".format(message_info, str_msg)
#     sys.stdout.flush()


def bark(title, content):
    if not BARK:
        log.info("bark服务的BARK未设置,\n取消推送")
        return
    log.info("bark服务启动")
    try:
        response = requests.get(
            f"""https://api.day.app/{BARK}/{title}/{urllib.parse.quote_plus(content)}""").json()
        if response['code'] == 200:
            log.info('推送成功！')
        else:
            log.info('推送失败！')
    except Exception as e:
        log.error(f"报错信息:{e}")
        log.info('推送失败！')


def bark_push(title, content):
    if not BARK_PUSH:
        log.info("bark自建服务的BARK_PUSH未设置,\n取消推送")
        return
    log.info("bark自建服务启动")
    try:
        response = requests.get(
            f"""{BARK_PUSH}/{title}/{urllib.parse.quote_plus(content)}""").json()
        if response['code'] == 200:
            log.info('推送成功！')
        else:
            log.info('推送失败！')
    except Exception as e:
        log.error(f"报错信息:{e}")
        log.info('推送失败！')


# server酱
def serverJ(title, content):
    if not PUSH_KEY:
        log.info("server酱服务的PUSH_KEY未设置!!\n取消推送")
        return
    log.info("serverJ服务启动")
    try:
        data = {
            "text": title,
            "desp": content.replace("\n", "\n\n")
        }
        response = requests.post(f"https://sc.ftqq.com/{PUSH_KEY}.send", data=data).json()
        log.debug(response)
        if response['errno'] == 0:
            log.info('推送成功！')
        else:
            log.info('推送失败！')
    except Exception as e:
        log.error(f"报错信息:{e}")
        log.info('推送失败！')


# tg通知
def telegram_bot(title, content):
    if not TG_BOT_TOKEN or not TG_USER_ID:
        log.info("tg服务的TG_BOT_TOKEN或者TG_USER_ID未设置!!\n取消推送")
        return
    log.info("tg服务启动")
    try:
        if TG_API_HOST:
            if 'http' in TG_API_HOST:
                url = f"{TG_API_HOST}/bot{TG_BOT_TOKEN}/sendMessage"
            else:
                url = f"https://{TG_API_HOST}/bot{TG_BOT_TOKEN}/sendMessage"
        else:
            url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        payload = {'chat_id': str(TG_USER_ID), 'text': f'{title}\n\n{content}', 'disable_web_page_preview': 'true'}
        proxies = None
        if TG_PROXY_IP and TG_PROXY_PORT:
            proxyStr = "http://{}:{}".format(TG_PROXY_IP, TG_PROXY_PORT)
            proxies = {"http": proxyStr, "https": proxyStr}
            response = requests.post(url=url, headers=headers, params=payload, proxies=proxies).json()
            log.debug(response)
            if response['ok']:
                log.info('推送成功！')
            else:
                log.info('推送失败！')
    except Exception as e:
        log.error(f"报错信息:{e}")
        log.info('推送失败！')


# 钉钉机器人
def dingding_bot(title, content):
    if not DD_BOT_TOKEN and not DD_BOT_SECRET:
        log.info("钉钉机器人服务的DD_BOT_TOKEN或者DD_BOT_SECRET未设置!!\n取消推送")
        return
    log.info("钉钉机器人服务启动")
    try:
        timestamp = str(round(time.time() * 1000))  # 时间戳
        secret_enc = DD_BOT_SECRET.encode('utf-8')
        string_to_sign = '{}\n{}'.format(timestamp, DD_BOT_SECRET)
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))  # 签名
        url = f'https://oapi.dingtalk.com/robot/send?access_token={DD_BOT_TOKEN}&timestamp={timestamp}&sign={sign}'
        headers = {'Content-Type': 'application/json;charset=utf-8'}
        data = {
            'msgtype': 'text',
            'text': {'content': f'{title}\n\n{content}'}
        }
        response = requests.post(url=url, data=json.dumps(data), headers=headers, timeout=15).json()
        log.debug(response)
        if not response['errcode']:
            log.info('推送成功！')
        else:
            log.info('推送失败！')
    except Exception as e:
        log.error(f"报错信息:{e}")
        log.info('推送失败！')


# qq机器人
def coolpush_bot(title, content):
    if not QQ_SKEY or not QQ_MODE:
        log.info("qq服务的QQ_SKEY或者QQ_MODE未设置!!\n取消推送")
        return
    log.info("qq服务启动")
    try:
        url = f"https://qmsg.zendee.cn/{QQ_MODE}/{QQ_SKEY}"
        payload = {'msg': f"{title}\n\n{content}".encode('utf-8')}
        response = requests.post(url=url, params=payload).json()
        if response['code'] == 0:
            log.info('推送成功！')
        else:
            log.info('推送失败！')
    except Exception as e:
        log.error(f"报错信息:{e}")
        log.info('推送失败！')


# push推送
def pushplus_bot(title, content):
    if not PUSH_PLUS_TOKEN:
        log.info("PUSHPLUS服务的token未设置!!\n取消推送")
        return
    log.info("PUSHPLUS服务启动")
    try:
        url = 'http://www.pushplus.plus/send'
        data = {
            "token": PUSH_PLUS_TOKEN,
            "title": title,
            "content": content
        }
        body = json.dumps(data).encode(encoding='utf-8')
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url=url, data=body, headers=headers).json()
        log.debug(response)
        if response['code'] == 200:
            log.info('推送成功！')
        else:
            log.info('推送失败！')
    except Exception as e:
        log.error(f"报错信息:{e}")
        log.info('推送失败！')


# 企业微信
def wecom_key(title, content):
    if not QYWX_KEY:
        log.info("QYWX_KEY未设置!!\n取消推送")
        return
    log.info("QYWX_KEY服务启动")
    try:
        # log.info("content" + content)
        headers = {'Content-Type': 'application/json'}
        data = {
            "msgtype": "text",
            "text": {
                "content": title + "\n" + content.replace("\n", "\n\n")
            }
        }
        # log.info(f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={QYWX_KEY}")
        response = requests.post(f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={QYWX_KEY}", json=data,
                                 headers=headers).json()
        log.debug(response)
        # todo 不知道怎么判断是否成功
    except Exception as e:
        log.error(f"报错信息:{e}")
        log.info("推送失败")


# 飞书机器人推送
def fs_key(title, content):
    if not FS_KEY:
        log.info("FS_KEY未设置!!\n取消推送")
        return
    log.info("FS_KEY服务启动")
    try:
        # log.info("content" + content)
        headers = {'Content-Type': 'application/json'}
        data = {
            "msg_type": "text",
            "content": {
                "text": title + "\n" + content.replace("\n", "\n\n")
            }
        }
        # log.info(f"https://open.feishu.cn/open-apis/bot/v2/hook/{FS_KEY}")
        response = requests.post(f"https://open.feishu.cn/open-apis/bot/v2/hook/{FS_KEY}", json=data,
                                 headers=headers).json()
        log.debug(response)
        # todo 不知道怎么判断是否成功
    except Exception as e:
        log.error(f"报错信息:{e}")
        log.info("推送失败")


# 企业微信 APP 推送
def wecom_app(title, content):
    if not QYWX_AM:
        log.info("QYWX_AM 并未设置！！\n取消推送")
        return
    QYWX_AM_AY = re.split(',', QYWX_AM)
    if 4 < len(QYWX_AM_AY) > 5:
        log.info("QYWX_AM 设置错误！！\n取消推送")
        return
    log.info("QYWX_APP服务启动")
    try:
        corpid = QYWX_AM_AY[0]
        corpsecret = QYWX_AM_AY[1]
        touser = QYWX_AM_AY[2]
        agentid = QYWX_AM_AY[3]
        try:
            media_id = QYWX_AM_AY[4]
        except:
            media_id = ''
        wx = WeCom(corpid, corpsecret, agentid)
        # 如果没有配置 media_id 默认就以 text 方式发送
        if not media_id:
            message = title + '\n\n' + content
            response = wx.send_text(message, touser)
        else:
            response = wx.send_mpnews(title, content, media_id, touser)
        if response == 'ok':
            log.info('推送成功！')
        else:
            log.info('推送失败！错误信息如下：\n', response)
    except Exception as e:
        log.error(f"报错信息:{e}")
        log.info("推送失败")


class WeCom:
    def __init__(self, corpid, corpsecret, agentid):
        self.CORPID = corpid
        self.CORPSECRET = corpsecret
        self.AGENTID = agentid

    def get_access_token(self):
        url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken'
        values = {'corpid': self.CORPID,
                  'corpsecret': self.CORPSECRET,
                  }
        req = requests.post(url, params=values)
        data = json.loads(req.text)
        return data["access_token"]

    def send_text(self, message, touser="@all"):
        send_url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=' + self.get_access_token()
        send_values = {
            "touser": touser,
            "msgtype": "text",
            "agentid": self.AGENTID,
            "text": {
                "content": message
            },
            "safe": "0"
        }
        send_msges = (bytes(json.dumps(send_values), 'utf-8'))
        respone = requests.post(send_url, send_msges)
        respone = respone.json()
        log.debug(respone)
        return respone["errmsg"]

    def send_mpnews(self, title, message, media_id, touser="@all"):
        send_url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=' + self.get_access_token()
        send_values = {
            "touser": touser,
            "msgtype": "mpnews",
            "agentid": self.AGENTID,
            "mpnews": {
                "articles": [
                    {
                        "title": title,
                        "thumb_media_id": media_id,
                        "author": "Author",
                        "content_source_url": "",
                        "content": message.replace('\n', '<br/>'),
                        "digest": message
                    }
                ]
            }
        }
        send_msges = (bytes(json.dumps(send_values), 'utf-8'))
        respone = requests.post(send_url, send_msges)
        respone = respone.json()
        log.debug(respone)
        return respone["errmsg"]


def one() -> str:
    """
    获取一条一言。
    :return:
    """
    url = "https://v1.hitokoto.cn/"
    res = requests.get(url).json()
    return res["hitokoto"] + "\n————" + res["from"]


def send(title, content):
    """
    使用 bark, telegram bot, dingding bot, server, feishuJ 发送手机推送
    :param title:
    :param content:
    :return:
    """
    # 获取一条一言
    content += f"\n\n{one()}" if HITOKOTO else ""
    if BARK:
        bark(title=title, content=content)
        print(content)
    if BARK_PUSH:
        bark_push(title=title, content=content)
    if PUSH_KEY:
        serverJ(title=title, content=content)
    if DD_BOT_TOKEN and DD_BOT_TOKEN:
        dingding_bot(title=title, content=content)
    if TG_BOT_TOKEN and TG_USER_ID:
        telegram_bot(title=title, content=content)
    if QQ_SKEY and QQ_MODE:
        coolpush_bot(title=title, content=content)
    if PUSH_PLUS_TOKEN:
        pushplus_bot(title=title, content=content)
    if QYWX_AM:
        wecom_app(title=title, content=content)
    if QYWX_KEY:
        for i in range(int(len(content) / 2000) + 1):
            wecom_key(title=title, content=content[i * 2000:(i + 1) * 2000])
    if QYWX_KEY:
        fs_key(title=title, content=content)


def main():
    send('title', message)


if __name__ == '__main__':
    main()
