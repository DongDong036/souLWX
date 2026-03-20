"""
韭研公社广播消息采集工具 - 稳定版
每次采集后刷新页面，避免 DOM 上下文错误
稳定采集最新 10 条广播消息
"""

from playwright.sync_api import sync_playwright
import json
import time
from datetime import datetime
import os

def main():
    print("=" * 60)
    print("韭研公社广播消息采集工具 - 稳定版")
    print("=" * 60)
    
    # 加载 cookies
    cookies_path = 'data/cookies/cookies.json'
    if not os.path.exists(cookies_path):
        print("[ERROR] 未找到 cookies 文件")
        return
    
    with open(cookies_path, 'r', encoding='utf-8') as f:
        cookies_data = json.load(f)
    
    print(f"[OK] Cookies 加载成功（保存时间：{cookies_data.get('timestamp', '未知')}）")
    
    broadcast_messages = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        try:
            # 访问首页
            print("\n正在访问首页...")
            context = browser.new_context(
                user_agent=cookies_data.get('user_agent', ''),
                viewport={'width': 1920, 'height': 1080}
            )
            context.add_cookies(cookies_data['cookies'])
            page = context.new_page()
            
            # 导航到社群页面
            page.goto('https://www.jiuyangongshe.com/', wait_until='load', timeout=60000)
            time.sleep(3)
            
            # 查找所有文章
            print("正在查找广播消息...")
            
            # 尝试多种选择器
            article_selectors = [
                '.jc-home-main .module',
                '.action-main .module',
                '.tab-content .item',
                '.time-article-item',
                '.community-bar li',
                '.broadcast-list li',
                '.message-list li'
            ]
            
            # 尝试从页面中获取文章链接
            print("正在查找文章链接...")
            
            # 尝试获取所有链接
            all_links = page.query_selector_all('a')
            article_links = []
            
            for link in all_links:
                href = link.get_attribute('href')
                # 匹配新的链接格式：/plan?pageType=search&stock_name=股票名称
                if href and ('/plan?pageType=search' in href or '/a/' in href) and len(href) > 10:
                    article_links.append(link)
            
            if not article_links:
                # 查看页面结构
                print("[ERROR] 未找到文章链接，查看页面结构...")
                page_source = page.inner_html('body')
                with open('page_debug.html', 'w', encoding='utf-8') as f:
                    f.write(page_source)
                print("[OK] 页面结构已保存到 page_debug.html")
                return
            
            print(f"[OK] 找到 {len(article_links)} 篇文章")
            
            # 处理每篇文章
            count = 0
            for i, link_elem in enumerate(article_links):
                if count >= 10:  # 采集 10 条就停止
                    break
                
                try:
                    # 提取标题
                    title = link_elem.inner_text().strip()
                    
                    # 跳过短标题
                    if len(title) < 5:
                        continue
                    
                    print(f"\n[{count+1}/10] {title[:50]}...")
                    
                    # 提取链接
                    article_url = link_elem.get_attribute('href')
                    if not article_url.startswith('http'):
                        article_url = 'https://www.jiuyangongshe.com' + article_url
                    
                    # 提取作者
                    author = '未知'
                    try:
                        # 尝试从文章元素中提取作者信息
                        author_elem = article_elem.query_selector('.user-name, .author, .username, .user, .poster')
                        if author_elem:
                            author = author_elem.inner_text().strip()
                        else:
                            # 尝试从其他可能的位置提取作者
                            author_elem = article_elem.query_selector('span:has-text("作者") + span')
                            if author_elem:
                                author = author_elem.inner_text().strip()
                    except Exception as e:
                        print(f"  [WARNING] 提取作者失败：{e}")
                    
                    # 提取时间（使用当前时间）
                    pub_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    # 采集完整内容
                    print(f"  正在采集完整内容...")
                    result = collect_article_content(browser, cookies_data, article_url)
                    
                    # 处理函数返回值
                    if isinstance(result, tuple) and len(result) == 2:
                        content, stocks = result
                    else:
                        content, stocks = result, []
                    
                    if content and len(content) > 100:
                        print(f"  [OK] 采集成功，{len(content)} 字符")
                        if stocks:
                            print(f"  [OK] 提取到 {len(stocks)} 只股票")
                        
                        message = {
                            'index': count + 1,
                            'title': title,
                            'author': author,
                            'publish_time': pub_time,
                            'url': article_url,
                            'content': content,
                            'stocks': stocks,
                            'collected_time': datetime.now().isoformat()
                        }
                        broadcast_messages.append(message)
                        count += 1
                    else:
                        print(f"  [ERROR] 内容太短或采集失败")
                    
                except Exception as e:
                    print(f"  [ERROR] 处理失败：{e}")
                    continue
            
            # 保存结果
            if broadcast_messages:
                save_results(broadcast_messages)
                print("\n" + "=" * 60)
                print(f"采集完成！共 {len(broadcast_messages)} 条广播消息")
                print("=" * 60)
            else:
                print("\n⚠️  未采集到任何广播消息")
        
        finally:
            browser.close()

