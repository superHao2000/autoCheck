"""多账号签到服务的公共执行器。"""

from collections.abc import Callable, Collection, Mapping
from typing import Any

from utils import log


AccountFields = Collection[str]
CheckinFunction = Callable[..., dict[str, Any]]


def _standard_account(account: Mapping[str, Any], fields: AccountFields) -> dict[str, Any]:
    """只读取标准字段，返回供站点 ``checkin`` 使用的参数字典。"""
    return {name: account.get(name, "") for name in fields}


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

        log.info("%s 开始签到: %s", service_name, display_name)
        try:
            result = checkin(**values)
            if not isinstance(result, dict):
                raise TypeError("checkin() 必须返回字典")
        except Exception as exc:
            # 服务实现的意外错误只标记当前账号失败，后续账号仍继续运行。
            log.exception("%s %s 签到执行异常", service_name, display_name)
            result = {"success": False, "message": f"执行异常: {exc}"}

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
