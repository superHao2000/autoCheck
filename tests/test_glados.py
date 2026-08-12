"""GlaDos（Railgun）的离线行为测试和可选真实账号验证。"""

import unittest
from unittest.mock import MagicMock, patch

import requests

from checkin import glados
from tests.live_helpers import run_configured_service


class GlaDosUnitTests(unittest.TestCase):
    """验证 Railgun 签到请求、积分解析和失败隔离。"""

    @patch("checkin.glados.requests.post")
    def test_checkin_reports_gained_and_total_points(self, post):
        response = MagicMock()
        response.json.return_value = {
            "code": 0,
            "message": "签到成功",
            "list": [{"change": 3, "balance": 27}],
        }
        post.return_value = response

        result = glados.checkin("https://railgun.info", "session=test")

        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "签到成功，本次获得 3 积分，当前总积分 27")
        post.assert_called_once()
        self.assertEqual(post.call_args.args[0], "https://railgun.info/api/user/checkin")
        self.assertEqual(post.call_args.kwargs["json"], {"token": "railgun.info"})

    @patch("checkin.glados.requests.post")
    def test_already_checked_in_keeps_current_points(self, post):
        response = MagicMock()
        response.json.return_value = {
            "code": 1,
            "message": "already checked in",
            "list": [{"balance": "27.00000000"}],
        }
        post.return_value = response

        result = glados.checkin("https://railgun.info/", "session=test")

        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "already checked in，当前总积分 27")

    @patch("checkin.glados.requests.post")
    def test_railgun_observation_logged_is_already_checked_in(self, post):
        response = MagicMock()
        response.json.return_value = {
            "code": 1,
            "message": "Today's observation logged. Return tomorrow for more points.",
            "list": [{"balance": "1.0000000000000000"}],
        }
        post.return_value = response

        result = glados.checkin("https://railgun.info", "session=test")

        self.assertTrue(result["success"])
        self.assertIn("当前总积分 1", result["message"])

    @patch("checkin.glados.requests.post", side_effect=requests.RequestException("offline"))
    def test_request_error_is_returned(self, _post):
        self.assertFalse(glados.checkin("https://railgun.info", "session=test")["success"])

    @patch("checkin.glados.requests.post")
    def test_checkin_failure_message_is_not_treated_as_success(self, post):
        response = MagicMock()
        response.json.return_value = {"code": 1, "message": "签到失败"}
        post.return_value = response

        self.assertFalse(glados.checkin("https://railgun.info", "session=test")["success"])

    @patch("checkin.glados.requests.post")
    def test_points_field_is_used_when_latest_record_is_unavailable(self, post):
        response = MagicMock()
        response.json.return_value = {"code": 0, "message": "签到成功", "points": 3}
        post.return_value = response

        result = glados.checkin("https://railgun.info", "session=test")

        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "签到成功，本次获得 3 积分")

    @patch("checkin.glados.checkin", return_value={"success": True, "message": "本次获得 3 积分，当前总积分 27"})
    @patch("utils.service_runner.log")
    def test_success_log_contains_points_message(self, log, _checkin):
        glados.run([{"url": "https://railgun.info", "cookies": "session=test"}])

        log.info.assert_any_call(
            "%s 签到成功: %s - %s",
            "GlaDos",
            "账号1",
            "本次获得 3 积分，当前总积分 27",
        )


if __name__ == "__main__":
    raise SystemExit(run_configured_service(glados))
