"""AirPort 签到服务：先登录获取会话，再调用用户签到接口。"""

import requests

from utils import config
from utils.service_runner import run_accounts


# 自动发现服务时使用的元数据；可被新服务实现作为模板。
SERVICE_NAME = "AirPort"
CONFIG_FILENAME = "airport.json"
ENV_KEY = "AIRPORT_ACCOUNTS"
ACCOUNT_FIELDS = ("base_url", "email", "password")
AUTH_FAILURE_MARKERS = (
    "账号或密码",
    "邮箱或密码",
    "密码错误",
    "密码不正确",
    "账号不存在",
    "用户不存在",
    "bad password",
    "invalid password",
    "invalid credentials",
    "incorrect password",
)


def _is_auth_failure(message: str) -> bool:
    """判断登录响应是否明确拒绝账号密码，临时服务错误仍允许重试。"""
    lowered = message.lower()
    return any(marker in lowered for marker in AUTH_FAILURE_MARKERS)


def checkin(base_url: str, email: str, password: str) -> dict:
    """登录 AirPort 站点并签到，兼容 JSON 与旧版文本响应。"""
    # 统一移除末尾斜杠，避免生成双斜杠接口地址。
    login_url = f"{base_url.rstrip('/')}/auth/login"
    checkin_url = f"{base_url.rstrip('/')}/user/checkin"
    
    headers = {
        'User-Agent': config.USER_AGENT or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    try:
        # 登录与签到必须共享 Session，才能复用服务端设置的 Cookie。
        login_data = {
            'email': email,
            'password': password
        }
        login_resp = session.post(login_url, data=login_data, timeout=30)
        
        # 401/403 表示凭据被明确拒绝，其他状态交给公共执行器重试。
        if login_resp.status_code != 200:
            result = {'success': False, 'message': f'登录请求失败: {login_resp.status_code}'}
            if login_resp.status_code in (401, 403):
                result['retryable'] = False
            return result
        
        # 尝试解析 JSON 响应
        try:
            login_json = login_resp.json()
            # 新版接口使用 success 布尔值，旧版可能只在正文中给出提示。
            if login_json.get('success') is True:
                pass  # 登录成功，继续签到。
            elif login_json.get('success') is False:
                msg = login_json.get('message', '登录失败')
                result = {'success': False, 'message': f'登录失败: {msg}'}
                if _is_auth_failure(str(msg)):
                    result['retryable'] = False
                return result
            else:
                # 旧版 API 未提供稳定 JSON 结构，回退到文本判断。
                if '登录成功' in login_resp.text or 'success' in login_resp.text.lower():
                    pass
                else:
                    return {'success': False, 'message': f'登录失败: {login_resp.text[:50]}'}
        except requests.exceptions.JSONDecodeError:
            # 非 JSON 响应同样使用旧版文本特征判断。
            if '登录成功' in login_resp.text or login_resp.status_code == 302:
                pass
            else:
                return {'success': False, 'message': f'登录失败: {login_resp.text[:50]}'}
        
        # 仅在登录确认成功后请求签到接口。
        checkin_resp = session.post(checkin_url, timeout=30)
        
        try:
            checkin_json = checkin_resp.json()
            if checkin_json.get('success') is True:
                return {'success': True, 'message': checkin_json.get('message', '签到成功')}
            else:
                msg = checkin_json.get('message', checkin_json.get('msg', ''))
                if '已签到' in msg:
                    return {'success': True, 'message': msg}
                return {'success': False, 'message': msg or '签到失败'}
        except requests.exceptions.JSONDecodeError:
            if '签到成功' in checkin_resp.text:
                return {'success': True, 'message': '签到成功'}
            return {'success': False, 'message': f'签到失败: {checkin_resp.text[:50]}'}
            
    except requests.exceptions.Timeout:
        return {'success': False, 'message': '请求超时'}
    except requests.exceptions.RequestException as e:
        return {'success': False, 'message': f'请求失败: {str(e)}'}


def run(accounts: list) -> dict:
    """使用公共执行器逐账号完成 AirPort 登录与签到。"""
    return run_accounts(SERVICE_NAME, accounts, ACCOUNT_FIELDS, checkin, "email")
