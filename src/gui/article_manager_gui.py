"""
热点与趋势 - 桌面应用
功能：批量采集、定时任务、搜索筛选、导出分享、数据统计
"""

import tkinter as tk
import re
from tkinter import ttk, messagebox, filedialog, scrolledtext
import json
import os
import subprocess
import time
from datetime import datetime, timedelta

# 导入Windows API模块
try:
    import win32gui
    import win32api
    import win32con
    has_win32 = True
except ImportError:
    has_win32 = False
import threading
import webbrowser
from pathlib import Path
import schedule
import time
import win32gui
import win32con
from paddleocr import PaddleOCR
from scrapling import Fetcher, Selector
from database.db_manager import DatabaseManager

class ArticleManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("热点与趋势")
        self.root.geometry("1200x800")
        
        # 数据文件
        self.articles_file = 'data/database/articles_database.json'
        self.config_file = 'config/manager_config.json'
        
        # 数据库管理
        self.db_manager = DatabaseManager()
        
        # 加载数据
        self.articles = self.load_articles()
        self.config = self.load_config()
        
        # 定时任务状态
        self.scheduler_running = False
        self.scheduler_thread = None
        
        # 显示模式状态（0: 显示当天, 1: 显示全部, 2: 显示重要）
        self.display_mode = 0
        
        # 创建界面
        self.create_menu()
        self.create_main_ui()
        self.update_stats()
        # 默认显示当天文章
        self.show_today_articles()
        
        # 启动时自动执行清理
        self.auto_cleanup_on_start()
        
        # 启动定时任务
        self.start_scheduler()
        
    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="采集最新文章", command=self.collect_articles)
        file_menu.add_command(label="导出数据", command=self.export_data)
        file_menu.add_separator()
        file_menu.add_command(label="打开原文", command=self.open_article_url)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        
        # 工具菜单
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="网站配置", command=self.open_config_manager)
        tools_menu.add_command(label="定时任务设置", command=self.open_scheduler)

        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self.show_help)
        help_menu.add_command(label="关于", command=self.show_about)
        
    def create_main_ui(self):
        """创建主界面"""
        # 顶部工具栏
        toolbar = tk.Frame(self.root, bg='#f8f9fa', bd=1, relief=tk.RAISED)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=10, pady=8)
        
        # 按钮样式
        button_style = {'font': ('微软雅黑', 10, 'bold'), 'padx': 12, 'pady': 6}
        
        # 左侧功能按钮
        left_toolbar = tk.Frame(toolbar, bg='#f8f9fa')
        left_toolbar.pack(side=tk.LEFT)
        
        # 采集按钮（最常用功能，放在最左侧）
        collect_btn = tk.Button(left_toolbar, text="🔄 采集最新", command=self.collect_articles, 
                               bg='#4CAF50', fg='white', **button_style, activebackground='#45a049')
        collect_btn.pack(side=tk.LEFT, padx=8)
        

        
        # 显示全部按钮
        self.show_all_btn = tk.Button(left_toolbar, text="📄 显示当天", command=self.show_all_articles, 
                               bg='#795548', fg='white', **button_style, activebackground='#5D4037')
        self.show_all_btn.pack(side=tk.LEFT, padx=8)
        
        # 右侧管理按钮
        right_toolbar = tk.Frame(toolbar, bg='#f8f9fa')
        right_toolbar.pack(side=tk.RIGHT)
        
        # 整理按钮
        organize_btn = tk.Button(right_toolbar, text="📋 整理", command=self.open_organize_window, 
                              bg='#607D8B', fg='white', **button_style, activebackground='#455A64')
        organize_btn.pack(side=tk.RIGHT, padx=8)
        
        # 配置管理按钮
        config_btn = tk.Button(right_toolbar, text="⚙️ 配置", command=self.open_api_config, 
                             bg='#9C27B0', fg='white', **button_style, activebackground='#7B1FA2')
        config_btn.pack(side=tk.RIGHT, padx=8)
        
        # 日期导航
        date_frame = tk.Frame(toolbar, bg='#f8f9fa')
        date_frame.pack(side=tk.RIGHT, padx=10)
        
        # 向左箭头按钮（后翻一天）
        prev_btn = tk.Button(date_frame, text="◀", command=self.prev_day, 
                           font=('微软雅黑', 9), padx=5, pady=2, 
                           bg='#2196F3', fg='white', activebackground='#1976D2')
        prev_btn.pack(side=tk.LEFT, padx=2)
        
        # 日期显示
        self.date_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        date_label = tk.Label(date_frame, textvariable=self.date_var, 
                            font=('微软雅黑', 10, 'bold'), bg='#ffffff', 
                            bd=2, relief=tk.GROOVE, width=12)
        date_label.pack(side=tk.LEFT, padx=2)
        
        # 向右箭头按钮（前翻一天）
        next_btn = tk.Button(date_frame, text="▶", command=self.next_day, 
                           font=('微软雅黑', 9), padx=5, pady=2, 
                           bg='#2196F3', fg='white', activebackground='#1976D2')
        next_btn.pack(side=tk.LEFT, padx=2)
        
        # 搜索框（合并文章和股票搜索）
        search_frame = tk.Frame(toolbar, bg='#f8f9fa')
        search_frame.pack(side=tk.RIGHT, padx=10)
        
        tk.Label(search_frame, text="搜索:", font=('微软雅黑', 10, 'bold'), bg='#f8f9fa').pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_articles)
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=60, 
                               font=('微软雅黑', 10), bd=2, relief=tk.GROOVE)
        search_entry.pack(side=tk.LEFT, padx=5)
        
        # 主内容区（左右分栏）
        main_paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=5, bg='#ffffff')
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
        
        # 左侧：文章列表
        left_frame = tk.Frame(main_paned, bg='#ffffff', bd=1, relief=tk.GROOVE)
        main_paned.add(left_frame, width=450)
        
        # 列表标题
        list_title_frame = tk.Frame(left_frame, bg='#e3f2fd')
        list_title_frame.pack(fill=tk.X, pady=5)
        
        # 列表滚动区域
        list_frame = tk.Frame(left_frame, bg='#ffffff')
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建 Treeview
        columns = ('序号', '标题', '作者', '时间')
        self.article_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=30)
        
        # 配置列
        for col in columns:
            self.article_tree.heading(col, text=col, anchor=tk.CENTER)
            if col == '序号':
                self.article_tree.column(col, width=50, anchor=tk.CENTER)
            elif col == '标题':
                self.article_tree.column(col, width=180, anchor=tk.W)
            elif col == '作者':
                self.article_tree.column(col, width=100, anchor=tk.CENTER)
            else:
                self.article_tree.column(col, width=120, anchor=tk.CENTER)
        
        # 配置样式
        style = ttk.Style()
        style.configure("Treeview.Heading", font=('微软雅黑', 10, 'bold'), foreground='#1976D2')
        style.configure("Treeview", font=('微软雅黑', 9), rowheight=28)
        style.map("Treeview", background=[('selected', '#e3f2fd')], foreground=[('selected', '#1976D2')])
        
        self.article_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.article_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.article_tree.configure(yscrollcommand=scrollbar.set)
        
        # 绑定双击事件 - 双击时打开浏览器
        self.article_tree.bind('<Double-1>', self.open_article_url)
        
        # 绑定右键菜单
        self.article_tree.bind('<Button-3>', self.show_context_menu)
        
        # 绑定选择事件 - 选择文章时更新股票池显示
        self.article_tree.bind('<<TreeviewSelect>>', self.on_article_select)
        
        # 创建右键菜单
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="发送AI分析", command=self.send_to_ai_analysis)
        self.context_menu.add_command(label="标记为重要", command=self.mark_as_importance)
        self.context_menu.add_command(label="取消重要标记", command=self.unmark_importance)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="删除", command=self.delete_selected_article)
        
        # 右侧：DeepSeek和股票池
        right_frame = tk.Frame(main_paned, bg='#ffffff', bd=1, relief=tk.GROOVE)
        main_paned.add(right_frame, width=600)
        
        # 上方：DeepSeek对话窗口（70%高度）
        deepseek_frame = tk.Frame(right_frame, bg='#ffffff', bd=1, relief=tk.RAISED)
        deepseek_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        

        
        # 嵌入DeepSeek对话窗口
        browser_frame = tk.Frame(deepseek_frame, bg='#ffffff')
        browser_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 保存浏览器框架的引用
        self.browser_frame = browser_frame
        
        # 嵌入DeepSeek对话窗口
        self.embed_deepseek_browser()
        
        # 下方：股票池（30%高度）
        stock_frame = tk.Frame(right_frame, bg='#ffffff', bd=1, relief=tk.RAISED)
        stock_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, padx=5, pady=5)
        
        # 股票池标题
        stock_title_frame = tk.Frame(stock_frame, bg='#e3f2fd')
        stock_title_frame.pack(fill=tk.X, pady=2)
        tk.Label(stock_title_frame, text="股票池", font=('微软雅黑', 10, 'bold'), bg='#e3f2fd', fg='#1976D2').pack(side=tk.LEFT, padx=10, pady=2)
        
        # 股票池内容
        stock_list_frame = tk.Frame(stock_frame, bg='#ffffff')
        stock_list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 创建股票池Treeview（根据股票名称长度调整列数，4个汉字宽度）
        stock_columns = ('股票1', '股票2', '股票3', '股票4', '股票5', '股票6')
        self.stock_tree = ttk.Treeview(stock_list_frame, columns=stock_columns, show='headings', height=4)
        
        # 配置列
        for col in stock_columns:
            self.stock_tree.heading(col, text=col, anchor=tk.CENTER)
            self.stock_tree.column(col, width=70, anchor=tk.W)
        
        # 配置样式
        style = ttk.Style()
        style.configure("Treeview.Heading", font=('微软雅黑', 9, 'bold'), foreground='#1976D2')
        style.configure("Treeview", font=('微软雅黑', 9), rowheight=28)
        style.map("Treeview", background=[('selected', '#e3f2fd')], foreground=[('selected', '#1976D2')])
        
        self.stock_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 滚动条
        stock_scrollbar = ttk.Scrollbar(stock_list_frame, orient=tk.VERTICAL, command=self.stock_tree.yview)
        stock_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.stock_tree.configure(yscrollcommand=stock_scrollbar.set)
        
        # 创建股票池右键菜单
        self.stock_context_menu = tk.Menu(self.root, tearoff=0)
        self.stock_context_menu.add_command(label="删除股票", command=self.delete_selected_stock)
        
        # 绑定右键菜单
        self.stock_tree.bind('<Button-3>', self.show_stock_context_menu)
        
        # 股票池按钮
        stock_btn_frame = tk.Frame(stock_frame, bg='#ffffff', bd=1, relief=tk.RAISED)
        stock_btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 左侧按钮
        left_stock_btns = tk.Frame(stock_btn_frame, bg='#ffffff')
        left_stock_btns.pack(side=tk.LEFT)
        
        # 从剪贴板添加股票按钮（最常用功能）
        clipboard_btn = tk.Button(left_stock_btns, text="📋 剪贴板", command=self.add_stocks_from_clipboard, 
                                bg='#FF9800', fg='white', font=('微软雅黑', 9), padx=5, pady=3)
        clipboard_btn.pack(side=tk.LEFT, padx=5)
        
        # 手动添加股票按钮
        add_manual_btn = tk.Button(left_stock_btns, text="➕ 手动添加", command=self.manual_add_stock, 
                                 bg='#4CAF50', fg='white', font=('微软雅黑', 9), padx=5, pady=3)
        add_manual_btn.pack(side=tk.LEFT, padx=5)
        
        # 分析股票按钮
        analyze_btn = tk.Button(left_stock_btns, text="🔍 分析", command=self.analyze_stocks, 
                              bg='#2196F3', fg='white', font=('微软雅黑', 9), padx=5, pady=3)
        analyze_btn.pack(side=tk.LEFT, padx=5)
        
        # 右侧按钮
        right_stock_btns = tk.Frame(stock_btn_frame, bg='#ffffff')
        right_stock_btns.pack(side=tk.RIGHT)
        
        # DeepSeek分析按钮
        deepseek_btn = tk.Button(right_stock_btns, text="🤖 DeepSeek", command=self.open_deepseek_analysis, 
                                bg='#9C27B0', fg='white', font=('微软雅黑', 9), padx=5, pady=3)
        deepseek_btn.pack(side=tk.RIGHT, padx=5)
        
        # OCR识别按钮
        ocr_btn = tk.Button(right_stock_btns, text="📷 OCR", command=self.ocr_recognition, 
                           bg='#795548', fg='white', font=('微软雅黑', 9), padx=5, pady=3)
        ocr_btn.pack(side=tk.RIGHT, padx=5)
        
        # 清空股票按钮（危险操作，放在最右侧）
        clear_stock_btn = tk.Button(right_stock_btns, text="🗑️ 清空", command=self.clear_stocks, 
                                  bg='#f44336', fg='white', font=('微软雅黑', 9), padx=5, pady=3)
        clear_stock_btn.pack(side=tk.RIGHT, padx=5)
        
        # 绑定窗口大小变化事件
        self.root.bind('<Configure>', self.on_window_resize)
        
        # 绑定键盘事件，左右箭头键控制日期切换
        self.root.bind('<Left>', lambda event: self.prev_day())
        self.root.bind('<Right>', lambda event: self.next_day())
        
        # 底部状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = tk.Label(self.root, textvariable=self.status_var, 
                             relief=tk.SUNKEN, anchor=tk.W, font=('微软雅黑', 10), bg='#f5f5f5')
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
    def load_articles(self):
        """加载文章数据"""
        try:
            # 从数据库加载文章
            articles = self.db_manager.load_articles()
            # 如果数据库中没有数据，尝试从JSON文件导入
            if not articles and os.path.exists(self.articles_file):
                with open(self.articles_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        articles = data
                    elif isinstance(data, dict):
                        articles = data.get('articles', [])
                    else:
                        articles = []
                # 将JSON数据导入到数据库
                for article in articles:
                    self.db_manager.save_article(article)
                # 再次从数据库加载
                articles = self.db_manager.load_articles()
            return articles
        except Exception as e:
            print(f"加载文章失败: {e}")
            return []
    
    def save_articles(self):
        """保存文章数据"""
        try:
            # 保存到数据库
            for article in self.articles:
                self.db_manager.save_article(article)
            # 同时备份数据库
            backup_path = self.db_manager.backup_database()
            if backup_path:
                print(f"数据库备份成功: {backup_path}")
        except Exception as e:
            print(f"保存文章失败: {e}")
    
    def load_config(self):
        """加载配置"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'auto_collect': False, 'collect_time': '09:00'}
    
    def get_source_icon(self, source):
        """根据信息源返回对应的图标"""
        source_icons = {
            '同花顺财经': '🔍',
            '韭研公社': '🏠',
            '同花顺数据中心': '📊'
        }
        return source_icons.get(source, '📄')
    
    def load_article_list(self):
        """加载文章列表"""
        # 清空列表
        for item in self.article_tree.get_children():
            self.article_tree.delete(item)
        
        # 添加文章，序号从文章总数开始递减，最新的文章序号最大
        total_articles = len(self.articles)
        for i, article in enumerate(self.articles, 1):
            title = article.get('title', '')
            # 为重要文章添加特殊标记
            if article.get('importance', False):
                title_display = "⭐ " + title[:28] + '...' if len(title) > 28 else "⭐ " + title
            else:
                title_display = title[:30] + '...' if len(title) > 30 else title
            author = article.get('author', '')
            pub_time = article.get('publish_time', '')
            source = article.get('source', '')
            
            # 获取信息源图标
            source_icon = self.get_source_icon(source)
            # 构建带图标的序号（最新的文章序号最大）
            icon_index = f"{source_icon}{total_articles - i + 1}"
            
            # 插入文章到列表
            item = self.article_tree.insert('', tk.END, values=(icon_index, title_display, author, pub_time))
            
            # 为重要文章设置不同的字体颜色
            if article.get('importance', False):
                self.article_tree.item(item, tags=('important',))
                # 配置重要文章的标签样式
                self.article_tree.tag_configure('important', foreground='#FF6B6B', font=('微软雅黑', 9, 'bold'))
    
    def filter_articles(self, *args):
        """筛选文章"""
        search_text = self.search_var.get().lower()
        
        # 清空列表
        for item in self.article_tree.get_children():
            self.article_tree.delete(item)
        
        # 标准化股票代码（返回纯数字代码）
        def standardize_stock_code(code):
            # 移除可能的前缀
            code = code.upper().replace('SH', '').replace('SZ', '')
            if len(code) == 6 and code.isdigit():
                return code
            return code
        
        # 筛选
        filtered_articles = []
        
        # 先收集所有符合条件的文章
        for article in self.articles:
            # 搜索过滤
            title = article.get('title', '').lower()
            author = article.get('author', '').lower()
            content = article.get('content', '').lower()
            
            # 检查文章内容是否匹配
            article_match = not search_text or search_text in title or search_text in author or search_text in content
            
            # 检查股票是否匹配
            stock_match = not search_text
            if search_text:
                article_stocks = article.get('stocks', [])
                standardized_stock = standardize_stock_code(search_text)
                
                for stock in article_stocks:
                    if isinstance(stock, dict):
                        # 检查股票代码
                        stock_code = standardize_stock_code(stock.get('code', ''))
                        if stock_code == standardized_stock:
                            stock_match = True
                            break
                        # 检查股票名称
                        stock_name = stock.get('name', '').lower()
                        if search_text.lower() in stock_name:
                            stock_match = True
                            break
                    else:
                        # 旧格式的股票数据
                        stock_str = str(stock).lower()
                        if standardized_stock.lower() in stock_str or search_text.lower() in stock_str:
                            stock_match = True
                            break
            
            # 如果文章内容或股票匹配，则保留
            if article_match or stock_match:
                # 添加到筛选列表
                filtered_articles.append(article)
        
        # 保存筛选后的文章列表，用于选择时获取正确的文章对象
        self.filtered_articles = filtered_articles
        
        # 然后按时间顺序添加到列表，序号从总数开始递减
        total_articles = len(filtered_articles)
        for i, article in enumerate(filtered_articles, 1):
            title = article.get('title', '')
            # 为重要文章添加特殊标记
            if article.get('importance', False):
                title_display = "⭐ " + title[:28] + '...' if len(title) > 28 else "⭐ " + title
            else:
                title_display = title[:30] + '...' if len(title) > 30 else title
            source = article.get('source', '')
            
            # 获取信息源图标
            source_icon = self.get_source_icon(source)
            # 构建带图标的序号（最新的文章序号最大）
            icon_index = f"{source_icon}{total_articles - i + 1}"
            
            # 插入文章到列表
            item = self.article_tree.insert('', tk.END, values=(icon_index, title_display, article.get('author', ''), article.get('publish_time', '')))
            
            # 为重要文章设置不同的字体颜色
            if article.get('importance', False):
                self.article_tree.item(item, tags=('important',))
                # 配置重要文章的标签样式
                self.article_tree.tag_configure('important', foreground='#FF6B6B', font=('微软雅黑', 9, 'bold'))
    

    
    def scrapling_collect_articles(self):
        """使用Scrapling采集文章"""
        print("开始使用Scrapling采集文章...")
        
        try:
            from collectors.scrapling_collector import ScraplingCollector
            
            # 创建采集器
            collector = ScraplingCollector()
            
            # 采集所有网站
            articles = collector.collect_from_all_websites(max_articles_per_website=10)
            
            if not articles:
                return False, "未采集到任何文章"
            
            # 保存文章
            total_count = collector.save_articles(articles, self.articles_file)
            
            print(f"\n成功采集 {len(articles)} 篇文章，总共有 {total_count} 篇文章")
            return True, f"成功采集 {len(articles)} 篇文章"
        except Exception as e:
            print(f"采集失败: {e}")
            return False, f"采集失败: {str(e)}"
    
    def collect_articles(self):
        """采集文章"""
        self.status_var.set("正在采集最新文章...")
        self.root.update()
        
        # 在新线程中执行采集
        def collect_thread():
            try:
                # 使用Scrapling采集文章
                success, message = self.scrapling_collect_articles()
                
                if success:
                    # 加载文章数据
                    self.articles = self.load_articles()
                    
                    # 清理非当天的信息
                    today = datetime.now().strftime('%Y-%m-%d')
                    today_articles = []
                    removed_count = 0
                    
                    for article in self.articles:
                        pub_time = article.get('publish_time', '')
                        if pub_time and today in pub_time:
                            today_articles.append(article)
                        else:
                            removed_count += 1
                    
                    # 保存过滤后的文章
                    self.articles = today_articles
                    self.save_articles()
                    
                    # 重新加载文章列表和更新统计信息
                    self.load_article_list()
                    self.update_stats()
                    self.root.after(0, lambda: self.status_var.set(f"采集完成，已清理 {removed_count} 篇非当天文章"))
                else:
                    # 检查是否是cookies问题
                    if "未找到cookies文件" in message or "加载cookies失败" in message:
                        self.root.after(0, lambda: messagebox.showinfo("需要登录", "请先运行 python src/login_save_cookies.py 完成登录"))
                        self.root.after(0, lambda: self.status_var.set("需要登录"))
                    else:
                        self.root.after(0, lambda: messagebox.showerror("采集失败", message))
                        self.root.after(0, lambda: self.status_var.set("采集失败"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("采集失败", str(e)))
                self.root.after(0, lambda: self.status_var.set("采集失败"))
        
        thread = threading.Thread(target=collect_thread, daemon=True)
        thread.start()
    
    def export_data(self):
        """导出数据"""
        filetypes = [
            ('CSV 表格', '*.csv'),
            ('JSON 文件', '*.json'),
            ('Markdown 文档', '*.md'),
            ('所有文件', '*.*')
        ]
        
        filename = filedialog.asksaveasfilename(
            title='导出数据',
            defaultextension='.csv',
            filetypes=filetypes
        )
        
        if not filename:
            return
        
        try:
            if filename.endswith('.csv'):
                import csv
                with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    # 写入表头
                    writer.writerow(['序号', '标题', '作者', '发布时间', '信息源', '链接', '股票']) 
                    # 写入数据
                    for i, article in enumerate(self.articles, 1):
                        title = article.get('title', '')
                        author = article.get('author', '')
                        pub_time = article.get('publish_time', '')
                        source = article.get('source', '')
                        url = article.get('url', '')
                        stocks = ', '.join(stock.get('name', '') for stock in article.get('stocks', []))
                        writer.writerow([i, title, author, pub_time, source, url, stocks])
            elif filename.endswith('.json'):
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump({'articles': self.articles}, f, ensure_ascii=False, indent=2)
            elif filename.endswith('.md'):
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("# 韭研公社文章合集\n\n")
                    f.write(f"导出时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"共 {len(self.articles)} 篇文章\n\n")
                    for i, article in enumerate(self.articles, 1):
                        f.write(f"## {i}. {article.get('title', '')}\n\n")
                        f.write(f"**作者**: {article.get('author', '')}\n\n")
                        f.write(f"**发布**: {article.get('publish_time', '')}\n\n")
                        f.write(f"**内容**:\n{article.get('content', '')}\n\n")
                        f.write("---\n\n")
            
            messagebox.showinfo("导出成功", f"数据已导出到:\n{filename}")
            self.status_var.set(f"已导出：{filename}")
        except Exception as e:
            messagebox.showerror("导出失败", str(e))
    
    def import_data(self):
        """导入数据"""
        filetypes = [
            ('CSV 表格', '*.csv'),
            ('JSON 文件', '*.json'),
            ('所有文件', '*.*')
        ]
        
        filename = filedialog.askopenfilename(
            title='导入数据',
            filetypes=filetypes
        )
        
        if not filename:
            return
        
        try:
            imported_count = 0
            
            if filename.endswith('.csv'):
                import csv
                with open(filename, 'r', encoding='utf-8-sig') as f:
                    reader = csv.reader(f)
                    next(reader)  # 跳过表头
                    for row in reader:
                        if len(row) >= 6:
                            article = {
                                'title': row[1],
                                'author': row[2],
                                'publish_time': row[3],
                                'source': row[4],
                                'url': row[5]
                            }
                            # 解析股票信息
                            if len(row) >= 7 and row[6]:
                                stocks = []
                                for stock_name in row[6].split(','):
                                    stock_name = stock_name.strip()
                                    if stock_name:
                                        stocks.append({'name': stock_name})
                                article['stocks'] = stocks
                            else:
                                article['stocks'] = []
                            
                            # 保存到数据库
                            if self.db_manager.save_article(article):
                                imported_count += 1
            elif filename.endswith('.json'):
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    articles = data.get('articles', [])
                    for article in articles:
                        if self.db_manager.save_article(article):
                            imported_count += 1
            
            # 重新加载文章列表
            self.articles = self.load_articles()
            # 根据当前显示模式重新筛选文章
            if self.display_mode == 0:
                # 显示当天
                self.articles = self.db_manager.get_today_articles()
            elif self.display_mode == 1:
                # 显示全部
                pass  # 已经是全部文章
            elif self.display_mode == 2:
                # 显示重要
                self.articles = self.db_manager.get_important_articles()
            self.load_article_list()
            self.update_stats()
            
            messagebox.showinfo("导入成功", f"成功导入 {imported_count} 篇文章")
            self.status_var.set(f"已导入 {imported_count} 篇文章")
        except Exception as e:
            messagebox.showerror("导入失败", str(e))
    
    def export_current_article(self):
        """导出当前文章"""
        selection = self.article_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一篇文章")
            return
        
        index = self.article_tree.index(selection[0])
        article = self.articles[index]
        
        filename = filedialog.asksaveasfilename(
            title='导出文章',
            defaultextension='.md',
            initialfile=f"{article.get('title', '文章')[:20]}.md"
        )
        
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"# {article.get('title', '')}\n\n")
                f.write(f"**作者**: {article.get('author', '')}\n\n")
                f.write(f"**发布时间**: {article.get('publish_time', '')}\n\n")
                f.write(f"**原文链接**: {article.get('url', '')}\n\n")
                f.write(f"**采集时间**: {article.get('collected_time', '')}\n\n")
                f.write("---\n\n")
                f.write(article.get('content', ''))
            
            messagebox.showinfo("导出成功", f"文章已导出到:\n{filename}")
    
    def copy_content(self):
        """复制全文"""
        selection = self.article_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一篇文章")
            return
        
        index = self.article_tree.index(selection[0])
        article = self.articles[index]
        
        self.root.clipboard_clear()
        self.root.clipboard_append(article.get('content', ''))
        messagebox.showinfo("复制成功", "文章内容已复制到剪贴板")
    
    def on_article_select(self, event=None):
        """选择文章时更新股票池显示"""
        selection = self.article_tree.selection()
        if selection:
            index = self.article_tree.index(selection[0])
            # 检查是否有筛选后的文章列表
            if hasattr(self, 'filtered_articles') and len(self.filtered_articles) > 0:
                # 使用筛选后的文章列表
                if index < len(self.filtered_articles):
                    article = self.filtered_articles[index]
                    # 更新股票池显示
                    self.update_stock_list(article)
            else:
                # 使用原始文章列表
                if index < len(self.articles):
                    article = self.articles[index]
                    # 更新股票池显示
                    self.update_stock_list(article)
    
    def open_article_url(self, event=None):
        """在浏览器打开原文并更新股票池显示"""
        selection = self.article_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一篇文章")
            return
        
        index = self.article_tree.index(selection[0])
        article = None
        
        # 检查是否有筛选后的文章列表
        if hasattr(self, 'filtered_articles') and len(self.filtered_articles) > 0:
            # 使用筛选后的文章列表
            if index < len(self.filtered_articles):
                article = self.filtered_articles[index]
        else:
            # 使用原始文章列表
            if index < len(self.articles):
                article = self.articles[index]
        
        if article:
            url = article.get('url', '')
            
            # 更新股票池显示
            self.update_stock_list(article)
            
            if url:
                try:
                    webbrowser.open(url)
                    self.status_var.set(f"已在浏览器打开：{url[:50]}...")
                except Exception as e:
                    messagebox.showerror("错误", f"无法打开浏览器：{str(e)}")
            else:
                messagebox.showwarning("提示", "该文章没有 URL 链接")
        else:
            messagebox.showwarning("提示", "无法获取文章信息")
    
    def show_context_menu(self, event):
        """显示右键菜单"""
        item = self.article_tree.identify_row(event.y)
        if item:
            self.article_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def send_to_ai_analysis(self):
        """发送AI分析"""
        # 获取选中的文章
        selection = self.article_tree.selection()
        if not selection:
            return
        
        # 获取文章URL
        index = self.article_tree.index(selection[0])
        if index < len(self.articles):
            article = self.articles[index]
            article_url = article.get('url', '')
            
            if article_url:
                # 构建DeepSeek分析请求
                prompt = f"帮我分析总结\"{article_url}\"的内容，并提取文章中提到的相关的股票名称信息输出成表格"
                
                # 尝试使用已打开的DeepSeek窗口
                if hasattr(self, 'deepseek_hwnd') and self.deepseek_hwnd:
                    try:
                        import pyperclip
                        import win32api
                        import win32con
                        import win32gui
                        
                        # 将提示词复制到剪贴板
                        pyperclip.copy(prompt)
                        
                        # 激活DeepSeek窗口
                        win32gui.SetForegroundWindow(self.deepseek_hwnd)
                        time.sleep(0.5)
                        
                        # 模拟Ctrl+V粘贴
                        win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
                        win32api.keybd_event(ord('V'), 0, 0, 0)
                        win32api.keybd_event(ord('V'), 0, win32con.KEYEVENTF_KEYUP, 0)
                        win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
                        time.sleep(0.3)
                        
                        # 模拟Enter发送
                        win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
                        win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
                    except Exception as e:
                        import urllib.parse
                        encoded_prompt = urllib.parse.quote(prompt)
                        deepseek_url = f"https://chat.deepseek.com/?q={encoded_prompt}"
                        import webbrowser
                        webbrowser.open(deepseek_url)
                        messagebox.showinfo("AI分析", f"已打开DeepSeek网页并填充分析请求")
                else:
                    import urllib.parse
                    encoded_prompt = urllib.parse.quote(prompt)
                    deepseek_url = f"https://chat.deepseek.com/?q={encoded_prompt}"
                    import webbrowser
                    webbrowser.open(deepseek_url)
                    messagebox.showinfo("AI分析", "已打开DeepSeek网页并填充分析请求")
            else:
                messagebox.showinfo("提示", "该文章没有URL")
    
    def mark_as_importance(self):
        """标记为重要"""
        selection = self.article_tree.selection()
        if not selection:
            return
        
        index = self.article_tree.index(selection[0])
        if index < len(self.articles):
            article = self.articles[index]
            article['importance'] = True
            # 更新数据库
            if 'id' in article:
                self.db_manager.update_article_importance(article['id'], True)
            self.save_articles()
            # 刷新文章列表显示
            self.load_article_list()
    
    def unmark_importance(self):
        """取消重要标记"""
        selection = self.article_tree.selection()
        if not selection:
            return
        
        index = self.article_tree.index(selection[0])
        if index < len(self.articles):
            article = self.articles[index]
            if 'importance' in article:
                del article['importance']
            # 更新数据库
            if 'id' in article:
                self.db_manager.update_article_importance(article['id'], False)
            self.save_articles()
            # 刷新文章列表显示
            self.load_article_list()
    
    def delete_selected_article(self):
        """删除选中的文章"""
        # 获取选中的文章
        selection = self.article_tree.selection()
        if not selection:
            return
        
        # 确认删除
        if messagebox.askyesno("确认删除", "确定要删除选中的文章吗？"):
            # 获取文章索引
            index = self.article_tree.index(selection[0])
            if 0 <= index < len(self.articles):
                # 删除文章
                article = self.articles[index]
                deleted_title = article.get('title', '')
                # 从数据库删除
                if 'id' in article:
                    self.db_manager.delete_article(article['id'])
                # 从内存中删除
                del self.articles[index]
                self.save_articles()
                self.load_article_list()
                self.update_stats()
                self.status_var.set(f"已删除文章：{deleted_title}")
    
    def set_yesterday_date(self):
        """设置日期为昨天"""
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        self.date_var.set(yesterday)
    
    def query_by_date(self):
        """根据日期查询文章"""
        date = self.date_var.get()
        if not date:
            messagebox.showwarning("提示", "请输入日期")
            return
        
        try:
            # 从数据库查询指定日期的文章
            date_articles = self.db_manager.get_articles_by_date(date)
            
            if not date_articles:
                messagebox.showinfo("查询结果", f"未找到 {date} 的文章")
                return
            
            # 保存原始文章列表
            self.original_articles = self.articles.copy()
            
            # 显示查询结果
            self.articles = date_articles
            self.load_article_list()
            self.update_stats()
            self.status_var.set(f"已查询 {date} 的文章，共 {len(date_articles)} 篇")
        except Exception as e:
            print(f"查询文章失败: {e}")
            messagebox.showerror("查询失败", f"查询文章失败: {str(e)}")
    
    def show_all_articles(self):
        """循环切换显示模式：显示当天 → 显示全部 → 显示重要"""
        try:
            # 切换显示模式
            self.display_mode = (self.display_mode + 1) % 3
            
            if self.display_mode == 0:
                # 显示当天
                self.show_today_articles()
            elif self.display_mode == 1:
                # 显示全部
                self.show_all_articles_internal()
            else:
                # 显示重要
                self.show_important_articles()
        except Exception as e:
            print(f"切换显示模式失败: {e}")
            messagebox.showerror("切换失败", f"切换显示模式失败: {str(e)}")
    
    def show_all_articles_internal(self):
        """显示所有文章"""
        try:
            # 重新加载所有文章
            self.articles = self.load_articles()
            self.load_article_list()
            self.update_stats()
            self.status_var.set("已显示所有文章")
            # 更新按钮文本
            self.show_all_btn.config(text="📄 显示全部")
        except Exception as e:
            print(f"加载所有文章失败: {e}")
            messagebox.showerror("加载失败", f"加载所有文章失败: {str(e)}")
    
    def show_today_articles(self):
        """显示当天文章"""
        try:
            # 从数据库获取当天文章
            today_articles = self.db_manager.get_today_articles()
            # 更新文章列表
            self.articles = today_articles
            self.load_article_list()
            self.update_stats()
            self.status_var.set(f"已显示当天文章，共 {len(today_articles)} 篇")
            # 更新按钮文本
            self.show_all_btn.config(text="📄 显示当天")
        except Exception as e:
            print(f"加载当天文章失败: {e}")
            messagebox.showerror("加载失败", f"加载当天文章失败: {str(e)}")
    
    def show_important_articles(self):
        """显示重要文章"""
        try:
            # 从数据库获取重要文章
            important_articles = self.db_manager.get_important_articles()
            # 更新文章列表
            self.articles = important_articles
            self.load_article_list()
            self.update_stats()
            self.status_var.set(f"已显示重要文章，共 {len(important_articles)} 篇")
            # 更新按钮文本
            self.show_all_btn.config(text="📄 显示重要")
        except Exception as e:
            print(f"加载重要文章失败: {e}")
            messagebox.showerror("加载失败", f"加载重要文章失败: {str(e)}")
    
    def prev_day(self):
        """向前翻一天（后一天）"""
        try:
            current_date = datetime.strptime(self.date_var.get(), '%Y-%m-%d')
            prev_date = current_date + timedelta(days=1)
            self.date_var.set(prev_date.strftime('%Y-%m-%d'))
            self.query_by_date()
        except Exception as e:
            print(f"日期转换失败: {e}")
    
    def next_day(self):
        """向后翻一天（前一天）"""
        try:
            current_date = datetime.strptime(self.date_var.get(), '%Y-%m-%d')
            next_date = current_date - timedelta(days=1)
            self.date_var.set(next_date.strftime('%Y-%m-%d'))
            self.query_by_date()
        except Exception as e:
            print(f"日期转换失败: {e}")
    

    
    def auto_cleanup_on_start(self):
        """启动时自动执行清理"""
        try:
            # 检查是否存在整理配置文件
            if os.path.exists('config/organize_config.json'):
                with open('config/organize_config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                    # 获取配置
                    cleanup_days = config.get('cleanup_days', 7)
                    keep_importance = config.get('keep_importance', True)
                    author_blacklist = config.get('author_blacklist', [])
                    
                    # 计算过期时间
                    cutoff_date = datetime.now() - timedelta(days=cleanup_days)
                    
                    # 过滤文章
                    filtered_articles = []
                    removed_count = 0
                    
                    for article in self.articles:
                        # 检查是否在黑名单中
                        author = article.get('author', '')
                        if author in author_blacklist:
                            removed_count += 1
                            continue
                        
                        # 检查是否过期
                        pub_time_str = article.get('publish_time', '')
                        if pub_time_str:
                            try:
                                pub_time = datetime.strptime(pub_time_str, '%Y-%m-%d %H:%M:%S')
                                if pub_time < cutoff_date:
                                    # 检查是否标记为重要
                                    if keep_importance and article.get('importance', False):
                                        filtered_articles.append(article)
                                    else:
                                        removed_count += 1
                                        continue
                            except:
                                pass
                        
                        filtered_articles.append(article)
                    
                    # 如果有清理的文章，更新列表
                    if removed_count > 0:
                        self.articles = filtered_articles
                        self.save_articles()
                        self.load_article_list()
                        self.update_stats()
                        # 显示清理结果
                        self.status_var.set(f"启动时自动清理：已清理 {removed_count} 篇文章")
                        print(f"启动时自动清理：已清理 {removed_count} 篇文章")
        except Exception as e:
            print(f"自动清理失败: {e}")
    
    def clear_articles(self):
        """清空文章"""
        if messagebox.askyesno("确认", "确定要清空所有文章吗？"):
            self.articles = []
            self.save_articles()
            self.load_article_list()
            self.update_stats()
            self.status_var.set("已清空")
    
    def update_stats(self):
        """更新统计"""
        total = len(self.articles)
        today = sum(1 for a in self.articles if datetime.now().strftime('%Y-%m-%d') in a.get('publish_time', ''))
        self.status_var.set(f"共 {total} 篇文章 | 今日 {today} 篇")
    

    
    def open_scheduler(self):
        """打开定时任务设置"""
        scheduler_win = tk.Toplevel(self.root)
        scheduler_win.title("⏰ 定时任务设置")
        scheduler_win.geometry("450x350")
        scheduler_win.resizable(False, False)
        
        # 窗口背景
        scheduler_win.configure(bg='#ffffff')
        
        # 标题栏
        title_frame = tk.Frame(scheduler_win, bg='#e3f2fd', bd=1, relief=tk.RAISED)
        title_frame.pack(fill=tk.X, pady=5)
        tk.Label(title_frame, text="⏰ 定时任务设置", font=('微软雅黑', 14, 'bold'), bg='#e3f2fd').pack(side=tk.LEFT, padx=15, pady=10)
        
        # 内容区域
        content_frame = tk.Frame(scheduler_win, bg='#ffffff')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        # 启用/禁用
        auto_var = tk.BooleanVar(value=self.config.get('auto_collect', False))
        check_frame = tk.Frame(content_frame, bg='#ffffff')
        check_frame.pack(pady=20)
        
        checkbutton = tk.Checkbutton(check_frame, text="启用定时采集", variable=auto_var, 
                                   font=('微软雅黑', 12, 'bold'), bg='#ffffff', fg='#333333')
        checkbutton.pack(anchor='w')
        
        # 采集时间
        time_frame = tk.Frame(content_frame, bg='#ffffff')
        time_frame.pack(pady=20)
        
        tk.Label(time_frame, text="采集时间:", font=('微软雅黑', 11, 'bold'), bg='#ffffff').pack(anchor='w', pady=5)
        time_entry = tk.Entry(time_frame, font=('微软雅黑', 11), width=20, bd=2, relief=tk.GROOVE)
        time_entry.insert(0, self.config.get('collect_time', '09:00'))
        time_entry.pack(anchor='w', pady=5)
        
        tk.Label(time_frame, text="格式：HH:MM (如 09:00)", font=('微软雅黑', 9), fg='#666', bg='#ffffff').pack(anchor='w', pady=5)
        
        # 保存按钮
        def save_config():
            self.config['auto_collect'] = auto_var.get()
            self.config['collect_time'] = time_entry.get()
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("保存成功", "设置已保存")
            scheduler_win.destroy()
        
        btn_frame = tk.Frame(content_frame, bg='#ffffff')
        btn_frame.pack(pady=30)
        
        save_btn = tk.Button(btn_frame, text="保存设置", command=save_config, 
                           bg='#4CAF50', fg='white', font=('微软雅黑', 11, 'bold'), 
                           padx=20, pady=8, activebackground='#45a049')
        save_btn.pack()
        
        # 提示信息
        hint_frame = tk.Frame(scheduler_win, bg='#fff3e0', bd=1, relief=tk.RAISED)
        hint_frame.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(hint_frame, text="💡 提示：定时任务将每30分钟自动执行一次", 
                font=('微软雅黑', 9), fg='#e65100', bg='#fff3e0').pack(padx=15, pady=8)
    
    def show_help(self):
        """显示帮助"""
        help_text = """
📖 使用说明

1. 采集文章
   - 点击"🔄 采集最新 10 篇"按钮
   - 系统会自动采集最新的 10 篇文章

2. 搜索筛选
   - 在搜索框输入关键词
   - 选择时间范围（今日/本周/本月）

3. 查看文章
   - 点击列表中的文章查看详情
   - 双击文章在浏览器打开原文

4. 导出分享
   - 点击"📤 导出"按钮导出所有文章
   - 选择单篇文章点击"📝 导出为 Markdown"
   - 点击"📋 复制全文"复制内容

5. 定时任务
   - 工具 → ⏰ 定时任务设置
   - 设置每天自动采集时间

6. 数据统计
   - 点击"📊 数据统计"查看分析
   - 包括作者统计、日期统计等

7. 快捷键
   - 双击文章：在浏览器打开
   - 搜索框：实时筛选
        """
        
        help_win = tk.Toplevel(self.root)
        help_win.title("📖 使用说明")
        help_win.geometry("550x450")
        help_win.resizable(True, True)
        
        # 窗口背景
        help_win.configure(bg='#ffffff')
        
        # 标题栏
        title_frame = tk.Frame(help_win, bg='#e3f2fd', bd=1, relief=tk.RAISED)
        title_frame.pack(fill=tk.X, pady=5)
        tk.Label(title_frame, text="📖 使用说明", font=('微软雅黑', 14, 'bold'), bg='#e3f2fd').pack(side=tk.LEFT, padx=15, pady=10)
        
        # 内容区域
        content_frame = tk.Frame(help_win, bg='#ffffff')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        text = scrolledtext.ScrolledText(content_frame, font=('微软雅黑', 11), bg='#f9f9f9', bd=1, relief=tk.GROOVE)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text.insert(tk.END, help_text)
        text.config(state=tk.DISABLED)
    
    def embed_deepseek_browser(self):
        """嵌入DeepSeek对话窗口"""
        try:
            # 启动Edge浏览器
            edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
            if not os.path.exists(edge_path):
                # 尝试其他可能的路径
                edge_path = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
                if not os.path.exists(edge_path):
                    messagebox.showinfo("提示", "未找到Edge浏览器，请确保已安装Edge浏览器")
                    return
            
            # 启动浏览器并打开DeepSeek对话
            subprocess.Popen([edge_path, "--app=https://chat.deepseek.com"])
            
            # 等待浏览器启动
            time.sleep(3)
            
            # 查找DeepSeek浏览器窗口
            def find_deepseek_window(hwnd, ctx):
                title = win32gui.GetWindowText(hwnd)
                if "DeepSeek" in title and win32gui.IsWindowVisible(hwnd):
                    ctx.append(hwnd)
            
            deepseek_windows = []
            win32gui.EnumWindows(find_deepseek_window, deepseek_windows)
            
            if deepseek_windows:
                self.deepseek_hwnd = deepseek_windows[0]
                
                # 获取浏览器框架的位置和大小
                browser_x = self.browser_frame.winfo_x()
                browser_y = self.browser_frame.winfo_y()
                browser_width = self.browser_frame.winfo_width()
                browser_height = self.browser_frame.winfo_height()
                
                # 获取主窗口的位置
                root_x = self.root.winfo_x()
                root_y = self.root.winfo_y()
                
                # 计算浏览器窗口的绝对位置
                absolute_x = root_x + browser_x + 20  # 20是边框和填充的估计值
                absolute_y = root_y + browser_y + 100  # 100是标题栏和工具栏的估计值
                
                # 设置浏览器窗口为子窗口
                win32gui.SetParent(self.deepseek_hwnd, self.browser_frame.winfo_id())
                
                # 调整浏览器窗口大小和位置
                win32gui.MoveWindow(self.deepseek_hwnd, 0, 0, browser_width, browser_height, True)
                
                # 显示浏览器窗口
                win32gui.ShowWindow(self.deepseek_hwnd, win32con.SW_SHOW)
            else:
                messagebox.showinfo("提示", "未找到DeepSeek浏览器窗口")
        except Exception as e:
            messagebox.showinfo("错误", f"嵌入DeepSeek窗口失败：{str(e)}")
    
    def on_window_resize(self, event):
        """窗口大小变化时调整DeepSeek窗口大小"""
        if hasattr(self, 'deepseek_hwnd') and self.deepseek_hwnd:
            try:
                # 获取浏览器框架的大小
                browser_width = self.browser_frame.winfo_width()
                browser_height = self.browser_frame.winfo_height()
                
                # 调整浏览器窗口大小
                win32gui.MoveWindow(self.deepseek_hwnd, 0, 0, browser_width, browser_height, True)
            except Exception:
                pass
    
    def open_api_config(self):
        """打开完整的配置管理界面"""
        from .config_gui import ConfigGUI
        config_gui = ConfigGUI(self.root)
        config_gui.open_config_window()
    
    def open_organize_window(self):
        """打开整理窗口"""
        # 创建整理窗口
        organize_win = tk.Toplevel(self.root)
        organize_win.title("📋 信息整理")
        organize_win.geometry("650x550")
        organize_win.resizable(False, False)
        
        # 窗口背景
        organize_win.configure(bg='#ffffff')
        
        # 顶部按钮栏
        top_btn_frame = tk.Frame(organize_win, bg='#ffffff', bd=1, relief=tk.RAISED)
        top_btn_frame.pack(fill=tk.X, padx=15, pady=8)
        
        def save_config():
            # 保存作者黑名单
            blacklist = [blacklist_listbox.get(i) for i in range(blacklist_listbox.size())]
            
            # 保存配置到文件
            organize_config = {
                'author_blacklist': blacklist,
                'cleanup_days': int(time_var.get()),
                'keep_importance': keep_importance_var.get()
            }
            
            with open('config/organize_config.json', 'w', encoding='utf-8') as f:
                json.dump(organize_config, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("保存成功", "配置已保存", parent=organize_win)
        
        def apply_cleanup():
            # 应用清理
            try:
                days = int(time_var.get())
                keep_importance = keep_importance_var.get()
                
                # 计算过期时间
                cutoff_date = datetime.now() - timedelta(days=days)
                cutoff_date_str = cutoff_date.strftime('%Y-%m-%d %H:%M:%S')
                
                # 获取作者黑名单
                blacklist = [blacklist_listbox.get(i) for i in range(blacklist_listbox.size())]
                
                # 从数据库中直接删除过期文章
                conn = self.db_manager._get_connection()
                cursor = conn.cursor()
                
                # 构建删除条件
                if keep_importance:
                    # 保留重要文章
                    if blacklist:
                        # 删除黑名单作者的文章和过期且非重要的文章
                        placeholders = ','.join('?' for _ in blacklist)
                        cursor.execute(f'''
                        DELETE FROM articles 
                        WHERE (author IN ({placeholders}) OR publish_time < ? AND importance = 0)
                        ''', (*blacklist, cutoff_date_str))
                    else:
                        # 只删除过期且非重要的文章
                        cursor.execute('''
                        DELETE FROM articles 
                        WHERE publish_time < ? AND importance = 0
                        ''', (cutoff_date_str,))
                else:
                    # 不保留重要文章
                    if blacklist:
                        # 删除黑名单作者的文章和过期文章
                        placeholders = ','.join('?' for _ in blacklist)
                        cursor.execute(f'''
                        DELETE FROM articles 
                        WHERE author IN ({placeholders}) OR publish_time < ?
                        ''', (*blacklist, cutoff_date_str))
                    else:
                        # 只删除过期文章
                        cursor.execute('''
                        DELETE FROM articles 
                        WHERE publish_time < ?
                        ''', (cutoff_date_str,))
                
                removed_count = cursor.rowcount
                conn.commit()
                conn.close()
                
                # 重新从数据库加载文章，确保数据一致性
                self.articles = self.load_articles()
                # 根据当前显示模式重新筛选文章
                if self.display_mode == 0:
                    # 显示当天
                    self.articles = self.db_manager.get_today_articles()
                elif self.display_mode == 1:
                    # 显示全部
                    pass  # 已经是全部文章
                elif self.display_mode == 2:
                    # 显示重要
                    self.articles = self.db_manager.get_important_articles()
                self.load_article_list()
                self.update_stats()
                
                messagebox.showinfo("清理完成", f"已清理 {removed_count} 篇文章", parent=organize_win)
            except Exception as e:
                messagebox.showerror("清理失败", str(e), parent=organize_win)
        
        # 保存配置按钮
        save_btn = tk.Button(top_btn_frame, text="保存配置", command=save_config, 
                           bg='#4CAF50', fg='white', font=('微软雅黑', 10, 'bold'), 
                           width=10, padx=10, pady=6, activebackground='#45a049', 
                           relief=tk.GROOVE, bd=2)
        save_btn.pack(side=tk.LEFT, padx=8)
        
        # 应用清理按钮
        apply_btn = tk.Button(top_btn_frame, text="应用清理", command=apply_cleanup, 
                            bg='#f44336', fg='white', font=('微软雅黑', 10, 'bold'), 
                            width=10, padx=10, pady=6, activebackground='#d32f2f', 
                            relief=tk.GROOVE, bd=2)
        apply_btn.pack(side=tk.LEFT, padx=8)
        
        # 清空按钮（危险操作，放在右侧）
        clear_btn = tk.Button(top_btn_frame, text="清空所有", command=self.clear_articles, 
                             bg='#f44336', fg='white', font=('微软雅黑', 10, 'bold'), 
                             width=10, padx=10, pady=6, activebackground='#d32f2f', 
                             relief=tk.GROOVE, bd=2)
        clear_btn.pack(side=tk.RIGHT, padx=8)
        
        # 导出按钮
        export_btn = tk.Button(top_btn_frame, text="导出", command=self.export_data, 
                             bg='#FF9800', fg='white', font=('微软雅黑', 10, 'bold'), 
                             width=10, padx=10, pady=6, activebackground='#F57C00', 
                             relief=tk.GROOVE, bd=2)
        export_btn.pack(side=tk.RIGHT, padx=8)
        
        # 导入按钮
        import_btn = tk.Button(top_btn_frame, text="导入", command=self.import_data, 
                             bg='#2196F3', fg='white', font=('微软雅黑', 10, 'bold'), 
                             width=10, padx=10, pady=6, activebackground='#1976D2', 
                             relief=tk.GROOVE, bd=2)
        import_btn.pack(side=tk.RIGHT, padx=8)
        

        
        # 主内容区域
        content_frame = tk.Frame(organize_win, bg='#ffffff')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=8)
        
        # 过期信息清理部分（上）
        cleanup_frame = tk.LabelFrame(content_frame, text="过期信息清理", font=('微软雅黑', 10, 'bold'), bg='#ffffff', bd=2, relief=tk.GROOVE)
        cleanup_frame.pack(fill=tk.X, pady=8, padx=5)
        
        # 时间选择
        time_frame = tk.Frame(cleanup_frame, bg='#ffffff')
        time_frame.pack(fill=tk.X, padx=12, pady=8)
        
        tk.Label(time_frame, text="清理时间：", font=('微软雅黑', 9), bg='#ffffff').pack(side=tk.LEFT, padx=5)
        time_var = tk.StringVar(value="365")
        
        # 时间输入框
        time_entry = tk.Entry(time_frame, textvariable=time_var, font=('微软雅黑', 9), width=8, bd=2, relief=tk.GROOVE)
        time_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Label(time_frame, text="天前", font=('微软雅黑', 9), bg='#ffffff').pack(side=tk.LEFT, padx=5)
        
        # 保留重要信息选项
        keep_importance_var = tk.BooleanVar(value=True)
        keep_importance_check = tk.Checkbutton(cleanup_frame, text="保留手动标记为重要的信息", variable=keep_importance_var, 
                                            font=('微软雅黑', 9), bg='#ffffff', 
                                            activebackground='#e3f2fd', selectcolor='#e3f2fd')
        keep_importance_check.pack(anchor='w', padx=12, pady=5)
        
        # 作者黑名单部分（下）
        blacklist_frame = tk.LabelFrame(content_frame, text="作者黑名单", font=('微软雅黑', 10, 'bold'), bg='#ffffff', bd=2, relief=tk.GROOVE)
        blacklist_frame.pack(fill=tk.BOTH, expand=True, pady=8, padx=5)
        
        # 黑名单输入框
        input_frame = tk.Frame(blacklist_frame, bg='#ffffff')
        input_frame.pack(fill=tk.X, padx=12, pady=8)
        
        tk.Label(input_frame, text="作者名称：", font=('微软雅黑', 9), bg='#ffffff').pack(side=tk.LEFT, padx=5)
        blacklist_entry = tk.Entry(input_frame, font=('微软雅黑', 9), width=35, bd=2, relief=tk.GROOVE)
        blacklist_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 黑名单列表
        list_frame = tk.Frame(blacklist_frame, bg='#ffffff')
        list_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=5)
        
        blacklist_listbox = tk.Listbox(list_frame, font=('微软雅黑', 9), bg='#f9f9f9', bd=2, relief=tk.GROOVE, height=8)
        blacklist_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=blacklist_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        blacklist_listbox.configure(yscrollcommand=scrollbar.set)
        
        # 黑名单按钮
        btn_frame = tk.Frame(blacklist_frame, bg='#ffffff')
        btn_frame.pack(fill=tk.X, padx=12, pady=8)
        
        def add_to_blacklist():
            author = blacklist_entry.get().strip()
            if author:
                blacklist_listbox.insert(tk.END, author)
                blacklist_entry.delete(0, tk.END)
        
        def remove_from_blacklist():
            selected = blacklist_listbox.curselection()
            if selected:
                blacklist_listbox.delete(selected[0])
        
        add_btn = tk.Button(btn_frame, text="添加", command=add_to_blacklist, 
                          bg='#4CAF50', fg='white', font=('微软雅黑', 8), padx=8, pady=3, 
                          activebackground='#45a049', relief=tk.GROOVE, bd=2)
        add_btn.pack(side=tk.LEFT, padx=5)
        
        remove_btn = tk.Button(btn_frame, text="移除", command=remove_from_blacklist, 
                             bg='#f44336', fg='white', font=('微软雅黑', 8), padx=8, pady=3, 
                             activebackground='#d32f2f', relief=tk.GROOVE, bd=2)
        remove_btn.pack(side=tk.LEFT, padx=5)
        

        
        # 加载现有配置
        try:
            if os.path.exists('config/organize_config.json'):
                with open('config/organize_config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 加载黑名单
                    for author in config.get('author_blacklist', []):
                        blacklist_listbox.insert(tk.END, author)
                    # 加载清理时间
                    time_var.set(str(config.get('cleanup_days', 7)))
                    # 加载保留重要信息选项
                    keep_importance_var.set(config.get('keep_importance', True))
        except Exception as e:
            print(f"加载配置失败: {e}")
        
    
    def open_deepseek_main(self):
        """打开DeepSeek主界面"""
        # DeepSeek主界面URL
        deepseek_url = "https://chat.deepseek.com"
        
        # 打开浏览器
        import webbrowser
        webbrowser.open(deepseek_url)
        
        messagebox.showinfo("DeepSeek", "已打开DeepSeek主界面")
    
    def update_stock_list(self, article):
        """更新股票池列表（每行显示6组股票）"""
        # 清空列表
        for item in self.stock_tree.get_children():
            self.stock_tree.delete(item)
        
        # 添加股票（每6个一组）
        stocks = article.get('stocks', [])
        
        # 将股票分组，每组6个
        stock_groups = []
        current_group = []
        
        for stock in stocks:
            current_group.append(stock)
            if len(current_group) == 6:
                stock_groups.append(current_group)
                current_group = []
        
        # 处理剩余的股票
        if current_group:
            # 不足6个的组，用空值填充
            while len(current_group) < 6:
                current_group.append({'name': ''})
            stock_groups.append(current_group)
        
        # 插入分组后的股票
        for group in stock_groups:
            # 准备一行的数据
            row_data = []
            
            for stock in group:
                if isinstance(stock, dict) and 'name' in stock:
                    row_data.append(stock['name'])
                else:
                    row_data.append(stock if stock else "")
            
            self.stock_tree.insert('', tk.END, values=tuple(row_data))
    
    def analyze_stocks(self):
        """分析DeepSeek页面表格并提取股票"""
        # 获取当前选中的文章
        selection = self.article_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择一篇文章")
            return
        
        index = self.article_tree.index(selection[0])
        if index < len(self.articles):
            article = self.articles[index]
            article_id = article.get('id')
            
            try:
                # 尝试从DeepSeek窗口获取内容
                stocks = self._extract_stocks_from_deepseek()
                
                if not stocks:
                    messagebox.showinfo("提示", "未从DeepSeek页面中识别到股票表格")
                    return
                
                # 导入股票池管理器
                from utils.stock_pool import stock_pool_manager
                
                # 添加股票到股票池
                new_stocks_added = 0
                for stock in stocks:
                    stock_name = stock.get('name', '')
                    if stock_name:
                        success = stock_pool_manager.add_stock_to_pool(article_id, {'name': stock_name})
                        if success:
                            new_stocks_added += 1
                
                if new_stocks_added > 0:
                    # 重新加载文章数据
                    self.articles = self.load_articles()
                    # 找到重新加载后的对应文章对象
                    updated_article = None
                    for art in self.articles:
                        if art.get('id') == article_id:
                            updated_article = art
                            break
                    # 更新股票池显示
                    if updated_article:
                        self.update_stock_list(updated_article)
                    else:
                        self.update_stock_list(article)
                    
                    # 更新状态栏
                    self.status_var.set(f"从DeepSeek页面提取了 {new_stocks_added} 只股票")
                    messagebox.showinfo("成功", f"从DeepSeek页面提取了 {new_stocks_added} 只股票到股票池")
                else:
                    messagebox.showinfo("提示", "没有新股票添加到股票池")
            except Exception as e:
                print(f"分析DeepSeek页面失败: {e}")
                messagebox.showerror("错误", f"分析DeepSeek页面失败: {str(e)}")
    
    def show_stock_context_menu(self, event):
        """显示股票池右键菜单"""
        item = self.stock_tree.identify_row(event.y)
        column = self.stock_tree.identify_column(event.x)
        if item:
            self.stock_tree.selection_set(item)
            # 记录点击的单元格信息
            self.last_clicked_cell = (item, column)
            self.stock_context_menu.post(event.x_root, event.y_root)
    
    def delete_selected_stock(self):
        """删除选中的股票"""
        # 检查是否有点击的单元格信息
        if not hasattr(self, 'last_clicked_cell') or not self.last_clicked_cell:
            return
        
        item, column = self.last_clicked_cell
        values = self.stock_tree.item(item, 'values')
        
        # 将列索引转换为整数（例如 '#1' → 0）
        try:
            col_index = int(column[1:]) - 1
            if 0 <= col_index < len(values):
                stock_name = values[col_index]
                if stock_name:
                    self.delete_stock(stock_name)
        except (ValueError, IndexError):
            pass
    
    def delete_stock(self, stock_name):
        """删除股票池中的股票"""
        # 获取当前选中的文章
        selection = self.article_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择一篇文章")
            return
        
        index = self.article_tree.index(selection[0])
        if index < len(self.articles):
            article = self.articles[index]
            article_id = article.get('id')
            
            # 导入股票池管理器
            from utils.stock_pool import stock_pool_manager
            
            # 删除股票
            success = stock_pool_manager.remove_stock_from_pool(article_id, stock_name)
            
            if success:
                # 保存当前显示模式
                current_mode = self.display_mode
                # 重新加载文章数据
                self.articles = self.load_articles()
                # 根据当前显示模式重新筛选文章
                if current_mode == 0:
                    # 显示当天
                    self.articles = self.db_manager.get_today_articles()
                elif current_mode == 1:
                    # 显示全部
                    pass  # 已经是全部文章
                elif current_mode == 2:
                    # 显示重要
                    self.articles = self.db_manager.get_important_articles()
                # 重新加载文章列表
                self.load_article_list()
                # 找到重新加载后的对应文章对象
                updated_article = None
                for art in self.articles:
                    if art.get('id') == article_id:
                        updated_article = art
                        break
                # 更新股票池显示
                if updated_article:
                    self.update_stock_list(updated_article)
                else:
                    self.update_stock_list(article)
                messagebox.showinfo("成功", f"成功删除股票：{stock_name}")
            else:
                messagebox.showinfo("提示", "删除股票失败")
    
    def clear_stocks(self):
        """清空股票池"""
        # 获取当前选中的文章
        selection = self.article_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择一篇文章")
            return
        
        index = self.article_tree.index(selection[0])
        if index < len(self.articles):
            article = self.articles[index]
            article_id = article.get('id')
            
            # 导入股票池管理器
            from utils.stock_pool import stock_pool_manager
            
            # 清空股票池
            success = stock_pool_manager.delete_stock_pool(article_id)
            
            if success:
                # 保存当前显示模式
                current_mode = self.display_mode
                # 重新加载文章数据
                self.articles = self.load_articles()
                # 根据当前显示模式重新筛选文章
                if current_mode == 0:
                    # 显示当天
                    self.articles = self.db_manager.get_today_articles()
                elif current_mode == 1:
                    # 显示全部
                    pass  # 已经是全部文章
                elif current_mode == 2:
                    # 显示重要
                    self.articles = self.db_manager.get_important_articles()
                # 重新加载文章列表
                self.load_article_list()
                # 找到重新加载后的对应文章对象
                updated_article = None
                for art in self.articles:
                    if art.get('id') == article_id:
                        updated_article = art
                        break
                # 更新股票池显示
                if updated_article:
                    self.update_stock_list(updated_article)
                else:
                    self.update_stock_list(article)
                
                # 更新状态栏
                self.status_var.set("股票池已清空")
                messagebox.showinfo("成功", "股票池已清空")
            else:
                messagebox.showinfo("错误", "清空股票池失败")
    
    def manual_add_stock(self):
        """手动添加股票"""
        # 获取当前选中的文章
        selection = self.article_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择一篇文章")
            return
        
        index = self.article_tree.index(selection[0])
        if index < len(self.articles):
            article = self.articles[index]
            article_id = article.get('id')
            
            # 创建手动添加股票的对话框
            import tkinter.simpledialog
            
            # 输入股票名称，支持批量输入
            stock_input = tkinter.simpledialog.askstring("手动添加股票", "请输入股票名称（支持批量输入，使用逗号、顿号、分号等分隔）：")
            if not stock_input:
                return
            
            # 解析输入的股票名称，支持多种分隔符
            stocks = []
            # 按行分割
            lines = stock_input.strip().split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 尝试不同的分隔符
                if '\t' in line:
                    parts = line.split('\t')
                elif ',' in line:
                    parts = line.split(',')
                elif ';' in line:
                    parts = line.split(';')
                elif ':' in line:
                    parts = line.split(':')
                elif '|' in line:
                    parts = line.split('|')
                elif '、' in line:
                    parts = line.split('、')
                else:
                    parts = line.split()
                
                # 清理空白
                parts = [part.strip() for part in parts if part.strip()]
                for part in parts:
                    stocks.append(part)
            
            if not stocks:
                messagebox.showinfo("提示", "未识别到股票名称")
                return
            
            # 导入股票池管理器
            from utils.stock_pool import stock_pool_manager
            
            # 批量添加股票
            new_stocks_added = 0
            for stock_name in stocks:
                success = stock_pool_manager.manual_add_stock(article_id, stock_name)
                if success:
                    new_stocks_added += 1
            
            if new_stocks_added > 0:
                # 保存当前显示模式
                current_mode = self.display_mode
                # 重新加载文章数据
                self.articles = self.load_articles()
                # 根据当前显示模式重新筛选文章
                if current_mode == 0:
                    # 显示当天
                    self.articles = self.db_manager.get_today_articles()
                elif current_mode == 1:
                    # 显示全部
                    pass  # 已经是全部文章
                elif current_mode == 2:
                    # 显示重要
                    self.articles = self.db_manager.get_important_articles()
                # 重新加载文章列表
                self.load_article_list()
                # 找到重新加载后的对应文章对象
                updated_article = None
                for art in self.articles:
                    if art.get('id') == article_id:
                        updated_article = art
                        break
                # 更新股票池显示
                if updated_article:
                    self.update_stock_list(updated_article)
                else:
                    self.update_stock_list(article)
                messagebox.showinfo("添加成功", f"成功添加 {new_stocks_added} 只股票")
            else:
                messagebox.showinfo("提示", "添加股票失败")
    

    
    def open_deepseek_analysis(self):
        """使用已打开的DeepSeek对话窗口进行分析"""
        # 获取当前选中的文章
        selection = self.article_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择一篇文章")
            return
        
        index = self.article_tree.index(selection[0])
        if index < len(self.articles):
            article = self.articles[index]
            article_url = article.get('url', '')
            
            if not article_url:
                messagebox.showinfo("提示", "当前文章没有URL信息")
                return
            
            # 构建DeepSeek分析请求
            prompt = f"帮我分析总结\"{article_url}\"的内容，并提取文章中提到的相关的股票名称信息，输出成表格格式，表格只包含股票名称一列"
            
            # 尝试使用已打开的DeepSeek窗口
            if hasattr(self, 'deepseek_hwnd') and self.deepseek_hwnd:
                try:
                    import pyperclip
                    import win32api
                    import win32con
                    import win32gui
                    
                    # 激活DeepSeek窗口
                    win32gui.SetForegroundWindow(self.deepseek_hwnd)
                    time.sleep(0.5)
                    
                    # 重置DeepSeek对话窗口（模拟Ctrl+K）
                    win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
                    win32api.keybd_event(ord('K'), 0, 0, 0)
                    win32api.keybd_event(ord('K'), 0, win32con.KEYEVENTF_KEYUP, 0)
                    win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
                    time.sleep(0.5)
                    
                    # 将提示词复制到剪贴板
                    pyperclip.copy(prompt)
                    
                    # 模拟Ctrl+V粘贴
                    win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
                    win32api.keybd_event(ord('V'), 0, 0, 0)
                    win32api.keybd_event(ord('V'), 0, win32con.KEYEVENTF_KEYUP, 0)
                    win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
                    time.sleep(0.3)
                    
                    # 模拟Enter发送
                    win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
                    win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
                except Exception as e:
                    import urllib.parse
                    encoded_prompt = urllib.parse.quote(prompt)
                    deepseek_url = f"https://chat.deepseek.com/?q={encoded_prompt}"
                    import webbrowser
                    webbrowser.open(deepseek_url)
                    messagebox.showinfo("DeepSeek分析", f"已打开DeepSeek网页并填充分析请求")
            else:
                import urllib.parse
                encoded_prompt = urllib.parse.quote(prompt)
                deepseek_url = f"https://chat.deepseek.com/?q={encoded_prompt}"
                import webbrowser
                webbrowser.open(deepseek_url)
                messagebox.showinfo("DeepSeek分析", "已打开DeepSeek网页并填充分析请求")
    
    def add_stocks_from_clipboard(self):
        """从剪贴板添加股票"""
        try:
            # 获取当前选中的文章
            selection = self.article_tree.selection()
            if not selection:
                messagebox.showinfo("提示", "请先选择一篇文章")
                return
            
            index = self.article_tree.index(selection[0])
            if index < len(self.articles):
                article = self.articles[index]
                article_id = article.get('id')
                
                # 从剪贴板获取内容
                import pyperclip
                clipboard_content = pyperclip.paste()
                
                if not clipboard_content:
                    messagebox.showinfo("提示", "剪贴板为空，请先复制股票表格")
                    return
                
                # 解析剪贴板内容
                stocks = self._parse_stocks_from_clipboard(clipboard_content)
                
                if not stocks:
                    messagebox.showinfo("提示", "未从剪贴板中识别到股票信息")
                    return
                
                # 导入股票池管理器
                from utils.stock_pool import stock_pool_manager
                
                # 添加股票到股票池
                new_stocks_added = 0
                for stock in stocks:
                    stock_name = stock.get('name', '')
                    if stock_name:
                        success = stock_pool_manager.add_stock_to_pool(article_id, {'name': stock_name})
                        if success:
                            new_stocks_added += 1
                
                if new_stocks_added > 0:
                    # 保存当前显示模式
                    current_mode = self.display_mode
                    # 重新加载文章数据
                    self.articles = self.load_articles()
                    # 根据当前显示模式重新筛选文章
                    if current_mode == 0:
                        # 显示当天
                        self.articles = self.db_manager.get_today_articles()
                    elif current_mode == 1:
                        # 显示全部
                        pass  # 已经是全部文章
                    elif current_mode == 2:
                        # 显示重要
                        self.articles = self.db_manager.get_important_articles()
                    # 重新加载文章列表
                    self.load_article_list()
                    # 找到重新加载后的对应文章对象
                    updated_article = None
                    for art in self.articles:
                        if art.get('id') == article_id:
                            updated_article = art
                            break
                    # 更新股票池显示
                    if updated_article:
                        self.update_stock_list(updated_article)
                    else:
                        self.update_stock_list(article)
                    
                    # 更新状态栏
                    self.status_var.set(f"从剪贴板添加了 {new_stocks_added} 只股票")
                    messagebox.showinfo("成功", f"从剪贴板添加了 {new_stocks_added} 只股票到股票池")
                else:
                    messagebox.showinfo("提示", "没有新股票添加到股票池")
        except Exception as e:
            print(f"从剪贴板添加股票失败: {e}")
            messagebox.showerror("错误", f"从剪贴板添加股票失败: {str(e)}")
    
    def _parse_stocks_from_clipboard(self, content):
        """从剪贴板内容中解析股票信息"""
        stocks = []
        
        # 打印剪贴板内容，用于调试
        print(f"剪贴板内容: {repr(content)}")
        
        # 按行分割内容
        lines = content.strip().split('\n')
        print(f"分割后的行: {lines}")
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 尝试不同的分隔符
            if '\t' in line:
                # 制表符分隔
                parts = line.split('\t')
            elif ',' in line:
                # 逗号分隔
                parts = line.split(',')
            elif ';' in line:
                # 分号分隔
                parts = line.split(';')
            elif ':' in line:
                # 冒号分隔
                parts = line.split(':')
            elif '|' in line:
                # 竖线分隔
                parts = line.split('|')
            elif '、' in line:
                # 顿号分隔
                parts = line.split('、')
            else:
                # 空格分隔
                parts = line.split()
            
            # 清理空白
            parts = [part.strip() for part in parts if part.strip()]
            print(f"处理行 '{line}' 得到 parts: {parts}")
            
            if len(parts) >= 1:
                # 只取第一列作为股票名称
                stock_name = parts[0]
                stocks.append({'name': stock_name})
                print(f"添加股票: {stock_name}")
        
        print(f"解析完成，共识别 {len(stocks)} 只股票")
        return stocks
    
    def _extract_stocks_from_deepseek(self):
        """从DeepSeek页面提取股票表格"""
        try:
            # 检查Windows API是否可用
            if not has_win32:
                raise Exception("Windows API模块不可用，无法监控DeepSeek窗口")
            
            # 检查DeepSeek窗口是否存在
            if not hasattr(self, 'deepseek_hwnd') or not self.deepseek_hwnd:
                # 尝试查找DeepSeek窗口
                def find_deepseek_window(hwnd, ctx):
                    title = win32gui.GetWindowText(hwnd)
                    if "DeepSeek" in title and win32gui.IsWindowVisible(hwnd):
                        ctx.append(hwnd)
                
                deepseek_windows = []
                win32gui.EnumWindows(find_deepseek_window, deepseek_windows)
                
                if not deepseek_windows:
                    raise Exception("未找到DeepSeek窗口")
                
                self.deepseek_hwnd = deepseek_windows[0]
            
            # 激活DeepSeek窗口
            win32gui.SetForegroundWindow(self.deepseek_hwnd)
            time.sleep(1)  # 等待窗口激活
            
            # 模拟Ctrl+A全选
            win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
            win32api.keybd_event(ord('A'), 0, 0, 0)
            win32api.keybd_event(ord('A'), 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(0.5)
            
            # 模拟Ctrl+C复制
            win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
            win32api.keybd_event(ord('C'), 0, 0, 0)
            win32api.keybd_event(ord('C'), 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(0.5)
            
            # 从剪贴板获取内容
            import pyperclip
            clipboard_content = pyperclip.paste()
            
            if not clipboard_content:
                raise Exception("剪贴板为空")
            
            # 解析内容中的股票表格
            return self._parse_stocks_from_clipboard(clipboard_content)
        except Exception as e:
            print(f"从DeepSeek提取股票失败: {e}")
            raise
    
    def ocr_recognition(self):
        """OCR识别图片中的股票信息"""
        # 打开文件选择对话框
        filetypes = [
            ('图片文件', '*.jpg *.jpeg *.png *.bmp'),
            ('所有文件', '*.*')
        ]
        
        filename = filedialog.askopenfilename(
            title='选择图片文件',
            filetypes=filetypes
        )
        
        if not filename:
            return
        
        # 显示加载提示
        self.status_var.set("正在进行OCR识别...")
        self.root.update()
        
        # 在新线程中执行OCR识别
        def ocr_thread():
            try:
                # 初始化PaddleOCR
                ocr = PaddleOCR(use_angle_cls=True, lang='ch')
                
                # 执行OCR识别
                result = ocr.ocr(filename, cls=True)
                
                # 提取识别结果
                ocr_text = ''
                for line in result:
                    for word in line:
                        ocr_text += word[1][0] + ' '
                
                # 提取股票代码和名称
                import re
                stock_code_pattern = r'(?:SZ|SH)?\d{6}'
                stock_codes = re.findall(stock_code_pattern, ocr_text)
                
                # 使用股票识别器
                from src.analyzers.stock_recognizer import StockRecognizer
                recognizer = StockRecognizer()
                
                # 识别股票
                standardized_stocks = recognizer.recognize_stocks(ocr_text)
                
                # 获取当前选中的文章
                selection = self.article_tree.selection()
                if selection:
                    index = self.article_tree.index(selection[0])
                    if index < len(self.articles):
                        article = self.articles[index]
                        existing_stocks = article.get('stocks', [])
                        
                        # 添加新识别的股票
                        added_count = 0
                        for stock in standardized_stocks:
                            exists = False
                            for existing_stock in existing_stocks:
                                if isinstance(existing_stock, dict) and existing_stock.get('code') == stock['code']:
                                    exists = True
                                    break
                                elif existing_stock == stock['code']:
                                    exists = True
                                    break
                            
                            if not exists:
                                existing_stocks.append(stock)
                                added_count += 1
                        
                        if added_count > 0:
                            # 更新文章的股票池
                            article['stocks'] = existing_stocks
                            
                            # 保存文章数据
                            self.save_articles()
                            
                            # 更新显示
                            self.root.after(0, lambda: self.update_stock_list(article))
                            
                            # 显示识别结果
                            result_text = f"OCR识别完成！\n\n识别文本：{ocr_text[:200]}...\n\n提取股票：{len(standardized_stocks)} 只\n添加到股票池：{added_count} 只"
                            self.root.after(0, lambda: messagebox.showinfo("OCR识别结果", result_text))
                        else:
                            self.root.after(0, lambda: messagebox.showinfo("OCR识别结果", f"OCR识别完成！\n\n识别文本：{ocr_text[:200]}...\n\n提取股票：{len(standardized_stocks)} 只\n所有股票已在股票池中"))
                    else:
                        self.root.after(0, lambda: messagebox.showinfo("OCR识别结果", f"OCR识别完成！\n\n识别文本：{ocr_text[:200]}...\n\n提取股票：{len(standardized_stocks)} 只\n\n{standardized_stocks}"))
                else:
                    self.root.after(0, lambda: messagebox.showinfo("OCR识别结果", f"OCR识别完成！\n\n识别文本：{ocr_text[:200]}...\n\n提取股票：{len(standardized_stocks)} 只\n\n{standardized_stocks}"))
                
                self.root.after(0, lambda: self.status_var.set("OCR识别完成"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("OCR识别失败", f"识别过程中出现错误：{str(e)}"))
                self.root.after(0, lambda: self.status_var.set("OCR识别失败"))
        
        thread = threading.Thread(target=ocr_thread, daemon=True)
        thread.start()
    
    def verify_and_add_stock(self, article):
        """验证并添加股票名称"""
        # 获取选中的文本
        try:
            selected_text = self.content_text.get(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            messagebox.showinfo("提示", "请先选中要验证的股票名称")
            return
        
        # 验证股票名称
        import requests
        import json
        
        try:
            # 使用股票识别器
            from src.analyzers.stock_recognizer import StockRecognizer
            recognizer = StockRecognizer()
            
            # 清理选中的文本
            clean_text = selected_text.strip()
            
            # 获取股票建议
            suggestions = recognizer.get_suggestions(clean_text)
            
            if suggestions:
                # 使用第一个建议
                stock_info = suggestions[0]
                stock_name = stock_info['name']
                stock_code = stock_info['code']
                standard_code = stock_code
                found = True
            else:
                # 尝试不同的股票代码格式
                stock_codes = []
                
                # 直接使用清理后的文本
                stock_codes.append(clean_text)
                
                # 尝试添加交易所前缀
                stock_codes.append(f'sh{clean_text}')
                stock_codes.append(f'sz{clean_text}')
                stock_codes.append(f'SH{clean_text}')
                stock_codes.append(f'SZ{clean_text}')
                
                # 遍历尝试不同的代码格式
                found = False
                for code in stock_codes:
                    # 腾讯证券API接口
                    url = f"https://qt.gtimg.cn/q={code}"
                    response = requests.get(url, timeout=5)
                    response.encoding = 'gbk'
                    
                    # 解析响应
                    content = response.text
                    if content.startswith('v_') and '~' in content:
                        # 解析股票数据
                        data = content.split('=')[1].strip(';')
                        stock_info = data.split('~')
                        
                        if len(stock_info) > 3 and stock_info[1]:
                            stock_name = stock_info[1]
                            stock_code = stock_info[2]
                            
                            # 标准化股票代码（使用纯数字）
                            standard_code = stock_code
                            
                            found = True
                            break
            
            if not found:
                # 手动输入股票代码
                import tkinter.simpledialog
                stock_code = tkinter.simpledialog.askstring("手动输入股票代码", f"未找到股票 '{clean_text}' 的信息，请手动输入股票代码（如 600666 或 300418）：")
                
                if stock_code:
                    # 清理输入的股票代码
                    stock_code = stock_code.strip()
                    
                    # 验证股票代码格式
                    import re
                    if re.match(r'^\d{6}$', stock_code):
                        # 标准化股票代码（使用纯数字）
                        standard_code = stock_code
                        stock_name = clean_text
                        found = True
                    else:
                        messagebox.showinfo("输入错误", "请输入有效的6位股票代码")
                        return
                else:
                    return
            
            # 获取现有股票
            existing_stocks = article.get('stocks', [])
            
            # 检查是否已存在
            exists = False
            for stock in existing_stocks:
                if isinstance(stock, dict) and stock.get('code') == standard_code:
                    exists = True
                    break
                elif stock == standard_code:
                    exists = True
                    break
            
            if not exists:
                # 添加新股票（使用字典格式）
                existing_stocks.append({'name': stock_name, 'code': standard_code})
                
                # 更新文章的股票池
                article['stocks'] = existing_stocks
                
                # 保存文章数据
                self.save_articles()
                
                # 更新显示
                self.update_stock_list(article)
                
                # 更新文章信息
                stock_text = ', '.join([f"{s['name']}({s['code']})" if isinstance(s, dict) else s for s in existing_stocks]) if existing_stocks else '无'
                meta_text = f"作者：{article.get('author', '')}  |  发布：{article.get('publish_time', '')}  |  股票：{stock_text}  |  字数：{len(article.get('content', ''))}"
                # 重新加载文章内容以更新显示
                self.on_article_select(None)
                
                messagebox.showinfo("验证成功", f"成功验证并添加股票：{stock_name} ({standard_code})")
            else:
                messagebox.showinfo("提示", "该股票已在股票池中")
        except Exception as e:
            messagebox.showinfo("验证失败", f"验证过程中出现错误：{str(e)}")
    
    def show_about(self):
        """显示关于"""
        messagebox.showinfo("关于", 
                           "热点与趋势 v1.0\n\n"
                           "功能：批量采集、定时任务、搜索筛选、导出分享、数据统计\n\n"
                           "开发时间：2026-03-19")
    
    def open_config_manager(self):
        """打开配置管理界面"""
        try:
            from .config_manager_gui import ConfigManagerGUI
            ConfigManagerGUI(self.root)
        except Exception as e:
            messagebox.showerror("错误", f"打开配置管理界面失败: {str(e)}")
    
    def start_scheduler(self):
        """启动定时任务"""
        if not self.scheduler_running:
            self.scheduler_running = True
            self.scheduler_thread = threading.Thread(target=self.scheduler_loop, daemon=True)
            self.scheduler_thread.start()
            print("定时任务已启动")
    
    def scheduler_loop(self):
        """定时任务循环"""
        # 每半小时执行一次
        schedule.every(30).minutes.do(self.schedule_collect)
        
        # 立即执行一次
        self.schedule_collect()
        
        while self.scheduler_running:
            schedule.run_pending()
            time.sleep(1)
    
    def schedule_collect(self):
        """定时采集任务"""
        print(f"[{datetime.now()}] 执行定时采集...")
        self.collect_articles()

def main():
    root = tk.Tk()
    app = ArticleManagerApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()
