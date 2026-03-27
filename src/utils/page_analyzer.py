"""
页面分析工具
功能：分析网页结构，提取时间等信息
"""

import requests
from scrapling import Selector

def analyze_page(url):
    """分析页面结构，提取时间等信息
    
    Args:
        url: 页面URL
        
    Returns:
        页面分析结果
    """
    print(f"分析页面: {url}")
    
    # 发送请求
    try:
        response = requests.get(url)
        response.raise_for_status()
    except Exception as e:
        print(f"请求失败: {e}")
        return None
    
    # 解析页面
    selector = Selector(response.text)
    
    # 提取时间相关元素
    print("\n=== 时间相关元素 ===")
    
    # 尝试不同的选择器
    time_selectors = [
        'meta[property="article:published_time"]',
        'meta[name="publish_time"]',
        'meta[name="datePublished"]',
        '.time',
        '.publish-time',
        '.post-time',
        '.date',
        '.article-time',
        '.article-meta time',
        '.meta time',
        'time',
        '.create-time',
        '.publishDate',
        '.date-time'
    ]
    
    for sel in time_selectors:
        try:
            elements = selector.css(sel)
            if elements:
                print(f"选择器 '{sel}' 找到 {len(elements)} 个元素")
                for i, elem in enumerate(elements):
                    if hasattr(elem, 'attrib'):
                        print(f"  元素 {i+1} 属性: {elem.attrib}")
                    if hasattr(elem, 'text') and elem.text:
                        print(f"  元素 {i+1} 文本: {elem.text.strip()}")
        except Exception as e:
            print(f"  选择器 '{sel}' 执行失败: {e}")
    
    # 提取所有meta标签
    print("\n=== 所有meta标签 ===")
    try:
        meta_elements = selector.css('meta')
        for elem in meta_elements[:20]:  # 只显示前20个
            if hasattr(elem, 'attrib'):
                attribs = elem.attrib
                if 'name' in attribs or 'property' in attribs:
                    print(f"  {attribs.get('name', attribs.get('property', ''))}: {attribs.get('content', '')}")
    except Exception as e:
        print(f"  提取meta标签失败: {e}")
    
    return "分析完成"

if __name__ == "__main__":
    # 分析一个具体的文章页面
    url = "https://www.jiuyangongshe.com/a/3fg8j25fyyu"
    analyze_page(url)