def extract_stocks(content):
    """从文章内容中提取股票信息"""
    import re
    
    # 股票代码模式：
    # 1. 深交所：SZ000001, SZ300001
    # 2. 上交所：SH600000
    # 3. 简写形式：600000, 000001, 300001
    stock_code_pattern = r'(?:SZ|SH)?\d{6}'
    
    # 提取所有匹配的股票代码
    stock_codes = re.findall(stock_code_pattern, content)
    
    # 标准化股票代码格式
    standardized_codes = []
    for code in stock_codes:
        code = code.upper()
        # 如果没有前缀，根据代码长度判断交易所
        if len(code) == 6:
            if code.startswith('6'):
                standardized_codes.append(f'SH{code}')
            else:
                standardized_codes.append(f'SZ{code}')
        else:
            standardized_codes.append(code)
    
    # 去重
    unique_stocks = list(set(standardized_codes))
    return unique_stocks

def collect_article_content(browser, cookies_data, article_url):
    """采集文章完整内容 - 每次创建新的页面上下文"""
    try:
        # 创建新的页面上下文（避免 DOM 上下文错误）
        context = browser.new_context(
            user_agent=cookies_data.get('user_agent', ''),
            viewport={'width': 1920, 'height': 1080}
        )
        context.add_cookies(cookies_data['cookies'])
        page = context.new_page()
        
        # 访问文章详情页
        page.goto(article_url, wait_until='networkidle', timeout=30000)
        time.sleep(3)
        
        # 尝试多种选择器提取内容
        content = ""
        html_content = ""
        
        # 方法 1: 尝试常见的内容选择器
        content_selectors = [
            '.pre',
            '.expound',
            '.article-content',
            '.article-detail',
            '[class*="article-content"]',
            '[class*="detail-content"]',
            'article',
            '.content',
            '.trade-plan-section'
        ]
        
        for selector in content_selectors:
            try:
                content_elem = page.query_selector(selector)
                if content_elem:
                    # 获取HTML内容（包含图片）
                    html_content = content_elem.inner_html().strip()
                    # 同时获取纯文本内容
                    content = content_elem.inner_text().strip()
                    if len(content) > 100:
                        break
            except:
                continue
        
        # 方法 2: 如果上面的选择器都不行，获取所有段落
        if not content or len(content) < 100:
            try:
                paragraphs = page.query_selector_all('p')
                if paragraphs:
                    # 获取HTML段落
                    para_html = []
                    para_texts = []
                    for p in paragraphs:
                        para_html.append(p.inner_html().strip())
                        para_texts.append(p.inner_text().strip())
                    html_content = '\n\n'.join(para_html)
                    content = '\n\n'.join([t for t in para_texts if len(t) > 20])
            except:
                pass
        
        # 方法 3: 获取整个页面的主要文本
        if not content or len(content) < 100:
            try:
                body_text = page.inner_text('body')
                lines = body_text.split('\n')
                # 过滤出有意义的行
                main_lines = []
                for line in lines:
                    line = line.strip()
                    if len(line) > 30 and not any(x in line for x in ['登录', '注册', '首页', '导航', '分享', '点赞', '评论']):
                        main_lines.append(line)
                content = '\n'.join(main_lines[:50])
            except:
                pass
        
        # 如果有HTML内容，使用HTML内容，否则使用纯文本
        if html_content:
            content = html_content
        
        # 提取股票信息
        stocks = extract_stocks(content)
        
        # 关闭页面
        context.close()
        
        return content, stocks
        
    except Exception as e:
        print(f"    采集失败：{e}")
        return ""

