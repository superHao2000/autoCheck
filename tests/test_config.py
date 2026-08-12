"""配置来源优先级和标准字段规则的离线测试。"""

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from utils import config


class ConfigLoadingTests(unittest.TestCase):
    """验证环境变量、聚合变量与标准字段的加载规则。"""

    def test_environment_accounts_are_loaded_before_lower_priority_sources(self):
        value = '[{"url":"https://example.test","username":"alice","password":"secret"}]'
        with TemporaryDirectory() as directory, patch.object(config, "SERVICE_CONFIG_DIR", Path(directory)):
            with patch.dict(os.environ, {"YUCHEN_ACCOUNTS": value}, clear=True):
                accounts = config.load_service_accounts("YuChen", "yuchen.json", "YUCHEN_ACCOUNTS")
        self.assertEqual(accounts, [{"url": "https://example.test", "username": "alice", "password": "secret"}])

    def test_sources_are_merged_by_priority_and_duplicate_accounts_are_skipped(self):
        direct_value = {
            "url": "https://shared.example/",
            "accounts": [
                {"username": "direct", "password": "first"},
                {"username": "duplicate", "password": "first"},
            ],
        }
        bundle_value = {
            "yuchen": {
                "url": "https://shared.example/",
                "accounts": [
                    {"username": "bundle", "password": "second"},
                    {"username": "duplicate", "password": "second"},
                ],
            }
        }
        local_value = {
            "url": "https://shared.example/",
            "accounts": [
                {"username": "local", "password": "third"},
                {"username": "duplicate", "password": "third"},
            ],
        }
        with TemporaryDirectory() as directory, patch.object(config, "SERVICE_CONFIG_DIR", Path(directory)):
            Path(directory, "yuchen.json").write_text(json.dumps(local_value), encoding="utf-8")
            environment = {
                "YUCHEN_ACCOUNTS": json.dumps(direct_value),
                "AUTOCHECK_ACCOUNTS": json.dumps(bundle_value),
            }
            with patch.dict(os.environ, environment, clear=True), patch.object(config, "log") as log:
                accounts = config.load_service_accounts("YuChen", "yuchen.json", "YUCHEN_ACCOUNTS")

        self.assertEqual([account["username"] for account in accounts], ["direct", "duplicate", "bundle", "local"])
        duplicate_logs = [call.args[0] for call in log.info.call_args_list]
        self.assertEqual(sum("检测到重复账号" in message for message in duplicate_logs), 2)

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

    def test_javbus_accounts_inherit_top_level_url_and_allow_override(self):
        accounts = config._accounts_from_value(
            {
                "url": "https://www.javbus.com",
                "accounts": [
                    {"cookies": "first"},
                    {"url": "https://mirror.example", "cookies": "second"},
                ],
            },
            "test",
            "JavBus",
        )

        self.assertEqual(accounts[0]["url"], "https://www.javbus.com")
        self.assertEqual(accounts[1]["url"], "https://mirror.example")

    def test_invalid_environment_json_skips_only_the_service(self):
        with TemporaryDirectory() as directory, patch.object(config, "SERVICE_CONFIG_DIR", Path(directory)):
            with patch.dict(os.environ, {"GLADOS_ACCOUNTS": "not-json"}, clear=True):
                self.assertEqual(config.load_service_accounts("GlaDos", "glados.json", "GLADOS_ACCOUNTS"), [])

    def test_bundle_supports_a_service_without_a_dedicated_environment_variable(self):
        with TemporaryDirectory() as directory, patch.object(config, "SERVICE_CONFIG_DIR", Path(directory)):
            with patch.dict(os.environ, {"AUTOCHECK_ACCOUNTS": '{"example":[{"token":"abc"}]}'}, clear=True):
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
