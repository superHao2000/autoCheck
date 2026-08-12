"""工具包：对外转导出统一日志对象和辅助模块。"""

# 日志的处理器、等级和输出格式仅由 logger 模块配置，避免重复初始化。
from utils.logger import log


__all__ = ['log', 'config']
