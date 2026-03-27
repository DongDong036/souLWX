"""
股票池管理模块
功能：
- 独立股票池创建
- 自动识别股票
- 手动添加股票
- 股票池与文章关联
- 股票池管理
"""

import os
from datetime import datetime
from database.db_manager import DatabaseManager

# 简单的日志函数
def log_app(message):
    print(f"[INFO] {message}")

def log_error(message):
    print(f"[ERROR] {message}")

# 尝试导入 deepseek_api，如果失败则使用空实现
try:
    from deepseek_api import deepseek_api
except ImportError:
    class MockDeepSeekAPI:
        def identify_stocks(self, content):
            return []
    deepseek_api = MockDeepSeekAPI()

class StockPoolManager:
    def __init__(self):
        """初始化股票池管理器"""
        self.db_manager = DatabaseManager()
        log_app("股票池管理器初始化完成")
    
    def create_stock_pool(self, article_id, article_title):
        """
        为文章创建股票池
        
        Args:
            article_id: 文章ID
            article_title: 文章标题
        
        Returns:
            dict: 股票池对象
        """
        # 股票池通过文章ID与文章关联，不需要单独创建
        log_app(f"为文章 '{article_title}' 准备股票池")
        return {"id": article_id, "article_title": article_title, "stocks": []}
    
    def get_stock_pool(self, article_id):
        """
        获取文章的股票池
        
        Args:
            article_id: 文章ID
        
        Returns:
            dict: 股票池对象
        """
        # 从数据库获取文章信息
        articles = self.db_manager.load_articles()
        for article in articles:
            if article.get('id') == article_id:
                return {
                    "id": article_id,
                    "article_title": article.get('title', ''),
                    "stocks": article.get('stocks', [])
                }
        return None
    
    def add_stock_to_pool(self, article_id, stock_info):
        """
        向股票池添加股票
        
        Args:
            article_id: 文章ID
            stock_info: 股票信息
        
        Returns:
            bool: 是否成功
        """
        try:
            log_app(f"开始添加股票到股票池，文章ID：{article_id}")
            log_app(f"股票信息：{stock_info}")
            
            # 从数据库获取文章
            log_app("从数据库加载文章...")
            articles = self.db_manager.load_articles()
            log_app(f"成功加载 {len(articles)} 篇文章")
            
            target_article = None
            for article in articles:
                if article.get('id') == article_id:
                    target_article = article
                    break
            
            if not target_article:
                log_error(f"文章不存在：{article_id}")
                return False
            
            log_app(f"找到目标文章：{target_article.get('title', '无标题')}")
            
            # 检查股票是否已存在
            existing_stocks = target_article.get('stocks', [])
            log_app(f"现有股票数量：{len(existing_stocks)}")
            
            stock_name = stock_info.get('name', '')
            if stock_name:
                log_app(f"要添加的股票名称：{stock_name}")
                for stock in existing_stocks:
                    if stock.get('name') == stock_name:
                        log_app(f"股票已存在：{stock_name}")
                        return False
            
            # 添加股票
            existing_stocks.append({'name': stock_name})
            target_article['stocks'] = existing_stocks
            log_app(f"添加后股票数量：{len(existing_stocks)}")
            
            # 保存到数据库
            log_app("保存文章到数据库...")
            success = self.db_manager.save_article(target_article)
            if success:
                log_app(f"向股票池添加股票成功：{stock_name}")
            else:
                log_error(f"保存文章失败")
            return success
        except Exception as e:
            log_error(f"添加股票失败：{str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def remove_stock_from_pool(self, article_id, stock_name):
        """
        从股票池移除股票
        
        Args:
            article_id: 文章ID
            stock_name: 股票名称
        
        Returns:
            bool: 是否成功
        """
        try:
            # 从数据库获取文章
            articles = self.db_manager.load_articles()
            target_article = None
            for article in articles:
                if article.get('id') == article_id:
                    target_article = article
                    break
            
            if not target_article:
                log_error(f"文章不存在：{article_id}")
                return False
            
            # 过滤掉要移除的股票
            existing_stocks = target_article.get('stocks', [])
            original_count = len(existing_stocks)
            
            filtered_stocks = [
                stock for stock in existing_stocks 
                if stock.get('name') != stock_name
            ]
            
            if len(filtered_stocks) < original_count:
                target_article['stocks'] = filtered_stocks
                # 保存到数据库
                success = self.db_manager.save_article(target_article)
                if success:
                    log_app(f"从股票池移除股票：{stock_name}")
                return success
            else:
                log_app(f"股票不存在：{stock_name}")
                return False
        except Exception as e:
            log_error(f"移除股票失败：{str(e)}")
            return False
    
    def auto_identify_stocks(self, article_id, article_content):
        """
        自动识别文章中的股票
        
        Args:
            article_id: 文章ID
            article_content: 文章内容
        
        Returns:
            list: 识别的股票列表
        """
        try:
            # 使用DEEPSEEK识别股票
            stocks = deepseek_api.identify_stocks(article_content)
            
            if stocks:
                # 为每个股票创建完整的股票信息
                stock_infos = []
                for stock_name in stocks:
                    stock_infos.append({
                        'name': stock_name
                    })
                
                # 添加到股票池
                for stock_info in stock_infos:
                    self.add_stock_to_pool(article_id, stock_info)
                
                log_app(f"自动识别并添加了 {len(stocks)} 只股票")
                return stocks
            
            return []
        except Exception as e:
            log_error(f"自动识别股票失败：{str(e)}")
            return []
    
    def manual_add_stock(self, article_id, stock_name):
        """
        手动添加股票
        
        Args:
            article_id: 文章ID
            stock_name: 股票名称
        
        Returns:
            bool: 是否成功
        """
        stock_info = {
            'name': stock_name
        }
        return self.add_stock_to_pool(article_id, stock_info)
    
    def get_all_stock_pools(self):
        """
        获取所有股票池
        
        Returns:
            dict: 所有股票池
        """
        stock_pools = {}
        articles = self.db_manager.load_articles()
        for article in articles:
            article_id = article.get('id')
            if article_id:
                stock_pools[article_id] = {
                    "id": article_id,
                    "article_title": article.get('title', ''),
                    "stocks": article.get('stocks', [])
                }
        return stock_pools
    
    def delete_stock_pool(self, article_id):
        """
        删除股票池
        
        Args:
            article_id: 文章ID
        
        Returns:
            bool: 是否成功
        """
        try:
            # 从数据库获取文章
            articles = self.db_manager.load_articles()
            target_article = None
            for article in articles:
                if article.get('id') == article_id:
                    target_article = article
                    break
            
            if target_article:
                # 清空股票池
                target_article['stocks'] = []
                # 保存到数据库
                success = self.db_manager.save_article(target_article)
                if success:
                    log_app(f"清空股票池：{article_id}")
                return success
            else:
                log_error(f"股票池不存在：{article_id}")
                return False
        except Exception as e:
            log_error(f"删除股票池失败：{str(e)}")
            return False
    
    def clear_all_stock_pools(self):
        """
        清空所有股票池
        
        Returns:
            bool: 是否成功
        """
        try:
            # 从数据库获取所有文章
            articles = self.db_manager.load_articles()
            for article in articles:
                # 清空股票池
                article['stocks'] = []
                # 保存到数据库
                self.db_manager.save_article(article)
            log_app("已清空所有股票池")
            return True
        except Exception as e:
            log_error(f"清空股票池失败：{str(e)}")
            return False

# 全局实例
stock_pool_manager = StockPoolManager()

if __name__ == '__main__':
    # 测试股票池管理
    manager = StockPoolManager()
    
    # 测试创建股票池
    test_article_id = 'test_article_1'
    test_article_title = '人工智能概念股分析'
    
    print("测试创建股票池...")
    stock_pool = manager.create_stock_pool(test_article_id, test_article_title)
    if stock_pool:
        print(f"股票池创建成功：{stock_pool['id']}")
    
    # 测试自动识别股票
    test_content = "近日，人工智能概念股持续走强，其中昆仑万维（300418）、佰维存储（688525）等个股表现突出。"
    print("\n测试自动识别股票...")
    identified_stocks = manager.auto_identify_stocks(test_article_id, test_content)
    print(f"自动识别的股票：{identified_stocks}")
    
    # 测试手动添加股票
    print("\n测试手动添加股票...")
    success = manager.manual_add_stock(test_article_id, 'SH600666', '奥瑞德')
    print(f"手动添加股票：{success}")
    
    # 测试获取股票池
    print("\n测试获取股票池...")
    retrieved_pool = manager.get_stock_pool(test_article_id)
    if retrieved_pool:
        print(f"股票池股票数量：{len(retrieved_pool['stocks'])}")
        for stock in retrieved_pool['stocks']:
            print(f"  - {stock['name']} ({stock['code']})")
    
    # 测试移除股票
    print("\n测试移除股票...")
    removed = manager.remove_stock_from_pool(test_article_id, 'SH600666')
    print(f"移除股票：{removed}")
    
    # 测试获取所有股票池
    print("\n测试获取所有股票池...")
    all_pools = manager.get_all_stock_pools()
    print(f"股票池数量：{len(all_pools)}")
    
    # 测试删除股票池
    print("\n测试删除股票池...")
    deleted = manager.delete_stock_pool(test_article_id)
    print(f"删除股票池：{deleted}")