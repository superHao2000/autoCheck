"""配置优先级和字段标准化的离线测试。"""

import os
import unittest
from unittest.mock import patch

from utils import config


class ConfigLoadingTests(unittest.TestCase):
    """验证环境变量、聚合变量与配置映射的加载规则。"""
    def test_environment_accounts_take_priority_over_local_file(self):
        with patch.dict(os.environ, {"YUCHEN_ACCOUNTS": '[{"url":"https://example.test","user":"alice","pass":"secret"}]'}, clear=False):
            accounts = config.load_service_accounts("YuChen", "yuchen.json", "YUCHEN_ACCOUNTS")
        self.assertEqual(accounts[0]["username"], "alice")
        self.assertEqual(accounts[0]["password"], "secret")

    def test_invalid_environment_json_skips_only_the_service(self):
        with patch.dict(os.environ, {"GLADOS_ACCOUNTS": "not-json"}, clear=False):
            self.assertEqual(config.load_service_accounts("GlaDos", "glados.json", "GLADOS_ACCOUNTS"), [])

    def test_bundle_supports_a_service_without_a_dedicated_environment_variable(self):
        with patch.dict(os.environ, {"AUTOCHECK_ACCOUNTS": '{"example":[{"token":"abc"}]}'}, clear=False):
            accounts = config.load_service_accounts("Example", "example.json", "EXAMPLE_ACCOUNTS")
        self.assertEqual(accounts, [{"token": "abc"}])


if __name__ == "__main__":
    unittest.main()
