"""GlaDos（Railgun）签到服务：使用站点地址和登录 Cookie 获取积分。"""

from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse

import requests

from utils import config
from utils.service_runner import run_accounts


# 自动发现服务时使用的元数据；url 可由 JSON 顶层共享给多个账号。
SERVICE_NAME = "GlaDos"
CONFIG_FILENAME = "glados.json"
ENV_KEY = "GLADOS_ACCOUNTS"
ACCOUNT_FIELDS = ("url", "cookies")


def _format_points(value: object) -> str:
    """去除积分数值无意义的小数尾零，保留站点返回的非数值内容。"""
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return str(value)
    return format(number.normalize(), "f")


def _points_message(data: dict) -> str:
    """从签到记录中提取本次获得积分和当前积分；字段缺失时保留站点消息。"""
    message = str(data.get("message") or "签到成功")
    records = data.get("list")
    latest = records[0] if isinstance(records, list) and records and isinstance(records[0], dict) else {}
    # 前端将 list[0] 作为最新记录；points 仅在缺少变动记录时作为本次积分回退。
    gained = latest.get("change", data.get("points"))
    balance = latest.get("balance")
    details: list[str] = []
    if gained is not None:
        details.append(f"本次获得 {_format_points(gained)} 积分")
    if balance is not None:
        details.append(f"当前总积分 {_format_points(balance)}")
    return f"{message}，{'，'.join(details)}" if details else message


def checkin(url: str, cookies: str) -> dict:
    """调用 Railgun 签到接口，并从最新记录返回本次与当前积分。"""
    base_url = url.rstrip("/")
    hostname = urlparse(base_url).hostname
    if not hostname:
        return {"success": False, "message": "GlaDos 站点地址无效"}

    headers = {
        "User-Agent": config.USER_AGENT or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Cookie": cookies,
        "Referer": f"{base_url}/",
    }
    try:
        response = requests.post(
            f"{base_url}/api/user/checkin",
            json={"token": hostname},
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.JSONDecodeError:
        return {"success": False, "message": "GlaDos 接口返回的 JSON 格式错误"}
    except requests.RequestException as exc:
        return {"success": False, "message": f"请求失败: {exc}"}

    if not isinstance(data, dict):
        return {"success": False, "message": "GlaDos 接口响应格式错误"}
    message = str(data.get("message") or "签到失败")
    # code 为 0 表示本次签到成功；已签到保持任务成功，以适配重复运行场景。
    if data.get("code") == 0:
        return {"success": True, "message": _points_message(data)}
    already_checked = "already checked" in message.lower() or "已签到" in message or "observation logged" in message.lower()
    if already_checked:
        return {"success": True, "message": _points_message(data)}
    return {"success": False, "message": message}


def run(accounts: list) -> dict:
    """使用公共执行器逐账号完成 GlaDos 签到。"""
    return run_accounts(SERVICE_NAME, accounts, ACCOUNT_FIELDS, checkin)
