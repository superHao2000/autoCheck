"""YuChen 签到服务：以账号密码提交站点提供的签到地址。"""

import requests

from utils import config
from utils.service_runner import run_accounts


# 自动发现服务时使用的元数据；新增服务可按此约定声明。
SERVICE_NAME = "YuChen"
CONFIG_FILENAME = "yuchen.json"
ENV_KEY = "YUCHEN_ACCOUNTS"
ACCOUNT_FIELDS = {
    "url": ("url",),
    "username": ("username",),
    "password": ("password",),
}


def checkin(url: str, username: str, password: str) -> dict:
    """向 YuChen 签到接口提交账号密码，并规范化不同响应格式。"""
    data = {
        'username': username,
        'password': password
    }
    headers = {}
    if config.USER_AGENT:
        headers['User-Agent'] = config.USER_AGENT
    
    try:
        response = requests.post(url, data=data, headers=headers, timeout=30)
        response.encoding = 'utf-8'
        
        # 部分站点返回 HTML/文本，先匹配常见关键字再尝试 JSON。
        text = response.text
        if '签到成功' in text or '已签到' in text or 'success' in text.lower():
            return {'success': True, 'message': '签到成功'}
        elif '密码错误' in text or '账号错误' in text:
            return {'success': False, 'message': '账号或密码错误'}
        else:
            # 尝试解析 JSON
            try:
                json_data = response.json()
                msg = json_data.get('message') or json_data.get('msg') or text[:50]
                return {'success': json_data.get('ret') == 1 or json_data.get('success'), 'message': msg}
            except requests.exceptions.JSONDecodeError:
                return {'success': False, 'message': text[:50]}
                
    except requests.RequestException as e:
        return {'success': False, 'message': f'请求失败: {str(e)}'}


def run(accounts: list) -> dict:
    """使用公共执行器逐账号完成 YuChen 签到。"""
    return run_accounts(SERVICE_NAME, accounts, ACCOUNT_FIELDS, checkin, "username")
