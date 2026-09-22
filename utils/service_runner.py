"""多账号签到服务的公共执行器。"""

import random
import time
from collections.abc import Callable, Collection, Mapping
from typing import Any

from utils import log


AccountFields = Collection[str]
CheckinFunction = Callable[..., dict[str, Any]]
MAX_RETRIES = 3
MIN_DELAY_SECONDS = 5
MAX_DELAY_SECONDS = 10


def _standard_account(account: Mapping[str, Any], fields: AccountFields) -> dict[str, Any]:
    """只读取标准字段，返回供站点 ``checkin`` 使用的参数字典。"""
    return {name: account.get(name, "") for name in fields}


def _wait_random_delay(service_name: str, reason: str) -> None:
    """在重试或账号切换前随机等待，降低连续请求对站点的压力。"""
    delay = random.randint(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS)
    log.info("%s %s，等待 %s 秒", service_name, reason, delay)
    time.sleep(delay)


def run_accounts(
    service_name: str,
    accounts: list[dict[str, Any]],
    fields: AccountFields,
    checkin: CheckinFunction,
    display_field: str | None = None,
) -> dict[str, Any]:
    """逐账号执行签到，并保证配置或单账号错误不会影响其他账号。

    ``fields`` 是 ``checkin`` 所需的标准配置字段名集合，不接受字段别名。
    """
    results: dict[str, Any] = {"total": len(accounts), "success": 0, "failed": 0, "details": []}
    required_names = "/".join(sorted(fields))
    has_run_account = False

    for index, account in enumerate(accounts, start=1):
        values = _standard_account(account, fields)
        display_name = values.get(display_field, "") if display_field else ""
        display_name = display_name or f"账号{index}"
        if not all(values.values()):
            result = {"username": display_name, "success": False, "message": f"缺少必要配置 ({required_names})"}
            results["failed"] += 1
            results["details"].append(result)
            log.warning("%s %s 配置不完整，跳过", service_name, display_name)
            continue

        if has_run_account:
            _wait_random_delay(service_name, "切换到下一个账号")
        has_run_account = True
        log.info("%s 开始签到: %s", service_name, display_name)
        for attempt in range(1, MAX_RETRIES + 2):
            try:
                result = checkin(**values)
                if not isinstance(result, dict):
                    raise TypeError("checkin() 必须返回字典")
                result = dict(result)
            except Exception as exc:
                # 账号隔离边界捕获意外错误，使重试及后续账号仍可继续。
                log.exception("%s %s 第 %s 次签到执行异常", service_name, display_name, attempt)
                result = {"success": False, "message": f"执行异常: {exc}"}

            if result.get("success") or result.get("retryable") is False or attempt > MAX_RETRIES:
                break

            log.warning(
                "%s %s 第 %s/%s 次签到失败，准备重试: %s",
                service_name,
                display_name,
                attempt,
                MAX_RETRIES + 1,
                result.get("message", "未知错误"),
            )
            _wait_random_delay(service_name, "准备重试")

        # retryable 只控制本地执行流程，不进入通知正文。
        result.pop("retryable", None)
        result["username"] = display_name
        if result.get("success"):
            results["success"] += 1
            # 成功摘要由服务返回，不包含密码或 Cookie；积分等业务结果可直接见于日志。
            log.info("%s 签到成功: %s - %s", service_name, display_name, result.get("message", "签到成功"))
        else:
            results["failed"] += 1
            log.warning("%s 签到失败: %s - %s", service_name, display_name, result.get("message", "未知错误"))
        results["details"].append(result)

    return results
