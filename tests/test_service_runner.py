"""公共账号执行器的重试、延时和最终结果测试。"""

import unittest
from unittest.mock import Mock, call, patch

from utils.service_runner import run_accounts


class ServiceRunnerTests(unittest.TestCase):
    """验证临时失败可恢复，永久失败不会重试或污染通知结果。"""

    @patch("utils.service_runner.time.sleep")
    @patch("utils.service_runner.random.randint", return_value=5)
    def test_failure_then_success_keeps_only_success(self, randint, sleep):
        checkin = Mock(
            side_effect=[
                {"success": False, "message": "请求超时"},
                {"success": True, "message": "签到成功"},
            ]
        )

        result = run_accounts("Example", [{"token": "secret"}], ("token",), checkin)

        self.assertEqual(checkin.call_count, 2)
        self.assertEqual(result["success"], 1)
        self.assertEqual(result["failed"], 0)
        self.assertEqual(len(result["details"]), 1)
        self.assertEqual(result["details"][0]["message"], "签到成功")
        randint.assert_called_once_with(5, 10)
        sleep.assert_called_once_with(5)

    @patch("utils.service_runner.time.sleep")
    @patch("utils.service_runner.random.randint", return_value=6)
    def test_four_failures_keep_only_last_failure(self, _randint, sleep):
        checkin = Mock(side_effect=[{"success": False, "message": f"失败{i}"} for i in range(1, 5)])

        result = run_accounts("Example", [{"token": "secret"}], ("token",), checkin)

        self.assertEqual(checkin.call_count, 4)
        self.assertEqual(result["failed"], 1)
        self.assertEqual(len(result["details"]), 1)
        self.assertEqual(result["details"][0]["message"], "失败4")
        self.assertEqual(sleep.call_count, 3)

    @patch("utils.service_runner.time.sleep")
    def test_permanent_auth_failure_is_not_retried(self, sleep):
        checkin = Mock(return_value={"success": False, "message": "密码错误", "retryable": False})

        result = run_accounts("Example", [{"token": "secret"}], ("token",), checkin)

        checkin.assert_called_once_with(token="secret")
        sleep.assert_not_called()
        self.assertNotIn("retryable", result["details"][0])

    @patch("utils.service_runner.time.sleep")
    @patch("utils.service_runner.random.randint", return_value=7)
    def test_multiple_accounts_wait_between_requests(self, randint, sleep):
        checkin = Mock(return_value={"success": True, "message": "签到成功"})

        run_accounts("Example", [{"token": "first"}, {"token": "second"}], ("token",), checkin)

        self.assertEqual(checkin.call_args_list, [call(token="first"), call(token="second")])
        randint.assert_called_once_with(5, 10)
        sleep.assert_called_once_with(7)


if __name__ == "__main__":
    unittest.main()
