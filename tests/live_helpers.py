"""真实签到测试的公共支持：只有显式开关开启时才会访问网站。"""

import os
from types import SimpleNamespace

from utils import config


# 默认关闭真实请求，避免常规 unittest 执行时消耗签到机会。
LIVE_TESTS_ENABLED = os.environ.get("RUN_LIVE_CHECKIN_TESTS", "").lower() == "true"


def configured_accounts(module):
    """按生产程序相同优先级加载指定服务的环境变量或 JSON 配置。"""
    service = SimpleNamespace(
        name=module.SERVICE_NAME,
        config_filename=module.CONFIG_FILENAME,
        env_key=module.ENV_KEY,
    )
    config.load_all_configs([service])
    return config.ACCOUNT.get(service.name, [])
