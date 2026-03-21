"""
文章分析服务
功能：
- 整合内容分析器和DEEPSEEK API
- 实现完整的文章分析流程
- 股票识别和分析
- 分析结果管理
"""

import json
import os
from datetime import datetime
from content_analyzer import content_analyzer
from deepseek_api import deepseek_api
from logger import log_app, log_error

class ArticleAnalyzer:
    def __init__(self):
        """初始化文章分析器"""
        self.analysis_history = []
        self.analysis_cache = {}
        log_app("文章分析服务初始化完成")
    
    def analyze_article(self, article):
        """
        分析文章
        
        Args:
            article: 文章对象
        
        Returns:
            dict: 分析结果
        """
        try:
            # 检查缓存
            article_id = article.get('url', '') or article.get('id', '')
            if article_id in self.analysis_cache:
                log_app(f"使用缓存的分析结果：{article_id}")
                return self.analysis_cache[article_id]
            
            # 1. 网页内容分析
            log_app(f"开始分析文章：{article.get('title', '未知')}")
            
            # 如果有URL，分析网页内容
            if article.get('url'):
                web_analysis = content_analyzer.analyze_webpage(article['url'])
                if web_analysis:
                    content = web_analysis['combined_content']
                else:
                    content = article.get('content', '')
            else:
                content = article.get('content', '')
            
            # 2. DEEPSEEK深度分析
            deepseek_analysis = deepseek_api.analyze_article(content)
            
            # 3. 股票识别
            stocks = []
            if deepseek_analysis and deepseek_analysis.get('stocks'):
                stocks = deepseek_analysis['stocks']
            else:
                # 备用：使用内容分析器提取股票
                stocks = content_analyzer.extract_stocks(content)
            
            # 4. 整合分析结果
            analysis_result = {
                'article_id': article_id,
                'title': article.get('title', ''),
                'url': article.get('url', ''),
                'analysis_time': datetime.now().isoformat(),
                'web_analysis': web_analysis,
                'deepseek_analysis': deepseek_analysis,
                'stocks': stocks,
                'summary': deepseek_analysis.get('summary', '') if deepseek_analysis else '',
                'topic': deepseek_analysis.get('topic', '') if deepseek_analysis else '',
                'key_points': deepseek_analysis.get('key_points', []) if deepseek_analysis else []
            }
            
            # 5. 缓存分析结果
            if article_id:
                self.analysis_cache[article_id] = analysis_result
            
            # 6. 记录分析历史
            self.analysis_history.append(analysis_result)
            
            log_app(f"文章分析完成，识别到 {len(stocks)} 只股票")
            return analysis_result
            
        except Exception as e:
            log_error(f"文章分析失败：{str(e)}")
            return None
    
    def batch_analyze_articles(self, articles):
        """
        批量分析文章
        
        Args:
            articles: 文章列表
        
        Returns:
            list: 分析结果列表
        """
        results = []
        for article in articles:
            result = self.analyze_article(article)
            if result:
                results.append(result)
        return results
    
    def analyze_article_by_url(self, url):
        """
        通过URL分析文章
        
        Args:
            url: 文章URL
        
        Returns:
            dict: 分析结果
        """
        article = {'url': url}
        return self.analyze_article(article)
    
    def get_analysis_history(self):
        """
        获取分析历史
        
        Returns:
            list: 分析历史
        """
        return self.analysis_history
    
    def clear_cache(self):
        """
        清除分析缓存
        """
        self.analysis_cache.clear()
        log_app("分析缓存已清除")
    
    def save_analysis_result(self, analysis_result, output_dir='data/analysis'):
        """
        保存分析结果
        
        Args:
            analysis_result: 分析结果
            output_dir: 输出目录
        
        Returns:
            str: 保存路径
        """
        try:
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"analysis_{timestamp}.json"
            filepath = os.path.join(output_dir, filename)
            
            # 保存分析结果
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(analysis_result, f, ensure_ascii=False, indent=2)
            
            log_app(f"分析结果已保存：{filepath}")
            return filepath
            
        except Exception as e:
            log_error(f"保存分析结果失败：{str(e)}")
            return None
    
    def load_analysis_result(self, filepath):
        """
        加载分析结果
        
        Args:
            filepath: 文件路径
        
        Returns:
            dict: 分析结果
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                analysis_result = json.load(f)
            
            log_app(f"分析结果已加载：{filepath}")
            return analysis_result
            
        except Exception as e:
            log_error(f"加载分析结果失败：{str(e)}")
            return None

# 全局实例
article_analyzer = ArticleAnalyzer()

if __name__ == '__main__':
    # 测试文章分析
    analyzer = ArticleAnalyzer()
    
    # 测试单篇文章分析
    test_article = {
        'title': '人工智能概念股持续走强',
        'url': 'https://www.jiuyangongshe.com/',
        'content': '近日，人工智能概念股持续走强，其中昆仑万维（300418）、佰维存储（688525）等个股表现突出。分析师认为，随着AI技术的不断发展，相关产业链公司有望持续受益。'
    }
    
    print("测试单篇文章分析...")
    result = analyzer.analyze_article(test_article)
    if result:
        print(f"文章标题：{result['title']}")
        print(f"识别的股票：{result['stocks']}")
        print(f"分析摘要：{result['summary'][:100]}...")
        
        # 保存分析结果
        save_path = analyzer.save_analysis_result(result)
        print(f"分析结果已保存：{save_path}")
    else:
        print("文章分析失败")
    
    # 测试批量分析
    test_articles = [
        {
            'title': '科技股表现活跃',
            'content': '科技股今日表现活跃，沪电股份（002463）、金安国纪（002636）等个股涨幅明显。'
        },
        {
            'title': '能源板块走势',
            'content': '能源板块今日走势平稳，金开新能（600821）、首航新能（300665）等个股表现良好。'
        }
    ]
    
    print("\n测试批量文章分析...")
    batch_results = analyzer.batch_analyze_articles(test_articles)
    for i, batch_result in enumerate(batch_results):
        print(f"\n文章 {i+1}：{batch_result['title']}")
        print(f"识别的股票：{batch_result['stocks']}")