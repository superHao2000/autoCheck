"""JavBus 的离线行为测试和可选真实账号验证。"""

import unittest
from unittest.mock import MagicMock, patch

import requests

from checkin import javbus
from tests.live_helpers import LIVE_TESTS_ENABLED, configured_accounts


class JavBusUnitTests(unittest.TestCase):
    """验证 JavBus 已签到和请求超时的离线处理。"""
    @patch("checkin.javbus.requests.post")
    def test_already_checked_in_counts_as_success(self, post):
        response = MagicMock(text="")
        response.json.return_value = {"success": False, "message": "已签到"}
        post.return_value = response

        self.assertTrue(javbus.checkin("https://javbus.example/", "session=test")["success"])
        self.assertEqual(post.call_args.args[0], "https://javbus.example/checkin")

    @patch("checkin.javbus.requests.post", side_effect=requests.exceptions.Timeout)
    def test_timeout_is_returned(self, _post):
        result = javbus.checkin("https://javbus.example", "session=test")
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "请求超时")


@unittest.skipUnless(LIVE_TESTS_ENABLED, "set RUN_LIVE_CHECKIN_TESTS=true to use configured JavBus accounts")
class JavBusLiveTests(unittest.TestCase):
    """使用用户填写的 JavBus Cookie 执行一次真实签到。"""
    def test_configured_accounts(self):
        accounts = configured_accounts(javbus)
        self.assertTrue(accounts, "请填写 config/services/javbus.json 或 JAVBUS_ACCOUNTS")
        result = javbus.run(accounts)
        self.assertEqual(result["failed"], 0, result["details"])
