"""
信息源分析工具
功能：分析新的信息源，找到合适的文章链接选择器
"""

import argparse
import requests
from scrapling import Selector

def analyze_source(url):
    """分析信息源，找到文章链接选择器
    
    Args:
        url: 信息源URL
    """
    print(f"开始分析信息源: {url}")
    
    # 发送请求
    try:
        response = requests.get(url)
        response.raise_for_status()
    except Exception as e:
        print(f"请求失败: {e}")
        return
    
    # 解析页面
    selector = Selector(response.text)
    
    # 提取所有链接
    print("\n=== 分析所有链接 ===")
    try:
        all_links = selector.css('a')
        print(f"找到 {len(all_links)} 个链接")
        
        # 分类链接
        internal_links = []
        external_links = []
        
        for i, link in enumerate(all_links[:50]):  # 只分析前50个链接
            try:
                if hasattr(link, 'attrib') and 'href' in link.attrib:
                    href = link.attrib['href']
                    text = link.text.strip() if hasattr(link, 'text') and link.text else ''
                    
                    # 分类链接
                    if href.startswith('/') or url in href:
                        internal_links.append((href, text))
                    else:
                        external_links.append((href, text))
            except Exception as e:
                print(f"  分析链接 {i+1} 失败: {e}")
        
        print(f"内部链接: {len(internal_links)}")
        print(f"外部链接: {len(external_links)}")
        
        # 分析内部链接模式
        print("\n=== 内部链接模式分析 ===")
        path_patterns = {}
        for href, text in internal_links:
            # 提取路径部分
            if href.startswith('/'):
                path = href
            elif url in href:
                path = href.replace(url, '')
            else:
                continue
            
            # 分析路径模式
            parts = path.split('/')
            if len(parts) >= 2:
                pattern = f"/{parts[1]}/"
                path_patterns[pattern] = path_patterns.get(pattern, 0) + 1
        
        # 排序并显示模式
        sorted_patterns = sorted(path_patterns.items(), key=lambda x: x[1], reverse=True)[:10]
        print("最常见的路径模式:")
        for pattern, count in sorted_patterns:
            print(f"  {pattern}: {count} 个链接")
        
        # 分析可能的文章链接选择器
        print("\n=== 可能的文章链接选择器 ===")
        possible_selectors = []
        
        # 基于路径模式生成选择器
        for pattern, count in sorted_patterns:
            if count >= 3:  # 至少出现3次
                # 生成选择器
                path_part = pattern.strip('/')
                selectors = [
                    f'a[href^="/{path_part}/"]',
                    f'a[href*="/{path_part}/"]'
                ]
                for sel in selectors:
                    try:
                        links = selector.css(sel)
                        if links:
                            possible_selectors.append((sel, len(links)))
                            print(f"  {sel}: {len(links)} 个元素")
                    except:
                        pass
        
        # 测试常见的选择器模式
        print("\n=== 测试常见选择器模式 ===")
        common_patterns = [
            '.article-item a',
            '.list-item a',
            'a.title',
            '.article a',
            'a[class*="title"]',
            '.news-item a',
            '.blog-item a',
            '.post-item a',
            '.content-item a',
            '.item a'
        ]
        
        for pattern in common_patterns:
            try:
                links = selector.css(pattern)
                if links:
                    possible_selectors.append((pattern, len(links)))
                    print(f"  {pattern}: {len(links)} 个元素")
            except:
                pass
        
        # 显示建议
        print("\n=== 建议 ===")
        if possible_selectors:
            # 排序并显示前5个
            sorted_selectors = sorted(possible_selectors, key=lambda x: x[1], reverse=True)[:5]
            print("推荐的文章链接选择器:")
            for sel, count in sorted_selectors:
                print(f"  {sel} (找到 {count} 个元素)")
        else:
            print("未找到合适的选择器，建议手动分析页面结构")
            
        # 提供手动分析指南
        print("\n=== 手动分析指南 ===")
        print("1. 打开浏览器，访问该网站")
        print("2. 右键点击一篇文章链接，选择'检查元素'")
        print("3. 查看链接的HTML结构，找到其class或id")
        print("4. 基于HTML结构创建选择器，例如:")
        print("   - 如果链接有class: 'a.article-link'")
        print("   - 如果链接在特定容器中: '.article-list a'")
        print("   - 如果链接路径有特定模式: 'a[href^=/article/]'")
        print("5. 使用以下命令添加网站并手动指定选择器:")
        print("   python src/scrapling_cli.py add 网站名称 网站URL --no-analyze")
        print("6. 然后编辑配置文件 config/scrapling_config.json，手动添加选择器")
        
    except Exception as e:
        print(f"分析失败: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='信息源分析工具')
    parser.add_argument('url', help='要分析的信息源URL')
    args = parser.parse_args()
    
    analyze_source(args.url)
