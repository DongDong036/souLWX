"""
项目迁移工具 - 重新组织目录结构
自动创建标准目录结构并迁移现有文件
"""

import os
import shutil
import json
from datetime import datetime

def create_directory_structure():
    """创建标准目录结构"""
    print("=" * 60)
    print("项目迁移工具 - 创建目录结构")
    print("=" * 60)
    
    # 定义目录结构
    directories = [
        'src',                      # 源代码
        'data/database',            # 数据库
        'data/cookies',             # Cookie
        'data/export/json',         # JSON 导出
        'data/export/markdown',     # Markdown 导出
        'logs',                     # 日志
        'config',                   # 配置
        'tools',                    # 工具
        'docs',                     # 文档
        'temp',                     # 临时文件
    ]
    
    print("\n创建目录结构...")
    for dir_path in directories:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"  ✓ 已创建：{dir_path}/")
        else:
            print(f"  - 已存在：{dir_path}/")
    
    print("\n目录结构创建完成！")

def migrate_files():
    """迁移现有文件到新位置"""
    print("\n" + "=" * 60)
    print("迁移文件")
    print("=" * 60)
    
    # 文件迁移映射
    migration_map = {
        # 源代码
        'article_manager_gui.py': 'src/article_manager_gui.py',
        'collect_broadcast_stable.py': 'src/collect_broadcast_stable.py',
        'login_save_cookies.py': 'src/login_save_cookies.py',
        
        # 数据文件
        'articles_database.json': 'data/database/articles_database.json',
        'cookies.json': 'data/cookies/cookies.json',
        
        # 工具
        'clean_project.py': 'tools/clean_project.py',
        
        # 文档
        'README.md': 'docs/README.md',
        '使用说明.md': 'docs/使用说明.md',
        'user_rules.md': 'docs/user_rules.md',
        '目录结构规划.md': 'docs/目录结构规划.md',
    }
    
    migrated_count = 0
    skipped_count = 0
    
    for src_file, dest_file in migration_map.items():
        if os.path.exists(src_file):
            try:
                # 如果目标文件已存在，跳过
                if os.path.exists(dest_file):
                    print(f"  - 已存在：{dest_file}")
                    skipped_count += 1
                else:
                    shutil.move(src_file, dest_file)
                    print(f"  ✓ 已迁移：{src_file} -> {dest_file}")
                    migrated_count += 1
            except Exception as e:
                print(f"  ✗ 迁移失败 {src_file}: {e}")
        else:
            print(f"  - 未找到：{src_file}")
            skipped_count += 1
    
    print(f"\n迁移完成！")
    print(f"  - 成功迁移：{migrated_count} 个文件")
    print(f"  - 跳过：{skipped_count} 个文件")

def create_default_config():
    """创建默认配置文件"""
    print("\n" + "=" * 60)
    print("创建配置文件")
    print("=" * 60)
    
    # 主配置文件
    manager_config = {
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
    
    config_file = 'config/manager_config.json'
    if not os.path.exists(config_file):
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(manager_config, f, ensure_ascii=False, indent=2)
        print(f"  ✓ 已创建：{config_file}")
    else:
        print(f"  - 已存在：{config_file}")
    
    # 定时任务配置
    scheduler_config = {
        "enabled": True,
        "schedule_type": "interval",
        "interval_minutes": 30,
        "fixed_times": ["09:00", "12:00", "18:00", "21:00"],
        "start_date": datetime.now().strftime('%Y-%m-%d'),
        "end_date": None
    }
    
    scheduler_file = 'config/scheduler_config.json'
    if not os.path.exists(scheduler_file):
        with open(scheduler_file, 'w', encoding='utf-8') as f:
            json.dump(scheduler_config, f, ensure_ascii=False, indent=2)
        print(f"  ✓ 已创建：{scheduler_file}")
    else:
        print(f"  - 已存在：{scheduler_file}")

def create_gitignore():
    """创建 .gitignore 文件"""
    print("\n" + "=" * 60)
    print("创建 .gitignore")
    print("=" * 60)
    
    gitignore_content = """# 敏感文件
data/cookies/cookies.json
*.key
*.pem

# 日志文件
logs/*.log

# 临时文件
temp/*
*.tmp
*.bak

# Python 缓存
__pycache__/
*.py[cod]
*$py.class
*.so

# 虚拟环境
venv/
env/
.env/

# IDE 配置
.vscode/
.idea/
*.swp
*.swo

# 操作系统文件
.DS_Store
Thumbs.db
"""
    
    gitignore_file = '.gitignore'
    with open(gitignore_file, 'w', encoding='utf-8') as f:
        f.write(gitignore_content)
    print(f"  ✓ 已创建：{gitignore_file}")

def create_readme():
    """更新根目录 README"""
    print("\n" + "=" * 60)
    print("更新根目录 README")
    print("=" * 60)
    
    readme_content = """# 韭研公社文章管理器

## 快速开始

### 1. 首次登录
```bash
python src/login_save_cookies.py
```

### 2. 启动程序
```bash
python src/article_manager_gui.py
```

## 目录结构

```
JC/
├── src/           # 源代码
├── data/          # 数据文件
├── logs/          # 日志
├── config/        # 配置
├── tools/         # 工具
├── docs/          # 文档
└── temp/          # 临时文件
```

## 功能特性

- ⏰ 定时采集（每 30 分钟）
- 💾 增量存储（自动去重）
- 🔍 搜索筛选
- 📤 导出分享
- 📊 数据统计

## 详细文档

请查看 [docs/使用说明.md](docs/使用说明.md)

---
**版本**: v2.0  
**更新时间**: 2026-03-20
"""
    
    readme_file = 'README.md'
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print(f"  ✓ 已更新：{readme_file}")

def show_final_structure():
    """显示最终目录结构"""
    print("\n" + "=" * 60)
    print("最终目录结构")
    print("=" * 60)
    
    # 简单的目录树显示
    for root, dirs, files in os.walk('.'):
        # 跳过隐藏目录
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        level = root.replace('.', '').count(os.sep)
        indent = ' ' * 2 * level
        print(f'{indent}{os.path.basename(root)}/')
        
        subindent = ' ' * 2 * (level + 1)
        for file in files[:5]:  # 只显示前 5 个文件
            print(f'{subindent}{file}')
        
        if len(files) > 5:
            print(f'{subindent}... 等 {len(files) - 5} 个文件')

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("韭研公社文章管理器 - 项目迁移工具")
    print("=" * 60)
    print(f"执行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 1. 创建目录结构
        create_directory_structure()
        
        # 2. 迁移文件
        migrate_files()
        
        # 3. 创建配置文件
        create_default_config()
        
        # 4. 创建 .gitignore
        create_gitignore()
        
        # 5. 更新 README
        create_readme()
        
        # 6. 显示最终结构
        show_final_structure()
        
        print("\n" + "=" * 60)
        print("✅ 迁移完成！")
        print("=" * 60)
        print("\n下一步:")
        print("1. 检查目录结构是否正确")
        print("2. 运行 python src/article_manager_gui.py 测试程序")
        print("3. 查看 docs/使用说明.md 了解详细功能")
        
    except Exception as e:
        print(f"\n❌ 迁移失败：{e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
