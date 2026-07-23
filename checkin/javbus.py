"""JavBus 签到服务：使用登录 Cookie 调用站点签到地址。"""

import requests

from utils import log, config


# 自动发现服务时使用的元数据；文件名对应默认配置文件名。
SERVICE_NAME = "JavBus"
CONFIG_FILENAME = "javbus.json"
ENV_KEY = "JAVBUS_ACCOUNTS"


def checkin(url: str, cookies: str) -> dict:
    """携带 Cookie 请求 JavBus 签到接口，兼容 JSON 和文本响应。"""
    checkin_url = f"{url.rstrip('/')}/checkin"
    
    headers = {
        'User-Agent': config.USER_AGENT or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Cookie': cookies,
        'Referer': url
    }
    
    try:
        response = requests.post(checkin_url, headers=headers, timeout=30)
        response.encoding = 'utf-8'
        
        try:
            # 首选接口的 JSON 状态；已签到同样视为本次任务成功。
            json_data = response.json()
            if json_data.get('success') is True:
                return {'success': True, 'message': json_data.get('message', '签到成功')}
            else:
                msg = json_data.get('message', json_data.get('msg', ''))
                if '已签到' in msg:
                    return {'success': True, 'message': msg}
                return {'success': False, 'message': msg or '签到失败'}
        except requests.exceptions.JSONDecodeError:
            # 部分镜像站返回文本页面，回退到关键字判断。
            text = response.text
            if '成功' in text or 'success' in text.lower():
                return {'success': True, 'message': '签到成功'}
            elif '已签到' in text:
                return {'success': True, 'message': '今日已签到'}
            return {'success': False, 'message': f'签到失败: {text[:50]}'}
            
    except requests.exceptions.Timeout:
        return {'success': False, 'message': '请求超时'}
    except requests.exceptions.RequestException as e:
        return {'success': False, 'message': f'请求失败: {str(e)}'}


def run(accounts: list) -> dict:
    """逐账号执行 JavBus 签到；账号配置错误不会影响其他账号。"""
    results = {
        'total': len(accounts),
        'success': 0,
        'failed': 0,
        'details': []
    }
    
    for i, account in enumerate(accounts):
        url = account.get('url', account.get('site_url', ''))
        cookies = account.get('cookies', account.get('cookie', ''))
        
        if not url or not cookies:
            result = {
                'username': f'账号{i+1}',
                'success': False,
                'message': '缺少必要配置 (url/cookies)'
            }
            results['failed'] += 1
            results['details'].append(result)
            log.warning(f"JavBus 账号 {i+1} 配置不完整，跳过")
            continue
        
        log.info(f"JavBus 开始签到账号 {i+1}")
        result = checkin(url, cookies)
        result['username'] = f'账号{i+1}'
        
        if result.get('success'):
            results['success'] += 1
            log.info(f"JavBus 签到成功: 账号{i+1}")
        else:
            results['failed'] += 1
            log.warning(f"JavBus 签到失败: 账号{i+1} - {result.get('message', '未知错误')}")
        
        results['details'].append(result)
    
    return results
