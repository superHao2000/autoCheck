"""YuChen 签到服务：以账号密码提交站点提供的签到地址。"""

import json
import re
from html import unescape
from urllib.parse import urljoin

import requests

from utils import config
from utils.service_runner import run_accounts


# 自动发现服务时使用的元数据；新增服务可按此约定声明。
SERVICE_NAME = "YuChen"
CONFIG_FILENAME = "yuchen.json"
ENV_KEY = "YUCHEN_ACCOUNTS"
ACCOUNT_FIELDS = ("url", "username", "password")


def _credit_summary(session: requests.Session, url: str, headers: dict) -> tuple[str | None, str | None]:
    """读取用户积分页，返回当前可用积分和最近签到奖励；读取失败不影响签到。"""
    try:
        credit_page = session.get(urljoin(url, "/users?tab=credit"), headers=headers, timeout=30)
    except requests.RequestException:
        return None, None

    text = re.sub(r'<[^>]+>', ' ', unescape(credit_page.text))
    balance_match = re.search(r'可用积分\s*[：:]\s*(\d+)', text)
    reward_match = re.search(r'每日签到赠送\s*(\d+)\s*积分', text)
    return (
        balance_match.group(1) if balance_match else None,
        reward_match.group(1) if reward_match else None,
    )


def _safe_message(message: object, username: str) -> str:
    """移除站点响应中的 HTML 与账号标识，避免错误日志泄露登录信息。"""
    text = re.sub(r'<[^>]+>', '', unescape(str(message)))
    return re.sub(re.escape(username), '该账号', text, flags=re.IGNORECASE).strip()


def checkin(url: str, username: str, password: str) -> dict:
    """登录 YuChen 站点并调用其 ``daily_sign`` 签到动作。"""
    headers = {'User-Agent': config.USER_AGENT} if config.USER_AGENT else {}
    session = requests.Session()
    try:
        # 登录页面提供 Ajax 地址和一次性 token；二者均可能随站点部署变化。
        page = session.get(url, headers=headers, timeout=30)
        ajax_match = re.search(r'var\s+chenxing\s*=\s*({.*?});', page.text, re.DOTALL)
        token_match = re.search(r'name=["\']token["\']\s+value=["\']([^"\']+)', page.text, re.IGNORECASE)
        if not ajax_match or not token_match:
            return {'success': False, 'message': '未找到 YuChen 登录接口或 token，请检查站点地址'}

        ajax_url = json.loads(ajax_match.group(1)).get('ajax_url')
        if not ajax_url:
            return {'success': False, 'message': 'YuChen 登录页面未提供 Ajax 地址'}

        login_response = session.post(
            ajax_url,
            data={
                'user_login': username,
                'password': password,
                'redirect': url,
                'action': 'userlogin_form',
                'token': token_match.group(1),
            },
            headers=headers,
            timeout=30,
        )
        login_data = login_response.json()
        if not isinstance(login_data, dict) or login_data.get('success') != 'success':
            message = login_data.get('msg', '登录失败') if isinstance(login_data, dict) else '登录响应格式错误'
            return {'success': False, 'message': _safe_message(message, username)}

        sign_response = session.post(ajax_url, data={'action': 'daily_sign'}, headers=headers, timeout=30)
        sign_data = sign_response.json()
        if not isinstance(sign_data, dict):
            return {'success': False, 'message': '签到响应格式错误'}
        message = _safe_message(sign_data.get('msg', '签到失败'), username)
        # success 是首次签到，info 是当日已签到，两者均视为任务成功。
        status = sign_data.get('success')
        if status not in ('success', 'info'):
            return {'success': False, 'message': message}

        balance, reward = _credit_summary(session, url, headers)
        separator = '' if message.endswith(('，', '。', '！', '!', '；', ';')) else '，'
        if status == 'success' and reward:
            message += f'{separator}本次获得 {reward} 积分'
            separator = '，'
        if balance:
            message += f'{separator}当前可用积分 {balance}'
        return {'success': True, 'message': message}
    except (json.JSONDecodeError, requests.exceptions.JSONDecodeError):
        return {'success': False, 'message': 'YuChen 接口返回的 JSON 格式错误'}
    except requests.RequestException as e:
        return {'success': False, 'message': f'请求失败: {str(e)}'}
    finally:
        session.close()


def run(accounts: list) -> dict:
    """使用公共执行器逐账号完成 YuChen 签到。"""
    return run_accounts(SERVICE_NAME, accounts, ACCOUNT_FIELDS, checkin, "username")
