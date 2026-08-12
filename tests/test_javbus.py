"""JavBus 论坛自动签到、积分与升级进度的离线测试。"""

import unittest
from unittest.mock import MagicMock, patch

import requests

from checkin import javbus
from tests.live_helpers import run_configured_service


class JavBusUnitTests(unittest.TestCase):
    """验证论坛访问触发自动签到时的积分解析和异常处理。"""

    @patch("checkin.javbus.requests.Session")
    def test_checkin_reports_balance_rewards_and_upgrade_days(self, session_class):
        session = session_class.return_value
        session.get.side_effect = [
            MagicMock(text="金錢: 10 里程: 20"),
            MagicMock(text='<a href="/logout">退出</a>'),
            MagicMock(text="金錢: 11 里程: 21"),
            MagicMock(text="您升級到此用戶組還需里程 79"),
        ]

        result = javbus.checkin("https://www.javbus.com/", "session=test")

        self.assertTrue(result["success"])
        self.assertEqual(
            result["message"],
            "本次金钱 +1，当前金钱 11；本次里程 +1，当前里程 21；升级还需里程 79，按每日登录预计 79 天",
        )
        self.assertEqual(session.get.call_args_list[1].args[0], "https://www.javbus.com/forum/")
        self.assertNotIn("/checkin", session.get.call_args_list[1].args[0])
        session.close.assert_called_once()

    @patch("checkin.javbus.requests.Session")
    def test_existing_daily_checkin_reports_zero_rewards(self, session_class):
        session = session_class.return_value
        session.get.side_effect = [
            MagicMock(text="金錢: 11 里程: 21"),
            MagicMock(text='<a href="/logout">退出</a>'),
            MagicMock(text="金錢: 11 里程: 21"),
            MagicMock(text="您升級到此用戶組還需里程 79"),
        ]

        result = javbus.checkin("https://www.javbus.com", "session=test")

        self.assertTrue(result["success"])
        self.assertIn("本次金钱 +0", result["message"])
        self.assertIn("本次里程 +0", result["message"])

    @patch("checkin.javbus.requests.Session")
    def test_missing_logout_marker_is_treated_as_invalid_cookie(self, session_class):
        session = session_class.return_value
        session.get.side_effect = [MagicMock(text="金錢: 10 里程: 20"), MagicMock(text='<a href="/login">登录</a>')]

        result = javbus.checkin("https://www.javbus.com", "session=test")

        self.assertFalse(result["success"])
        self.assertIn("Cookie", result["message"])
        session.close.assert_called_once()

    @patch("checkin.javbus.requests.Session")
    def test_timeout_is_returned(self, session_class):
        session_class.return_value.get.side_effect = requests.exceptions.Timeout

        result = javbus.checkin("https://www.javbus.com", "session=test")

        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "请求超时")


if __name__ == "__main__":
    raise SystemExit(run_configured_service(javbus))
