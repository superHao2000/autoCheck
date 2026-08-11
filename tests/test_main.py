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


if __name__ == "__main__":
    unittest.main()