def save_results(messages):
    """保存采集结果（增量存储）"""
    timestamp = datetime.now().isoformat()
    
    # 读取现有数据
    existing_articles = []
    db_path = 'data/database/articles_database.json'
    if os.path.exists(db_path):
        try:
            with open(db_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                existing_articles = existing_data.get('articles', [])
                print(f"[OK] 已读取 {len(existing_articles)} 篇现有文章")
        except:
            print("[WARN] 读取现有数据失败，将创建新文件")
    
    # 增量存储 - 去重
    existing_urls = set(article.get('url', '') for article in existing_articles)
    new_articles = []
    
    for message in messages:
        if message.get('url', '') not in existing_urls:
            new_articles.append(message)
            existing_urls.add(message.get('url', ''))
    
    if new_articles:
        # 合并数据
        all_articles = new_articles + existing_articles
        print(f"[OK] 新增 {len(new_articles)} 篇文章，总计 {len(all_articles)} 篇")
    else:
        all_articles = existing_articles
        print("[OK] 没有新增文章")
    
    # 按时间降序排序
    all_articles.sort(key=lambda x: x.get('publish_time', ''), reverse=True)
    
    # JSON 格式（完整数据）
    data = {
        'timestamp': timestamp,
        'total': len(all_articles),
        'messages': all_articles
    }
    
    json_path = 'data/database/broadcast_full.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n[OK] JSON 已保存：{json_path}")
    
    # 同时保存为 GUI 程序使用的格式
    gui_data = {
        'timestamp': timestamp,
        'total': len(all_articles),
        'articles': all_articles
    }
    
    db_path = 'data/database/articles_database.json'
    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(gui_data, f, ensure_ascii=False, indent=2)
    
    print(f"[OK] GUI 数据已保存：{db_path}")
    
    # Markdown 格式（推荐查看）
    md_path = 'data/database/broadcast_full.md'
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# 韭研公社广播消息采集\n\n")
        f.write(f"采集时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"共 {len(messages)} 条消息\n\n")
        f.write("=" * 80 + "\n\n")
        
        for msg in messages:
            f.write(f"## {msg['index']}. {msg['title']}\n\n")
            f.write(f"**作者**: {msg['author']}\n\n")
            f.write(f"**发布时间**: {msg['publish_time']}\n\n")
            f.write(f"**原文链接**: {msg['url']}\n\n")
            f.write(f"**采集时间**: {msg['collected_time']}\n\n")
            f.write("---\n\n")
            f.write("### 正文内容\n\n")
            
            # 整理内容格式
            content = msg['content']
            lines = content.split('\n')
            cleaned = [l.strip() for l in lines if l.strip()]
            content = '\n\n'.join(cleaned)
            
            f.write(content)
            f.write("\n\n")
            f.write("=" * 80 + "\n\n")
        
        f.write(f"\n**文档生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    print(f"[OK] Markdown 已保存：broadcast_full.md")
    
    # 摘要格式
    with open('broadcast_summary.txt', 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("韭研公社广播消息摘要\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"采集时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"消息总数：{len(messages)}\n\n")
        f.write("=" * 80 + "\n\n")
        
        for msg in messages:
            f.write(f"【{msg['index']}】{msg['title']}\n")
            f.write(f"作者：{msg['author']}\n")
            f.write(f"时间：{msg['publish_time']}\n")
            f.write(f"链接：{msg['url']}\n")
            
            # 前 300 字摘要
            content = msg['content']
            if len(content) > 300:
                summary = content[:300] + "..."
            else:
                summary = content
            f.write(f"摘要：{summary}\n")
            f.write("\n" + "-" * 80 + "\n\n")
        
        f.write("=" * 80 + "\n")
        f.write("完整内容请查看：broadcast_full.md\n")
        f.write("=" * 80 + "\n")
    
    print(f"[OK] 摘要已保存：broadcast_summary.txt")

if __name__ == '__main__':
    main()
