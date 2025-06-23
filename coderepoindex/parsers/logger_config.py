# coding: utf-8
"""
日志配置模块

提供统一的日志管理和配置功能。
"""

import sys
from typing import Optional
from pathlib import Path
from loguru import logger


class LoggerConfig:
    """日志配置管理器"""
    
    _initialized = False
    
    @classmethod
    def setup_logger(
        cls,
        level: str = "INFO",
        format_string: Optional[str] = None,
        log_file: Optional[str] = None,
        enable_console: bool = True,
        enable_file: bool = False,
        rotation: str = "10 MB",
        retention: str = "7 days"
    ):
        """
        设置日志配置
        
        Args:
            level: 日志级别 (TRACE, DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL)
            format_string: 自定义格式字符串
            log_file: 日志文件路径
            enable_console: 是否启用控制台输出
            enable_file: 是否启用文件输出
            rotation: 文件轮转设置
            retention: 日志保留时间
        """
        if cls._initialized:
            return
        
        # 移除默认的handler
        logger.remove()
        
        # 默认格式
        if format_string is None:
            format_string = (
                "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                "<level>{message}</level>"
            )
        
        # 控制台输出
        if enable_console:
            logger.add(
                sys.stdout,
                format=format_string,
                level=level,
                colorize=True
            )
        
        # 文件输出
        if enable_file and log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.add(
                log_path,
                format=format_string,
                level=level,
                rotation=rotation,
                retention=retention,
                encoding="utf-8"
            )
        
        cls._initialized = True
        logger.info(f"日志系统初始化完成，级别: {level}")
    
    @classmethod
    def setup_debug_mode(cls):
        """设置调试模式"""
        cls.setup_logger(
            level="DEBUG",
            enable_console=True,
            enable_file=True,
            log_file="logs/parser_debug.log"
        )
        logger.debug("启用调试模式")
    
    @classmethod
    def setup_production_mode(cls):
        """设置生产模式"""
        cls.setup_logger(
            level="INFO",
            enable_console=True,
            enable_file=True,
            log_file="logs/parser.log"
        )
        logger.info("启用生产模式")
    
    @classmethod
    def setup_silent_mode(cls):
        """设置静默模式"""
        cls.setup_logger(
            level="ERROR",
            enable_console=False,
            enable_file=True,
            log_file="logs/parser_errors.log"
        )
    
    @classmethod
    def add_file_handler(cls, file_path: str, level: str = "DEBUG"):
        """添加文件日志处理器"""
        log_path = Path(file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_path,
            level=level,
            rotation="10 MB",
            retention="7 days",
            encoding="utf-8"
        )
        logger.info(f"添加文件日志处理器: {file_path}")
    
    @classmethod
    def set_level(cls, level: str):
        """动态设置日志级别"""
        # 注意：这个方法需要重新配置所有handler
        cls._initialized = False
        cls.setup_logger(level=level)
        logger.info(f"日志级别已设置为: {level}")


# 便利函数
def setup_parser_logging(mode: str = "info"):
    """
    设置解析器日志
    
    Args:
        mode: 日志模式 ("debug", "info", "production", "silent")
    """
    mode = mode.lower()
    
    if mode == "debug":
        LoggerConfig.setup_debug_mode()
    elif mode == "production":
        LoggerConfig.setup_production_mode()
    elif mode == "silent":
        LoggerConfig.setup_silent_mode()
    else:  # default to info
        LoggerConfig.setup_logger(level="INFO")


def log_function_call(func_name: str, *args, **kwargs):
    """记录函数调用"""
    args_str = ", ".join([str(arg) for arg in args])
    kwargs_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
    params = ", ".join(filter(None, [args_str, kwargs_str]))
    logger.debug(f"调用函数: {func_name}({params})")


def log_performance(func_name: str, duration: float, **metrics):
    """记录性能指标"""
    metrics_str = ", ".join([f"{k}={v}" for k, v in metrics.items()])
    logger.info(f"性能统计 {func_name}: 耗时 {duration:.4f}s, {metrics_str}")


def log_error_with_context(error: Exception, context: dict):
    """记录带上下文的错误"""
    context_str = ", ".join([f"{k}={v}" for k, v in context.items()])
    logger.error(f"错误: {error}, 上下文: {context_str}")


# 预定义的日志格式
FORMATS = {
    "simple": "{time:HH:mm:ss} | {level} | {message}",
    "detailed": "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
    "json": '{"time": "{time}", "level": "{level}", "module": "{name}", "function": "{function}", "line": {line}, "message": "{message}"}',
    "colorful": "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>"
}


if __name__ == "__main__":
    # 演示不同的日志配置
    print("演示日志配置...")
    
    # 调试模式
    LoggerConfig.setup_debug_mode()
    logger.debug("这是调试信息")
    logger.info("这是普通信息")
    logger.success("这是成功信息")
    logger.warning("这是警告信息")
    logger.error("这是错误信息")
    
    # 性能日志演示
    log_performance("test_function", 0.123, files_processed=10, errors=0)
    
    # 函数调用日志演示
    log_function_call("parse_file", "example.py", debug=True)
    
    print("日志演示完成") 