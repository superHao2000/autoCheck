#!/usr/bin/env python3
"""程序入口：自动发现签到服务，独立执行并汇总结果。"""

import importlib
import pkgutil
import signal
import sys
from dataclasses import dataclass
from typing import Callable

from utils import config, log


@dataclass(frozen=True)
class Service:
    """一个可被自动执行的签到服务及其配置定位信息。"""

    name: str
    module: str
    config_filename: str
    env_key: str


# 仅保存本次运行中已执行服务的结果，供汇总和通知复用。
SUMMARY: dict[str, dict] = {}


def signal_handler(_sig, _frame):
    """收到终止信号时以正常退出码结束当前进程。"""
    log.info("收到中断信号，正在退出...")
    raise SystemExit(0)


def empty_result() -> dict:
    """返回统一的空结果结构，供未配置服务使用。"""
    return {"total": 0, "success": 0, "failed": 0, "details": []}


def discover_services() -> list[Service]:
    """扫描 ``checkin`` 包，将每个公开模块转换为服务定义。

    新服务只需提供模块及同名 JSON 文件；模块可用常量覆盖显示名、
    配置文件名和环境变量名，无须修改入口。
    """
    import checkin

    services = []
    for module_info in pkgutil.iter_modules(checkin.__path__):
        if module_info.name.startswith("_"):
            continue
        module_name = f"checkin.{module_info.name}"
        default_env_key = f"{module_info.name.upper()}_ACCOUNTS"
        try:
            module = importlib.import_module(module_name)
            name = getattr(module, "SERVICE_NAME", module_info.name)
            filename = getattr(module, "CONFIG_FILENAME", f"{module_info.name}.json")
            env_key = getattr(module, "ENV_KEY", default_env_key)
        except Exception:
            # 保留故障模块，使其在运行阶段单独报错而不阻断其他服务。
            log.exception("发现签到模块 %s 时出错", module_name)
            name, filename, env_key = module_info.name, f"{module_info.name}.json", default_env_key
        services.append(Service(name, module_name, filename, env_key))
    return services


def run_task(service: Service, accounts: list[dict]) -> dict:
    """执行一个服务，并将导入或实现异常转换为该服务的失败结果。"""
    if not accounts:
        log.info("%s 没有配置账号，跳过", service.name)
        return empty_result()

    log.info("========== %s 开始签到 (共 %s 个账号) ==========", service.name, len(accounts))
    try:
        task_func: Callable[[list[dict]], dict] = importlib.import_module(service.module).run
        result = task_func(accounts)
        if not isinstance(result, dict):
            # 强制服务模块遵守统一结果协议，便于汇总和通知。
            raise TypeError("服务 run() 必须返回字典")
    except Exception as exc:
        log.exception("%s 任务异常", service.name)
        result = {"total": len(accounts), "success": 0, "failed": len(accounts), "details": [{"success": False, "message": str(exc)}]}

    SUMMARY[service.name] = result
    log.info("========== %s 签到完成: 成功 %s/%s ==========", service.name, result.get("success", 0), result.get("total", 0))
    return result


def main() -> int:
    """加载配置、依次执行已发现服务，并返回适合调度器的退出码。"""
    log.info("========== AutoCheck 开始 ==========")
    services = discover_services()
    config.load_all_configs(services)
    SUMMARY.clear()
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 逐服务执行，run_task 内部负责隔离单个服务的异常。
    for service in services:
        run_task(service, config.ACCOUNT.get(service.name, []))

    total_success = sum(item.get("success", 0) for item in SUMMARY.values())
    total_failed = sum(item.get("failed", 0) for item in SUMMARY.values())
    log.info("========== 签到汇总：成功 %s，失败 %s ==========", total_success, total_failed)
    send_notification()
    return 0 if total_failed == 0 else 1


def send_notification() -> None:
    """在全部签到结束后发送汇总；推送失败不会改变签到结果。"""
    if not config.PUSH:
        return
    try:
        from utils.sendNotify import send

        content = "\n".join(
            f"{name}: 成功 {result.get('success', 0)}/{result.get('total', 0)}"
            for name, result in SUMMARY.items()
        )
        send("AutoCheck 签到结果", content)
    except Exception:
        log.exception("推送通知失败")


if __name__ == "__main__":
    raise SystemExit(main())
