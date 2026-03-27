"""
Scrapling命令行工具
功能：管理网站配置，分析网站结构，执行采集任务
"""

import argparse
import json
import os
from collectors.scrapling_config import ScraplingConfigManager
from collectors.scrapling_collector import ScraplingCollector

def main():
    parser = argparse.ArgumentParser(description='Scrapling命令行工具')
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # 添加网站
    add_parser = subparsers.add_parser('add', help='添加新网站')
    add_parser.add_argument('name', help='网站名称')
    add_parser.add_argument('url', help='网站URL')
    add_parser.add_argument('--no-analyze', action='store_true', help='不自动分析网站结构')
    
    # 列出网站
    list_parser = subparsers.add_parser('list', help='列出所有网站')
    
    # 查看网站配置
    show_parser = subparsers.add_parser('show', help='查看网站配置')
    show_parser.add_argument('name', help='网站名称')
    
    # 更新网站配置
    update_parser = subparsers.add_parser('update', help='更新网站配置')
    update_parser.add_argument('name', help='网站名称')
    update_parser.add_argument('--url', help='新的网站URL')
    update_parser.add_argument('--enable', action='store_true', help='启用网站')
    update_parser.add_argument('--disable', action='store_true', help='禁用网站')
    update_parser.add_argument('--reanalyze', action='store_true', help='重新分析网站结构')
    
    # 删除网站
    remove_parser = subparsers.add_parser('remove', help='删除网站')
    remove_parser.add_argument('name', help='网站名称')
    
    # 采集文章
    collect_parser = subparsers.add_parser('collect', help='采集文章')
    collect_parser.add_argument('--website', help='指定网站名称')
    collect_parser.add_argument('--all', action='store_true', help='采集所有网站')
    collect_parser.add_argument('--max-articles', type=int, default=10, help='最大采集文章数量')
    
    # 运行命令
    args = parser.parse_args()
    
    config_manager = ScraplingConfigManager()
    collector = ScraplingCollector()
    
    if args.command == 'add':
        # 添加网站
        auto_analyze = not args.no_analyze
        selectors = config_manager.add_website(args.name, args.url, auto_analyze=auto_analyze)
        print(f"成功添加网站: {args.name}")
        print(f"网站URL: {args.url}")
        if auto_analyze:
            print("自动分析完成，提取的选择器:")
            print(json.dumps(selectors, ensure_ascii=False, indent=2))
    
    elif args.command == 'list':
        # 列出网站
        websites = config_manager.list_websites()
        if not websites:
            print("没有配置任何网站")
        else:
            print("配置的网站:")
            for website in websites:
                config = config_manager.get_website_config(website)
                status = "启用" if config.get('enabled', True) else "禁用"
                print(f"  - {website} ({status})")
                print(f"    URL: {config.get('url', '')}")
    
    elif args.command == 'show':
        # 查看网站配置
        config = config_manager.get_website_config(args.name)
        if not config:
            print(f"未找到网站: {args.name}")
        else:
            print(f"网站: {args.name}")
            print(f"URL: {config.get('url', '')}")
            print(f"状态: {'启用' if config.get('enabled', True) else '禁用'}")
            print(f"最后更新: {config.get('last_updated', '')}")
            print("选择器:")
            print(json.dumps(config.get('selectors', {}), ensure_ascii=False, indent=2))
    
    elif args.command == 'update':
        # 更新网站配置
        config = config_manager.get_website_config(args.name)
        if not config:
            print(f"未找到网站: {args.name}")
            return
        
        update_data = {}
        if args.url:
            update_data['url'] = args.url
        if args.enable:
            update_data['enabled'] = True
        if args.disable:
            update_data['enabled'] = False
        
        if args.reanalyze:
            # 重新分析网站结构
            url = args.url or config.get('url')
            if url:
                selectors = config_manager.analyze_website(url)
                update_data['selectors'] = selectors
                print("重新分析完成，提取的选择器:")
                print(json.dumps(selectors, ensure_ascii=False, indent=2))
            else:
                print("无法重新分析，网站URL为空")
                return
        
        if update_data:
            success = config_manager.update_website_config(args.name, update_data)
            if success:
                print(f"成功更新网站配置: {args.name}")
            else:
                print(f"更新网站配置失败: {args.name}")
        else:
            print("没有提供更新数据")
    
    elif args.command == 'remove':
        # 删除网站
        success = config_manager.remove_website(args.name)
        if success:
            print(f"成功删除网站: {args.name}")
        else:
            print(f"删除网站失败: {args.name}")
    
    elif args.command == 'collect':
        # 采集文章
        if args.website:
            # 采集指定网站
            success, message, articles = collector.collect_from_website(args.website, args.max_articles)
            print(f"采集结果: {success}, {message}")
            if articles:
                collector.save_articles(articles)
        elif args.all:
            # 采集所有网站
            articles = collector.collect_from_all_websites(args.max_articles)
            if articles:
                collector.save_articles(articles)
        else:
            print("请指定网站名称或使用 --all 采集所有网站")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
