"""GlaDos 签到服务：使用登录 Cookie 调用固定签到接口。"""

import requests

from utils import config
from utils.service_runner import run_accounts


# 自动发现服务时使用的元数据；文件名同时决定默认本地配置路径。
SERVICE_NAME = "GlaDos"
CONFIG_FILENAME = "glados.json"
ENV_KEY = "GLADOS_ACCOUNTS"
ACCOUNT_FIELDS = ("cookies",)


def checkin(cookies: str) -> dict:
    """携带 Cookie 请求 GlaDos 签到接口，并识别“已签到”状态。"""
    url = 'https://glados.one/api/user/checkin'
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': config.USER_AGENT or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Cookie': cookies,
        'Referer': 'https://glados.one/'
    }
    payload = {
        'token': 'glados_network'
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.encoding = 'utf-8'
        
        try:
            json_data = response.json()
            code = json_data.get('code', -1)
            message = json_data.get('message', '')
            
            # 不同接口版本可能仅通过 code 或消息文本标识成功。
            if code == 0:
                return {'success': True, 'message': message or '签到成功'}
            elif 'already checked' in message.lower() or '已签到' in message:
                return {'success': True, 'message': message}
            else:
                return {'success': False, 'message': message}
        except requests.exceptions.JSONDecodeError:
            return {'success': False, 'message': f'解析失败: {response.text[:50]}'}
            
    except requests.RequestException as e:
        return {'success': False, 'message': f'请求失败: {str(e)}'}


def run(accounts: list) -> dict:
    """使用公共执行器逐账号完成 GlaDos 签到。"""
    return run_accounts(SERVICE_NAME, accounts, ACCOUNT_FIELDS, checkin)
