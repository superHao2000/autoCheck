"""YuChen 的离线行为测试和可选真实账号验证。"""

import unittest
from unittest.mock import MagicMock, patch

import requests

from checkin import yuchen
from tests.live_helpers import LIVE_TESTS_ENABLED, configured_accounts


class YuChenUnitTests(unittest.TestCase):
    """使用 Mock 验证 YuChen 请求和异常转换，不访问网络。"""
    @patch("checkin.yuchen.requests.post")
    def test_checkin_success(self, post):
        response = MagicMock(text='{"success": true}')
        response.json.return_value = {"success": True}
        post.return_value = response

        result = yuchen.checkin("https://yuchen.example/checkin", "alice", "secret")

        self.assertTrue(result["success"])
        post.assert_called_once()

    @patch("checkin.yuchen.requests.post", side_effect=requests.RequestException("offline"))
    def test_request_error_is_returned(self, _post):
        self.assertFalse(yuchen.checkin("https://yuchen.example", "alice", "secret")["success"])


@unittest.skipUnless(LIVE_TESTS_ENABLED, "set RUN_LIVE_CHECKIN_TESTS=true to use configured YuChen accounts")
class YuChenLiveTests(unittest.TestCase):
    """使用用户填写的 YuChen 配置执行一次真实签到。"""
    def test_configured_accounts(self):
        accounts = configured_accounts(yuchen)
        self.assertTrue(accounts, "请填写 config/services/yuchen.json 或 YUCHEN_ACCOUNTS")
        result = yuchen.run(accounts)
        self.assertEqual(result["failed"], 0, result["details"])
