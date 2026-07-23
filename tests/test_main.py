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


if __name__ == "__main__":
    unittest.main()
