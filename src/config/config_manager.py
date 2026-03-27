"""
配置管理模块 - 统一的配置加载和保存
"""

import json
import os
from datetime import datetime

# 配置目录
CONFIG_DIR = 'config'

def get_config_path(config_name='manager_config.json'):
    """获取配置文件路径"""
    return os.path.join(CONFIG_DIR, config_name)

def load_config(config_name='manager_config.json'):
    """
    加载配置文件
    
    Args:
        config_name: 配置文件名称
    
    Returns:
        dict: 配置数据
    """
    config_path = get_config_path(config_name)
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"[OK] 加载配置：{config_path}")
            return config
        except Exception as e:
            print(f"[ERROR] 加载配置失败：{e}")
            return get_default_config()
    else:
        print(f"[WARN] 配置文件不存在，使用默认配置：{config_path}")
        return get_default_config()

def save_config(config, config_name='manager_config.json'):
    """
    保存配置文件
    
    Args:
        config: 配置数据
        config_name: 配置文件名称
    """
    config_path = get_config_path(config_name)
    
    try:
        # 确保配置目录存在
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        print(f"[OK] 保存配置：{config_path}")
        return True
    except Exception as e:
        print(f"[ERROR] 保存配置失败：{e}")
        return False

def get_default_config():
    """获取默认配置"""
    return {
        "app": {
            "name": "韭研公社文章管理器",
            "version": "1.0",
            "language": "zh-CN"
        },
        "paths": {
            "data_dir": "./data",
            "log_dir": "./logs",
            "export_dir": "./data/export"
        },
        "collection": {
            "auto_collect": True,
            "interval_minutes": 30,
            "max_articles": 10,
            "dedup_enabled": True
        },
        "storage": {
            "format": "json",
            "backup_enabled": True,
            "backup_days": 7
        },
        "log": {
            "level": "INFO",
            "max_size_mb": 10,
            "backup_count": 30
        }
    }

def get_scheduler_config():
    """获取定时任务配置"""
    return load_config('scheduler_config.json')

def save_scheduler_config(config):
    """保存定时任务配置"""
    return save_config(config, 'scheduler_config.json')

def get_data_path():
    """获取数据目录路径"""
    config = load_config()
    return config.get('paths', {}).get('data_dir', './data')

def get_database_path():
    """获取数据库文件路径"""
    data_dir = get_data_path()
    return os.path.join(data_dir, 'database', 'articles_database.json')

def get_cookies_path():
    """获取 Cookie 文件路径"""
    data_dir = get_data_path()
    return os.path.join(data_dir, 'cookies', 'cookies.json')

def get_export_path(export_type='json'):
    """获取导出目录路径"""
    data_dir = get_data_path()
    return os.path.join(data_dir, 'export', export_type)

def get_log_path():
    """获取日志目录路径"""
    config = load_config()
    return config.get('paths', {}).get('log_dir', './logs')

# 使用示例
if __name__ == '__main__':
    # 测试配置加载
    config = load_config()
    print("\n当前配置:")
    print(json.dumps(config, ensure_ascii=False, indent=2))
    
    # 测试路径获取
    print("\n路径信息:")
    print(f"数据目录：{get_data_path()}")
    print(f"数据库文件：{get_database_path()}")
    print(f"Cookie 文件：{get_cookies_path()}")
    print(f"导出目录：{get_export_path()}")
    print(f"日志目录：{get_log_path()}")
