"""
分析同花顺行业研究页面
功能：分析 https://stock.10jqka.com.cn/bkfy_list/ 页面结构
"""

import requests
from bs4 import BeautifulSoup

def analyze_10jqka():
    """分析同花顺行业研究页面
    """
    url = "https://stock.10jqka.com.cn/bkfy_list/"
    print(f"分析页面: {url}")
    
    # 发送请求，添加请求头模拟浏览器
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        print(f"请求成功，状态码: {response.status_code}")
    except Exception as e:
        print(f"请求失败: {e}")
        return
    
    # 处理响应内容
    content = response.text
    print(f"页面长度: {len(content)} 字符")
    
    # 解析页面
    soup = BeautifulSoup(content, 'html.parser')
    
    # 提取标题
    print("\n=== 页面标题 ===")
    try:
        title = soup.title.string
        print(f"标题: {title}")
    except Exception as e:
        print(f"提取标题失败: {e}")
    
    # 提取行业研究文章链接
    print("\n=== 行业研究文章链接 ===")
    try:
        # 尝试不同的选择器
        selectors = [
            '.list-content .list-item a',
            '.article-list .article-item a',
            '.list-item a',
            '.item a',
            'a[href^="/bkfy_detail/"]',
            'a[href*="/bkfy_detail/"]'
        ]
        
        found = False
        for sel in selectors:
            links = soup.select(sel)
            if links:
                print(f"选择器 '{sel}' 找到 {len(links)} 个元素")
                for i, link in enumerate(links[:10], 1):
                    try:
                        href = link.get('href', '')
                        text = link.get_text(strip=True) if link.get_text() else ''
                        print(f"  {i}. {text} -> {href}")
                    except Exception as e:
                        print(f"  解析链接 {i} 失败: {e}")
                found = True
                break
        if not found:
            print("未找到行业研究文章链接")
            
            # 打印所有链接，看看页面结构
            print("\n=== 所有链接 ===")
            all_links = soup.find_all('a')
            print(f"找到 {len(all_links)} 个链接")
            for i, link in enumerate(all_links[:20], 1):
                try:
                    href = link.get('href', '')
                    text = link.get_text(strip=True) if link.get_text() else ''
                    if href and text:
                        print(f"  {i}. {text} -> {href}")
                except Exception as e:
                    pass
    except Exception as e:
        print(f"提取链接失败: {e}")
    
    # 提取页面结构
    print("\n=== 页面结构 ===")
    try:
        # 提取主要容器
        containers = soup.select('.main-content, .content, .list-content')
        if containers:
            print(f"找到 {len(containers)} 个主要容器")
            for i, container in enumerate(containers, 1):
                class_name = container.get('class', [])
                print(f"  容器 {i} 类名: {class_name}")
                # 提取容器内的子元素
                child_elements = container.find_all(['div', 'ul', 'li', 'a'])
                print(f"  子元素数量: {len(child_elements)}")
        else:
            print("未找到主要容器")
            
            # 打印页面的主要结构
            print("\n=== 页面主要结构 ===")
            body = soup.body
            if body:
                for child in body.children:
                    if child.name:
                        print(f"  {child.name} - {child.get('class', [])}")
    except Exception as e:
        print(f"提取页面结构失败: {e}")
    
    # 提取脚本和样式
    print("\n=== 页面特性 ===")
    try:
        # 检查是否使用了JavaScript渲染
        scripts = soup.find_all('script')
        print(f"脚本数量: {len(scripts)}")
        
        # 检查是否有异步加载的内容
        async_scripts = [script for script in scripts if script.get('async')]
        print(f"异步脚本数量: {len(async_scripts)}")
        
        # 检查是否有API调用
        api_calls = [script for script in scripts if script.string and ('api' in script.string or 'ajax' in script.string)]
        print(f"可能的API调用脚本数量: {len(api_calls)}")
        
        # 检查是否有JSON数据
        json_data = [script for script in scripts if script.string and ('window.' in script.string or 'var ' in script.string)]
        print(f"可能包含数据的脚本数量: {len(json_data)}")
        
        # 检查是否有动态加载的内容
        if json_data:
            print("\n=== 可能的动态数据 ===")
            for i, script in enumerate(json_data[:2], 1):
                if script.string:
                    # 打印前200个字符
                    print(f"  脚本 {i}: {script.string[:200]}...")
    except Exception as e:
        print(f"提取页面特性失败: {e}")

if __name__ == "__main__":
    analyze_10jqka()
