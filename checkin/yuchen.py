"""YuChen 签到服务：以账号密码提交站点提供的签到地址。"""

import requests

from utils import log, config


# 自动发现服务时使用的元数据；新增服务可按此约定声明。
SERVICE_NAME = "YuChen"
CONFIG_FILENAME = "yuchen.json"
ENV_KEY = "YUCHEN_ACCOUNTS"


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
            except Exception:
                return {'success': False, 'message': text[:50]}
                
    except Exception as e:
        return {'success': False, 'message': f'请求失败: {str(e)}'}


def run(accounts: list) -> dict:
    """逐账号执行 YuChen 签到；配置或请求失败不影响后续账号。"""
    results = {
        'total': len(accounts),
        'success': 0,
        'failed': 0,
        'details': []
    }
    
    for i, account in enumerate(accounts):
        # 同时兼容未经过配置标准化的旧字段。
        url = account.get('url', '')
        username = account.get('username', account.get('user', ''))
        password = account.get('password', account.get('pass', ''))
        
        # 缺少凭据属于单账号配置错误，记录后继续处理下一账号。
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
        
        # checkin 已将网络和响应解析错误转换为结果字典。
        log.info(f"YuChen 开始签到: {username}")
        result = checkin(url, username, password)
        
        # 每个账号均保存明细，供入口汇总和推送展示。
        result['username'] = username
        if result.get('success'):
            results['success'] += 1
            log.info(f"YuChen 签到成功: {username}")
        else:
            results['failed'] += 1
            log.warning(f"YuChen 签到失败: {username} - {result.get('message', '未知错误')}")
        
        results['details'].append(result)
    
    return results
