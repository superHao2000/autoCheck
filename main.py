#!/usr/bin/env python3
"""
AutoCheck 主程序
自动执行多个服务的签到任务
"""

import sys
import signal

from utils import log, config
from checkin import yuchen, glados, airport, javbus


# 任务汇总
SUMMARY = {}


def signal_handler(sig, frame):
    """处理 Ctrl+C"""
    log.info("收到中断信号，正在退出...")
    sys.exit(0)


def run_task(name: str, task_func, accounts: list) -> dict:
    """
    运行单个任务
    
    Args:
        name: 任务名称
        task_func: 任务函数
        accounts: 账号列表
        
    Returns:
        任务结果
    """
    if not accounts:
        log.info(f"{name} 没有配置账号，跳过")
        return {'total': 0, 'success': 0, 'failed': 0, 'details': []}
    
    log.info(f"========== {name} 开始签到 (共 {len(accounts)} 个账号) ==========")
    result = task_func(accounts)
    SUMMARY[name] = result
    
    # 输出结果
    success = result.get('success', 0)
    failed = result.get('failed', 0)
    total = result.get('total', 0)
    
    log.info(f"========== {name} 签到完成: 成功 {success}/{total} ==========")
    
    # 输出详细失败信息
    for detail in result.get('details', []):
        if not detail.get('success'):
            log.warning(f"  - {name} 账号 {detail.get('username', '未知')} 失败: {detail.get('message', '未知错误')}")
    
    return result


def main():
    """主函数"""
    log.info("========== AutoCheck 开始 ==========")
    
    # 加载配置
    config.load_all_configs()
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 运行各服务签到任务
    run_task("YuChen", yuchen.run, config.YUCHEN_ACCOUNTS)
    run_task("GlaDos", glados.run, config.GLADOS_ACCOUNTS)
    run_task("AirPort", airport.run, config.AIRPORT_ACCOUNTS)
    run_task("JavBus", javbus.run, config.JAVBUS_ACCOUNTS)
    
    # 汇总结果
    log.info("")
    log.info("========== 签到汇总 ==========")
    total_success = 0
    total_failed = 0
    
    for name, result in SUMMARY.items():
        success = result.get('success', 0)
        failed = result.get('failed', 0)
        total = result.get('total', 0)
        total_success += success
        total_failed += failed
        
        log.info(f"  {name}: 成功 {success}/{total}")
    
    log.info(f"总计: 成功 {total_success}, 失败 {total_failed}")
    log.info("========== 全部完成 ==========")
    
    # 推送通知
    if config.PUSH:
        send_notification()
    
    # 返回退出码
    return 0 if total_failed == 0 else 1


def send_notification():
    """发送通知"""
    try:
        push_config = config.PUSH
        push_type = push_config.get('type', '').lower()
        
        if push_type == 'gotify':
            from utils.gotify import send_gotify
            send_gotify(push_config, SUMMARY)
        elif push_type == 'telegram':
            from utils.telegram import send_telegram
            send_telegram(push_config, SUMMARY)
        elif push_type == 'webhook':
            from utils.webhook import send_webhook
            send_webhook(push_config, SUMMARY)
        elif push_type == 'mail':
            from utils.mail import send_mail
            send_mail(push_config, SUMMARY)
        else:
            log.warning(f"未知的推送类型: {push_type}")
    except Exception as e:
        log.error(f"推送失败: {e}")


if __name__ == '__main__':
    sys.exit(main())