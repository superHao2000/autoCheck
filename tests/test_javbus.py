"""JavBus 的离线行为测试和可选真实账号验证。"""

import unittest
from unittest.mock import MagicMock, patch

import requests

from checkin import javbus
from tests.live_helpers import run_configured_service


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


if __name__ == "__main__":
    raise SystemExit(run_configured_service(javbus))
