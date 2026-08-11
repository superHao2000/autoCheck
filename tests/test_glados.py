"""GlaDos 的离线行为测试和可选真实账号验证。"""

import unittest
from unittest.mock import MagicMock, patch

import requests

from checkin import glados
from tests.live_helpers import run_configured_service


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

    @patch("checkin.glados.requests.post")
    def test_checkin_failure_message_is_not_treated_as_success(self, post):
        response = MagicMock(text="")
        response.json.return_value = {"code": 1, "message": "签到失败"}
        post.return_value = response

        self.assertFalse(glados.checkin("session=test")["success"])


if __name__ == "__main__":
    raise SystemExit(run_configured_service(glados))
