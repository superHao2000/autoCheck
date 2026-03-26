import json
import os
import os.path
import shutil
import sys
from json import JSONDecodeError
from typing import Any, Dict, List, Optional

import yaml


# ============ 字段映射配置 (实现配置与代码解耦) ============
# 允许配置文件使用任意键名，代码通过映射获取值
SERVICE_FIELD_MAPPING = {
    "YuChen": {
        "url": ["url", "base_url", "domain"],
        "username": ["username", "user", "account"],
        "password": ["password", "pass", "pwd"],
    },
    "GlaDos": {
        "cookies": ["cookies", "cookie"],
    },
    "AirPort": {
        "base_url": ["base_url", "url", "site"],
        "email": ["email", "username", "user", "account"],
        "password": ["password", "pass", "pwd"],
    },
    "JavBus": {
        "url": ["url", "site_url", "domain"],
        "cookies": ["cookies", "cookie"],
    },
    "_common": {
        "user_agent": ["user_agent", "user-agent", "ua"],
    }
}


def get_field_value(account: Dict[str, Any], service: str) -> Dict[str, Any]:
    """
    根据映射获取账号信息
    
    Args:
        account: 原始账号配置字典
        service: 服务名称
        
    Returns:
        标准化后的账号字典
    """
    result = {}
    mapping = SERVICE_FIELD_MAPPING.get(service, {})
    common_mapping = SERVICE_FIELD_MAPPING.get("_common", {})
    
    # 合并服务专属映射和通用映射
    all_mappings = {**common_mapping, **mapping}
    
    for std_key, alt_keys in all_mappings.items():
        for alt_key in alt_keys:
            if alt_key in account:
                result[std_key] = account[alt_key]
                break
    
    return result


def normalize_account(account: Dict[str, Any], service: str) -> Dict[str, Any]:
    """
    标准化账号配置
    
    允许配置文件使用任意字段名，自动映射到标准字段
    """
    normalized = get_field_value(account, service)
    # 添加原始字段（保留兼容性）
    for k, v in account.items():
        if k not in normalized:
            normalized[k] = v
    return normalized

# 判断是否在 GitHub Actions 环境中运行
IS_GITHUB_ACTIONS = os.environ.get('GITHUB_ACTIONS', '').lower() == 'true'

from utils.logger import log

ROOT_PATH = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
"""主目录"""
CONFIG_DIR = os.path.join(ROOT_PATH, 'config')
"""配置目录"""
CONFIG_PATH = os.path.join(ROOT_PATH, 'config.yaml')
"""旧版数据文件目录 (兼容)"""
CONFIG_PATH_BAK = os.path.join(ROOT_PATH, 'config.yaml.bak')

# 服务配置文件路径
SERVICE_CONFIG_DIR = os.path.join(CONFIG_DIR, 'services')
YUCHEN_CONFIG = os.path.join(SERVICE_CONFIG_DIR, 'yuchen.yaml')
GLADOS_CONFIG = os.path.join(SERVICE_CONFIG_DIR, 'glados.yaml')
AIRPORT_CONFIG = os.path.join(SERVICE_CONFIG_DIR, 'airport.yaml')
JAVBUS_CONFIG = os.path.join(SERVICE_CONFIG_DIR, 'javbus.yaml')
PUSH_CONFIG = os.path.join(CONFIG_DIR, 'push.yaml')


def read_yaml(file_path: str) -> Optional[Dict[str, Any]]:
    """
    读取 YAML 配置文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        解析后的字典，文件不存在返回 None
    """
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except (ValidationError, JSONDecodeError):
        log.exception(f"读取配置文件失败: {file_path}")
        raise
    except Exception:
        log.exception(f"读取配置文件失败: {file_path}")
        raise


def load_service_config(config_path: str) -> List[Dict[str, Any]]:
    """
    加载服务配置
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        账号列表
    """
    config = read_yaml(config_path)
    if config:
        # 支持 'accounts' 或直接是列表的格式
        if isinstance(config, list):
            return config
        return config.get('accounts', [])
    return []


def load_service_accounts(service: str, config_path: str) -> List[Dict[str, Any]]:
    """
    加载并标准化服务账号配置
    
    Args:
        service: 服务名称 (YuChen, GlaDos, AirPort, JavBus)
        config_path: 配置文件路径
        
    Returns:
        标准化后的账号列表
    """
    raw_accounts = load_service_config(config_path)
    # 应用字段映射，标准化每个账号
    return [normalize_account(acc, service) for acc in raw_accounts]


