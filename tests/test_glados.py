"""GlaDos 的离线行为测试和可选真实账号验证。"""

import unittest
from unittest.mock import MagicMock, patch

import requests

from checkin import glados
from tests.live_helpers import LIVE_TESTS_ENABLED, configured_accounts


class GlaDosUnitTests(unittest.TestCase):
    """验证 GlaDos 成功状态和请求异常的离线测试。"""
    @patch("checkin.glados.requests.post")
    def test_already_checked_in_counts_as_success(self, post):
        response = MagicMock(text="")
        response.json.return_value = {"code": 1, "message": "already checked in"}
        post.return_value = response

        self.assertTrue(glados.checkin("session=test")["success"])

    @patch("checkin.glados.requests.post", side_effect=requests.RequestException("offline"))
    def test_request_error_is_returned(self, _post):
        self.assertFalse(glados.checkin("session=test")["success"])


@unittest.skipUnless(LIVE_TESTS_ENABLED, "set RUN_LIVE_CHECKIN_TESTS=true to use configured GlaDos accounts")
class GlaDosLiveTests(unittest.TestCase):
    """使用用户填写的 GlaDos Cookie 执行一次真实签到。"""
    def test_configured_accounts(self):
        accounts = configured_accounts(glados)
        self.assertTrue(accounts, "请填写 config/services/glados.json 或 GLADOS_ACCOUNTS")
        result = glados.run(accounts)
        self.assertEqual(result["failed"], 0, result["details"])
