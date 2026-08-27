"""服务运行器的异常隔离与空配置跳过测试。"""

import unittest
from unittest.mock import patch

import main


class RunnerTests(unittest.TestCase):
    """验证入口不会让单个服务故障阻断后续任务。"""
    def test_service_exception_is_converted_to_a_failed_result(self):
        service = main.Service("Broken", "does.not.exist", "broken.json", "BROKEN_ACCOUNTS")
        with patch.object(main, "log"):
            result = main.run_task(service, [{"username": "alice"}])
        self.assertEqual(result["failed"], 1)
        self.assertEqual(result["success"], 0)

    def test_empty_accounts_are_skipped(self):
        service = main.Service("Empty", "does.not.exist", "empty.json", "EMPTY_ACCOUNTS")
        self.assertEqual(main.run_task(service, []), main.empty_result())

    def test_incomplete_service_result_is_converted_to_a_failed_result(self):
        service = main.Service("Broken", "checkin.yuchen", "broken.json", "BROKEN_ACCOUNTS")
        with patch("main.importlib.import_module") as import_module, patch.object(main, "log"):
            import_module.return_value.run.return_value = {}
            result = main.run_task(service, [{"username": "alice"}])
        self.assertEqual(result["failed"], 1)

    def test_result_validator_rejects_inconsistent_counts(self):
        self.assertFalse(main.is_valid_result({"total": 1, "success": 1, "failed": 1, "details": []}, 1))

    def test_notification_includes_account_results_and_failure_reason(self):
        """通知应包含账号级成功信息和不会暴露凭据的失败原因。"""
        content = main.format_notification(
            {
                "GlaDos": {
                    "total": 1,
                    "success": 1,
                    "failed": 0,
                    "details": [{"username": "账号1", "success": True, "message": "本次获得 1 积分"}],
                },
                "YuChen": {
                    "total": 2,
                    "success": 1,
                    "failed": 1,
                    "details": [
                        {"username": "user_a", "success": True, "message": "当前可用积分 128"},
                        {
                            "username": "user_b",
                            "success": False,
                            "message": "登录失败，token=private-value",
                        },
                    ],
                },
            }
        )

        self.assertIn("GlaDos：成功 1/1", content)
        self.assertIn("✓ 账号1：本次获得 1 积分", content)
        self.assertIn("YuChen：成功 1/2，失败 1", content)
        self.assertIn("✗ user_b：登录失败，token=已隐藏", content)
        self.assertIn("签到汇总：成功 2，失败 1", content)
        self.assertNotIn("private-value", content)

    def test_notification_message_is_length_limited(self):
        """异常页等超长消息不能无限扩张第三方通知正文。"""
        message = main._safe_notification_message("x" * 301)

        self.assertEqual(len(message), 301)
        self.assertTrue(message.endswith("…"))


if __name__ == "__main__":
    unittest.main()
