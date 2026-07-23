#!/usr/bin/env python3
"""项目统一日志配置：所有模块输出到标准输出，便于本地和调度器采集。"""

import logging
import sys


# 在模块加载时只初始化日志格式，不读取业务配置。
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

log = logging.getLogger('autocheck')


__all__ = ['log']