def load_github_service_accounts(service: str, env_key: str) -> List[Dict[str, Any]]:
    """
    从 GitHub Actions 环境变量加载并标准化服务账号配置
    
    Args:
        service: 服务名称
        env_key: 环境变量键名
        
    Returns:
        标准化后的账号列表
    """
    env_val = os.environ.get(env_key, '')
    if not env_val:
        return []
    try:
        raw_accounts = json.loads(env_val)
        if isinstance(raw_accounts, list):
            return [normalize_account(acc, service) for acc in raw_accounts]
    except json.JSONDecodeError:
        log.warning(f"GitHub 环境变量 {env_key} JSON 解析失败")
    return []


def load_push_config() -> Dict[str, Any]:
    """
    加载推送配置
    
    Returns:
        推送配置字典
    """
    # 优先从新配置文件加载
    push_config = read_yaml(PUSH_CONFIG)
    if push_config:
        return push_config
    
    # 回退到旧配置
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
                return config.get('PUSH', {})
        except Exception:
            pass
    return {}


def get_user_agent() -> str:
    """
    获取 User-Agent
    
    Returns:
        User-Agent 字符串
    """
    # 优先从 push.yaml 加载
    push_config = read_yaml(PUSH_CONFIG)
    if push_config and push_config.get('USER_AGENT'):
        return push_config['USER_AGENT']
    
    # 回退到旧配置
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
                return config.get('USER_AGENT', '')
        except Exception:
            pass
    return ''


# ============ 加载配置 ============

def load_github_config() -> Dict[str, Any]:
    """
    从 GitHub Actions 环境变量加载配置
    
    环境变量格式:
    - YUCHEN_ACCOUNTS: JSON 字符串数组
    - GLADOS_ACCOUNTS: JSON 字符串数组
    - AIRPORT_ACCOUNTS: JSON 字符串数组
    - JAVBUS_ACCOUNTS: JSON 字符串数组
    - PUSH_CONFIG: JSON 对象
    - USER_AGENT: 字符串
    
    Returns:
        包含所有配置的字典
    """
    config = {
        'YUCHEN_ACCOUNTS': [],
        'GLADOS_ACCOUNTS': [],
        'AIRPORT_ACCOUNTS': [],
        'JAVBUS_ACCOUNTS': [],
        'PUSH': {},
        'USER_AGENT': ''
    }
    
    # 读取各服务账号 (JSON 字符串)
    for key in ['YUCHEN_ACCOUNTS', 'GLADOS_ACCOUNTS', 'AIRPORT_ACCOUNTS', 'JAVBUS_ACCOUNTS']:
        env_val = os.environ.get(key, '')
        if env_val:
            try:
                config[key] = json.loads(env_val)
            except json.JSONDecodeError:
                log.warning(f"GitHub 环境变量 {key} JSON 解析失败")
    
    # 读取推送配置
    push_env = os.environ.get('PUSH_CONFIG', '')
    if push_env:
        try:
            config['PUSH'] = json.loads(push_env)
        except json.JSONDecodeError:
            log.warning("GitHub 环境变量 PUSH_CONFIG JSON 解析失败")
    
    # 读取 User-Agent
    config['USER_AGENT'] = os.environ.get('USER_AGENT', '')
    
    return config


