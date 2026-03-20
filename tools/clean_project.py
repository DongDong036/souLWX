"""
清理工具 - 清理历史数据和无用文件
保留核心文件，删除临时文件和测试文件
"""

import os
import json
from datetime import datetime

def clean_project():
    """清理项目文件"""
    print("=" * 60)
    print("项目清理工具")
    print("=" * 60)
    
    # 需要删除的文件列表
    files_to_delete = [
        # 临时文件
        'page_debug.html',
        'test_collect_update.py',
        'test_broadcast.py',
        
        # 旧的采集脚本
        'collect_articles.py',
        'collect_articles_v2.py',
        'collect_broadcast.py',
        'collect_broadcast_latest.py',
        'collect_notifications_v2.py',
        
        # 旧的测试报告
        '广播消息测试报告.md',
        '数据采集最终报告.md',
        '韭研公社数据采集方案.md',
        'README_广播消息采集.md',
        
        # 旧的数据文件
        'articles_full.json',
        'articles_full.md',
        'articles_summary_v2.txt',
        'broadcast_articles.json',
        'broadcast_articles.md',
        'broadcast_full.json',
        'broadcast_full.md',
        'broadcast_summary.txt',
        
        # 脱敏和提取工具
        'desensitize_data.py',
        'extract_messages_simple.py',
        'messages_desensitized.json',
        'messages_extracted.json',
        'messages_extracted.md',
        'messages_readable.txt',
    ]
    
    # 统计
    deleted_count = 0
    not_found_count = 0
    
    print("\n开始删除文件...")
    for filename in files_to_delete:
        if os.path.exists(filename):
            try:
                os.remove(filename)
                print(f"  ✓ 已删除：{filename}")
                deleted_count += 1
            except Exception as e:
                print(f"  ✗ 删除失败 {filename}: {e}")
        else:
            print(f"  - 未找到：{filename}")
            not_found_count += 1
    
    print(f"\n删除完成！")
    print(f"  - 成功删除：{deleted_count} 个文件")
    print(f"  - 未找到：{not_found_count} 个文件")
    
    # 清空文章数据库
    print("\n清空文章数据库...")
    try:
        data = {
            'timestamp': datetime.now().isoformat(),
            'total': 0,
            'articles': []
        }
        with open('articles_database.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("  ✓ 数据库已清空")
    except Exception as e:
        print(f"  ✗ 清空数据库失败：{e}")
    
    print("\n" + "=" * 60)
    print("清理完成！")
    print("=" * 60)
    
    # 显示保留的核心文件
    print("\n保留的核心文件:")
    core_files = [
        'article_manager_gui.py',           # GUI 主程序
        'collect_broadcast_stable.py',      # 采集脚本
        'login_save_cookies.py',            # 登录工具
        'cookies.json',                      # 登录凭证
        'articles_database.json',           # 文章数据库
        'manager_config.json',              # 配置文件
        '使用说明.md',                       # 使用说明
        'user_rules.md',                     # 项目规则
    ]
    for f in core_files:
        if os.path.exists(f):
            print(f"  ✓ {f}")
        else:
            print(f"  - {f} (不存在)")

if __name__ == '__main__':
    clean_project()
