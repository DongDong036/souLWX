"""
热点与趋势 - 桌面应用
功能：批量采集、定时任务、搜索筛选、导出分享、数据统计
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import json
import os
import subprocess
from datetime import datetime, timedelta
import threading
import webbrowser
from pathlib import Path
import schedule
import time
import win32gui
import win32con
from paddleocr import PaddleOCR

class ArticleManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("热点与趋势")
        self.root.geometry("1200x800")
        
        # 数据文件
        self.articles_file = 'data/database/articles_database.json'
        self.config_file = 'config/manager_config.json'
        
        # 加载数据
        self.articles = self.load_articles()
        self.config = self.load_config()
        
        # 定时任务状态
        self.scheduler_running = False
        self.scheduler_thread = None
        
        # 创建界面
        self.create_menu()
        self.create_main_ui()
        self.update_stats()
        self.load_article_list()
        
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
        tools_menu.add_command(label="定时任务设置", command=self.open_scheduler)
        tools_menu.add_command(label="数据统计", command=self.show_statistics)
        
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
        
        # 采集按钮
        collect_btn = tk.Button(toolbar, text="🔄 采集最新 10 篇", command=self.collect_articles, 
                               bg='#4CAF50', fg='white', **button_style, activebackground='#45a049')
        collect_btn.pack(side=tk.LEFT, padx=8)
        
        # 统计按钮
        stats_btn = tk.Button(toolbar, text="📊 数据统计", command=self.show_statistics, 
                             bg='#2196F3', fg='white', **button_style, activebackground='#1976D2')
        stats_btn.pack(side=tk.LEFT, padx=8)
        
        # 导出按钮
        export_btn = tk.Button(toolbar, text="📤 导出", command=self.export_data, 
                             bg='#FF9800', fg='white', **button_style, activebackground='#F57C00')
        export_btn.pack(side=tk.LEFT, padx=8)
        
        # 清空按钮
        clear_btn = tk.Button(toolbar, text="🗑️ 清空", command=self.clear_articles, 
                             bg='#f44336', fg='white', **button_style, activebackground='#d32f2f')
        clear_btn.pack(side=tk.LEFT, padx=8)
        
        # 配置管理按钮
        config_btn = tk.Button(toolbar, text="⚙️ 配置管理", command=self.open_api_config, 
                             bg='#9C27B0', fg='white', **button_style, activebackground='#7B1FA2')
        config_btn.pack(side=tk.LEFT, padx=8)
        
        # 搜索框
        search_frame = tk.Frame(toolbar, bg='#f8f9fa')
        search_frame.pack(side=tk.RIGHT, padx=10)
        
        tk.Label(search_frame, text="搜索:", font=('微软雅黑', 10, 'bold'), bg='#f8f9fa').pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_articles)
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=30, 
                               font=('微软雅黑', 10), bd=2, relief=tk.GROOVE)
        search_entry.pack(side=tk.LEFT, padx=5)
        
        # 股票搜索
        tk.Label(search_frame, text="股票:", font=('微软雅黑', 10, 'bold'), bg='#f8f9fa').pack(side=tk.LEFT, padx=10)
        self.stock_var = tk.StringVar()
        self.stock_var.trace('w', self.filter_articles)
        stock_entry = tk.Entry(search_frame, textvariable=self.stock_var, width=20, 
                              font=('微软雅黑', 10), bd=2, relief=tk.GROOVE)
        stock_entry.pack(side=tk.LEFT, padx=5)
        
        # 筛选下拉框
        tk.Label(search_frame, text="类型:", font=('微软雅黑', 10, 'bold'), bg='#f8f9fa').pack(side=tk.LEFT, padx=10)
        self.type_var = tk.StringVar(value="全部")
        type_combo = ttk.Combobox(search_frame, textvariable=self.type_var, 
                                 values=["全部", "今日", "本周", "本月"], 
                                 width=10, font=('微软雅黑', 10))
        type_combo.pack(side=tk.LEFT, padx=5)
        type_combo.bind('<<ComboboxSelected>>', self.filter_articles)
        
        # 主内容区（左中右分栏）
        main_paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=5, bg='#ffffff')
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
        
        # 左侧：文章列表
        left_frame = tk.Frame(main_paned, bg='#ffffff', bd=1, relief=tk.GROOVE)
        main_paned.add(left_frame, width=450)
        
        # 列表标题
        list_title_frame = tk.Frame(left_frame, bg='#e3f2fd')
        list_title_frame.pack(fill=tk.X, pady=5)
        tk.Label(list_title_frame, text="📋 文章列表", font=('微软雅黑', 12, 'bold'), bg='#e3f2fd').pack(side=tk.LEFT, padx=10, pady=5)
        
        # 列表滚动区域
        list_frame = tk.Frame(left_frame, bg='#ffffff')
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建 Treeview
        columns = ('序号', '标题', '作者', '时间')
        self.article_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=22)
        
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
        
        # 绑定选择事件
        self.article_tree.bind('<<TreeviewSelect>>', self.on_article_select)
        self.article_tree.bind('<Double-1>', self.open_article_url)
        
        # 绑定右键菜单
        self.article_tree.bind('<Button-3>', self.show_context_menu)
        
        # 创建右键菜单
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="发送AI分析", command=self.send_to_ai_analysis)
        
        # 中间：文章内容
        center_frame = tk.Frame(main_paned, bg='#ffffff', bd=1, relief=tk.GROOVE)
        main_paned.add(center_frame, width=500)
        
        # 文章内容
        content_frame = tk.Frame(center_frame, bg='#ffffff', bd=1, relief=tk.RAISED)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        self.content_text = scrolledtext.ScrolledText(content_frame, wrap=tk.WORD, font=('微软雅黑', 11), bg='#f9f9f9')
        self.content_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 右侧：DeepSeek和股票池
        right_frame = tk.Frame(main_paned, bg='#ffffff', bd=1, relief=tk.GROOVE)
        main_paned.add(right_frame, width=400)
        
        # 上方：DeepSeek对话窗口（70%高度）
        deepseek_frame = tk.Frame(right_frame, bg='#ffffff', bd=1, relief=tk.RAISED)
        deepseek_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 浏览器标题
        deepseek_title_frame = tk.Frame(deepseek_frame, bg='#e3f2fd')
        deepseek_title_frame.pack(fill=tk.X, pady=5)
        tk.Label(deepseek_title_frame, text="🤖 DeepSeek对话", font=('微软雅黑', 12, 'bold'), bg='#e3f2fd').pack(side=tk.LEFT, padx=10, pady=5)
        

        
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
        stock_title_frame.pack(fill=tk.X, pady=5)
        tk.Label(stock_title_frame, text="📈 股票池", font=('微软雅黑', 12, 'bold'), bg='#e3f2fd').pack(side=tk.LEFT, padx=10, pady=5)
        
        # 股票池内容
        stock_list_frame = tk.Frame(stock_frame, bg='#ffffff')
        stock_list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 创建股票池Treeview（每行显示3组股票）
        stock_columns = ('股票名称1', '股票代码1', '股票名称2', '股票代码2', '股票名称3', '股票代码3')
        self.stock_tree = ttk.Treeview(stock_list_frame, columns=stock_columns, show='headings', height=3)
        
        # 配置列
        for col in stock_columns:
            self.stock_tree.heading(col, text=col, anchor=tk.CENTER)
            if '股票名称' in col:
                self.stock_tree.column(col, width=80, anchor=tk.W)
            else:
                self.stock_tree.column(col, width=60, anchor=tk.CENTER)
        
        # 配置样式
        style = ttk.Style()
        style.configure("Treeview.Heading", font=('微软雅黑', 9, 'bold'), foreground='#1976D2')
        style.configure("Treeview", font=('微软雅黑', 8), rowheight=25)
        style.map("Treeview", background=[('selected', '#e3f2fd')], foreground=[('selected', '#1976D2')])
        
        self.stock_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 滚动条
        stock_scrollbar = ttk.Scrollbar(stock_list_frame, orient=tk.VERTICAL, command=self.stock_tree.yview)
        stock_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.stock_tree.configure(yscrollcommand=stock_scrollbar.set)
        
        # 股票池按钮
        stock_btn_frame = tk.Frame(stock_frame, bg='#ffffff', bd=1, relief=tk.RAISED)
        stock_btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 分析股票按钮
        analyze_btn = tk.Button(stock_btn_frame, text="🔍 分析股票", command=self.analyze_stocks, 
                              bg='#2196F3', fg='white', font=('微软雅黑', 9), padx=5, pady=3)
        analyze_btn.pack(side=tk.LEFT, padx=5)
        
        # 手动添加股票按钮
        add_manual_btn = tk.Button(stock_btn_frame, text="➕ 手动添加", command=self.manual_add_stock, 
                                 bg='#4CAF50', fg='white', font=('微软雅黑', 9), padx=5, pady=3)
        add_manual_btn.pack(side=tk.LEFT, padx=5)
        
        # OCR识别按钮
        ocr_btn = tk.Button(stock_btn_frame, text="📷 OCR识别", command=self.ocr_recognition, 
                           bg='#FF9800', fg='white', font=('微软雅黑', 9), padx=5, pady=3)
        ocr_btn.pack(side=tk.LEFT, padx=5)
        
        # DeepSeek分析按钮
        deepseek_btn = tk.Button(stock_btn_frame, text="🤖 DeepSeek分析", command=self.open_deepseek_analysis, 
                                bg='#9C27B0', fg='white', font=('微软雅黑', 9), padx=5, pady=3)
        deepseek_btn.pack(side=tk.LEFT, padx=5)
        
        # 清空股票按钮
        clear_stock_btn = tk.Button(stock_btn_frame, text="🗑️ 清空", command=self.clear_stocks, 
                                  bg='#f44336', fg='white', font=('微软雅黑', 9), padx=5, pady=3)
        clear_stock_btn.pack(side=tk.RIGHT, padx=5)
        
        # 绑定窗口大小变化事件
        self.root.bind('<Configure>', self.on_window_resize)
        
        # 底部状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = tk.Label(self.root, textvariable=self.status_var, 
                             relief=tk.SUNKEN, anchor=tk.W, font=('微软雅黑', 10), bg='#f5f5f5')
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
    def load_articles(self):
        """加载文章数据"""
        if os.path.exists(self.articles_file):
            with open(self.articles_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                articles = data.get('articles', [])
                # 按时间降序排序
                articles.sort(key=lambda x: x.get('publish_time', ''), reverse=True)
                return articles
        return []
    
    def save_articles(self):
        """保存文章数据"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'total': len(self.articles),
            'articles': self.articles
        }
        with open(self.articles_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_config(self):
        """加载配置"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'auto_collect': False, 'collect_time': '09:00'}
    
    def load_article_list(self):
        """加载文章列表"""
        # 清空列表
        for item in self.article_tree.get_children():
            self.article_tree.delete(item)
        
        # 添加文章
        for i, article in enumerate(self.articles, 1):
            title = article.get('title', '')[:30] + '...' if len(article.get('title', '')) > 30 else article.get('title', '')
            author = article.get('author', '')
            pub_time = article.get('publish_time', '')
            
            self.article_tree.insert('', tk.END, values=(i, title, author, pub_time))
    
    def filter_articles(self, *args):
        """筛选文章"""
        search_text = self.search_var.get().lower()
        stock_text = self.stock_var.get().strip().upper()
        time_filter = self.type_var.get()
        
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
        now = datetime.now()
        for article in self.articles:
            # 搜索过滤
            title = article.get('title', '').lower()
            author = article.get('author', '').lower()
            content = article.get('content', '').lower()
            
            if search_text and search_text not in title and search_text not in author and search_text not in content:
                continue
            
            # 股票过滤
            if stock_text:
                article_stocks = article.get('stocks', [])
                standardized_stock = standardize_stock_code(stock_text)
                if standardized_stock not in article_stocks:
                    continue
            
            # 时间过滤
            if time_filter != "全部":
                pub_time_str = article.get('publish_time', '')
                try:
                    pub_date = datetime.strptime(pub_time_str, '%Y-%m-%d %H:%M:%S')
                    if time_filter == "今日":
                        if pub_date.date() != now.date():
                            continue
                    elif time_filter == "本周":
                        if now - pub_date > timedelta(days=7):
                            continue
                    elif time_filter == "本月":
                        if now - pub_date > timedelta(days=30):
                            continue
                except:
                    pass
            
            # 添加到列表
            title_display = article.get('title', '')[:30] + '...' if len(article.get('title', '')) > 30 else article.get('title', '')
            # 计算序号（从1开始）
            article_index = len(self.article_tree.get_children()) + 1
            self.article_tree.insert('', tk.END, values=(article_index, title_display, article.get('author', ''), article.get('publish_time', '')))
    
    def on_article_select(self, event):
        """选择文章时显示详情"""
        selection = self.article_tree.selection()
        if not selection:
            return
        
        # 获取选中的文章索引
        index = self.article_tree.index(selection[0])
        if index < len(self.articles):
            article = self.articles[index]
            
            # 不再更新详情标题，因为已移除
            
            # 显示内容（将HTML转换为纯文本并脱水处理）
            content = article.get('content', '')
            # 简单的HTML转纯文本
            import re
            # 移除HTML标签
            plain_text = re.sub(r'<[^>]+>', '', content)
            # 替换HTML实体
            plain_text = plain_text.replace('&nbsp;', ' ')
            plain_text = plain_text.replace('&lt;', '<')
            plain_text = plain_text.replace('&gt;', '>')
            plain_text = plain_text.replace('&amp;', '&')
            
            # 脱水处理
            plain_text = self.dehydrate_content(plain_text)
            
            # 准备文章信息
            stocks = article.get('stocks', [])
            # 处理股票池数据
            stock_text_list = []
            for stock in stocks:
                if isinstance(stock, dict) and 'name' in stock and 'code' in stock:
                    stock_text_list.append(f"{stock['name']}({stock['code']})")
                else:
                    stock_text_list.append(stock)
            stock_text = ', '.join(stock_text_list) if stock_text_list else '无'
            meta_text = f"作者：{article.get('author', '')}  |  发布：{article.get('publish_time', '')}  |  股票：{stock_text}  |  字数：{len(article.get('content', ''))}"
            
            # 组合文章信息和内容
            full_content = f"【文章信息】\n{meta_text}\n\n【文章内容】\n{plain_text}"
            
            self.content_text.delete(1.0, tk.END)
            self.content_text.insert(tk.END, full_content)
            
            # 显示股票池
            self.update_stock_list(article)
            
            # 绑定右键菜单
            self.content_text.bind('<Button-3>', lambda e: self.show_content_context_menu(e, article))
    
    def collect_articles(self):
        """采集文章"""
        self.status_var.set("正在采集最新文章...")
        self.root.update()
        
        # 在新线程中执行采集
        def collect_thread():
            try:
                # 调用采集脚本
                import subprocess
                result = subprocess.run(['python', 'src/collect_broadcast_stable.py'], 
                                       capture_output=True, text=True, timeout=120)
                
                # 输出采集结果
                print("采集脚本输出:")
                print(result.stdout)
                print("采集脚本错误:")
                print(result.stderr)
                
                # 重新加载数据
                self.articles = self.load_articles()
                self.load_article_list()
                self.update_stats()
                
                self.root.after(0, lambda: self.status_var.set("采集完成"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("采集失败", str(e)))
                self.root.after(0, lambda: self.status_var.set("采集失败"))
        
        thread = threading.Thread(target=collect_thread, daemon=True)
        thread.start()
    
    def export_data(self):
        """导出数据"""
        filetypes = [
            ('JSON 文件', '*.json'),
            ('Markdown 文档', '*.md'),
            ('所有文件', '*.*')
        ]
        
        filename = filedialog.asksaveasfilename(
            title='导出数据',
            defaultextension='.json',
            filetypes=filetypes
        )
        
        if not filename:
            return
        
        try:
            if filename.endswith('.json'):
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
    
    def open_article_url(self, event=None):
        """在浏览器打开原文"""
        selection = self.article_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一篇文章")
            return
        
        index = self.article_tree.index(selection[0])
        if index < len(self.articles):
            url = self.articles[index].get('url', '')
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
                prompt = f"请分析此链接内容：{article_url}"
                
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
    
    def show_statistics(self):
        """显示统计信息"""
        # 计算统计数据
        total = len(self.articles)
        
        # 按作者统计
        author_count = {}
        for article in self.articles:
            author = article.get('author', '未知')
            author_count[author] = author_count.get(author, 0) + 1
        
        # 按日期统计
        date_count = {}
        for article in self.articles:
            date = article.get('publish_time', '')[:10]
            if date:
                date_count[date] = date_count.get(date, 0) + 1
        
        # 创建统计窗口
        stats_win = tk.Toplevel(self.root)
        stats_win.title("📊 数据统计")
        stats_win.geometry("650x550")
        stats_win.resizable(True, True)
        
        # 窗口背景
        stats_win.configure(bg='#ffffff')
        
        # 标题栏
        title_frame = tk.Frame(stats_win, bg='#e3f2fd', bd=1, relief=tk.RAISED)
        title_frame.pack(fill=tk.X, pady=5)
        tk.Label(title_frame, text="📊 数据统计", font=('微软雅黑', 14, 'bold'), bg='#e3f2fd').pack(side=tk.LEFT, padx=15, pady=10)
        
        # 总体统计
        total_frame = tk.Frame(stats_win, bg='#ffffff', bd=1, relief=tk.GROOVE)
        total_frame.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(total_frame, text="=== 总体统计 ===", font=('微软雅黑', 12, 'bold'), bg='#ffffff').pack(pady=10)
        
        total_info_frame = tk.Frame(total_frame, bg='#ffffff')
        total_info_frame.pack(padx=20, pady=10)
        tk.Label(total_info_frame, text=f"📄 文章总数：{total}", font=('微软雅黑', 11), bg='#ffffff').pack(anchor='w', pady=5)
        tk.Label(total_info_frame, text=f"👤 作者数量：{len(author_count)}", font=('微软雅黑', 11), bg='#ffffff').pack(anchor='w', pady=5)
        
        # 作者统计
        author_frame = tk.Frame(stats_win, bg='#ffffff', bd=1, relief=tk.GROOVE)
        author_frame.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(author_frame, text="=== 作者统计 (Top 10) ===", font=('微软雅黑', 12, 'bold'), bg='#ffffff').pack(pady=10)
        
        top_authors = sorted(author_count.items(), key=lambda x: x[1], reverse=True)[:10]
        author_list_frame = tk.Frame(author_frame, bg='#ffffff')
        author_list_frame.pack(padx=20, pady=10)
        
        for author, count in top_authors:
            tk.Label(author_list_frame, text=f"👤 {author}: {count} 篇", font=('微软雅黑', 10), bg='#ffffff').pack(anchor='w', pady=3)
        
        # 日期统计
        date_frame = tk.Frame(stats_win, bg='#ffffff', bd=1, relief=tk.GROOVE)
        date_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        tk.Label(date_frame, text="=== 按日期统计 ===", font=('微软雅黑', 12, 'bold'), bg='#ffffff').pack(pady=10)
        
        date_text = tk.Text(date_frame, height=12, font=('微软雅黑', 10), bg='#f9f9f9')
        date_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        for date in sorted(date_count.keys(), reverse=True):
            date_text.insert(tk.END, f"{date}: {date_count[date]} 篇\n")
    
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
    
    def update_stock_list(self, article):
        """更新股票池列表（每行显示3组股票）"""
        # 清空列表
        for item in self.stock_tree.get_children():
            self.stock_tree.delete(item)
        
        # 添加股票（每3个一组）
        stocks = article.get('stocks', [])
        
        # 将股票分组，每组3个
        stock_groups = []
        current_group = []
        
        for stock in stocks:
            current_group.append(stock)
            if len(current_group) == 3:
                stock_groups.append(current_group)
                current_group = []
        
        # 处理剩余的股票
        if current_group:
            # 不足3个的组，用空值填充
            while len(current_group) < 3:
                current_group.append({'name': '', 'code': ''})
            stock_groups.append(current_group)
        
        # 插入分组后的股票
        for group in stock_groups:
            # 准备一行的数据
            row_data = []
            
            for stock in group:
                if isinstance(stock, dict) and 'name' in stock and 'code' in stock:
                    row_data.extend([stock['name'], stock['code']])
                else:
                    row_data.extend(["未知", stock if stock else ""])
            
            self.stock_tree.insert('', tk.END, values=tuple(row_data))
    
    def analyze_stocks(self):
        """分析文章内容并提取股票"""
        # 获取当前选中的文章
        selection = self.article_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择一篇文章")
            return
        
        index = self.article_tree.index(selection[0])
        if index < len(self.articles):
            article = self.articles[index]
            content = article.get('content', '')
            
            # 使用股票识别器
            from stock_recognizer import StockRecognizer
            recognizer = StockRecognizer()
            
            # 识别股票
            stock_list = recognizer.recognize_stocks(content)
            code_set = set(stock['code'] for stock in stock_list)
            
            # 获取现有股票池
            existing_stocks = article.get('stocks', [])
            
            # 合并现有股票和新分析的股票
            existing_code_set = set()
            for stock in existing_stocks:
                if isinstance(stock, dict) and 'code' in stock:
                    existing_code_set.add(stock['code'])
                else:
                    existing_code_set.add(stock)
            
            # 添加新分析的股票
            for stock in stock_list:
                if stock['code'] not in existing_code_set:
                    existing_stocks.append(stock)
                    existing_code_set.add(stock['code'])
            
            # 确保所有股票都有完整的信息
            updated_stocks = []
            for stock in existing_stocks:
                if isinstance(stock, dict) and 'name' in stock and 'code' in stock:
                    updated_stocks.append(stock)
                else:
                    # 为旧格式的股票添加名称
                    code = stock
                    stock_name = "未知"
                    for name, code_num in stock_mapping.items():
                        if code.endswith(code_num):
                            stock_name = name
                            break
                    updated_stocks.append({'name': stock_name, 'code': code})
            
            # 更新文章的股票池
            article['stocks'] = updated_stocks
            
            # 保存文章数据
            self.save_articles()
            
            # 更新显示
            self.update_stock_list(article)
            
            # 更新文章信息
            stock_text = ', '.join([f"{s['name']}({s['code']})" for s in updated_stocks]) if updated_stocks else '无'
            meta_text = f"作者：{article.get('author', '')}  |  发布：{article.get('publish_time', '')}  |  股票：{stock_text}  |  字数：{len(article.get('content', ''))}"
            # 重新加载文章内容以更新显示
            self.on_article_select(None)
            
            # 更新状态栏
            self.status_var.set(f"股票分析完成，现有 {len(updated_stocks)} 只股票")
    
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
            
            # 清空股票池
            article['stocks'] = []
            
            # 保存文章数据
            self.save_articles()
            
            # 更新显示
            self.update_stock_list(article)
            
            # 更新文章信息
            meta_text = f"作者：{article.get('author', '')}  |  发布：{article.get('publish_time', '')}  |  股票：无  |  字数：{len(article.get('content', ''))}"
            # 重新加载文章内容以更新显示
            self.on_article_select(None)
            
            # 更新状态栏
            self.status_var.set("股票池已清空")
    
    def show_content_context_menu(self, event, article):
        """显示内容右键菜单"""
        # 创建右键菜单
        context_menu = tk.Menu(self.root, tearoff=0)
        
        # 添加菜单项
        context_menu.add_command(label="添加选中文本为股票", 
                               command=lambda: self.add_stock_from_selection(article))
        context_menu.add_command(label="验证并添加股票名称", 
                               command=lambda: self.verify_and_add_stock(article))
        
        # 显示菜单
        context_menu.post(event.x_root, event.y_root)
    
    def add_stock_from_selection(self, article):
        """从选中的文本添加股票"""
        # 获取选中的文本
        try:
            selected_text = self.content_text.get(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            messagebox.showinfo("提示", "请先选中要添加的股票代码")
            return
        
        # 标准化股票代码
        import re
        stock_code_pattern = r'(?:SZ|SH)?\d{6}'
        stock_codes = re.findall(stock_code_pattern, selected_text)
        
        if not stock_codes:
            messagebox.showinfo("提示", "选中的文本中没有找到有效的股票代码")
            return
        
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
        
        # 获取现有股票
        existing_stocks = article.get('stocks', [])
        
        # 添加新股票
        for stock in unique_stocks:
            if stock not in existing_stocks:
                existing_stocks.append(stock)
        
        # 更新文章的股票池
        article['stocks'] = existing_stocks
        
        # 保存文章数据
        self.save_articles()
        
        # 更新显示
        self.update_stock_list(article)
        
        # 更新文章信息
        stock_text = ', '.join(existing_stocks) if existing_stocks else '无'
        meta_text = f"作者：{article.get('author', '')}  |  发布：{article.get('publish_time', '')}  |  股票：{stock_text}  |  字数：{len(article.get('content', ''))}"
        # 重新加载文章内容以更新显示
        self.on_article_select(None)
        
        messagebox.showinfo("添加成功", f"成功添加 {len(unique_stocks)} 只股票")
    
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
            
            # 创建手动添加股票的对话框
            import tkinter.simpledialog
            
            # 输入股票名称
            stock_name = tkinter.simpledialog.askstring("手动添加股票", "请输入股票名称：")
            if not stock_name:
                return
            
            # 输入股票代码
            stock_code = tkinter.simpledialog.askstring("手动添加股票", "请输入股票代码（6位数字）：")
            if not stock_code:
                return
            
            # 验证股票代码格式
            import re
            if not re.match(r'^\d{6}$', stock_code):
                messagebox.showinfo("输入错误", "请输入有效的6位股票代码")
                return
            
            # 标准化股票代码（使用纯数字）
            standard_code = stock_code
            
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
                
                messagebox.showinfo("添加成功", f"成功添加股票：{stock_name} ({standard_code})")
            else:
                messagebox.showinfo("提示", "该股票已在股票池中")
    
    def dehydrate_content(self, content):
        """文章内容脱水处理"""
        import re
        
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
        from config_gui import ConfigGUI
        config_gui = ConfigGUI(self.root)
        config_gui.open_config_window()
        
    
    def open_deepseek_main(self):
        """打开DeepSeek主界面"""
        # DeepSeek主界面URL
        deepseek_url = "https://chat.deepseek.com"
        
        # 打开浏览器
        import webbrowser
        webbrowser.open(deepseek_url)
        
        messagebox.showinfo("DeepSeek", "已打开DeepSeek主界面")
    
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
            prompt = f"帮我分析总结\"{article_url}\"的内容，并提取相关的股票信息"
            
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
                    messagebox.showinfo("DeepSeek分析", f"已打开DeepSeek网页并填充分析请求")
            else:
                import urllib.parse
                encoded_prompt = urllib.parse.quote(prompt)
                deepseek_url = f"https://chat.deepseek.com/?q={encoded_prompt}"
                import webbrowser
                webbrowser.open(deepseek_url)
                messagebox.showinfo("DeepSeek分析", "已打开DeepSeek网页并填充分析请求")
    
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
                from stock_recognizer import StockRecognizer
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
            from stock_recognizer import StockRecognizer
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
