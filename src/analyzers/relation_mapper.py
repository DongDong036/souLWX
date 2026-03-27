"""
关联映射系统
功能：
- 文章与股票的双向映射
- 高效互查功能
- 数据索引系统
- 关联关系可视化
"""

import json
import os
from datetime import datetime
from logger import log_app, log_error

class RelationMapper:
    def __init__(self):
        """初始化关联映射系统"""
        self.article_stock_map = {}  # 文章到股票的映射
        self.stock_article_map = {}  # 股票到文章的映射
        self.relation_file = 'data/database/relations.json'
        self._load_relations()
        log_app("关联映射系统初始化完成")
    
    def _load_relations(self):
        """
        加载关联关系数据
        """
        try:
            if os.path.exists(self.relation_file):
                with open(self.relation_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.article_stock_map = data.get('article_stock_map', {})
                    self.stock_article_map = data.get('stock_article_map', {})
                log_app(f"已加载 {len(self.article_stock_map)} 个文章-股票关联")
        except Exception as e:
            log_error(f"加载关联关系失败：{str(e)}")
            self.article_stock_map = {}
            self.stock_article_map = {}
    
    def _save_relations(self):
        """
        保存关联关系数据
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.relation_file), exist_ok=True)
            
            data = {
                'article_stock_map': self.article_stock_map,
                'stock_article_map': self.stock_article_map,
                'updated_at': datetime.now().isoformat()
            }
            
            with open(self.relation_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            log_app("关联关系已保存")
        except Exception as e:
            log_error(f"保存关联关系失败：{str(e)}")
    
    def add_relation(self, article_id, stock_code, article_title=None):
        """
        添加文章与股票的关联
        
        Args:
            article_id: 文章ID
            stock_code: 股票代码
            article_title: 文章标题（可选）
        
        Returns:
            bool: 是否成功
        """
        try:
            # 更新文章到股票的映射
            if article_id not in self.article_stock_map:
                self.article_stock_map[article_id] = {
                    'title': article_title or '',
                    'stocks': []
                }
            
            if stock_code not in self.article_stock_map[article_id]['stocks']:
                self.article_stock_map[article_id]['stocks'].append(stock_code)
            
            # 更新股票到文章的映射
            if stock_code not in self.stock_article_map:
                self.stock_article_map[stock_code] = []
            
            article_info = {
                'id': article_id,
                'title': article_title or '',
                'added_at': datetime.now().isoformat()
            }
            
            # 检查文章是否已存在
            article_exists = False
            for existing_article in self.stock_article_map[stock_code]:
                if existing_article['id'] == article_id:
                    article_exists = True
                    break
            
            if not article_exists:
                self.stock_article_map[stock_code].append(article_info)
            
            self._save_relations()
            log_app(f"添加关联：{article_id} -> {stock_code}")
            return True
        except Exception as e:
            log_error(f"添加关联失败：{str(e)}")
            return False
    
    def remove_relation(self, article_id, stock_code):
        """
        移除文章与股票的关联
        
        Args:
            article_id: 文章ID
            stock_code: 股票代码
        
        Returns:
            bool: 是否成功
        """
        try:
            # 从文章到股票的映射中移除
            if article_id in self.article_stock_map:
                if stock_code in self.article_stock_map[article_id]['stocks']:
                    self.article_stock_map[article_id]['stocks'].remove(stock_code)
                    # 如果文章没有关联股票，删除该文章的映射
                    if not self.article_stock_map[article_id]['stocks']:
                        del self.article_stock_map[article_id]
            
            # 从股票到文章的映射中移除
            if stock_code in self.stock_article_map:
                self.stock_article_map[stock_code] = [
                    article for article in self.stock_article_map[stock_code]
                    if article['id'] != article_id
                ]
                # 如果股票没有关联文章，删除该股票的映射
                if not self.stock_article_map[stock_code]:
                    del self.stock_article_map[stock_code]
            
            self._save_relations()
            log_app(f"移除关联：{article_id} -> {stock_code}")
            return True
        except Exception as e:
            log_error(f"移除关联失败：{str(e)}")
            return False
    
    def get_stocks_by_article(self, article_id):
        """
        通过文章查询关联的股票
        
        Args:
            article_id: 文章ID
        
        Returns:
            list: 股票代码列表
        """
        if article_id in self.article_stock_map:
            return self.article_stock_map[article_id]['stocks']
        return []
    
    def get_articles_by_stock(self, stock_code):
        """
        通过股票查询相关的文章
        
        Args:
            stock_code: 股票代码
        
        Returns:
            list: 文章信息列表
        """
        if stock_code in self.stock_article_map:
            return self.stock_article_map[stock_code]
        return []
    
    def get_all_relations(self):
        """
        获取所有关联关系
        
        Returns:
            dict: 关联关系数据
        """
        return {
            'article_stock_map': self.article_stock_map,
            'stock_article_map': self.stock_article_map
        }
    
    def batch_add_relations(self, article_id, stock_codes, article_title=None):
        """
        批量添加文章与股票的关联
        
        Args:
            article_id: 文章ID
            stock_codes: 股票代码列表
            article_title: 文章标题（可选）
        
        Returns:
            int: 成功添加的关联数量
        """
        count = 0
        for stock_code in stock_codes:
            if self.add_relation(article_id, stock_code, article_title):
                count += 1
        return count
    
    def get_relation_stats(self):
        """
        获取关联关系统计
        
        Returns:
            dict: 统计信息
        """
        total_articles = len(self.article_stock_map)
        total_stocks = len(self.stock_article_map)
        total_relations = 0
        
        for article_id, data in self.article_stock_map.items():
            total_relations += len(data['stocks'])
        
        return {
            'total_articles': total_articles,
            'total_stocks': total_stocks,
            'total_relations': total_relations,
            'avg_stocks_per_article': total_relations / total_articles if total_articles > 0 else 0,
            'avg_articles_per_stock': total_relations / total_stocks if total_stocks > 0 else 0
        }
    
    def export_relations(self, output_dir='data/export'):
        """
        导出关联关系
        
        Args:
            output_dir: 输出目录
        
        Returns:
            str: 保存路径
        """
        try:
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"relations_{timestamp}.json"
            filepath = os.path.join(output_dir, filename)
            
            # 保存关联关系
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.get_all_relations(), f, ensure_ascii=False, indent=2)
            
            log_app(f"关联关系已导出：{filepath}")
            return filepath
        except Exception as e:
            log_error(f"导出关联关系失败：{str(e)}")
            return None
    
    def import_relations(self, filepath):
        """
        导入关联关系
        
        Args:
            filepath: 文件路径
        
        Returns:
            bool: 是否成功
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # 合并关联关系
                if 'article_stock_map' in data:
                    for article_id, article_data in data['article_stock_map'].items():
                        if article_id not in self.article_stock_map:
                            self.article_stock_map[article_id] = article_data
                        else:
                            # 合并股票列表
                            existing_stocks = set(self.article_stock_map[article_id]['stocks'])
                            new_stocks = set(article_data['stocks'])
                            self.article_stock_map[article_id]['stocks'] = list(existing_stocks | new_stocks)
                
                if 'stock_article_map' in data:
                    for stock_code, articles in data['stock_article_map'].items():
                        if stock_code not in self.stock_article_map:
                            self.stock_article_map[stock_code] = articles
                        else:
                            # 合并文章列表
                            existing_article_ids = set(article['id'] for article in self.stock_article_map[stock_code])
                            new_articles = [article for article in articles if article['id'] not in existing_article_ids]
                            self.stock_article_map[stock_code].extend(new_articles)
            
            self._save_relations()
            log_app(f"关联关系已导入：{filepath}")
            return True
        except Exception as e:
            log_error(f"导入关联关系失败：{str(e)}")
            return False
    
    def clear_relations(self):
        """
        清空所有关联关系
        
        Returns:
            bool: 是否成功
        """
        try:
            self.article_stock_map = {}
            self.stock_article_map = {}
            self._save_relations()
            log_app("已清空所有关联关系")
            return True
        except Exception as e:
            log_error(f"清空关联关系失败：{str(e)}")
            return False
    
    def generate_visualization_data(self):
        """
        生成可视化数据
        
        Returns:
            dict: 可视化数据
        """
        try:
            nodes = []
            links = []
            node_id = 0
            node_map = {}
            
            # 添加文章节点
            for article_id, article_data in self.article_stock_map.items():
                node_map[article_id] = node_id
                nodes.append({
                    'id': node_id,
                    'label': article_data['title'][:20] + '...' if len(article_data['title']) > 20 else article_data['title'],
                    'type': 'article',
                    'article_id': article_id
                })
                node_id += 1
            
            # 添加股票节点
            for stock_code in self.stock_article_map.keys():
                node_map[stock_code] = node_id
                nodes.append({
                    'id': node_id,
                    'label': stock_code,
                    'type': 'stock',
                    'stock_code': stock_code
                })
                node_id += 1
            
            # 添加链接
            for article_id, article_data in self.article_stock_map.items():
                article_node_id = node_map[article_id]
                for stock_code in article_data['stocks']:
                    if stock_code in node_map:
                        stock_node_id = node_map[stock_code]
                        links.append({
                            'source': article_node_id,
                            'target': stock_node_id,
                            'value': 1
                        })
            
            return {
                'nodes': nodes,
                'links': links
            }
        except Exception as e:
            log_error(f"生成可视化数据失败：{str(e)}")
            return {'nodes': [], 'links': []}

# 全局实例
relation_mapper = RelationMapper()

if __name__ == '__main__':
    # 测试关联映射系统
    mapper = RelationMapper()
    
    # 测试添加关联
    test_article_id = 'test_article_1'
    test_article_title = '人工智能概念股分析'
    test_stocks = ['SZ300418', 'SH688525', 'SH600666']
    
    print("测试添加关联...")
    count = mapper.batch_add_relations(test_article_id, test_stocks, test_article_title)
    print(f"成功添加 {count} 个关联")
    
    # 测试通过文章查询股票
    print("\n测试通过文章查询股票...")
    stocks = mapper.get_stocks_by_article(test_article_id)
    print(f"文章关联的股票：{stocks}")
    
    # 测试通过股票查询文章
    print("\n测试通过股票查询文章...")
    articles = mapper.get_articles_by_stock('SZ300418')
    print(f"股票关联的文章数量：{len(articles)}")
    for article in articles:
        print(f"  - {article['title']}")
    
    # 测试移除关联
    print("\n测试移除关联...")
    removed = mapper.remove_relation(test_article_id, 'SH600666')
    print(f"移除关联：{removed}")
    
    # 测试统计信息
    print("\n测试统计信息...")
    stats = mapper.get_relation_stats()
    print(f"总文章数：{stats['total_articles']}")
    print(f"总股票数：{stats['total_stocks']}")
    print(f"总关联数：{stats['total_relations']}")
    
    # 测试生成可视化数据
    print("\n测试生成可视化数据...")
    viz_data = mapper.generate_visualization_data()
    print(f"节点数量：{len(viz_data['nodes'])}")
    print(f"链接数量：{len(viz_data['links'])}")
    
    # 测试导出关联关系
    print("\n测试导出关联关系...")
    export_path = mapper.export_relations()
    print(f"关联关系已导出：{export_path}")
    
    # 测试清空关联关系
    print("\n测试清空关联关系...")
    cleared = mapper.clear_relations()
    print(f"清空关联关系：{cleared}")