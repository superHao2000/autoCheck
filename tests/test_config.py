"""配置来源优先级和标准字段规则的离线测试。"""

import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from utils import config


class ConfigLoadingTests(unittest.TestCase):
    """验证环境变量、聚合变量与标准字段的加载规则。"""

    def test_environment_accounts_take_priority_over_local_file(self):
        value = '[{"url":"https://example.test","username":"alice","password":"secret"}]'
        with patch.dict(os.environ, {"YUCHEN_ACCOUNTS": value}, clear=False):
            accounts = config.load_service_accounts("YuChen", "yuchen.json", "YUCHEN_ACCOUNTS")
        self.assertEqual(accounts, [{"url": "https://example.test", "username": "alice", "password": "secret"}])

    def test_legacy_field_names_are_not_normalised(self):
        accounts = config._accounts_from_value([{"user": "alice", "pass": "secret"}], "test", "YuChen")
        self.assertEqual(accounts, [{"user": "alice", "pass": "secret"}])
        self.assertNotIn("username", accounts[0])
        self.assertNotIn("password", accounts[0])

    def test_yuchen_accounts_inherit_top_level_url_and_allow_override(self):
        accounts = config._accounts_from_value(
            {
                "url": "https://shared.example/",
                "accounts": [
                    {"username": "alice", "password": "secret"},
                    {"url": "https://override.example/", "username": "bob", "password": "secret"},
                ],
            },
            "test",
            "YuChen",
        )

        self.assertEqual(accounts[0]["url"], "https://shared.example/")
        self.assertEqual(accounts[1]["url"], "https://override.example/")

    def test_invalid_environment_json_skips_only_the_service(self):
        with patch.dict(os.environ, {"GLADOS_ACCOUNTS": "not-json"}, clear=False):
            self.assertEqual(config.load_service_accounts("GlaDos", "glados.json", "GLADOS_ACCOUNTS"), [])

    def test_bundle_supports_a_service_without_a_dedicated_environment_variable(self):
        with patch.dict(os.environ, {"AUTOCHECK_ACCOUNTS": '{"example":[{"token":"abc"}]}'}, clear=False):
            accounts = config.load_service_accounts("Example", "example.json", "EXAMPLE_ACCOUNTS")
        self.assertEqual(accounts, [{"token": "abc"}])

    def test_invalid_local_json_skips_only_affected_service(self):
        services = [
            SimpleNamespace(name="Broken", config_filename="broken.json", env_key="BROKEN_ACCOUNTS"),
            SimpleNamespace(name="Working", config_filename="working.json", env_key="WORKING_ACCOUNTS"),
        ]
        with TemporaryDirectory() as directory, patch.object(config, "SERVICE_CONFIG_DIR", Path(directory)):
            Path(directory, "broken.json").write_text("{", encoding="utf-8")
            Path(directory, "working.json").write_text('{"accounts":[{"token":"ok"}]}', encoding="utf-8")
            config.load_all_configs(services, local_only=True)

        self.assertNotIn("Broken", config.ACCOUNT)
        self.assertEqual(config.ACCOUNT["Working"], [{"token": "ok"}])


if __name__ == "__main__":
    unittest.main()
