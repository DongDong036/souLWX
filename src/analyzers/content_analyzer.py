"""
网页内容分析模块
功能：
- 网页内容处理
- 文字信息脱水
- PaddleOCR图像识别集成
- 统一信息提取接口
"""

import requests
from bs4 import BeautifulSoup
import re
from paddleocr import PaddleOCR
from PIL import Image
import io
import logging
from logger import log_app, log_error

class ContentAnalyzer:
    def __init__(self):
        """初始化内容分析器"""
        self.ocr = PaddleOCR(use_angle_cls=True, lang='ch')
        log_app("内容分析器初始化完成")
    
    def analyze_webpage(self, url, html_content=None):
        """
        分析网页内容
        
        Args:
            url: 网页URL
            html_content: 网页HTML内容（如果已获取）
        
        Returns:
            dict: 分析结果
        """
        try:
            # 获取网页内容
            if not html_content:
                html_content = self.fetch_webpage(url)
            
            # 解析HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 提取标题
            title = self.extract_title(soup)
            
            # 提取正文内容
            content = self.extract_content(soup)
            
            # 提取图片
            images = self.extract_images(soup, url)
            
            # 处理图片（OCR识别）
            image_texts = self.process_images(images)
            
            # 脱水处理
            dehydrated_content = self.dehydrate_content(content)
            
            # 合并内容（文字 + 图片OCR结果）
            combined_content = f"{dehydrated_content}\n\n[图片识别内容]\n{image_texts}"
            
            result = {
                'url': url,
                'title': title,
                'content': content,
                'dehydrated_content': dehydrated_content,
                'image_texts': image_texts,
                'combined_content': combined_content,
                'images': len(images),
                'processed_images': len([img for img in images if img.get('text')])
            }
            
            log_app(f"网页分析完成：{url}")
            return result
            
        except Exception as e:
            log_error(f"网页分析失败：{str(e)}")
            return None
    
    def fetch_webpage(self, url):
        """
        获取网页内容
        
        Args:
            url: 网页URL
        
        Returns:
            str: 网页HTML内容
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.encoding = response.apparent_encoding
            return response.text
        except Exception as e:
            log_error(f"获取网页失败：{str(e)}")
            raise
    
    def extract_title(self, soup):
        """
        提取网页标题
        
        Args:
            soup: BeautifulSoup对象
        
        Returns:
            str: 标题
        """
        title = ""
        if soup.title:
            title = soup.title.string.strip()
        elif soup.find('h1'):
            title = soup.find('h1').get_text().strip()
        return title
    
    def extract_content(self, soup):
        """
        提取网页正文内容
        
        Args:
            soup: BeautifulSoup对象
        
        Returns:
            str: 正文内容
        """
        # 移除脚本和样式
        for script in soup(['script', 'style']):
            script.decompose()
        
        # 尝试不同的内容选择器
        content_selectors = [
            '.article-content',
            '.content',
            '.article-body',
            'article',
            '.post-content',
            '.entry-content',
            'main',
            '.main-content'
        ]
        
        content = ""
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                content = element.get_text(separator='\n', strip=True)
                break
        
        # 如果没有找到特定的内容区域，使用整个页面
        if not content:
            content = soup.get_text(separator='\n', strip=True)
        
        return content
    
    def extract_images(self, soup, base_url):
        """
        提取网页中的图片
        
        Args:
            soup: BeautifulSoup对象
            base_url: 基础URL
        
        Returns:
            list: 图片信息列表
        """
        images = []
        img_tags = soup.find_all('img')
        
        for img in img_tags:
            src = img.get('src')
            if src:
                # 处理相对路径
                if not src.startswith('http'):
                    from urllib.parse import urljoin
                    src = urljoin(base_url, src)
                
                images.append({
                    'src': src,
                    'alt': img.get('alt', ''),
                    'text': ''  # 后续OCR识别结果
                })
        
        return images
    
    def process_images(self, images):
        """
        处理图片（OCR识别）
        
        Args:
            images: 图片信息列表
        
        Returns:
            str: 图片识别的文本
        """
        image_texts = []
        
        for img_info in images:
            try:
                # 下载图片
                response = requests.get(img_info['src'], timeout=10)
                img = Image.open(io.BytesIO(response.content))
                
                # OCR识别
                result = self.ocr.ocr(img)
                
                # 提取识别结果
                text = ""
                for line in result:
                    for word in line:
                        text += word[1][0] + ' '
                
                img_info['text'] = text.strip()
                if text:
                    image_texts.append(f"图片 [{img_info['src']}]：{text.strip()}")
                    
            except Exception as e:
                log_error(f"图片处理失败：{str(e)}")
                continue
        
        return '\n'.join(image_texts)
    
    def dehydrate_content(self, content):
        """
        文字信息脱水处理
        
        Args:
            content: 原始内容
        
        Returns:
            str: 脱水后的内容
        """
        # 1. 去除重复的空白字符
        content = re.sub(r'\s+', ' ', content)
        
        # 2. 去除常见的冗余内容
        redundant_patterns = [
            r'来源：.*?\s',
            r'作者：.*?\s',
            r'发布时间：.*?\s',
            r'编辑：.*?\s',
            r'责任编辑：.*?\s',
            r'版权声明：.*?\s',
            r'本文来源：.*?\s',
            r'本文作者：.*?\s',
            r'原文链接：.*?\s',
            r'\(.*?\)',  # 去除括号内的内容
            r'\[.*?\]',  # 去除方括号内的内容
        ]
        
        for pattern in redundant_patterns:
            content = re.sub(pattern, '', content)
        
        # 3. 去除首尾空白
        content = content.strip()
        
        # 4. 保留核心内容，去除无关信息
        # 提取段落
        paragraphs = content.split('。')
        meaningful_paragraphs = []
        
        for para in paragraphs:
            para = para.strip()
            if para and len(para) > 10:  # 只保留长度大于10的段落
                meaningful_paragraphs.append(para)
        
        # 重新组合内容
        dehydrated_content = '。'.join(meaningful_paragraphs)
        
        # 5. 如果内容太短，保留原始内容
        if len(dehydrated_content) < 100 and len(content) > 100:
            return content
        
        return dehydrated_content
    
    def extract_stocks(self, content):
        """
        从内容中提取股票信息
        
        Args:
            content: 文本内容
        
        Returns:
            list: 股票代码列表
        """
        # 股票代码模式
        stock_code_pattern = r'(?:SZ|SH)?\d{6}'
        stock_codes = re.findall(stock_code_pattern, content)
        
        # 标准化股票代码
        standardized_codes = []
        for code in stock_codes:
            code = code.upper()
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

# 全局实例
content_analyzer = ContentAnalyzer()

if __name__ == '__main__':
    # 测试内容分析器
    analyzer = ContentAnalyzer()
    
    # 测试网页分析
    test_url = "https://www.jiuyangongshe.com/"
    result = analyzer.analyze_webpage(test_url)
    
    if result:
        print(f"标题：{result['title']}")
        print(f"原始内容长度：{len(result['content'])}")
        print(f"脱水内容长度：{len(result['dehydrated_content'])}")
        print(f"图片数量：{result['images']}")
        print(f"处理图片数量：{result['processed_images']}")
        print(f"\n脱水内容预览：{result['dehydrated_content'][:200]}...")
        
        # 测试股票提取
        stocks = analyzer.extract_stocks(result['combined_content'])
        print(f"\n提取的股票：{stocks}")
    else:
        print("网页分析失败")