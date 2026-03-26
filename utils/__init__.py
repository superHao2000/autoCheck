#!/usr/bin/env python3
"""
工具模块
"""

import logging
import sys


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

# 使用标准 logging 替代 loguru
log = logging.getLogger('autocheck')


__all__ = ['log', 'config']