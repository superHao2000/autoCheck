#!/usr/bin/env python3
"""
日志模块
"""

import logging
import sys


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

log = logging.getLogger('autocheck')


__all__ = ['log']