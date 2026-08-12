"""JavBus 签到服务：访问已登录论坛首页触发自动签到并汇报里程。"""

import math
import re
from html import unescape

import requests

from utils import config
from utils.service_runner import run_accounts


# 自动发现服务时使用的元数据；文件名对应默认配置文件名。
SERVICE_NAME = "JavBus"
CONFIG_FILENAME = "javbus.json"
ENV_KEY = "JAVBUS_ACCOUNTS"
ACCOUNT_FIELDS = ("url", "cookies")
DAILY_LOGIN_MILEAGE = 1


def _page_text(page: str) -> str:
    """将论坛 HTML 转为紧凑文本，供固定积分字段解析使用。"""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", unescape(page)))


def _credit_balance(page: str) -> tuple[int | None, int | None]:
    """从里程页读取当前金钱和里程；页面字段缺失时返回 None。"""
    text = _page_text(page)
    money_match = re.search(r"金[钱錢]\s*[:：]\s*(\d+)", text)
    mileage_match = re.search(r"里程\s*[:：]\s*(\d+)", text)
    return (
        int(money_match.group(1)) if money_match else None,
        int(mileage_match.group(1)) if mileage_match else None,
    )


def _upgrade_remaining(page: str) -> int | None:
    """从晋级用户组页面提取距离下一等级所需的里程。"""
    match = re.search(r"(?:您)?升[级級]到此用[户戶][组組][还還]需里程\s*(\d+)", _page_text(page))
    return int(match.group(1)) if match else None


def _summary_message(
    before: tuple[int | None, int | None],
    after: tuple[int | None, int | None],
    remaining: int | None,
) -> str:
    """汇总本次增量、当前余额和按每日登录奖励估算的升级天数。"""
    before_money, before_mileage = before
    money, mileage = after
    details: list[str] = []
    if money is not None:
        earned_money = money - before_money if before_money is not None else 0
        details.append(f"本次金钱 +{earned_money}，当前金钱 {money}")
    if mileage is not None:
        earned_mileage = mileage - before_mileage if before_mileage is not None else 0
        details.append(f"本次里程 +{earned_mileage}，当前里程 {mileage}")
    if remaining is not None:
        days = math.ceil(remaining / DAILY_LOGIN_MILEAGE)
        details.append(f"升级还需里程 {remaining}，按每日登录预计 {days} 天")
    return "；".join(details) if details else "已触发登录态自动签到，但未解析到积分信息"


def _is_logged_in(page: str) -> bool:
    """通过论坛页面中的退出入口判断 Cookie 是否仍保持登录态。"""
    text = page.lower()
    return "logout" in text or "退出登录" in page or "退出" in page


def checkin(url: str, cookies: str) -> dict:
    """访问论坛首页触发自动签到，再读取积分和升级进度。"""
    base_url = url.rstrip("/")
    forum_url = f"{base_url}/forum/"
    credit_url = f"{base_url}/forum/home.php?mod=spacecp&ac=credit"
    group_url = f"{base_url}/forum/home.php?mod=spacecp&ac=usergroup"
    headers = {
        "User-Agent": config.USER_AGENT or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Cookie": cookies,
        "Referer": forum_url,
    }
    session = requests.Session()
    try:
        before = _credit_balance(session.get(credit_url, headers=headers, timeout=30).text)
        response = session.get(forum_url, headers=headers, timeout=30)
        response.raise_for_status()
        if not _is_logged_in(response.text):
            return {"success": False, "message": "未检测到登录状态，请更新 JavBus Cookie"}
        after = _credit_balance(session.get(credit_url, headers=headers, timeout=30).text)
        remaining = _upgrade_remaining(session.get(group_url, headers=headers, timeout=30).text)
        return {"success": True, "message": _summary_message(before, after, remaining)}
    except requests.exceptions.Timeout:
        return {"success": False, "message": "请求超时"}
    except requests.RequestException as exc:
        return {"success": False, "message": f"请求失败: {exc}"}
    finally:
        session.close()


def run(accounts: list) -> dict:
    """使用公共执行器逐账号完成 JavBus 自动签到。"""
    return run_accounts(SERVICE_NAME, accounts, ACCOUNT_FIELDS, checkin)
