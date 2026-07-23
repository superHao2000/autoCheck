"""可选通知渠道。

本模块只在全部签到完成后由入口调用。每个渠道自行捕获异常，保证通知故障
不会影响已经完成的签到结果。
"""

import base64
import hashlib
import hmac
import time
import urllib.parse

import requests

from utils import config
from utils.logger import log


REQUEST_TIMEOUT = 15


def _value(name: str, default: str = "") -> str:
    """读取当前推送配置，避免缓存导入时尚未加载的旧配置。"""
    return str(config.PUSH.get(name, default) or default)


def _report(channel: str, response: dict, success: bool) -> None:
    """按渠道统一记录推送结果，响应结构不符合预期时也视为失败。"""
    if success:
        log.info("%s 推送成功", channel)
    else:
        log.warning("%s 推送失败: %s", channel, response)


def bark(title: str, content: str) -> None:
    """通过官方 Bark 服务推送 URL 编码后的标题和正文。"""
    token = _value("BARK")
    if not token:
        return
    try:
        response = requests.get(
            f"https://api.day.app/{token}/{urllib.parse.quote(title)}/{urllib.parse.quote(content)}",
            timeout=REQUEST_TIMEOUT,
        ).json()
        _report("Bark", response, response.get("code") == 200)
    except requests.RequestException as exc:
        log.warning("Bark 推送请求失败: %s", exc)


def bark_push(title: str, content: str) -> None:
    """通过自建 Bark 服务推送；BARK_PUSH 需为不带尾斜杠的服务地址。"""
    endpoint = _value("BARK_PUSH").rstrip("/")
    if not endpoint:
        return
    try:
        response = requests.get(
            f"{endpoint}/{urllib.parse.quote(title)}/{urllib.parse.quote(content)}",
            timeout=REQUEST_TIMEOUT,
        ).json()
        _report("自建 Bark", response, response.get("code") == 200)
    except requests.RequestException as exc:
        log.warning("自建 Bark 推送请求失败: %s", exc)


def serverJ(title: str, content: str) -> None:
    """使用 Server 酱旧版接口发送 Markdown 正文。"""
    key = _value("PUSH_KEY")
    if not key:
        return
    try:
        response = requests.post(
            f"https://sc.ftqq.com/{key}.send",
            data={"text": title, "desp": content.replace("\n", "\n\n")},
            timeout=REQUEST_TIMEOUT,
        ).json()
        _report("Server 酱", response, response.get("data", {}).get("errno") == 0)
    except requests.RequestException as exc:
        log.warning("Server 酱推送请求失败: %s", exc)


def telegram_bot(title: str, content: str) -> None:
    """调用 Telegram Bot API；配置代理时同时用于 HTTP 和 HTTPS。"""
    token, chat_id = _value("TG_BOT_TOKEN"), _value("TG_USER_ID")
    if not token or not chat_id:
        return
    host = _value("TG_API_HOST") or "https://api.telegram.org"
    if not host.startswith("http"):
        host = f"https://{host}"
    proxy_host, proxy_port = _value("TG_PROXY_IP"), _value("TG_PROXY_PORT")
    proxies = None
    if proxy_host and proxy_port:
        proxy = f"http://{proxy_host}:{proxy_port}"
        proxies = {"http": proxy, "https": proxy}
    try:
        response = requests.post(
            f"{host.rstrip('/')}/bot{token}/sendMessage",
            data={"chat_id": chat_id, "text": f"{title}\n\n{content}", "disable_web_page_preview": "true"},
            proxies=proxies,
            timeout=REQUEST_TIMEOUT,
        ).json()
        _report("Telegram", response, response.get("ok") is True)
    except requests.RequestException as exc:
        log.warning("Telegram 推送请求失败: %s", exc)


def dingding_bot(title: str, content: str) -> None:
    """生成钉钉签名并发送文本机器人消息。"""
    token, secret = _value("DD_BOT_TOKEN"), _value("DD_BOT_SECRET")
    if not token or not secret:
        return
    timestamp = str(round(time.time() * 1000))
    signature = base64.b64encode(
        hmac.new(secret.encode(), f"{timestamp}\n{secret}".encode(), hashlib.sha256).digest()
    ).decode()
    url = f"https://oapi.dingtalk.com/robot/send?access_token={token}&timestamp={timestamp}&sign={urllib.parse.quote_plus(signature)}"
    try:
        response = requests.post(
            url,
            json={"msgtype": "text", "text": {"content": f"{title}\n\n{content}"}},
            timeout=REQUEST_TIMEOUT,
        ).json()
        _report("钉钉", response, response.get("errcode") == 0)
    except requests.RequestException as exc:
        log.warning("钉钉推送请求失败: %s", exc)


