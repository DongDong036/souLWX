"""基于Scrapling框架的文章采集脚本"""

import json
import os
from datetime import datetime
from scrapling import Fetcher, Selector, DynamicFetcher

def load_cookies(cookie_file):
    """加载cookies"""
    if os.path.exists(cookie_file):
        try:
            with open(cookie_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载cookies失败: {e}")
    return {}

def collect_articles():
    """采集文章"""
    print("开始使用Scrapling采集文章...")
    
    # 配置
    cookie_file = 'cookies.json'
    output_file = 'broadcast_messages.json'
    
    # 加载cookies
    cookies = load_cookies(cookie_file)
    
    # 创建Fetcher
    fetcher = Fetcher()
    
    # 配置cookies
    if cookies:
        print("加载cookies成功")
    
    # 配置抓取器
    fetcher.configure(
        adaptive=True
    )
    
    # 抓取首页
    print("抓取韭研公社首页...")
    # 使用具体的首页URL，避免重定向到plan页面
    response = fetcher.get("https://www.jiuyangongshe.com/?tab=new")
    
    print(f"响应状态: {response.status}")
    print(f"响应类型: {type(response)}")
    
    # 查看响应对象的属性
    print("响应属性:")
    for attr in dir(response):
        if not attr.startswith('_') and not callable(getattr(response, attr)):
            print(f"  - {attr}")
    
    # 尝试获取不同的内容属性
    print("\n尝试获取内容:")
    if hasattr(response, 'text'):
        print(f"text属性存在: {len(response.text) if response.text else 0} 字符")
    if hasattr(response, 'content'):
        print(f"content属性存在: {len(response.content) if response.content else 0} 字符")
    if hasattr(response, 'body'):
        print(f"body属性存在: {len(response.body) if response.body else 0} 字符")
    
    if response.status == 200:
        print("\n首页抓取成功")
        
        # 查看响应内容
        content = ""
        if hasattr(response, 'text') and response.text:
            content = response.text
        elif hasattr(response, 'content') and response.content:
            content = response.content
        elif hasattr(response, 'body') and response.body:
            # 处理二进制内容
            if isinstance(response.body, bytes):
                try:
                    content = response.body.decode('utf-8')
                except:
                    content = str(response.body)
            else:
                content = response.body
        
        if content:
            print(f"响应内容长度: {len(content)} 字符")
            print(f"内容预览: {content[:500]}...")
            print(f"当前URL: {response.url}")
            
            # 解析页面
            selector = Selector(content)
            
            # 提取文章链接
            print("提取文章链接...")
            article_links = []
            
            # 尝试不同的选择器
            selectors = [
                'a[href^="/a/"]',
                'a[href*="/a/"]',
                '.article-item a',
                '.list-item a',
                'a.title',
                '.article a',
                'a[class*="title"]'
            ]
            
            for sel in selectors:
                try:
                    links = selector.css(sel)
                    print(f"选择器 {sel} 找到 {len(links)} 个元素")
                    for link in links:
                        # 尝试不同的方法获取href
                        try:
                            # 方法1: 使用attrib属性
                            if hasattr(link, 'attrib') and 'href' in link.attrib:
                                href = link.attrib['href']
                            # 方法2: 使用getattr
                            elif hasattr(link, 'get'):
                                href = link.get('href')
                            # 方法3: 尝试其他属性
                            else:
                                href = str(link)
                            
                            if href and '/a/' in href:
                                full_url = f"https://www.jiuyangongshe.com{href}" if href.startswith('/') else href
                                article_links.append(full_url)
                        except Exception as e:
                            print(f"获取href失败: {e}")
                except Exception as e:
                    print(f"选择器 {sel} 失败: {e}")
            
            # 去重
            article_links = list(set(article_links))
            print(f"找到 {len(article_links)} 篇文章")
            
            # 采集文章详情
            articles = []
            for i, url in enumerate(article_links[:10], 1):  # 只采集前10篇
                print(f"\n采集第 {i} 篇: {url}")
                try:
                    # 抓取文章详情
                    article_response = fetcher.get(url)
                    if article_response.status == 200:
                        # 处理响应内容
                        article_content = ""
                        if hasattr(article_response, 'text') and article_response.text:
                            article_content = article_response.text
                        elif hasattr(article_response, 'body') and article_response.body:
                            if isinstance(article_response.body, bytes):
                                try:
                                    article_content = article_response.body.decode('utf-8')
                                except:
                                    article_content = str(article_response.body)
                            else:
                                article_content = article_response.body
                        
                        article_selector = Selector(article_content)
                        
                        # 添加调试信息
                        print("\n文章页面结构预览:")
                        print(article_content[:1000] + "...")
                        
                        # 提取标题
                        title = ""
                        try:
                            # 从title标签提取
                            title_elems = article_selector.css('title')
                            if title_elems:
                                title = title_elems[0].text.strip()
                                # 移除"-韭研公社"后缀
                                if "-韭研公社" in title:
                                    title = title.replace("-韭研公社", "").strip()
                            
                            # 如果title标签中没有，尝试其他选择器
                            if not title:
                                title_selectors = ['h1', '.title', 'h2.title', '.article-title']
                                for sel in title_selectors:
                                    try:
                                        title_elems = article_selector.css(sel)
                                        if title_elems:
                                            title = title_elems[0].text.strip()
                                            if title:
                                                break
                                    except:
                                        continue
                        except Exception as e:
                            print(f"提取标题失败: {e}")
                        
                        # 提取作者
                        author = "未知"
                        try:
                            author_selectors = [
                                '.username-box .fs16-bold',
                                '.username-box .name .fs16-bold',
                                '.detail-container .fs16-bold',
                                '[data-v-234fd4b4].fs16-bold',
                                '.user-info .name',
                                '.author-name',
                                '.username',
                                '.user-name'
                            ]
                            for sel in author_selectors:
                                try:
                                    author_elems = article_selector.css(sel)
                                    if author_elems:
                                        author_text = author_elems[0].text.strip()
                                        if author_text and len(author_text) > 0 and len(author_text) < 50:
                                            author = author_text
                                            break
                                except:
                                    continue
                        except Exception as e:
                            print(f"提取作者失败: {e}")
                        
                        # 提取发布时间
                        publish_time = ""
                        try:
                            # 尝试从meta标签提取时间
                            meta_time_elems = article_selector.css('meta[property="article:published_time"]')
                            if meta_time_elems:
                                try:
                                    if hasattr(meta_time_elems[0], 'attrib') and 'content' in meta_time_elems[0].attrib:
                                        publish_time = meta_time_elems[0].attrib['content']
                                except:
                                    pass
                            
                            # 如果meta中没有，尝试其他选择器
                            if not publish_time:
                                time_selectors = ['.time', '.publish-time', '.post-time', '.article-time', '.date']
                                for sel in time_selectors:
                                    try:
                                        time_elems = article_selector.css(sel)
                                        if time_elems:
                                            publish_time = time_elems[0].text.strip()
                                            if publish_time:
                                                break
                                    except:
                                        continue
                        except Exception as e:
                            print(f"提取时间失败: {e}")
                        
                        # 提取内容
                        content = ""
                        try:
                            # 尝试从meta description提取
                            meta_elems = article_selector.css('meta[name="description"]')
                            if meta_elems:
                                try:
                                    # 尝试不同的方法获取content属性
                                    if hasattr(meta_elems[0], 'attrib') and 'content' in meta_elems[0].attrib:
                                        meta_content = meta_elems[0].attrib['content']
                                    else:
                                        # 尝试其他方法
                                        meta_content = str(meta_elems[0])
                                    if meta_content:
                                        content = meta_content.strip()
                                except:
                                    pass
                            
                            # 如果meta中没有，尝试其他选择器
                            if not content:
                                content_selectors = [
                                    '.text-box.text-justify.fsDetail',
                                    '.text-box',
                                    '.fsDetail',
                                    'section .text-box',
                                    'section',
                                    '.content',
                                    '.article-content',
                                    '.detail-container',
                                    '.article-body'
                                ]
                                for sel in content_selectors:
                                    try:
                                        content_elems = article_selector.css(sel)
                                        if content_elems:
                                            # 尝试获取文本
                                            try:
                                                content = content_elems[0].text.strip()
                                            except:
                                                # 尝试其他方法
                                                content = str(content_elems[0])
                                            if content:
                                                break
                                    except:
                                        continue
                            
                            # 如果还是没有内容，尝试获取所有p标签
                            if not content:
                                p_elems = article_selector.css('p')
                                content_parts = []
                                for p in p_elems:
                                    try:
                                        text = p.text.strip()
                                        if text and len(text) > 10:
                                            content_parts.append(text)
                                    except:
                                        continue
                                content = '\n'.join(content_parts)
                        except Exception as e:
                            print(f"提取内容失败: {e}")
                        
                        # 提取股票（改进版）
                        stocks = []
                        try:
                            import re
                            # 提取股票代码
                            stock_codes = re.findall(r'\b(60[0-9]{4}|00[0-9]{4}|30[0-9]{4})\b', content)
                            
                            # 去重
                            stock_codes = list(set(stock_codes))
                            
                            # 尝试从keywords meta标签提取股票名称
                            keywords = ""
                            meta_keywords_elems = article_selector.css('meta[name="keywords"]')
                            if meta_keywords_elems:
                                try:
                                    if hasattr(meta_keywords_elems[0], 'attrib') and 'content' in meta_keywords_elems[0].attrib:
                                        keywords = meta_keywords_elems[0].attrib['content']
                                except:
                                    pass
                            
                            # 提取股票名称
                            stock_names = []
                            if keywords:
                                # 从keywords中提取股票名称
                                stock_name_patterns = [
                                    r'([\u4e00-\u9fa5]{2,4})',  # 2-4个汉字的股票名称
                                    r'([\u4e00-\u9fa5]+[A-Za-z0-9]*[\u4e00-\u9fa5]+)',  # 包含字母数字的股票名称
                                ]
                                for pattern in stock_name_patterns:
                                    stock_names.extend(re.findall(pattern, keywords))
                            
                            # 去重
                            stock_names = list(set(stock_names))
                            
                            # 构建股票列表
                            stock_dict = {}
                            
                            # 添加从代码提取的股票
                            for code in stock_codes[:10]:  # 最多提取10个股票
                                stock_dict[code] = f"股票{code}"
                            
                            # 添加从名称提取的股票
                            for name in stock_names[:10]:  # 最多提取10个股票
                                stock_dict[f"NAME_{name}"] = name
                            
                            # 转换为列表
                            for code, name in stock_dict.items():
                                if code.startswith('NAME_'):
                                    stocks.append({'code': '', 'name': name})
                                else:
                                    stocks.append({'code': code, 'name': name})
                        except Exception as e:
                            print(f"提取股票失败: {e}")
                        
                        # 构建文章数据
                        article = {
                            'url': url,
                            'title': title,
                            'author': author,
                            'publish_time': publish_time,
                            'content': content,
                            'stocks': stocks,
                            'collect_time': datetime.now().isoformat(),
                            'word_count': len(content)
                        }
                        
                        articles.append(article)
                        print(f"  标题: {title}")
                        print(f"  作者: {author}")
                        print(f"  时间: {publish_time}")
                        print(f"  字数: {len(content)}")
                        print(f"  股票: {len(stocks)}")
                    else:
                        print(f"  抓取失败，状态码: {article_response.status}")
                except Exception as e:
                    print(f"  采集失败: {e}")
            
            # 保存数据
            if articles:
                print(f"\n成功采集 {len(articles)} 篇文章")
                
                # 保存到文件
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(articles, f, ensure_ascii=False, indent=2)
                print(f"数据保存到: {output_file}")
            else:
                print("未采集到任何文章")
        else:
            print("响应内容为空")
    else:
        print(f"首页抓取失败，状态码: {response.status}")

if __name__ == "__main__":
    collect_articles()
