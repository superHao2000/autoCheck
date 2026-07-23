"""AirPort 的离线行为测试和可选真实账号验证。"""

import unittest
from unittest.mock import MagicMock, patch

from checkin import airport
from tests.live_helpers import LIVE_TESTS_ENABLED, configured_accounts


def response(data):
    """构造同时具备状态码、正文和 JSON 方法的模拟 HTTP 响应。"""
    mocked = MagicMock(status_code=200, text="")
    mocked.json.return_value = data
    return mocked


class AirPortUnitTests(unittest.TestCase):
    """验证 AirPort 登录、签到和登录失败短路逻辑。"""
    @patch("checkin.airport.requests.Session")
    def test_login_then_checkin_success(self, session_class):
        session = session_class.return_value
        session.post.side_effect = [response({"success": True}), response({"success": True, "message": "签到成功"})]

        result = airport.checkin("https://airport.example/", "alice@example.test", "secret")

        self.assertTrue(result["success"])
        self.assertEqual(session.post.call_count, 2)

    @patch("checkin.airport.requests.Session")
    def test_login_failure_stops_before_checkin(self, session_class):
        session = session_class.return_value
        session.post.return_value = response({"success": False, "message": "bad password"})

        self.assertFalse(airport.checkin("https://airport.example", "alice@example.test", "secret")["success"])
        self.assertEqual(session.post.call_count, 1)


@unittest.skipUnless(LIVE_TESTS_ENABLED, "set RUN_LIVE_CHECKIN_TESTS=true to use configured AirPort accounts")
class AirPortLiveTests(unittest.TestCase):
    """使用用户填写的 AirPort 配置执行一次真实登录与签到。"""
    def test_configured_accounts(self):
        accounts = configured_accounts(airport)
        self.assertTrue(accounts, "请填写 config/services/airport.json 或 AIRPORT_ACCOUNTS")
        result = airport.run(accounts)
        self.assertEqual(result["failed"], 0, result["details"])