def coolpush_bot(title: str, content: str) -> None:
    """通过 Qmsg/Cool Push 发送纯文本消息。"""
    key, mode = _value("QQ_SKEY"), _value("QQ_MODE")
    if not key or not mode:
        return
    try:
        response = requests.post(
            f"https://qmsg.zendee.cn/{mode}/{key}", data={"msg": f"{title}\n\n{content}"}, timeout=REQUEST_TIMEOUT
        ).json()
        _report("Cool Push", response, response.get("code") == 0)
    except requests.RequestException as exc:
        log.warning("Cool Push 请求失败: %s", exc)


def pushplus_bot(title: str, content: str) -> None:
    """使用 PushPlus Token 发送签到结果。"""
    token = _value("PUSH_PLUS_TOKEN")
    if not token:
        return
    try:
        response = requests.post(
            "https://www.pushplus.plus/send",
            json={"token": token, "title": title, "content": content},
            timeout=REQUEST_TIMEOUT,
        ).json()
        _report("PushPlus", response, response.get("code") == 200)
    except requests.RequestException as exc:
        log.warning("PushPlus 请求失败: %s", exc)


def wecom_key(title: str, content: str) -> None:
    """通过企业微信群机器人发送文本；长正文由 send 分段调用。"""
    key = _value("QYWX_KEY")
    if not key:
        return
    try:
        response = requests.post(
            f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={key}",
            json={"msgtype": "text", "text": {"content": f"{title}\n{content}"}},
            timeout=REQUEST_TIMEOUT,
        ).json()
        _report("企业微信群机器人", response, response.get("errcode") == 0)
    except requests.RequestException as exc:
        log.warning("企业微信机器人请求失败: %s", exc)


def fs_key(title: str, content: str) -> None:
    """通过飞书群机器人 Webhook 发送文本消息。"""
    key = _value("FS_KEY")
    if not key:
        return
    try:
        response = requests.post(
            f"https://open.feishu.cn/open-apis/bot/v2/hook/{key}",
            json={"msg_type": "text", "content": {"text": f"{title}\n{content}"}},
            timeout=REQUEST_TIMEOUT,
        ).json()
        _report("飞书", response, response.get("StatusCode") == 0 or response.get("code") == 0)
    except requests.RequestException as exc:
        log.warning("飞书机器人请求失败: %s", exc)


class WeCom:
    """企业微信应用消息客户端，负责 Token 获取和消息提交。"""

    def __init__(self, corpid: str, corpsecret: str, agentid: str):
        self.corpid = corpid
        self.corpsecret = corpsecret
        self.agentid = agentid

    def get_access_token(self) -> str:
        """获取企业微信应用访问令牌；失败时抛出请求或字段异常给调用方处理。"""
        response = requests.get(
            "https://qyapi.weixin.qq.com/cgi-bin/gettoken",
            params={"corpid": self.corpid, "corpsecret": self.corpsecret},
            timeout=REQUEST_TIMEOUT,
        ).json()
        return response["access_token"]

    def send_text(self, message: str, touser: str) -> dict:
        """向指定成员或 @all 发送企业微信应用文本。"""
        return requests.post(
            f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={self.get_access_token()}",
            json={"touser": touser, "msgtype": "text", "agentid": self.agentid, "text": {"content": message}},
            timeout=REQUEST_TIMEOUT,
        ).json()


def wecom_app(title: str, content: str) -> None:
    """按 QYWX_AM 的 corpId,secret,user,agentId 格式发送企业微信应用消息。"""
    parts = [part.strip() for part in _value("QYWX_AM").split(",") if part.strip()]
    if not parts:
        return
    if len(parts) != 4:
        log.warning("QYWX_AM 应包含 corpid,corpsecret,touser,agentid 四项")
        return
    try:
        response = WeCom(parts[0], parts[1], parts[3]).send_text(f"{title}\n\n{content}", parts[2])
        _report("企业微信应用", response, response.get("errcode") == 0)
    except (KeyError, requests.RequestException) as exc:
        log.warning("企业微信应用请求失败: %s", exc)


def one() -> str:
    """获取一条一言文本；调用方应在失败时继续发送原始通知。"""
    response = requests.get("https://v1.hitokoto.cn/", timeout=REQUEST_TIMEOUT).json()
    return f"{response['hitokoto']}\n————{response['from']}"


def send(title: str, content: str) -> None:
    """将同一签到汇总分发到所有已配置的通知渠道。"""
    if _value("HITOKOTO"):
        try:
            content = f"{content}\n\n{one()}"
        except (KeyError, requests.RequestException) as exc:
            log.warning("获取一言失败，继续发送原通知: %s", exc)

    # 每个函数会先检查自身配置，未配置的渠道无需额外判断。
    bark(title, content)
    bark_push(title, content)
    serverJ(title, content)
    telegram_bot(title, content)
    dingding_bot(title, content)
    coolpush_bot(title, content)
    pushplus_bot(title, content)
    wecom_app(title, content)

    # 企业微信机器人单条文本上限约 2,000 字符，按正文切分避免被接口拒绝。
    if _value("QYWX_KEY"):
        for start in range(0, len(content) or 1, 2000):
            wecom_key(title, content[start : start + 2000])
    fs_key(title, content)