def load_all_configs() -> None:
    """
    加载所有配置 (全局变量)
    
    加载优先级:
    1. GitHub Actions 环境变量 (如果 GITHUB_ACTIONS=true)
    2. config/services/ 下的独立配置文件
    3. 旧的 config.yaml (向后兼容)
    """
    global ACCOUNT, PUSH, USER_AGENT
    global YUCHEN_ACCOUNTS, GLADOS_ACCOUNTS, AIRPORT_ACCOUNTS, JAVBUS_ACCOUNTS
    
    # 初始化
    ACCOUNT = {}
    PUSH = {}
    USER_AGENT = ''
    YUCHEN_ACCOUNTS = []
    GLADOS_ACCOUNTS = []
    AIRPORT_ACCOUNTS = []
    JAVBUS_ACCOUNTS = []
    
    # 1. 优先: GitHub Actions 环境变量
    if IS_GITHUB_ACTIONS:
        log.info("检测到 GitHub Actions 环境，使用环境变量配置")
        
        # 使用标准化的账号加载函数
        YUCHEN_ACCOUNTS = load_github_service_accounts('YuChen', 'YUCHEN_ACCOUNTS')
        GLADOS_ACCOUNTS = load_github_service_accounts('GlaDos', 'GLADOS_ACCOUNTS')
        AIRPORT_ACCOUNTS = load_github_service_accounts('AirPort', 'AIRPORT_ACCOUNTS')
        JAVBUS_ACCOUNTS = load_github_service_accounts('JavBus', 'JAVBUS_ACCOUNTS')
        
        if YUCHEN_ACCOUNTS:
            ACCOUNT['YuChen'] = YUCHEN_ACCOUNTS
        if GLADOS_ACCOUNTS:
            ACCOUNT['GlaDos'] = GLADOS_ACCOUNTS
        if AIRPORT_ACCOUNTS:
            ACCOUNT['AirPort'] = AIRPORT_ACCOUNTS
        if JAVBUS_ACCOUNTS:
            ACCOUNT['JavBus'] = JAVBUS_ACCOUNTS
        
        # 加载推送配置
        push_env = os.environ.get('PUSH_CONFIG', '')
        if push_env:
            try:
                PUSH = json.loads(push_env)
            except json.JSONDecodeError:
                log.warning("GitHub 环境变量 PUSH_CONFIG JSON 解析失败")
        
        # 加载 User-Agent
        USER_AGENT = os.environ.get('USER_AGENT', '')
        
    else:
        # 2. 加载服务配置 (新配置优先)
        # 使用标准化账号加载函数
        yuchen = load_service_accounts('YuChen', YUCHEN_CONFIG)
        glados = load_service_accounts('GlaDos', GLADOS_CONFIG)
        airport = load_service_accounts('AirPort', AIRPORT_CONFIG)
        javbus = load_service_accounts('JavBus', JAVBUS_CONFIG)
        
        # 如果新配置存在则使用，否则尝试旧配置
        if yuchen or glados or airport or javbus:
            # 使用新配置
            if yuchen:
                ACCOUNT['YuChen'] = yuchen
                YUCHEN_ACCOUNTS = yuchen
            if glados:
                ACCOUNT['GlaDos'] = glados
                GLADOS_ACCOUNTS = glados
            if airport:
                ACCOUNT['AirPort'] = airport
                AIRPORT_ACCOUNTS = airport
            if javbus:
                ACCOUNT['JavBus'] = javbus
                JAVBUS_ACCOUNTS = javbus
        elif os.path.exists(CONFIG_PATH):
            # 回退到旧配置
            try:
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    Conf = yaml.safe_load(f) or {}
                    ACCOUNT = Conf.get('ACCOUNT', {})
                    PUSH = Conf.get('PUSH', {})
                    USER_AGENT = Conf.get('USER_AGENT', '')
                    # 兼容旧结构
                    YUCHEN_ACCOUNTS = ACCOUNT.get('YuChen', [])
                    GLADOS_ACCOUNTS = ACCOUNT.get('GlaDos', [])
                    AIRPORT_ACCOUNTS = ACCOUNT.get('AirPort', [])
                    JAVBUS_ACCOUNTS = ACCOUNT.get('JavBus', [])
            except Exception:
                log.warning("旧配置文件加载失败")
        else:
            # 没有配置文件，提示用户
            pass
        
        # 加载推送配置
        PUSH = load_push_config()
        
        # 加载 User-Agent
        USER_AGENT = get_user_agent()
    
    log.debug(f"已加载配置: YuChen={len(YUCHEN_ACCOUNTS)}, GlaDos={len(GLADOS_ACCOUNTS)}, AirPort={len(AIRPORT_ACCOUNTS)}, JavBus={len(JAVBUS_ACCOUNTS)}")


def write_data() -> None:
    """从备份文件生成配置文件"""
    source = CONFIG_PATH_BAK
    destination = CONFIG_PATH
    try:
        if os.path.exists(source):
            shutil.copyfile(source, destination)
            log.info(f"配置文件 {source} 已成功生成")
        else:
            log.info(f"配置文件备份 {source} 不存在。")
    except Exception as e:
        log.debug(f"发生错误: {e}")


# 初始化配置
if os.path.exists(CONFIG_PATH) or os.path.exists(YUCHEN_CONFIG):
    load_all_configs()
else:
    write_data()
    log.info("请填写配置文件后重新启动")
    sys.exit()


# ============ 向后兼容的导出 ============
# 保持旧代码的兼容性，直接使用全局变量


if __name__ == '__main__':
    print("YuChen accounts:", YUCHEN_ACCOUNTS)
    print("GlaDos accounts:", GLADOS_ACCOUNTS)
    print("AirPort accounts:", AIRPORT_ACCOUNTS)
    print("JavBus accounts:", JAVBUS_ACCOUNTS)
    print("PUSH config:", PUSH)
    print("USER_AGENT:", USER_AGENT)