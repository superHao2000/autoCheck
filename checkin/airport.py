import requests

from ..utils import log, config


def checkin(base_url: str, email: str, password: str) -> dict:
    """
    Airport 签到
    
    Args:
        base_url: 站点地址
        email: 邮箱/用户名
        password: 密码
        
    Returns:
        签到结果字典
    """
    # 构造登录 URL
    login_url = f"{base_url.rstrip('/')}/auth/login"
    checkin_url = f"{base_url.rstrip('/')}/user/checkin"
    
    headers = {
        'User-Agent': config.USER_AGENT or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    try:
        # 1. 登录
        login_data = {
            'email': email,
            'password': password
        }
        login_resp = session.post(login_url, data=login_data, timeout=30)
        
        # 检查登录结果
        if login_resp.status_code != 200:
            return {'success': False, 'message': f'登录请求失败: {login_resp.status_code}'}
        
        # 尝试解析 JSON 响应
        try:
            login_json = login_resp.json()
            # 检查是否登录成功
            if login_json.get('success') is True:
                pass  # 登录成功，继续签到
            elif login_json.get('success') is False:
                msg = login_json.get('message', '登录失败')
                return {'success': False, 'message': f'登录失败: {msg}'}
            else:
                # 可能是旧版 API，直接检查文本
                if '登录成功' in login_resp.text or 'success' in login_resp.text.lower():
                    pass
                else:
                    return {'success': False, 'message': f'登录失败: {login_resp.text[:50]}'}
        except Exception:
            # 非 JSON 响应，检查文本
            if '登录成功' in login_resp.text or login_resp.status_code == 302:
                pass
            else:
                return {'success': False, 'message': f'登录失败: {login_resp.text[:50]}'}
        
        # 2. 执行签到
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
        except Exception:
            if '签到成功' in checkin_resp.text:
                return {'success': True, 'message': '签到成功'}
            return {'success': False, 'message': f'签到失败: {checkin_resp.text[:50]}'}
            
    except requests.exceptions.Timeout:
        return {'success': False, 'message': '请求超时'}
    except requests.exceptions.RequestException as e:
        return {'success': False, 'message': f'请求失败: {str(e)}'}
    except Exception as e:
        return {'success': False, 'message': f'未知错误: {str(e)}'}


def run(accounts: list) -> dict:
    """
    运行签到任务
    
    Args:
        accounts: 账号列表，每个账号应为包含 base_url, email, password 的字典
        
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
        base_url = account.get('base_url', account.get('url', ''))
        email = account.get('email', account.get('username', account.get('user', '')))
        password = account.get('password', account.get('pass', ''))
        
        if not base_url or not email or not password:
            result = {
                'username': email or f'账号{i+1}',
                'success': False,
                'message': '缺少必要配置 (base_url/email/password)'
            }
            results['failed'] += 1
            results['details'].append(result)
            log.warning(f"AirPort 账号 {email or i+1} 配置不完整，跳过")
            continue
        
        log.info(f"AirPort 开始签到: {email}")
        result = checkin(base_url, email, password)
        result['username'] = email
        
        if result.get('success'):
            results['success'] += 1
            log.info(f"AirPort 签到成功: {email}")
        else:
            results['failed'] += 1
            log.warning(f"AirPort 签到失败: {email} - {result.get('message', '未知错误')}")
        
        results['details'].append(result)
    
    return results