"""真实签到测试的公共支持：只读取本地 JSON 配置。"""

from utils import config


def configured_accounts(module):
    """只从当前服务对应的本地 JSON 文件读取账号。"""
    return config.load_local_service_accounts(module.SERVICE_NAME, module.CONFIG_FILENAME)


def run_configured_service(module) -> int:
    """执行单个服务的本地真实测试，不读取环境变量也不发送通知。"""
    try:
        accounts = configured_accounts(module)
    except ValueError as exc:
        print(f"{module.SERVICE_NAME} 配置错误：{exc}")
        return 1
    if not accounts:
        print(f"请填写 config/{module.CONFIG_FILENAME}")
        return 1
    result = module.run(accounts)
    print(f"{module.SERVICE_NAME}: 成功 {result['success']}/{result['total']}")
    return 0 if result["failed"] == 0 else 1
