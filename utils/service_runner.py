"""多账号签到服务的公共执行器。"""

from collections.abc import Callable, Mapping
from typing import Any

from utils import log


AccountFields = Mapping[str, tuple[str, ...]]
CheckinFunction = Callable[..., dict[str, Any]]


def _normalise_account(account: Mapping[str, Any], fields: AccountFields) -> dict[str, Any]:
    """按字段别名读取账号配置，返回供站点 ``checkin`` 使用的规范字段。"""
    return {
        name: next((account.get(alias) for alias in aliases if account.get(alias)), "")
        for name, aliases in fields.items()
    }


def run_accounts(
    service_name: str,
    accounts: list[dict[str, Any]],
    fields: AccountFields,
    checkin: CheckinFunction,
    display_field: str | None = None,
) -> dict[str, Any]:
    """逐账号执行签到，并保证配置或单账号错误不会影响其他账号。

    ``fields`` 的键是 ``checkin`` 的参数名，值是依次尝试读取的配置字段别名。
    """
    results: dict[str, Any] = {"total": len(accounts), "success": 0, "failed": 0, "details": []}
    required_names = "/".join(fields)

    for index, account in enumerate(accounts, start=1):
        values = _normalise_account(account, fields)
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
            log.info("%s 签到成功: %s", service_name, display_name)
        else:
            results["failed"] += 1
            log.warning("%s 签到失败: %s - %s", service_name, display_name, result.get("message", "未知错误"))
        results["details"].append(result)

    return results
