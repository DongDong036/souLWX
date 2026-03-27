"""
Scrapling框架配置管理
功能：管理多个网站的采集配置，支持自动分析和自愈机制
"""

import json
import os
from scrapling import Fetcher, Selector
from datetime import datetime

class ScraplingConfigManager:
    def __init__(self, config_file='config/scrapling_config.json'):
        self.config_file = config_file
        self.configs = self.load_configs()
    
    def load_configs(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                return {}
        return {}
    
    def save_configs(self):
        """保存配置文件"""
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.configs, f, ensure_ascii=False, indent=2)
    
    def add_website(self, name, url, selectors=None, auto_analyze=True):
        """添加新网站配置
        
        Args:
            name: 网站名称
            url: 网站首页URL
            selectors: 手动指定的选择器
            auto_analyze: 是否自动分析网站结构
        """
        if auto_analyze and selectors is None:
            selectors = self.analyze_website(url)
        
        self.configs[name] = {
            'url': url,
            'selectors': selectors,
            'last_updated': datetime.now().isoformat(),
            'enabled': True
        }
        self.save_configs()
        return selectors
    
    def analyze_website(self, url):
        """自动分析网站结构，提取选择器和相关网址
        
        Args:
            url: 网站URL
            
        Returns:
            提取的选择器配置，包含相关网址
        """
        print(f"开始分析网站: {url}")
        
        # 创建Fetcher
        fetcher = Fetcher()
        fetcher.configure(adaptive=True)
        
        # 抓取页面
        try:
            response = fetcher.get(url)
            if response.status != 200:
                print(f"抓取失败，状态码: {response.status}")
                return self.get_default_selectors()
        except Exception as e:
            print(f"抓取失败: {e}")
            return self.get_default_selectors()
        
        # 处理响应内容
        content = ""
        if hasattr(response, 'text') and response.text:
            content = response.text
        elif hasattr(response, 'body') and response.body:
            if isinstance(response.body, bytes):
                try:
                    content = response.body.decode('utf-8')
                except:
                    content = str(response.body)
            else:
                content = response.body
        
        if not content:
            print("响应内容为空")
            return self.get_default_selectors()
        
        # 解析页面
        selector = Selector(content)
        
        # 分析文章链接选择器
        link_selectors = self.analyze_link_selectors(selector)
        
        # 分析文章详情选择器
        detail_selectors = self.analyze_detail_selectors()
        
        # 提取相关网址
        related_urls = self.extract_related_urls(selector, url)
        
        selectors = {
            'article_links': link_selectors,
            'article_detail': detail_selectors,
            'related_urls': related_urls
        }
        
        print(f"网站分析完成，提取的选择器: {selectors}")
        return selectors
    
    def extract_related_urls(self, selector, base_url):
        """提取相关网址
        
        Args:
            selector: 页面选择器
            base_url: 基础URL
            
        Returns:
            相关网址列表
        """
        print("  提取相关网址...")
        
        # 提取所有链接
        links = []
        try:
            # 尝试不同的选择器
            common_patterns = [
                'a[href^="/a/"]',
                'a[href*="/a/"]',
                'a[href^="/article/"]',
                'a[href*="/article/"]',
                'a[href^="/post/"]',
                'a[href*="/post/"]',
                '.article-item a',
                '.list-item a',
                'a.title',
                '.article a',
                'a[class*="title"]',
                '.news-item a',
                '.blog-item a',
                '.item a',  # 同花顺行业研究页面使用的选择器
                'a[href*="yuanchuang.10jqka.com.cn"]',  # 同花顺原创文章链接
                'a[href*="stock.10jqka.com.cn"]',  # 同花顺股票文章链接
                'a[href*="/202"]',  # 年份链接，如2026
                'a[href*=".shtml"]',  # 文章链接
                'a[href*="/c6"]'  # 文章ID链接
            ]
            
            for pattern in common_patterns:
                try:
                    elements = selector.css(pattern)
                    for element in elements:
                        if hasattr(element, 'attrib') and 'href' in element.attrib:
                            href = element.attrib['href']
                            # 处理相对路径
                            if href.startswith('/'):
                                # 提取base_url的域名部分
                                from urllib.parse import urlparse
                                parsed_url = urlparse(base_url)
                                domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
                                full_url = domain + href
                            elif not href.startswith('http'):
                                full_url = base_url.rstrip('/') + '/' + href.lstrip('/')
                            else:
                                full_url = href
                            
                            # 提取链接文本
                            text = ""
                            if hasattr(element, 'text') and element.text:
                                text = element.text.strip()
                            
                            # 处理编码问题
                            try:
                                if isinstance(text, bytes):
                                    text = text.decode('utf-8')
                                elif '\\x' in str(text):
                                    # 尝试修复乱码
                                    import ast
                                    byte_text = ast.literal_eval(f"b'{text}'")
                                    text = byte_text.decode('gbk')
                            except:
                                pass
                            
                            # 过滤不符合特征的链接
                            if self._is_valid_article_link(full_url, text):
                                links.append({
                                    'url': full_url,
                                    'text': text,
                                    'selector': pattern
                                })
                except:
                    continue
        except Exception as e:
            print(f"  提取链接失败: {e}")
        
        # 去重
        unique_links = []
        seen_urls = set()
        for link in links:
            if link['url'] not in seen_urls:
                seen_urls.add(link['url'])
                unique_links.append(link)
        
        print(f"  提取到 {len(unique_links)} 个相关网址")
        return unique_links
    
    def analyze_link_selectors(self, selector):
        """分析文章链接选择器
        
        Args:
            selector: 页面选择器
            
        Returns:
            文章链接选择器列表
        """
        # 常见的文章链接选择器模式
        common_patterns = [
            'a[href^="/a/"]',
            'a[href*="/a/"]',
            'a[href^="/article/"]',
            'a[href*="/article/"]',
            'a[href^="/post/"]',
            'a[href*="/post/"]',
            '.article-item a',
            '.list-item a',
            'a.title',
            '.article a',
            'a[class*="title"]',
            '.news-item a',
            '.blog-item a',
            '.item a',  # 同花顺行业研究页面使用的选择器
            'a[href*="yuanchuang.10jqka.com.cn"]',  # 同花顺原创文章链接
            'a[href*="stock.10jqka.com.cn"]'  # 同花顺股票文章链接
        ]
        
        # 测试每个选择器
        valid_selectors = []
        for pattern in common_patterns:
            try:
                links = selector.css(pattern)
                if links:
                    valid_selectors.append(pattern)
                    print(f"  选择器 '{pattern}' 找到 {len(links)} 个元素")
            except:
                continue
        
        if not valid_selectors:
            print("  未找到有效的链接选择器，使用默认值")
            valid_selectors = ['a[href^="/a/"]', 'a[href*="/a/"]']
        
        return valid_selectors
    
    def analyze_detail_selectors(self):
        """分析文章详情选择器
        
        Returns:
            文章详情选择器配置
        """
        # 默认的文章详情选择器
        return {
            'title': ['title', 'h1', '.article-title', '.post-title', '.title'],
            'author': ['.username-box .fs16-bold', '.author-name', '.username', '.user-name'],
            'publish_time': ['meta[property="article:published_time"]', '.date', '.time', '.publish-time', '.post-time', '.article-time'],
            'content': ['meta[name="description"]', '.article-content', '.post-content', '.content'],
            'stocks': ['meta[name="keywords"]']
        }
    
    def get_default_selectors(self):
        """获取默认选择器配置"""
        return {
            'article_links': ['a[href^="/a/"]', 'a[href*="/a/"]'],
            'article_detail': {
                'title': ['title', 'h1'],
                'author': ['.author-name', '.username'],
                'publish_time': ['.date', '.time', '.publish-time', '.post-time'],

                'content': ['.article-content', '.content'],
                'stocks': []
            }
        }
    
    def get_website_config(self, name):
        """获取网站配置
        
        Args:
            name: 网站名称
            
        Returns:
            网站配置，如果不存在返回None
        """
        return self.configs.get(name)
    
    def update_website_config(self, name, config):
        """更新网站配置
        
        Args:
            name: 网站名称
            config: 新的配置
        """
        if name in self.configs:
            self.configs[name].update(config)
            self.configs[name]['last_updated'] = datetime.now().isoformat()
            self.save_configs()
            return True
        return False
    
    def list_websites(self):
        """列出所有配置的网站
        
        Returns:
            网站名称列表
        """
        return list(self.configs.keys())
    
    def remove_website(self, name):
        """移除网站配置
        
        Args:
            name: 网站名称
        """
        if name in self.configs:
            del self.configs[name]
            self.save_configs()
            return True
        return False
    
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

if __name__ == "__main__":
    # 示例用法
    config_manager = ScraplingConfigManager()
    
    # 分析并添加新网站
    config_manager.add_website('韭研公社', 'https://www.jiuyangongshe.com/')
    
    # 列出所有网站
    print("配置的网站:", config_manager.list_websites())
    
    # 获取网站配置
    jiuyangongshe_config = config_manager.get_website_config('韭研公社')
    print("韭研公社配置:", jiuyangongshe_config)
