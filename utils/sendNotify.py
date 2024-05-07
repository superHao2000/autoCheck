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

config_sendNotify = Conf.PUSH
# 通知服务
HITOKOTO = 'true'
# 启用一言（随机句子）; 为空即关闭
BARK = '1111'
# bark服务,自行搜索; secrets可填;
BARK_PUSH = '2222'
# bark自建服务器，要填完整链接，结尾的/不要
PUSH_KEY = '1111'
# Server酱的PUSH_KEY; secrets可填
TG_BOT_TOKEN = '111'
# tg机器人的TG_BOT_TOKEN; secrets可填1407203283:AAG9rt-6RDaaX0HBLZQq0laNOh898iFYaRQ
TG_USER_ID = '111'
# tg机器人的TG_USER_ID; secrets可填 1434078534
TG_API_HOST = '111'
# tg 代理api
TG_PROXY_IP = '111'
# tg机器人的TG_PROXY_IP; secrets可填
TG_PROXY_PORT = '111'
# tg机器人的TG_PROXY_PORT; secrets可填
DD_BOT_TOKEN = '111'
# 钉钉机器人的DD_BOT_TOKEN; secrets可填
DD_BOT_SECRET = '111'
# 钉钉机器人的DD_BOT_SECRET; secrets可填
QQ_SKEY = '111'
# qq机器人的QQ_SKEY; secrets可填
QQ_MODE = '111'
# qq机器人的QQ_MODE; secrets可填
QYWX_AM = '111'
# 企业微信
QYWX_KEY = '111'
# 企业微信BOT
PUSH_PLUS_TOKEN = '111'
# 微信推送Plus+
FS_KEY = '111'
# 飞书群BOT

notify_mode = []

message_info = ''''''

if BARK or BARK_PUSH:
    notify_mode.append('bark')
    # print("BARK 推送打开")
if PUSH_KEY:
    notify_mode.append('sc_key')
    # print("Server酱 推送打开")
if TG_BOT_TOKEN and TG_USER_ID:
    notify_mode.append('telegram_bot')
    # print("Telegram 推送打开")
if DD_BOT_TOKEN and DD_BOT_SECRET:
    notify_mode.append('dingding_bot')
    # print("钉钉机器人 推送打开")
if QQ_SKEY and QQ_MODE:
    notify_mode.append('coolpush_bot')
    # print("QQ机器人 推送打开")

if PUSH_PLUS_TOKEN:
    notify_mode.append('pushplus_bot')
    # print("微信推送Plus机器人 推送打开")
if QYWX_AM:
    notify_mode.append('wecom_app')
    # print("企业微信机器人 推送打开")

if QYWX_KEY:
    notify_mode.append('wecom_key')
    # print("企业微信机器人 推送打开")

if FS_KEY:
    notify_mode.append('fs_key')
    # print("飞书机器人 推送打开")


def message(str_msg):
    global message_info
    print(str_msg)
    message_info = "{}\n{}".format(message_info, str_msg)
    sys.stdout.flush()


def bark(title, content):
    """bark推送"""
    print("\n")
    print("bark服务启动")
    if BARK:
        try:
            response = requests.get(
                f"""https://api.day.app/{BARK}/{title}/{urllib.parse.quote_plus(content)}""").json()
            if response['code'] == 200:
                print('推送成功！')
            else:
                print('推送失败！')
        except:
            print('推送失败！')
    if BARK_PUSH:
        try:
            response = requests.get(
                f"""{BARK_PUSH}/{title}/{urllib.parse.quote_plus(content)}""").json()
            if response['code'] == 200:
                print('推送成功！')
            else:
                print('推送失败！')
        except:
            print('推送失败！')

    if BARK == '' and BARK_PUSH == '':
        print("bark服务的bark_token未设置!!\n取消推送")
        return


def serverJ(title, content):
    print("\n")
    if not PUSH_KEY:
        print("server酱服务的PUSH_KEY未设置!!\n取消推送")
        return
    print("serverJ服务启动")
    data = {
        "text": title,
        "desp": content.replace("\n", "\n\n")
    }
    response = requests.post(f"https://sc.ftqq.com/{PUSH_KEY}.send", data=data).json()
    if response['errno'] == 0:
        print('推送成功！')
    else:
        print('推送失败！')


# tg通知
def telegram_bot(title, content):
    try:
        print("\n")
        bot_token = TG_BOT_TOKEN
        user_id = TG_USER_ID
        if not bot_token or not user_id:
            print("tg服务的bot_token或者user_id未设置!!\n取消推送")
            return
        print("tg服务启动")
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
        try:
            response = requests.post(url=url, headers=headers, params=payload, proxies=proxies).json()
        except:
            print('推送失败！')
        if response['ok']:
            print('推送成功！')
        else:
            print('推送失败！')
    except Exception as e:
        print(e)


def dingding_bot(title, content):
    timestamp = str(round(time.time() * 1000))  # 时间戳
    secret_enc = DD_BOT_SECRET.encode('utf-8')
    string_to_sign = '{}\n{}'.format(timestamp, DD_BOT_SECRET)
    string_to_sign_enc = string_to_sign.encode('utf-8')
    hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))  # 签名
    print('开始使用 钉钉机器人 推送消息...', end='')
    url = f'https://oapi.dingtalk.com/robot/send?access_token={DD_BOT_TOKEN}&timestamp={timestamp}&sign={sign}'
    headers = {'Content-Type': 'application/json;charset=utf-8'}
    data = {
        'msgtype': 'text',
        'text': {'content': f'{title}\n\n{content}'}
    }
    response = requests.post(url=url, data=json.dumps(data), headers=headers, timeout=15).json()
    if not response['errcode']:
        print('推送成功！')
    else:
        print('推送失败！')


