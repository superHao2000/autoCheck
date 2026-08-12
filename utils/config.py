"""配置加载器：统一处理本地 JSON、单服务环境变量和聚合环境变量。"""

import json
import os
from pathlib import Path
from typing import Any

from utils.logger import log


# 所有配置路径均相对项目根目录计算，避免依赖启动时的工作目录。
ROOT_PATH = Path(__file__).resolve().parents[1]
SERVICE_CONFIG_DIR = ROOT_PATH / "config"
PUSH_CONFIG = ROOT_PATH / "config" / "push.json"
ACCOUNTS_BUNDLE_ENV_KEY = "AUTOCHECK_ACCOUNTS"
# 仅为站点地址在同一账号组中固定的服务声明可继承字段；不提供字段别名。
SERVICE_SHARED_FIELDS = {"YuChen": ("url",), "GlaDos": ("url",)}
# 用于判断同一服务中的同一账号。字段值不会写入日志，避免泄露凭据。
SERVICE_ACCOUNT_ID_FIELDS = {
    "YuChen": ("url", "username"),
    "GlaDos": ("url", "cookies"),
    "AirPort": ("base_url", "email"),
    "JavBus": ("url", "cookies"),
}

# 以下值仅由 load_all_configs 显式刷新，不在模块导入时读取文件或退出进程。
ACCOUNT: dict[str, list[dict[str, Any]]] = {}
PUSH: dict[str, Any] = {}
USER_AGENT = ""


def read_json(path: Path) -> Any:
    """读取一个 JSON 文件；不存在返回 None，格式错误给出包含路径的异常。"""
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(f"配置文件格式错误: {path}") from exc


def _accounts_from_value(value: Any, source: str, service: str) -> list[dict[str, Any]]:
    """校验账号列表格式，并为指定服务合并顶层标准共享字段。"""
    shared_fields: dict[str, Any] = {}
    if isinstance(value, dict):
        # YuChen 的站点地址可放在顶层；账号对象的同名字段优先级更高。
        shared_fields = {
            field: value[field]
            for field in SERVICE_SHARED_FIELDS.get(service, ())
            if value.get(field)
        }
        value = value.get("accounts", [])
    if value is None:
        return []
    if not isinstance(value, list):
        log.warning("%s 的账号配置必须是列表，已跳过", source)
        return []

    accounts: list[dict[str, Any]] = []
    for index, account in enumerate(value, start=1):
        if not isinstance(account, dict):
            log.warning("%s 第 %s 个账号不是对象，已跳过", source, index)
            continue
        # 仅合并已声明的标准共享字段；必填字段仍由对应服务验证。
        accounts.append({**shared_fields, **account})
    return accounts


def _load_accounts_bundle() -> dict[str, Any]:
    """解析可选的 AUTOCHECK_ACCOUNTS 聚合 JSON 对象。"""
    raw = os.environ.get(ACCOUNTS_BUNDLE_ENV_KEY)
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        log.warning("环境变量 %s 不是有效 JSON，已忽略", ACCOUNTS_BUNDLE_ENV_KEY)
        return {}
    if not isinstance(value, dict):
        log.warning("环境变量 %s 必须是 JSON 对象，已忽略", ACCOUNTS_BUNDLE_ENV_KEY)
        return {}
    return value


def _account_identity(service: str, account: dict[str, Any]) -> str:
    """生成仅供内存比较的账号标识，不将标识或字段值输出到日志。"""
    fields = SERVICE_ACCOUNT_ID_FIELDS.get(service)
    if fields and all(account.get(field) for field in fields):
        value = {field: account[field] for field in fields}
    else:
        # 未知服务或字段不完整时，使用完整对象，避免把不同的不完整配置误判为重复。
        value = account
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _merge_accounts(
    service: str, sources: list[tuple[str, list[dict[str, Any]]]],
) -> list[dict[str, Any]]:
    """按来源优先级合并账号，并跳过已由高优先级来源提供的重复账号。"""
    accounts: list[dict[str, Any]] = []
    identities: set[str] = set()
    for source, source_accounts in sources:
        for account in source_accounts:
            identity = _account_identity(service, account)
            if identity in identities:
                log.info("%s 检测到重复账号，已跳过来自 %s 的低优先级配置", service, source)
                continue
            identities.add(identity)
            accounts.append(account)
    return accounts


