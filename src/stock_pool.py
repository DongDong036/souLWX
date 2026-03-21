"""
股票池管理模块
功能：
- 独立股票池创建
- 自动识别股票
- 手动添加股票
- 股票池与文章关联
- 股票池管理
"""

import json
import os
from datetime import datetime
from logger import log_app, log_error
from deepseek_api import deepseek_api

class StockPoolManager:
    def __init__(self):
        """初始化股票池管理器"""
        self.stock_pools = {}
        self.stock_pool_file = 'data/database/stock_pools.json'
        self._load_stock_pools()
        log_app("股票池管理器初始化完成")
    
    def _load_stock_pools(self):
        """
        加载股票池数据
        """
        try:
            if os.path.exists(self.stock_pool_file):
                with open(self.stock_pool_file, 'r', encoding='utf-8') as f:
                    self.stock_pools = json.load(f)
                log_app(f"已加载 {len(self.stock_pools)} 个股票池")
        except Exception as e:
            log_error(f"加载股票池失败：{str(e)}")
            self.stock_pools = {}
    
    def _save_stock_pools(self):
        """
        保存股票池数据
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.stock_pool_file), exist_ok=True)
            
            with open(self.stock_pool_file, 'w', encoding='utf-8') as f:
                json.dump(self.stock_pools, f, ensure_ascii=False, indent=2)
            log_app(f"已保存 {len(self.stock_pools)} 个股票池")
        except Exception as e:
            log_error(f"保存股票池失败：{str(e)}")
    
    def create_stock_pool(self, article_id, article_title):
        """
        为文章创建股票池
        
        Args:
            article_id: 文章ID
            article_title: 文章标题
        
        Returns:
            dict: 股票池对象
        """
        try:
            stock_pool = {
                'id': article_id,
                'article_title': article_title,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'stocks': [],
                'analysis_results': {}
            }
            
            self.stock_pools[article_id] = stock_pool
            self._save_stock_pools()
            log_app(f"为文章 '{article_title}' 创建了股票池")
            return stock_pool
        except Exception as e:
            log_error(f"创建股票池失败：{str(e)}")
            return None
    
    def get_stock_pool(self, article_id):
        """
        获取文章的股票池
        
        Args:
            article_id: 文章ID
        
        Returns:
            dict: 股票池对象
        """
        return self.stock_pools.get(article_id)
    
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
            if article_id not in self.stock_pools:
                log_error(f"股票池不存在：{article_id}")
                return False
            
            stock_pool = self.stock_pools[article_id]
            
            # 检查股票是否已存在
            stock_code = stock_info.get('code', '')
            if stock_code:
                for stock in stock_pool['stocks']:
                    if stock.get('code') == stock_code:
                        log_app(f"股票已存在：{stock_code}")
                        return False
            
            # 添加股票
            stock_info['added_at'] = datetime.now().isoformat()
            stock_pool['stocks'].append(stock_info)
            stock_pool['updated_at'] = datetime.now().isoformat()
            
            self._save_stock_pools()
            log_app(f"向股票池添加股票：{stock_code}")
            return True
        except Exception as e:
            log_error(f"添加股票失败：{str(e)}")
            return False
    
    def remove_stock_from_pool(self, article_id, stock_code):
        """
        从股票池移除股票
        
        Args:
            article_id: 文章ID
            stock_code: 股票代码
        
        Returns:
            bool: 是否成功
        """
        try:
            if article_id not in self.stock_pools:
                log_error(f"股票池不存在：{article_id}")
                return False
            
            stock_pool = self.stock_pools[article_id]
            original_count = len(stock_pool['stocks'])
            
            # 过滤掉要移除的股票
            stock_pool['stocks'] = [
                stock for stock in stock_pool['stocks'] 
                if stock.get('code') != stock_code
            ]
            
            if len(stock_pool['stocks']) < original_count:
                stock_pool['updated_at'] = datetime.now().isoformat()
                self._save_stock_pools()
                log_app(f"从股票池移除股票：{stock_code}")
                return True
            else:
                log_app(f"股票不存在：{stock_code}")
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
                for stock_code in stocks:
                    stock_infos.append({
                        'code': stock_code,
                        'name': self._get_stock_name(stock_code),
                        'identified_by': 'deepseek',
                        'confidence': 'high'
                    })
                
                # 添加到股票池
                for stock_info in stock_infos:
                    self.add_stock_to_pool(article_id, stock_info)
                
                log_app(f"自动识别并添加了 {len(stocks)} 只股票")
                return stocks
            else:
                # 备用：使用正则表达式提取
                import re
                stock_code_pattern = r'(?:SZ|SH)?\d{6}'
                stock_codes = re.findall(stock_code_pattern, article_content)
                
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
                
                if unique_stocks:
                    # 添加到股票池
                    for stock_code in unique_stocks:
                        self.add_stock_to_pool(article_id, {
                            'code': stock_code,
                            'name': self._get_stock_name(stock_code),
                            'identified_by': 'regex',
                            'confidence': 'medium'
                        })
                    
                    log_app(f"使用正则表达式识别并添加了 {len(unique_stocks)} 只股票")
                    return unique_stocks
            
            return []
        except Exception as e:
            log_error(f"自动识别股票失败：{str(e)}")
            return []
    
    def manual_add_stock(self, article_id, stock_code, stock_name):
        """
        手动添加股票
        
        Args:
            article_id: 文章ID
            stock_code: 股票代码
            stock_name: 股票名称
        
        Returns:
            bool: 是否成功
        """
        stock_info = {
            'code': stock_code,
            'name': stock_name,
            'identified_by': 'manual',
            'confidence': 'high'
        }
        return self.add_stock_to_pool(article_id, stock_info)
    
    def _get_stock_name(self, stock_code):
        """
        获取股票名称
        
        Args:
            stock_code: 股票代码
        
        Returns:
            str: 股票名称
        """
        # 常见股票代码映射
        stock_mapping = {
            # 算力相关
            '600666': '奥瑞德',
            '300418': '昆仑万维',
            '600590': '泰豪科技',
            '300166': '东方国信',
            '603629': '利通电子',
            '601868': '中国能建',
            '601789': '宁波建工',
            '001896': '豫能控股',
            '002298': '中电鑫龙',
            
            # 科技相关
            '002463': '沪电股份',
            '002636': '金安国纪',
            '688525': '佰维存储',
            '001309': '德明利',
            '688553': '凯德石英',
            '002028': '思源电气',
            '601512': '中新集团',
            '002606': '大连电瓷',
            
            # 能源相关
            '600821': '金开新能',
            '300665': '首航新能',
            '600125': '铁龙物流',
            '002015': '协鑫能科',
            '600726': '华电能源',
            '000539': '粤电力A'
        }
        
        # 提取数字部分
        import re
        code_match = re.search(r'\d{6}', stock_code)
        if code_match:
            code_num = code_match.group(0)
            return stock_mapping.get(code_num, '未知')
        return '未知'
    
    def get_all_stock_pools(self):
        """
        获取所有股票池
        
        Returns:
            dict: 所有股票池
        """
        return self.stock_pools
    
    def delete_stock_pool(self, article_id):
        """
        删除股票池
        
        Args:
            article_id: 文章ID
        
        Returns:
            bool: 是否成功
        """
        try:
            if article_id in self.stock_pools:
                del self.stock_pools[article_id]
                self._save_stock_pools()
                log_app(f"删除股票池：{article_id}")
                return True
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
            self.stock_pools = {}
            self._save_stock_pools()
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