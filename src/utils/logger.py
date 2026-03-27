"""
日志模块 - 统一的日志管理
支持日志轮转、分级记录、自动清理
"""

import logging
import os
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime

# 日志目录
LOG_DIR = 'logs'

# 确保日志目录存在
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def get_logger(name='app', log_type='daily'):
    """
    获取日志记录器
    
    Args:
        name: 日志名称
        log_type: 日志类型 ('daily' - 按天，'size' - 按大小)
    
    Returns:
        logging.Logger: 日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # 如果已经有处理器，直接返回
    if logger.handlers:
        return logger
    
    # 创建 formatter
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 根据类型创建不同的处理器
    if log_type == 'daily':
        # 按天轮转
        log_file = os.path.join(LOG_DIR, f'{name}_%Y-%m-%d.log')
        handler = TimedRotatingFileHandler(
            filename=os.path.join(LOG_DIR, f'{name}.log'),
            when='D',
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        handler.suffix = '%Y-%m-%d.log'
    elif log_type == 'size':
        # 按大小轮转
        handler = RotatingFileHandler(
            filename=os.path.join(LOG_DIR, f'{name}.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
    else:
        # 默认：按天
        handler = TimedRotatingFileHandler(
            filename=os.path.join(LOG_DIR, f'{name}.log'),
            when='D',
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

# 预定义的日志记录器
app_logger = get_logger('app')          # 应用日志
collect_logger = get_logger('collect')  # 采集日志
error_logger = get_logger('error')      # 错误日志

def log_app(message, level='info'):
    """记录应用日志"""
    if level == 'info':
        app_logger.info(message)
    elif level == 'warning':
        app_logger.warning(message)
    elif level == 'error':
        app_logger.error(message)
    elif level == 'debug':
        app_logger.debug(message)

def log_collect(message, level='info'):
    """记录采集日志"""
    if level == 'info':
        collect_logger.info(message)
    elif level == 'warning':
        collect_logger.warning(message)
    elif level == 'error':
        collect_logger.error(message)
    elif level == 'debug':
        collect_logger.debug(message)

def log_error(message, level='error'):
    """记录错误日志"""
    if level == 'error':
        error_logger.error(message)
    elif level == 'warning':
        error_logger.warning(message)
    elif level == 'critical':
        error_logger.critical(message)

def clean_old_logs(days=30):
    """
    清理旧日志
    
    Args:
        days: 保留天数
    """
    import os
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.now() - timedelta(days=days)
    
    for filename in os.listdir(LOG_DIR):
        if filename.endswith('.log'):
            file_path = os.path.join(LOG_DIR, filename)
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            
            if file_time < cutoff_date:
                os.remove(file_path)
                print(f"已删除旧日志：{filename}")

# 使用示例
if __name__ == '__main__':
    # 测试日志
    log_app('应用程序启动')
    log_app('这是一个警告', level='warning')
    
    log_collect('开始采集任务')
    log_collect('采集成功', level='info')
    
    log_error('这是一个错误', level='error')
    
    print("日志测试完成！")