def load_service_accounts(service: str, filename: str, env_key: str) -> list[dict[str, Any]]:
    """合并三类账号来源；高优先级账号优先，重复账号只保留一次。"""
    sources: list[tuple[str, list[dict[str, Any]]]] = []

    env_value = os.environ.get(env_key)
    if env_value:
        try:
            source = f"环境变量 {env_key}"
            sources.append((source, _accounts_from_value(json.loads(env_value), source, service)))
        except json.JSONDecodeError:
            log.warning("环境变量 %s 不是有效 JSON，已跳过该来源", env_key)

    bundle = _load_accounts_bundle()
    # 聚合配置优先使用模块名，也兼容显示名和单服务环境变量名。
    bundle_keys = (Path(filename).stem, service, env_key)
    for bundle_key in bundle_keys:
        if bundle_key in bundle:
            source = f"环境变量 {ACCOUNTS_BUNDLE_ENV_KEY}.{bundle_key}"
            sources.append((source, _accounts_from_value(bundle[bundle_key], source, service)))
            break

    # 仅加载 config 根目录的真实 JSON；services 中的模板绝不作为运行期凭据。
    config_path = SERVICE_CONFIG_DIR / filename
    try:
        local_value = read_json(config_path)
    except ValueError as exc:
        # 本地文件损坏不应使可用的环境变量账号失效。
        log.warning("%s 配置加载失败，已跳过该来源：%s", service, exc)
    else:
        if local_value is not None:
            sources.append((str(config_path), _accounts_from_value(local_value, str(config_path), service)))
    return _merge_accounts(service, sources)


def load_local_service_accounts(service: str, filename: str) -> list[dict[str, Any]]:
    """只从指定本地 JSON 文件加载账号，供真实测试使用。

    此函数刻意不读取环境变量，确保手动测试不会误用 CI 或青龙的账号。
    """
    config_path = SERVICE_CONFIG_DIR / filename
    local_value = read_json(config_path)
    return _accounts_from_value(local_value, str(config_path), service) if local_value is not None else []


def load_push_config() -> dict[str, Any]:
    """加载推送配置；环境变量 PUSH_CONFIG 优先于本地 push.json。"""
    raw = os.environ.get("PUSH_CONFIG")
    if raw:
        try:
            value = json.loads(raw)
            return value if isinstance(value, dict) else {}
        except json.JSONDecodeError:
            log.warning("环境变量 PUSH_CONFIG 不是有效 JSON，已忽略")
            return {}
    value = read_json(PUSH_CONFIG)
    return value if isinstance(value, dict) else {}


def load_all_configs(services: list[Any], local_only: bool = False) -> None:
    """为已发现服务刷新运行期配置，并隔离单个服务的配置错误。"""
    global ACCOUNT, PUSH, USER_AGENT

    accounts_by_service: dict[str, list[dict[str, Any]]] = {}
    for service in services:
        try:
            if local_only:
                accounts = load_local_service_accounts(service.name, service.config_filename)
            else:
                accounts = load_service_accounts(service.name, service.config_filename, service.env_key)
        except ValueError as exc:
            # 格式错误只影响当前服务，其他已配置服务仍可继续运行。
            log.error("%s 配置加载失败，已跳过：%s", service.name, exc)
            accounts = []
        accounts_by_service[service.name] = accounts

    ACCOUNT = {service: accounts for service, accounts in accounts_by_service.items() if accounts}
    PUSH = {} if local_only else load_push_config()
    USER_AGENT = "" if local_only else os.environ.get("USER_AGENT") or PUSH.get("USER_AGENT", "")
    log.debug("已加载账号数: %s", {name: len(accounts) for name, accounts in accounts_by_service.items()})
