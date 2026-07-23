"""工具包：对外导出统一日志对象，并按需加载其他辅助模块。"""

import logging
import sys


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

# 使用标准 logging，避免调用方依赖第三方日志库。
log = logging.getLogger('autocheck')


__all__ = ['log', 'config']
