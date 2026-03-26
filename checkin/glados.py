import requests

from ..utils import log, config


def checkin(cookies: str) -> dict:
    """
    GlaDos 签到
    
    Args:
        cookies: 登录 Cookie
        
    Returns:
        签到结果字典
    """
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
            
            if code == 0 or 'Checkin' in message or '签到' in message:
                # 提取剩余天数
                msg = message
                if 'Left days' in message or '剩余' in message:
                    msg = message
                return {'success': True, 'message': msg or '签到成功'}
            elif 'already' in message.lower() or '已签到' in message:
                return {'success': True, 'message': message}
            else:
                return {'success': False, 'message': message}
        except Exception:
            return {'success': False, 'message': f'解析失败: {response.text[:50]}'}
            
    except Exception as e:
        return {'success': False, 'message': f'请求失败: {str(e)}'}


def run(accounts: list) -> dict:
    """
    运行签到任务
    
    Args:
        accounts: 账号列表，每个账号应为包含 cookies 的字典
        
    Returns:
        结果汇总
    """
    results = {
        'total': len(accounts),
        'success': 0,
        'failed': 0,
        'details': []
    }
    
    for i, account in enumerate(accounts):
        cookies = account.get('cookies', account.get('cookie', ''))
        
        if not cookies:
            result = {
                'username': f'账号{i+1}',
                'success': False,
                'message': '缺少 cookies 配置'
            }
            results['failed'] += 1
            results['details'].append(result)
            log.warning(f"GlaDos 账号 {i+1} 缺少 cookies，跳过")
            continue
        
        log.info(f"GlaDos 开始签到账号 {i+1}")
        result = checkin(cookies)
        result['username'] = f'账号{i+1}'
        
        if result.get('success'):
            results['success'] += 1
            log.info(f"GlaDos 签到成功: 账号{i+1}")
        else:
            results['failed'] += 1
            log.warning(f"GlaDos 签到失败: 账号{i+1} - {result.get('message', '未知错误')}")
        
        results['details'].append(result)
    
    return results