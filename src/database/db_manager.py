import sqlite3
import json
from datetime import datetime
import os

class DatabaseManager:
    def __init__(self, db_path='data/database/articles.db'):
        self.db_path = db_path
        # 确保数据库目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        # 初始化数据库表结构
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建文章表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            author TEXT,
            publish_time TEXT,
            content TEXT,
            source TEXT,
            word_count INTEGER,
            importance INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建股票表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER,
            stock_name TEXT NOT NULL,
            FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
        )
        ''')
        
        # 创建索引以提高搜索性能
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_publish_time ON articles(publish_time)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_stocks_article_id ON stocks(article_id)')
        
        conn.commit()
        conn.close()
    
    def _get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)
    
    def close(self):
        """关闭数据库连接"""
        # 由于每个方法都使用自己的连接，这里不需要关闭
    
    def save_article(self, article):
        """保存单篇文章到数据库"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # 检查文章是否已存在
            cursor.execute('SELECT id FROM articles WHERE url = ?', (article['url'],))
            existing = cursor.fetchone()
            
            if existing:
                # 更新现有文章，保留重要性标记
                article_id = existing[0]
                # 先获取原有的重要性标记
                cursor.execute('SELECT importance FROM articles WHERE id = ?', (article_id,))
                existing_importance = cursor.fetchone()[0]
                
                cursor.execute('''
                UPDATE articles SET 
                    title = ?, author = ?, publish_time = ?, 
                    content = ?, source = ?, word_count = ?
                WHERE id = ?
                ''', (
                    article.get('title', ''),
                    article.get('author', ''),
                    article.get('publish_time', ''),
                    article.get('content', ''),
                    article.get('source', ''),
                    article.get('word_count', 0),
                    article_id
                ))
            else:
                # 插入新文章
                cursor.execute('''
                INSERT INTO articles 
                (url, title, author, publish_time, content, source, word_count, importance)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    article['url'],
                    article.get('title', ''),
                    article.get('author', ''),
                    article.get('publish_time', ''),
                    article.get('content', ''),
                    article.get('source', ''),
                    article.get('word_count', 0),
                    1 if article.get('importance', False) else 0
                ))
                article_id = cursor.lastrowid
            
            # 保存股票信息
            # 只有当文章对象中包含股票信息且不为空时才更新股票数据
            # 采集器创建的文章对象中stocks为空列表，所以需要特殊处理
            stocks = article.get('stocks', [])
            if isinstance(stocks, list) and len(stocks) > 0:
                # 只有当股票列表不为空时才更新
                cursor.execute('DELETE FROM stocks WHERE article_id = ?', (article_id,))
                for stock in stocks:
                    if isinstance(stock, dict):
                        stock_name = stock.get('name', '')
                    else:
                        stock_name = str(stock)
                    if stock_name:
                        cursor.execute('''
                        INSERT INTO stocks (article_id, stock_name)
                        VALUES (?, ?)
                        ''', (article_id, stock_name))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"保存文章失败: {e}")
            conn.rollback()
            conn.close()
            return False
    
    def save_articles(self, articles):
        """批量保存文章到数据库"""
        try:
            for article in articles:
                self.save_article(article)
            return len(articles)
        except Exception as e:
            print(f"批量保存文章失败: {e}")
            return 0
    
    def load_articles(self):
        """加载所有文章，按时间降序排序"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
            SELECT * FROM articles
            ORDER BY publish_time DESC
            ''')
            rows = cursor.fetchall()
            
            articles = []
            for row in rows:
                article = {
                    'id': row[0],
                    'url': row[1],
                    'title': row[2],
                    'author': row[3],
                    'publish_time': row[4],
                    'content': row[5],
                    'source': row[6],
                    'word_count': row[7],
                    'importance': bool(row[8]),
                    'created_at': row[9]
                }
                # 加载股票信息
                cursor.execute('''
                SELECT stock_name FROM stocks WHERE article_id = ?
                ''', (row[0],))
                stocks = []
                for stock_row in cursor.fetchall():
                    stocks.append({'name': stock_row[0]})
                article['stocks'] = stocks
                articles.append(article)
            
            conn.close()
            return articles
        except Exception as e:
            print(f"加载文章失败: {e}")
            conn.close()
            return []
    
    def get_articles_by_date(self, date):
        """获取指定日期的文章"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
            SELECT * FROM articles WHERE publish_time LIKE ?
            ORDER BY publish_time DESC
            ''', (f'{date}%',))
            rows = cursor.fetchall()
            
            articles = []
            for row in rows:
                article = {
                    'id': row[0],
                    'url': row[1],
                    'title': row[2],
                    'author': row[3],
                    'publish_time': row[4],
                    'content': row[5],
                    'source': row[6],
                    'word_count': row[7],
                    'importance': bool(row[8]),
                    'created_at': row[9]
                }
                # 加载股票信息
                cursor.execute('''
                SELECT stock_name FROM stocks WHERE article_id = ?
                ''', (row[0],))
                stocks = []
                for stock_row in cursor.fetchall():
                    stocks.append({'name': stock_row[0]})
                article['stocks'] = stocks
                articles.append(article)
            
            conn.close()
            return articles
        except Exception as e:
            print(f"按日期获取文章失败: {e}")
            conn.close()
            return []
    
    def get_important_articles(self):
        """获取重要文章"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
            SELECT * FROM articles WHERE importance = 1
            ORDER BY publish_time DESC
            ''')
            rows = cursor.fetchall()
            
            articles = []
            for row in rows:
                article = {
                    'id': row[0],
                    'url': row[1],
                    'title': row[2],
                    'author': row[3],
                    'publish_time': row[4],
                    'content': row[5],
                    'source': row[6],
                    'word_count': row[7],
                    'importance': bool(row[8]),
                    'created_at': row[9]
                }
                # 加载股票信息
                cursor.execute('''
                SELECT stock_name FROM stocks WHERE article_id = ?
                ''', (row[0],))
                stocks = []
                for stock_row in cursor.fetchall():
                    stocks.append({'name': stock_row[0]})
                article['stocks'] = stocks
                articles.append(article)
            
            conn.close()
            return articles
        except Exception as e:
            print(f"获取重要文章失败: {e}")
            conn.close()
            return []
    
    def get_today_articles(self):
        """获取当天文章"""
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        return self.get_articles_by_date(today)
    
    def update_article_importance(self, article_id, importance):
        """更新文章的重要性标记"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
            UPDATE articles SET importance = ? WHERE id = ?
            ''', (1 if importance else 0, article_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"更新文章重要性失败: {e}")
            conn.close()
            return False
    
    def delete_article(self, article_id):
        """删除文章及其关联的股票信息"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('DELETE FROM articles WHERE id = ?', (article_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"删除文章失败: {e}")
            conn.rollback()
            conn.close()
            return False
    
    def backup_database(self, backup_path=None):
        """备份数据库"""
        try:
            if not backup_path:
                backup_path = f"data/database/backup/articles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            
            # 确保备份目录存在
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # 连接到源数据库
            source_conn = self._get_connection()
            
            # 连接到新数据库
            backup_conn = sqlite3.connect(backup_path)
            
            # 备份数据
            with backup_conn:
                source_conn.backup(backup_conn)
            
            source_conn.close()
            backup_conn.close()
            return backup_path
        except Exception as e:
            print(f"备份数据库失败: {e}")
            return None
