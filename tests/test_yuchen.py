"""YuChen 的离线行为测试和可选真实账号验证。"""

import unittest
from unittest.mock import MagicMock, patch

import requests

from checkin import yuchen
from tests.live_helpers import run_configured_service


class YuChenUnitTests(unittest.TestCase):
    """使用 Mock 验证 YuChen 请求和异常转换，不访问网络。"""
    @patch("checkin.yuchen.requests.Session")
    def test_checkin_success(self, session_class):
        session = session_class.return_value
        session.get.side_effect = [
            MagicMock(text='<script>var chenxing = {"ajax_url":"https://yuchen.example/ajax"};</script><input name="token" value="token">'),
            MagicMock(text='您目前可用积分： 495 积分变更记录 每日签到赠送2积分'),
        ]
        login_response = MagicMock()
        login_response.json.return_value = {"success": "success", "msg": "登录成功"}
        sign_response = MagicMock()
        sign_response.json.return_value = {"success": "success", "msg": "签到成功"}
        session.post.side_effect = [login_response, sign_response]

        result = yuchen.checkin("https://yuchen.example", "alice", "secret")

        self.assertTrue(result["success"])
        self.assertEqual(session.post.call_count, 2)
        self.assertIn("本次获得 2 积分", result["message"])
        self.assertIn("当前可用积分 495", result["message"])

    @patch("checkin.yuchen.requests.Session")
    def test_request_error_is_returned(self, session_class):
        session_class.return_value.get.side_effect = requests.RequestException("offline")
        self.assertFalse(yuchen.checkin("https://yuchen.example", "alice", "secret")["success"])

    @patch("checkin.yuchen.requests.Session")
    def test_page_without_login_metadata_is_rejected(self, session_class):
        session_class.return_value.get.return_value = MagicMock(text="<!doctype html><html>success 签到成功</html>")

        result = yuchen.checkin("https://yuchen.example", "alice", "secret")

        self.assertFalse(result["success"])
        self.assertIn("登录接口", result["message"])

    @patch("checkin.yuchen.requests.Session")
    def test_login_error_message_is_sanitised(self, session_class):
        session = session_class.return_value
        session.get.return_value = MagicMock(
            text='<script>var chenxing = {"ajax_url":"https://yuchen.example/ajax"};</script><input name="token" value="token">'
        )
        response = MagicMock()
        response.json.return_value = {"success": "error", "msg": '<strong>错误：</strong>用户名alice未注册'}
        session.post.return_value = response

        result = yuchen.checkin("https://yuchen.example", "alice", "secret")

        self.assertFalse(result["success"])
        self.assertNotIn("alice", result["message"])
        self.assertNotIn("<strong>", result["message"])


if __name__ == "__main__":
    raise SystemExit(run_configured_service(yuchen))