def coolpush_bot(title, content):
    print("\n")
    if not QQ_SKEY or not QQ_MODE:
        print("qq服务的QQ_SKEY或者QQ_MODE未设置!!\n取消推送")
        return
    try:
        print("qq服务启动")
        url = f"https://qmsg.zendee.cn/{QQ_MODE}/{QQ_SKEY}"
        payload = {'msg': f"{title}\n\n{content}".encode('utf-8')}
        response = requests.post(url=url, params=payload).json()
        if response['code'] == 0:
            print('推送成功！')
        else:
            print('推送失败！')
    except:
        print('推送失败！')


# push推送
def pushplus_bot(title, content):
    try:
        print("\n")
        if not PUSH_PLUS_TOKEN:
            print("PUSHPLUS服务的token未设置!!\n取消推送")
            return
        print("PUSHPLUS服务启动")
        url = 'http://www.pushplus.plus/send'
        data = {
            "token": PUSH_PLUS_TOKEN,
            "title": title,
            "content": content
        }
        body = json.dumps(data).encode(encoding='utf-8')
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url=url, data=body, headers=headers).json()
        if response['code'] == 200:
            print('推送成功！')
        else:
            print('推送失败！')
    except Exception as e:
        print(e)


def wecom_key(title, content):
    print("\n")
    if not QYWX_KEY:
        print("QYWX_KEY未设置!!\n取消推送")
        return
    print("QYWX_KEY服务启动")
    print("content" + content)
    headers = {'Content-Type': 'application/json'}
    data = {
        "msgtype": "text",
        "text": {
            "content": title + "\n" + content.replace("\n", "\n\n")
        }
    }

    print(f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={QYWX_KEY}")
    response = requests.post(f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={QYWX_KEY}", json=data,
                             headers=headers).json()
    print(response)


# 飞书机器人推送
def fs_key(title, content):
    print("\n")
    if not FS_KEY:
        print("FS_KEY未设置!!\n取消推送")
        return
    print("FS_KEY服务启动")
    print("content" + content)
    headers = {'Content-Type': 'application/json'}
    data = {
        "msg_type": "text",
        "content": {
            "text": title + "\n" + content.replace("\n", "\n\n")
        }
    }

    print(f"https://open.feishu.cn/open-apis/bot/v2/hook/{FS_KEY}")
    response = requests.post(f"https://open.feishu.cn/open-apis/bot/v2/hook/{FS_KEY}", json=data,
                             headers=headers).json()
    print(response)


# 企业微信 APP 推送
def wecom_app(title, content):
    try:
        if not QYWX_AM:
            print("QYWX_AM 并未设置！！\n取消推送")
            return
        QYWX_AM_AY = re.split(',', QYWX_AM)
        if 4 < len(QYWX_AM_AY) > 5:
            print("QYWX_AM 设置错误！！\n取消推送")
            return
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
            print('推送成功！')
        else:
            print('推送失败！错误信息如下：\n', response)
    except Exception as e:
        print(e)


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

    for i in notify_mode:
        if i == 'bark':
            if BARK or BARK_PUSH:
                bark(title=title, content=content)
            else:
                print('未启用 bark')
            continue
        if i == 'sc_key':
            if PUSH_KEY:
                serverJ(title=title, content=content)
            else:
                print('未启用 Server酱')
            continue
        elif i == 'dingding_bot':
            if DD_BOT_TOKEN and DD_BOT_SECRET:
                dingding_bot(title=title, content=content)
            else:
                print('未启用 钉钉机器人')
            continue
        elif i == 'telegram_bot':
            if TG_BOT_TOKEN and TG_USER_ID:
                telegram_bot(title=title, content=content)
            else:
                print('未启用 telegram机器人')
            continue
        elif i == 'coolpush_bot':
            if QQ_SKEY and QQ_MODE:
                coolpush_bot(title=title, content=content)
            else:
                print('未启用 QQ机器人')
            continue
        elif i == 'pushplus_bot':
            if PUSH_PLUS_TOKEN:
                pushplus_bot(title=title, content=content)
            else:
                print('未启用 PUSHPLUS机器人')
            continue
        elif i == 'wecom_app':
            if QYWX_AM:
                wecom_app(title=title, content=content)
            else:
                print('未启用企业微信应用消息推送')
            continue
        elif i == 'wecom_key':
            if QYWX_KEY:

                for i in range(int(len(content) / 2000) + 1):
                    wecom_key(title=title, content=content[i * 2000:(i + 1) * 2000])
            else:
                print('未启用企业微信应用消息推送')
            continue
        elif i == 'fs_key':
            if FS_KEY:
                fs_key(title=title, content=content)
            else:
                print('未启用飞书机器人消息推送')
            continue
        else:
            print('此类推送方式不存在')


def main():
    send('title', 'content')


if __name__ == '__main__':
    main()
