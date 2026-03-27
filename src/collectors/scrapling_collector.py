"""
Scrapling通用采集器
功能：使用配置管理器管理多个网站的采集，支持自愈机制
"""

import os
import re
import json
from datetime import datetime
from urllib.parse import urlparse, urljoin
from scrapling import Fetcher, Selector
from collectors.scrapling_config import ScraplingConfigManager
from database.db_manager import DatabaseManager

class ScraplingCollector:
    def __init__(self, config_file='config/scrapling_config.json'):
        self.config_manager = ScraplingConfigManager(config_file)
    
    def collect_from_website(self, website_name, max_articles=10):
        """从指定网站采集文章
        
        Args:
            website_name: 网站名称
            max_articles: 最大采集文章数量
            
        Returns:
            (成功标志, 消息, 采集的文章列表)
        """
        # 获取网站配置
        config = self.config_manager.get_website_config(website_name)
        if not config:
            return False, f"未找到网站配置: {website_name}", []
        
        if not config.get('enabled', True):
            return False, f"网站 {website_name} 已禁用", []
        
        url = config['url']
        selectors = config['selectors']
        
        print(f"开始从 {website_name} 采集文章...")
        print(f"网站URL: {url}")
        
        # 创建Fetcher
        fetcher = Fetcher()
        fetcher.configure(adaptive=True)
        
        # 抓取首页
        try:
            response = fetcher.get(url)
            if response.status != 200:
                return False, f"首页抓取失败，状态码: {response.status}", []
        except Exception as e:
            return False, f"抓取首页失败: {e}", []
        
        # 处理响应内容
        content = ""
        if hasattr(response, 'body') and response.body:
            if isinstance(response.body, bytes):
                # 尝试多种编码
                encodings = ['utf-8', 'gbk', 'gb2312', 'iso-8859-1']
                for encoding in encodings:
                    try:
                        content = response.body.decode(encoding)
                        # 检查是否有乱码
                        if '\\x' not in str(content):
                            break
                    except:
                        continue
                if not content:
                    content = str(response.body)
            else:
                content = response.body
        elif hasattr(response, 'text') and response.text:
            content = response.text
        
        if not content:
            return False, "响应内容为空", []
        
        # 解析页面
        selector = Selector(content)
        
        # 提取文章链接
        article_links = []
        link_selectors = selectors.get('article_links', [])
        
        print(f"提取文章链接，使用 {len(link_selectors)} 个选择器...")
        
        for sel in link_selectors:
            try:
                links = selector.css(sel)
                for link in links:
                    try:
                        if hasattr(link, 'attrib') and 'href' in link.attrib:
                            href = link.attrib['href']
                        else:
                            href = str(link)
                        
                        if href:
                            # 构建完整URL
                            if href.startswith('http://') or href.startswith('https://'):
                                full_url = href
                            elif href.startswith('/'):
                                # 从基础URL构建完整URL
                                parsed_url = urlparse(url)
                                base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                                full_url = urljoin(base_url, href)
                            else:
                                full_url = urljoin(url, href)
                            
                            # 提取链接文本
                            text = ""
                            if hasattr(link, 'text') and link.text:
                                text = link.text.strip()
                            
                            # 过滤不符合特征的链接
                            if self._is_valid_article_link(full_url, text):
                                article_links.append(full_url)
                    except Exception as e:
                        print(f"  解析链接失败: {e}")
                        continue
            except Exception as e:
                print(f"  选择器 {sel} 执行失败: {e}")
                continue
        
        # 去重
        article_links = list(set(article_links))
        print(f"找到 {len(article_links)} 篇文章")
        
        if not article_links:
            return False, "未找到文章链接", []
        
        # 采集文章详情
        articles = []
        detail_selectors = selectors.get('article_detail', {})
        
        for i, article_url in enumerate(article_links[:max_articles], 1):
            print(f"\n采集第 {i} 篇: {article_url}")
            try:
                # 抓取文章详情
                article_response = fetcher.get(article_url)
                if article_response.status != 200:
                    print(f"  抓取失败，状态码: {article_response.status}")
                    continue
                
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
                
                if not article_content:
                    print("  内容为空")
                    continue
                
                article_selector = Selector(article_content)
                
                # 提取标题
                title = self._extract_field(article_selector, detail_selectors.get('title', []), '标题')
                
                # 提取作者
                author = self._extract_field(article_selector, detail_selectors.get('author', []), '作者', default='未知')
                
                # 提取发布时间
                publish_time = self._extract_field(article_selector, detail_selectors.get('publish_time', []), '时间')
                
                # 提取内容
                content = self._extract_field(article_selector, detail_selectors.get('content', []), '内容')
                
                # 提取股票
                stocks = []  # 取消股票提取
                
                # 构建文章数据
                article = {
                    'url': article_url,
                    'title': title,
                    'author': author,
                    'publish_time': publish_time,
                    'content': content,
                    'stocks': stocks,
                    'collect_time': datetime.now().isoformat(),
                    'word_count': len(content),
                    'source': website_name
                }
                
                articles.append(article)
                print(f"  标题: {title}")
                print(f"  作者: {author}")
                print(f"  时间: {publish_time}")
                print(f"  字数: {len(content)}")
                print(f"  股票: {len(stocks)}")
                
            except Exception as e:
                print(f"  采集失败: {e}")
                continue
        
        if not articles:
            return False, "未采集到任何文章", []
        
        print(f"\n成功采集 {len(articles)} 篇文章")
        return True, f"成功采集 {len(articles)} 篇文章", articles
    
    def _fix_encoding(self, text):
        """修复编码问题
        
        Args:
            text: 可能有编码问题的文本
            
        Returns:
            修复后的文本
        """
        if not text:
            return text
        
        # 尝试修复乱码
        try:
            # 检查是否是乱码（包含\x）
            if '\\x' in str(text):
                # 尝试将乱码转换为正确的编码
                # 首先尝试GBK编码
                try:
                    # 将字符串转换为字节，然后用GBK解码
                    # 注意：这里需要处理Python的字符串表示形式
                    import ast
                    # 尝试将字符串转换为字节
                    byte_text = ast.literal_eval(f"b'{text}'")
                    return byte_text.decode('gbk')
                except:
                    # 尝试其他编码
                    try:
                        return text.encode('iso-8859-1').decode('gbk')
                    except:
                        pass
            
            # 尝试直接解码
            try:
                return text.encode('iso-8859-1').decode('gbk')
            except:
                pass
                
        except Exception as e:
            print(f"  修复编码失败: {e}")
        
        return text
    
    def _extract_field(self, selector, selectors, field_name, default=''):
        """提取字段值
        
        Args:
            selector: 页面选择器
            selectors: 选择器列表
            field_name: 字段名称
            default: 默认值
            
        Returns:
            提取的字段值
        """
        for sel in selectors:
            try:
                elements = selector.css(sel)
                if elements:
                    # 处理meta标签
                    if sel.startswith('meta['):
                        if hasattr(elements[0], 'attrib') and 'content' in elements[0].attrib:
                            text = elements[0].attrib['content'].strip()
                            return self._fix_encoding(text)
                    else:
                        # 处理普通元素
                        text = elements[0].text
                        if text:
                            return self._fix_encoding(text.strip())
            except Exception as e:
                print(f"  提取{field_name}失败: {e}")
                continue
        
        # 针对同花顺网站的特殊处理
        if field_name == '时间' or field_name == '发布时间':
            try:
                # 尝试从特定的时间元素中提取
                time_elements = selector.css('span.text-black\\/40.text-\\[12px\\]')
                if time_elements:
                    text = time_elements[0].text
                    if text:
                        return self._fix_encoding(text.strip())
                
                # 尝试从包含日期格式的元素中提取
                all_spans = selector.css('span')
                for span in all_spans:
                    if hasattr(span, 'text') and span.text:
                        text = span.text.strip()
                        # 匹配日期时间格式
                        import re
                        if re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$', text):
                            return text
            except Exception as e:
                print(f"  同花顺时间提取失败: {e}")
        
        # 针对同花顺网站的作者信息提取
        elif field_name == '作者' or field_name == '来源':
            try:
                # 尝试从多种来源信息中提取
                source_selectors = [
                    'div.flex.text-black\\/40.text-\\[12px\\]',
                    'div.article-info',
                    'div.author-info',
                    'div.source-info',
                    'p.article-source',
                    'span.source',
                    'span.author',
                    'div.info',
                    'div.article-meta',
                    'div.meta-info'
                ]
                
                for sel in source_selectors:
                    source_elements = selector.css(sel)
                    if source_elements:
                        for element in source_elements:
                            text = element.text
                            if text:
                                # 提取来源后面的内容
                                if '来源：' in text:
                                    author = text.split('来源：')[1].strip()
                                    # 如果包含链接，提取链接文本
                                    link_elements = element.css('a')
                                    if link_elements:
                                        link_text = link_elements[0].text
                                        if link_text:
                                            author = link_text.strip()
                                    return self._fix_encoding(author)
                                elif '作者：' in text:
                                    author = text.split('作者：')[1].strip()
                                    return self._fix_encoding(author)
                                elif '来源' in text:
                                    # 尝试提取来源信息
                                    import re
                                    match = re.search(r'来源[：:](.*)', text)
                                    if match:
                                        author = match.group(1).strip()
                                        return self._fix_encoding(author)
                                elif '作者' in text:
                                    # 尝试提取作者信息
                                    import re
                                    match = re.search(r'作者[：:](.*)', text)
                                    if match:
                                        author = match.group(1).strip()
                                        return self._fix_encoding(author)
                
                # 尝试从所有包含链接的元素中提取
                all_links = selector.css('a')
                for link in all_links:
                    text = link.text
                    if text and len(text) > 2 and len(text) < 20:
                        # 检查是否可能是作者名称
                        import re
                        if not re.match(r'^https?://', text) and not re.match(r'^#', text):
                            # 检查链接是否包含作者相关关键词
                            href = link.attrib.get('href', '')
                            if 'author' in href or 'source' in href or 'user' in href:
                                return self._fix_encoding(text.strip())
            except Exception as e:
                print(f"  同花顺作者提取失败: {e}")
        
        # 针对同花顺网站的文章内容提取
        elif field_name == '内容':
            try:
                # 尝试从meta description中提取
                meta_elements = selector.css('meta[name="description"]')
                if meta_elements and hasattr(meta_elements[0], 'attrib') and 'content' in meta_elements[0].attrib:
                    content = meta_elements[0].attrib['content'].strip()
                    if content:
                        return self._fix_encoding(content)
                
                # 尝试从页面主体内容中提取
                content_elements = selector.css('.article-content, .post-content, .content, .text-content')
                if content_elements:
                    content = ''
                    for element in content_elements:
                        if hasattr(element, 'text') and element.text:
                            content += element.text.strip() + '\n'
                    if content:
                        return self._fix_encoding(content.strip())
            except Exception as e:
                print(f"  同花顺内容提取失败: {e}")
                
        return default
    

    
    def _extract_stocks(self, selector, selectors, content):
        """提取股票信息
        
        Args:
            selector: 页面选择器
            selectors: 选择器列表
            content: 文章内容
            
        Returns:
            股票列表
        """
        stocks = []
        stock_dict = {}
        
        try:
            # 从内容中提取股票代码
            stock_codes = re.findall(r'\b(60[0-9]{4}|00[0-9]{4}|30[0-9]{4})\b', content)
            stock_codes = list(set(stock_codes))
            
            for code in stock_codes[:10]:  # 最多提取10个股票
                stock_dict[code] = f"股票{code}"
            
            # 从选择器中提取股票名称
            for sel in selectors:
                try:
                    elements = selector.css(sel)
                    if elements:
                        if hasattr(elements[0], 'attrib') and 'content' in elements[0].attrib:
                            keywords = elements[0].attrib['content']
                            # 提取股票名称
                            stock_name_patterns = [
                                r'([\u4e00-\u9fa5]{2,4})',
                                r'([\u4e00-\u9fa5]+[A-Za-z0-9]*[\u4e00-\u9fa5]+)',
                            ]
                            for pattern in stock_name_patterns:
                                stock_names = re.findall(pattern, keywords)
                                for name in stock_names[:10]:
                                    stock_dict[f"NAME_{name}"] = name
                except Exception as e:
                    print(f"  提取股票名称失败: {e}")
                    continue
            
            # 转换为列表
            for code, name in stock_dict.items():
                if code.startswith('NAME_'):
                    stocks.append({'code': '', 'name': name})
                else:
                    stocks.append({'code': code, 'name': name})
        except Exception as e:
            print(f"  提取股票失败: {e}")
        
        return stocks
    
    def collect_from_all_websites(self, max_articles_per_website=10):
        """从所有配置的网站采集文章
        
        Args:
            max_articles_per_website: 每个网站最大采集文章数量
            
        Returns:
            所有采集的文章列表
        """
        all_articles = []
        websites = self.config_manager.list_websites()
        
        for website in websites:
            success, message, articles = self.collect_from_website(website, max_articles_per_website)
            if success:
                all_articles.extend(articles)
            print(f"{website}: {message}")
        
        return all_articles
    
    def collect_from_url(self, url, max_articles=10):
        """从指定URL采集文章
        
        Args:
            url: 网站URL
            max_articles: 最大采集文章数量
            
        Returns:
            采集的文章列表
        """
        print(f"开始从URL采集文章: {url}")
        
        # 创建Fetcher
        fetcher = Fetcher()
        fetcher.configure(adaptive=True)
        
        # 抓取首页
        try:
            response = fetcher.get(url)
            if response.status != 200:
                print(f"首页抓取失败，状态码: {response.status}")
                return []
        except Exception as e:
            print(f"抓取首页失败: {e}")
            return []
        
        # 处理响应内容
        content = ""
        if hasattr(response, 'body') and response.body:
            if isinstance(response.body, bytes):
                # 尝试多种编码
                encodings = ['utf-8', 'gbk', 'gb2312', 'iso-8859-1']
                for encoding in encodings:
                    try:
                        content = response.body.decode(encoding)
                        # 检查是否有乱码
                        if '\\x' not in str(content):
                            break
                    except:
                        continue
                if not content:
                    content = str(response.body)
            else:
                content = response.body
        elif hasattr(response, 'text') and response.text:
            content = response.text
        
        if not content:
            print("响应内容为空")
            return []
        
        # 解析页面
        selector = Selector(content)
        
        # 分析网站结构，提取选择器
        config_manager = ScraplingConfigManager()
        selectors = config_manager.analyze_website(url)
        
        # 提取文章链接
        article_links = []
        link_selectors = selectors.get('article_links', [])
        
        print(f"提取文章链接，使用 {len(link_selectors)} 个选择器...")
        
        for sel in link_selectors:
            try:
                links = selector.css(sel)
                for link in links:
                    try:
                        if hasattr(link, 'attrib') and 'href' in link.attrib:
                            href = link.attrib['href']
                        else:
                            href = str(link)
                        
                        if href:
                            # 构建完整URL
                            if href.startswith('http://') or href.startswith('https://'):
                                full_url = href
                            elif href.startswith('/'):
                                # 从基础URL构建完整URL
                                parsed_url = urlparse(url)
                                base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                                full_url = urljoin(base_url, href)
                            else:
                                full_url = urljoin(url, href)
                            
                            # 提取链接文本
                            text = ""
                            if hasattr(link, 'text') and link.text:
                                text = link.text.strip()
                            
                            # 过滤不符合特征的链接
                            if self._is_valid_article_link(full_url, text):
                                article_links.append(full_url)
                    except Exception as e:
                        print(f"  解析链接失败: {e}")
                        continue
            except Exception as e:
                print(f"  选择器 {sel} 执行失败: {e}")
                continue
        
        # 去重
        article_links = list(set(article_links))
        print(f"找到 {len(article_links)} 篇文章")
        
        if not article_links:
            print("未找到文章链接")
            return []
        
        # 采集文章详情
        articles = []
        detail_selectors = selectors.get('article_detail', {})
        
        for i, article_url in enumerate(article_links[:max_articles], 1):
            print(f"\n采集第 {i} 篇: {article_url}")
            try:
                # 抓取文章详情
                article_response = fetcher.get(article_url)
                if article_response.status != 200:
                    print(f"  抓取失败，状态码: {article_response.status}")
                    continue
                
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
                
                if not article_content:
                    print("  内容为空")
                    continue
                
                article_selector = Selector(article_content)
                
                # 提取标题
                title = self._extract_field(article_selector, detail_selectors.get('title', []), '标题')
                
                # 提取作者
                author = self._extract_field(article_selector, detail_selectors.get('author', []), '作者')
                
                # 提取发布时间
                publish_time = self._extract_field(article_selector, detail_selectors.get('publish_time', []), '发布时间')
                
                # 提取内容
                content = self._extract_field(article_selector, detail_selectors.get('content', []), '内容')
                
                # 提取股票信息
                stocks = []  # 取消股票提取
                
                # 构建文章对象
                article = {
                    'url': article_url,
                    'title': title,
                    'author': author,
                    'publish_time': publish_time,
                    'content': content,
                    'stocks': stocks,
                    'collect_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'word_count': len(content)
                }
                
                articles.append(article)
                
                print(f"  标题: {title}")
                print(f"  作者: {author}")
                print(f"  时间: {publish_time}")
                print(f"  字数: {len(content)}")
                print(f"  股票: {len(stocks)}")
                
            except Exception as e:
                print(f"  采集失败: {e}")
                continue
        
        return articles
    
    def _is_valid_article_link(self, url, text):
        """判断是否为有效的文章链接
        
        Args:
            url: 链接URL
            text: 链接文本
            
        Returns:
            bool: 是否为有效的文章链接
        """
        # 过滤条件
        
        # 1. 过滤空文本链接
        if not text or len(text.strip()) < 5:
            return False
        
        # 2. 过滤数字分页链接
        if text.isdigit():
            return False
        
        # 3. 过滤JavaScript链接
        if 'javascript:' in url or 'void(0)' in url:
            return False
        
        # 4. 过滤邮箱链接
        if 'mailto:' in url:
            return False
        
        # 5. 过滤非文章链接格式
        article_patterns = [
            r'\d{6,}',  # 包含6位以上数字（文章ID）
            r'/\d{4}\d{2}\d{2}/',  # 包含日期格式
            r'\.shtml$',  # 以.shtml结尾
            r'/article/',  # 包含/article/路径
            r'/a/',  # 包含/a/路径
            r'/post/'  # 包含/post/路径
        ]
        
        import re
        has_article_pattern = False
        for pattern in article_patterns:
            if re.search(pattern, url):
                has_article_pattern = True
                break
        
        if not has_article_pattern:
            # 对于同花顺网站的特殊处理
            if 'stock.10jqka.com.cn' in url or 'yuanchuang.10jqka.com.cn' in url:
                # 同花顺的文章链接通常包含日期和文章ID
                if re.search(r'/\d{8}/c\d+\.shtml$', url):
                    return True
                # 同花顺原创文章链接
                if 'yuanchuang.10jqka.com.cn' in url and re.search(r'/\d{8}/c\d+\.shtml$', url):
                    return True
            else:
                return False
        
        # 6. 过滤导航链接
        navigation_keywords = [
            '首页', '导航', '菜单', '关于我们', '联系我们', '登录', '注册',
            '首页', '财经', '股票', '必读', '全球', '数据中心', '行情中心',
            '理财', '同顺号', '期货', '其他', '下载中心', '滚动新闻', '市场',
            '股市温度计', '行业', '要闻', '主力', '新三板', 'B股', '原创',
            '事件掘金', '异动观察', '网上商城', '股民学校', '量化回测', '私募之家',
            '银柿财经', '企洞察', 'PC免费版', 'PC新一代', '期货PC版',
            '四大报精华', '网站地图'
        ]
        
        for keyword in navigation_keywords:
            if keyword in text:
                return False
        
        return True

    def save_articles(self, articles, output_file='data/database/articles_database.json'):
        """保存采集的文章
        
        Args:
            articles: 文章列表
            output_file: 输出文件路径（保持向后兼容）
        """
        # 使用数据库保存文章
        db_manager = DatabaseManager()
        
        # 保存新文章
        new_count = 0
        for article in articles:
            if isinstance(article, dict) and 'url' in article:
                if db_manager.save_article(article):
                    new_count += 1
        
        # 备份数据库
        backup_path = db_manager.backup_database()
        if backup_path:
            print(f"数据库备份成功: {backup_path}")
        
        # 加载所有文章以获取总数
        all_articles = db_manager.load_articles()
        total_count = len(all_articles)
        
        print(f"成功保存 {new_count} 篇文章，总共有 {total_count} 篇文章")
        
        # 关闭数据库连接
        db_manager.close()
        
        return total_count

if __name__ == "__main__":
    # 示例用法
    collector = ScraplingCollector()
    
    # 从特定网站采集
    success, message, articles = collector.collect_from_website('韭研公社', max_articles=5)
    print(f"采集结果: {success}, {message}")
    
    # 保存文章
    if articles:
        collector.save_articles(articles)
