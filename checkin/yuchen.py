import requests

from ..utils import log, config


def checkin(url: str, username: str, password: str) -> dict:
    """
    签到请求
    
    Args:
        url: 签到地址
        username: 用户名
        password: 密码
        
    Returns:
        签到结果字典
    """
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
        
        # 解析返回
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
            except Exception:
                return {'success': False, 'message': text[:50]}
                
    except Exception as e:
        return {'success': False, 'message': f'请求失败: {str(e)}'}


def run(accounts: list) -> dict:
    """
    运行签到任务
    
    Args:
        accounts: 账号列表，每个账号应为包含 username, password, url 的字典
        
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
        # 提取账号信息
        url = account.get('url', '')
        username = account.get('username', account.get('user', ''))
        password = account.get('password', account.get('pass', ''))
        
        # 检查必要字段
        if not url or not username or not password:
            result = {
                'username': username or f'账号{i+1}',
                'success': False,
                'message': '缺少必要配置 (url/username/password)'
            }
            results['failed'] += 1
            results['details'].append(result)
            log.warning(f"YuChen 账号 {username or i+1} 配置不完整，跳过")
            continue
        
        # 执行签到
        log.info(f"YuChen 开始签到: {username}")
        result = checkin(url, username, password)
        
        # 记录结果
        result['username'] = username
        if result.get('success'):
            results['success'] += 1
            log.info(f"YuChen 签到成功: {username}")
        else:
            results['failed'] += 1
            log.warning(f"YuChen 签到失败: {username} - {result.get('message', '未知错误')}")
        
        results['details'].append(result)
    
    return results