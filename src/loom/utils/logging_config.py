"""
日志配置模块
提供统一的日志配置和格式化
"""

import logging
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# 默认日志格式
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# JSON 日志格式
JSON_FORMAT = {
    "timestamp": "%(asctime)s",
    "name": "%(name)s",
    "level": "%(levelname)s",
    "message": "%(message)s",
    "module": "%(module)s",
    "function": "%(funcName)s",
    "line": "%(lineno)d",
}


class JSONFormatter(logging.Formatter):
    """JSON 格式的日志格式化器"""
    
    def __init__(self, fmt_dict: Optional[Dict[str, str]] = None):
        super().__init__()
        self.fmt_dict = fmt_dict or JSON_FORMAT
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为 JSON 字符串"""
        log_obj = {}
        
        for key, fmt in self.fmt_dict.items():
            if fmt:
                log_obj[key] = fmt % record.__dict__
        
        # 添加额外字段
        log_obj["timestamp"] = datetime.fromtimestamp(record.created).isoformat()
        
        # 处理异常信息
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_obj, ensure_ascii=False)


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    json_format: bool = False,
    console: bool = True,
    name: str = "loom"
) -> logging.Logger:
    """
    设置日志配置
    
    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径，如果为 None 则不写入文件
        json_format: 是否使用 JSON 格式
        console: 是否输出到控制台
        name: 日志器名称
        
    Returns:
        配置好的日志器
    """
    # 获取日志级别
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # 创建日志器
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # 清除现有的处理器
    logger.handlers.clear()
    
    # 创建格式化器
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(DEFAULT_FORMAT, DEFAULT_DATE_FORMAT)
    
    # 控制台处理器
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # 文件处理器
    if log_file:
        # 确保日志目录存在
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # 避免日志传播到根日志器
    logger.propagate = False
    
    return logger


def get_logger(name: str = "loom") -> logging.Logger:
    """
    获取配置好的日志器
    
    Args:
        name: 日志器名称
        
    Returns:
        日志器实例
    """
    return logging.getLogger(name)


class LogContext:
    """
    日志上下文管理器
    用于临时修改日志级别
    """
    
    def __init__(self, logger: logging.Logger, level: str):
        self.logger = logger
        self.new_level = getattr(logging, level.upper())
        self.old_level = logger.level
        self.old_handlers_level = [
            (handler, handler.level) for handler in logger.handlers
        ]
    
    def __enter__(self):
        """进入上下文，设置新日志级别"""
        self.logger.setLevel(self.new_level)
        for handler, _ in self.old_handlers_level:
            handler.setLevel(self.new_level)
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文，恢复原日志级别"""
        self.logger.setLevel(self.old_level)
        for handler, old_level in self.old_handlers_level:
            handler.setLevel(old_level)


def log_execution_time(logger: logging.Logger):
    """
    记录函数执行时间的装饰器
    
    Args:
        logger: 日志器实例
    """
    def decorator(func):
        import functools
        import time
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                elapsed = time.time() - start_time
                logger.debug(
                    f"函数 {func.__name__} 执行时间: {elapsed:.3f} 秒"
                )
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed = time.time() - start_time
                logger.debug(
                    f"函数 {func.__name__} 执行时间: {elapsed:.3f} 秒"
                )
        
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# 模块级日志器
_loom_logger = None


def get_loom_logger() -> logging.Logger:
    """
    获取 LOOM 默认日志器
    
    Returns:
        LOOM 日志器
    """
    global _loom_logger
    
    if _loom_logger is None:
        # 从环境变量读取配置
        import os
        level = os.environ.get("LOG_LEVEL", "INFO")
        log_file = os.environ.get("LOG_FILE")
        json_format = os.environ.get("LOG_JSON", "").lower() == "true"
        
        _loom_logger = setup_logging(
            level=level,
            log_file=log_file,
            json_format=json_format,
            console=True,
            name="loom"
        )
    
    return _loom_logger


# 常用日志函数
def log_info(message: str, **kwargs):
    """记录 INFO 级别日志"""
    logger = get_loom_logger()
    if kwargs:
        message = f"{message} | {kwargs}"
    logger.info(message)


def log_warning(message: str, **kwargs):
    """记录 WARNING 级别日志"""
    logger = get_loom_logger()
    if kwargs:
        message = f"{message} | {kwargs}"
    logger.warning(message)


def log_error(message: str, exc_info: bool = False, **kwargs):
    """记录 ERROR 级别日志"""
    logger = get_loom_logger()
    if kwargs:
        message = f"{message} | {kwargs}"
    logger.error(message, exc_info=exc_info)


def log_debug(message: str, **kwargs):
    """记录 DEBUG 级别日志"""
    logger = get_loom_logger()
    if kwargs:
        message = f"{message} | {kwargs}"
    logger.debug(message)


# 导入 inspect 用于装饰器
import inspect