"""
配置管理界面
包含信息源管理、定时任务设置等功能
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import threading
from config.source_manager import SourceManager
from collectors.scrapling_config import ScraplingConfigManager
from collectors.scrapling_collector import ScraplingCollector

class ConfigGUI:
    def __init__(self, parent):
        self.parent = parent
        self.source_manager = SourceManager()
    
    def open_config_window(self):
        """打开配置管理窗口"""
        self.config_window = tk.Toplevel(self.parent)
        self.config_window.title("配置管理")
        self.config_window.geometry("800x600")
        self.config_window.resizable(True, True)
        
        # 创建笔记本（标签页）
        notebook = ttk.Notebook(self.config_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 信息源管理标签页
        sources_frame = ttk.Frame(notebook)
        notebook.add(sources_frame, text="信息源管理")
        self.create_sources_tab(sources_frame)
        
        # 全局设置标签页
        global_frame = ttk.Frame(notebook)
        notebook.add(global_frame, text="全局设置")
        self.create_global_tab(global_frame)
    
    def create_sources_tab(self, frame):
        """创建信息源管理标签页"""
        # 顶部按钮
        button_frame = tk.Frame(frame, bg='#f8f9fa')
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        add_btn = tk.Button(button_frame, text="➕ 添加信息源", command=self.add_source, 
                          bg='#4CAF50', fg='white', font=('微软雅黑', 10, 'bold'), padx=12, pady=6)
        add_btn.pack(side=tk.LEFT, padx=5)
        
        edit_btn = tk.Button(button_frame, text="✏️ 编辑信息源", command=self.edit_source, 
                           bg='#2196F3', fg='white', font=('微软雅黑', 10, 'bold'), padx=12, pady=6)
        edit_btn.pack(side=tk.LEFT, padx=5)
        
        delete_btn = tk.Button(button_frame, text="🗑️ 删除信息源", command=self.delete_source, 
                             bg='#f44336', fg='white', font=('微软雅黑', 10, 'bold'), padx=12, pady=6)
        delete_btn.pack(side=tk.LEFT, padx=5)
        
        refresh_btn = tk.Button(button_frame, text="🔄 刷新", command=self.refresh_sources, 
                              bg='#FF9800', fg='white', font=('微软雅黑', 10, 'bold'), padx=12, pady=6)
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # 信息源列表
        list_frame = tk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 树形视图
        columns = ('id', 'name', 'url', 'enabled', 'interval')
        self.sources_tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        # 配置列
        self.sources_tree.heading('id', text='ID', anchor=tk.CENTER)
        self.sources_tree.heading('name', text='名称', anchor=tk.W)
        self.sources_tree.heading('url', text='URL', anchor=tk.W)
        self.sources_tree.heading('enabled', text='状态', anchor=tk.CENTER)
        self.sources_tree.heading('interval', text='采集间隔(分钟)', anchor=tk.CENTER)
        
        # 设置列宽
        self.sources_tree.column('id', width=100, anchor=tk.CENTER)
        self.sources_tree.column('name', width=120, anchor=tk.W)
        self.sources_tree.column('url', width=400, anchor=tk.W)
        self.sources_tree.column('enabled', width=60, anchor=tk.CENTER)
        self.sources_tree.column('interval', width=100, anchor=tk.CENTER)
        
        # 配置样式
        style = ttk.Style()
        style.configure("Treeview.Heading", font=('微软雅黑', 9, 'bold'), foreground='#1976D2')
        style.configure("Treeview", font=('微软雅黑', 8), rowheight=25)
        style.map("Treeview", background=[('selected', '#e3f2fd')], foreground=[('selected', '#1976D2')])
        
        self.sources_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.sources_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.sources_tree.configure(yscrollcommand=scrollbar.set)
        
        # 加载信息源
        self.load_sources()
    
    def create_global_tab(self, frame):
        """创建全局设置标签页"""
        # 全局设置表单
        form_frame = tk.Frame(frame, padx=20, pady=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # 默认采集间隔
        tk.Label(form_frame, text="默认采集间隔（分钟）:", font=('微软雅黑', 10)).grid(row=0, column=0, sticky=tk.W, pady=10)
        self.default_interval_var = tk.StringVar(value=str(self.source_manager.global_config.get('default_interval', 30)))
        tk.Entry(form_frame, textvariable=self.default_interval_var, width=10).grid(row=0, column=1, sticky=tk.W, pady=10)
        
        # 最大并发数
        tk.Label(form_frame, text="最大并发数:", font=('微软雅黑', 10)).grid(row=1, column=0, sticky=tk.W, pady=10)
        self.max_concurrent_var = tk.StringVar(value=str(self.source_manager.global_config.get('max_concurrent', 3)))
        tk.Entry(form_frame, textvariable=self.max_concurrent_var, width=10).grid(row=1, column=1, sticky=tk.W, pady=10)
        
        # 超时设置
        tk.Label(form_frame, text="超时设置（秒）:", font=('微软雅黑', 10)).grid(row=2, column=0, sticky=tk.W, pady=10)
        self.timeout_var = tk.StringVar(value=str(self.source_manager.global_config.get('timeout', 60)))
        tk.Entry(form_frame, textvariable=self.timeout_var, width=10).grid(row=2, column=1, sticky=tk.W, pady=10)
        
        # 保存按钮
        save_btn = tk.Button(form_frame, text="💾 保存设置", command=self.save_global_settings, 
                           bg='#4CAF50', fg='white', font=('微软雅黑', 10, 'bold'), padx=20, pady=8)
        save_btn.grid(row=3, column=0, columnspan=2, pady=20)
    
    def load_sources(self):
        """加载信息源到树形视图"""
        # 清空现有数据
        for item in self.sources_tree.get_children():
            self.sources_tree.delete(item)
        
        # 加载信息源
        for source in self.source_manager.sources:
            enabled = "启用" if source.get('enabled', True) else "禁用"
            self.sources_tree.insert('', tk.END, values=(
                source.get('id'),
                source.get('name'),
                source.get('url'),
                enabled,
                source.get('interval', 30)
            ))
    
    def add_source(self):
        """添加新信息源"""
        self.source_dialog("添加信息源")
    
    def edit_source(self):
        """编辑选中的信息源"""
        selection = self.sources_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择一个信息源")
            return
        
        item = selection[0]
        source_id = self.sources_tree.item(item, "values")[0]
        source = self.source_manager.get_source_by_id(source_id)
        
        if source:
            self.source_dialog("编辑信息源", source)
    
    def delete_source(self):
        """删除选中的信息源"""
        selection = self.sources_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择一个信息源")
            return
        
        item = selection[0]
        source_id = self.sources_tree.item(item, "values")[0]
        source_name = self.sources_tree.item(item, "values")[1]
        
        if messagebox.askyesno("确认", f"确定要删除信息源 '{source_name}' 吗？"):
            self.source_manager.remove_source(source_id)
            self.load_sources()
            messagebox.showinfo("提示", "删除成功")
    
    def refresh_sources(self):
        """刷新信息源列表"""
        self.source_manager.load_config()
        self.load_sources()
        messagebox.showinfo("提示", "刷新成功")
    
    def source_dialog(self, title, source=None):
        """信息源编辑对话框"""
        dialog = tk.Toplevel(self.config_window)
        dialog.title(title)
        dialog.geometry("600x500")
        dialog.resizable(False, False)
        
        # 表单框架
        form_frame = tk.Frame(dialog, padx=20, pady=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # 名称
        tk.Label(form_frame, text="名称:", font=('微软雅黑', 10)).grid(row=0, column=0, sticky=tk.W, pady=10)
        name_var = tk.StringVar(value=source.get('name', '') if source else '')
        tk.Entry(form_frame, textvariable=name_var, width=40).grid(row=0, column=1, sticky=tk.W, pady=10)
        
        # URL
        tk.Label(form_frame, text="URL:", font=('微软雅黑', 10)).grid(row=1, column=0, sticky=tk.W, pady=10)
        url_var = tk.StringVar(value=source.get('url', '') if source else '')
        url_entry = tk.Entry(form_frame, textvariable=url_var, width=30)
        url_entry.grid(row=1, column=1, sticky=tk.W, pady=10)
        
        # 分析结果
        tk.Label(form_frame, text="分析结果:", font=('微软雅黑', 10)).grid(row=2, column=0, sticky=tk.W, pady=10)
        analysis_text = tk.Text(form_frame, width=50, height=5, font=('微软雅黑', 9))
        analysis_text.grid(row=2, column=1, columnspan=2, sticky=tk.W, pady=10)
        
        # 分析按钮
        analyze_btn = tk.Button(form_frame, text="🔍 分析", command=lambda: self.analyze_source(url_var, analysis_text), 
                              bg='#2196F3', fg='white', font=('微软雅黑', 9, 'bold'), padx=10, pady=4)
        analyze_btn.grid(row=1, column=2, sticky=tk.W, pady=10, padx=5)
        

        
        # 最大文章数
        tk.Label(form_frame, text="最大文章数:", font=('微软雅黑', 10)).grid(row=4, column=0, sticky=tk.W, pady=10)
        max_articles_var = tk.StringVar(value=str(source.get('max_articles', 10)) if source else '10')
        tk.Entry(form_frame, textvariable=max_articles_var, width=10).grid(row=4, column=1, sticky=tk.W, pady=10)
        
        # 采集间隔
        tk.Label(form_frame, text="采集间隔（分钟）:", font=('微软雅黑', 10)).grid(row=5, column=0, sticky=tk.W, pady=10)
        interval_var = tk.StringVar(value=str(source.get('interval', 30)) if source else '30')
        tk.Entry(form_frame, textvariable=interval_var, width=10).grid(row=5, column=1, sticky=tk.W, pady=10)
        
        # 启用状态
        enabled_var = tk.BooleanVar(value=source.get('enabled', True) if source else True)
        tk.Checkbutton(form_frame, text="启用", variable=enabled_var, font=('微软雅黑', 10)).grid(row=6, column=1, sticky=tk.W, pady=10)
        
        # 测试按钮
        def test_source():
            # 测试采集功能
            url = url_var.get()
            if not url:
                messagebox.showinfo("提示", "请先输入URL")
                return
            
            # 显示测试状态
            analysis_text.delete(1.0, tk.END)
            analysis_text.insert(tk.END, "正在测试采集...\n")
            dialog.update()
            
            # 启动测试线程
            def test_thread():
                try:
                    # 创建采集器
                    collector = ScraplingCollector()
                    # 测试采集
                    articles = collector.collect_from_url(url, max_articles=3)
                    
                    # 显示测试结果
                    analysis_text.delete(1.0, tk.END)
                    if articles:
                        analysis_text.insert(tk.END, f"测试成功！采集到 {len(articles)} 篇文章\n")
                        for i, article in enumerate(articles[:2], 1):
                            analysis_text.insert(tk.END, f"{i}. {article.get('title', '无标题')}\n")
                        analysis_text.insert(tk.END, "\n可以保存并加入自动采集作业")
                    else:
                        analysis_text.insert(tk.END, "测试失败，未采集到文章\n")
                        analysis_text.insert(tk.END, "请检查URL或选择器配置")
                except Exception as e:
                    analysis_text.delete(1.0, tk.END)
                    analysis_text.insert(tk.END, f"测试失败: {str(e)}")
            
            threading.Thread(target=test_thread, daemon=True).start()
        
        # 编辑选择器按钮
        def edit_selectors():
            # 获取当前选择器
            config_manager = ScraplingConfigManager()
            website_name = name_var.get()
            url = url_var.get()
            
            if not website_name or not url:
                messagebox.showinfo("提示", "请先输入网站名称和URL")
                return
            
            # 分析网站，获取选择器
            selectors = config_manager.analyze_website(url)
            
            # 创建选择器编辑窗口
            selector_window = tk.Toplevel(dialog)
            selector_window.title("编辑选择器")
            selector_window.geometry("800x600")
            selector_window.resizable(True, True)
            
            # 创建滚动区域
            canvas = tk.Canvas(selector_window)
            scrollbar = ttk.Scrollbar(selector_window, orient="vertical", command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(
                    scrollregion=canvas.bbox("all")
                )
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # 编辑文章链接选择器
            tk.Label(scrollable_frame, text="文章链接选择器:", font=('微软雅黑', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=10)
            link_selectors_var = tk.StringVar(value=", ".join(selectors.get('article_links', [])))
            tk.Entry(scrollable_frame, textvariable=link_selectors_var, width=70).grid(row=0, column=1, sticky=tk.W, pady=10)
            
            # 编辑详情页选择器
            field_vars = {}
            row = 1
            for field, field_selectors in selectors.get('article_detail', {}).items():
                tk.Label(scrollable_frame, text=f"{field}选择器:", font=('微软雅黑', 10)).grid(row=row, column=0, sticky=tk.W, pady=5)
                field_var = tk.StringVar(value=", ".join(field_selectors))
                field_vars[field] = field_var
                tk.Entry(scrollable_frame, textvariable=field_var, width=70).grid(row=row, column=1, sticky=tk.W, pady=5)
                row += 1
            
            # 保存按钮
            def save_selectors():
                # 构建新的选择器配置
                new_selectors = {
                    'article_links': [s.strip() for s in link_selectors_var.get().split(',')],
                    'article_detail': {}
                }
                
                # 添加详情页选择器
                for field, var in field_vars.items():
                    new_selectors['article_detail'][field] = [s.strip() for s in var.get().split(',')]
                
                # 保存选择器
                config_manager.add_website(website_name, url, selectors=new_selectors, auto_analyze=False)
                messagebox.showinfo("提示", "选择器保存成功")
                selector_window.destroy()
            
            save_btn = tk.Button(scrollable_frame, text="保存选择器", command=save_selectors, 
                               bg='#4CAF50', fg='white', font=('微软雅黑', 10, 'bold'), padx=20, pady=8)
            save_btn.grid(row=row, column=0, columnspan=2, pady=20)
        
        # 保存按钮
        def save_source():
            # 先添加到Scrapling配置，获取选择器
            config_manager = ScraplingConfigManager()
            selectors = config_manager.add_website(name_var.get(), url_var.get())
            
            # 构建source_config
            source_config = {
                "name": name_var.get(),
                "url": url_var.get(),
                "max_articles": int(max_articles_var.get()),
                "interval": int(interval_var.get()),
                "enabled": enabled_var.get(),
                "selectors": selectors  # 添加选择器
            }
            
            # 验证
            errors = self.source_manager.validate_source(source_config)
            if errors:
                messagebox.showerror("错误", "\n".join(errors))
                return
            
            if source:
                # 更新现有源
                source_config['id'] = source['id']
                self.source_manager.update_source(source['id'], source_config)
            else:
                # 添加新源
                self.source_manager.add_source(source_config)
            
            self.load_sources()
            dialog.destroy()
            messagebox.showinfo("提示", "保存成功，已加入自动采集作业")
        
        # 按钮框架
        button_frame = tk.Frame(form_frame)
        button_frame.grid(row=7, column=0, columnspan=3, pady=20)
        
        edit_selectors_btn = tk.Button(button_frame, text="⚙️ 编辑选择器", command=edit_selectors, 
                                    bg='#9C27B0', fg='white', font=('微软雅黑', 10, 'bold'), padx=20, pady=8)
        edit_selectors_btn.pack(side=tk.LEFT, padx=5)
        
        test_btn = tk.Button(button_frame, text="🧪 测试", command=test_source, 
                           bg='#FF9800', fg='white', font=('微软雅黑', 10, 'bold'), padx=20, pady=8)
        test_btn.pack(side=tk.LEFT, padx=5)
        
        save_btn = tk.Button(button_frame, text="💾 保存", command=save_source, 
                           bg='#4CAF50', fg='white', font=('微软雅黑', 10, 'bold'), padx=20, pady=8)
        save_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = tk.Button(button_frame, text="取消", command=dialog.destroy, 
                             bg='#9E9E9E', fg='white', font=('微软雅黑', 10, 'bold'), padx=20, pady=8)
        cancel_btn.pack(side=tk.LEFT, padx=5)
    
    def analyze_source(self, url_var, analysis_text):
        """分析信息源"""
        url = url_var.get()
        if not url:
            messagebox.showinfo("提示", "请先输入URL")
            return
        
        # 显示分析状态
        analysis_text.delete(1.0, tk.END)
        analysis_text.insert(tk.END, "正在分析网站结构...\n")
        self.config_window.update()
        
        # 启动分析线程
        def analyze_thread():
            try:
                # 创建配置管理器
                config_manager = ScraplingConfigManager()
                # 分析网站结构
                selectors = config_manager.analyze_website(url)
                
                # 显示分析结果
                analysis_text.delete(1.0, tk.END)
                analysis_text.insert(tk.END, "分析完成！\n\n")
                analysis_text.insert(tk.END, "提取的选择器:\n")
                analysis_text.insert(tk.END, f"文章链接选择器: {', '.join(selectors.get('article_links', []))}\n\n")
                analysis_text.insert(tk.END, "详情页选择器:\n")
                for field, field_selectors in selectors.get('article_detail', {}).items():
                    analysis_text.insert(tk.END, f"  {field}: {', '.join(field_selectors)}\n")
                analysis_text.insert(tk.END, "\n建议: 点击测试按钮验证采集功能")
                
                # 显示相关网址列表
                related_urls = selectors.get('related_urls', [])
                if related_urls:
                    self.show_related_urls(related_urls)
            except Exception as e:
                analysis_text.delete(1.0, tk.END)
                analysis_text.insert(tk.END, f"分析失败: {str(e)}")
        
        threading.Thread(target=analyze_thread, daemon=True).start()
    
    def show_related_urls(self, related_urls):
        """显示相关网址列表并让用户选择"""
        if not related_urls:
            return
        
        # 创建网址选择窗口
        url_window = tk.Toplevel(self.config_window)
        url_window.title("相关网址选择")
        url_window.geometry("900x600")
        url_window.resizable(True, True)
        
        # 创建滚动区域
        canvas = tk.Canvas(url_window)
        scrollbar = ttk.Scrollbar(url_window, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 标题
        tk.Label(scrollable_frame, text="请选择相关的网址:", font=('微软雅黑', 12, 'bold')).grid(row=0, column=0, columnspan=4, pady=10)
        
        # 表头
        tk.Label(scrollable_frame, text="选择", font=('微软雅黑', 10, 'bold')).grid(row=1, column=0, padx=10)
        tk.Label(scrollable_frame, text="网址", font=('微软雅黑', 10, 'bold')).grid(row=1, column=1, padx=10)
        tk.Label(scrollable_frame, text="标题", font=('微软雅黑', 10, 'bold')).grid(row=1, column=2, padx=10)
        tk.Label(scrollable_frame, text="选择器", font=('微软雅黑', 10, 'bold')).grid(row=1, column=3, padx=10)
        
        # 选择框变量
        selected_urls = []
        check_vars = []
        
        # 显示网址列表
        for i, url_info in enumerate(related_urls, 2):
            var = tk.BooleanVar()
            check_vars.append(var)
            
            tk.Checkbutton(scrollable_frame, variable=var).grid(row=i, column=0, padx=10)
            tk.Label(scrollable_frame, text=url_info['url'], font=('微软雅黑', 10), wraplength=300).grid(row=i, column=1, padx=10, sticky=tk.W)
            tk.Label(scrollable_frame, text=url_info['text'], font=('微软雅黑', 10), wraplength=200).grid(row=i, column=2, padx=10, sticky=tk.W)
            tk.Label(scrollable_frame, text=url_info['selector'], font=('微软雅黑', 10), wraplength=150).grid(row=i, column=3, padx=10, sticky=tk.W)
        
        # 保存按钮
        def save_selections():
            # 收集选中的网址
            for i, var in enumerate(check_vars):
                if var.get():
                    selected_urls.append(related_urls[i])
            
            # 保存选择结果
            if selected_urls:
                # 这里可以将选择结果保存到配置中
                print(f"用户选择了 {len(selected_urls)} 个网址")
                messagebox.showinfo("提示", f"已保存 {len(selected_urls)} 个选中的网址")
            else:
                messagebox.showinfo("提示", "未选择任何网址")
            
            url_window.destroy()
        
        # 按钮框架
        button_frame = tk.Frame(scrollable_frame)
        button_frame.grid(row=len(related_urls) + 2, column=0, columnspan=4, pady=20)
        
        save_btn = tk.Button(button_frame, text="保存选择", command=save_selections, 
                           bg='#4CAF50', fg='white', font=('微软雅黑', 10, 'bold'), padx=20, pady=8)
        save_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = tk.Button(button_frame, text="取消", command=url_window.destroy, 
                             bg='#9E9E9E', fg='white', font=('微软雅黑', 10, 'bold'), padx=20, pady=8)
        cancel_btn.pack(side=tk.LEFT, padx=5)

    def save_global_settings(self):
        """保存全局设置"""
        try:
            global_config = {
                "default_interval": int(self.default_interval_var.get()),
                "max_concurrent": int(self.max_concurrent_var.get()),
                "timeout": int(self.timeout_var.get())
            }
            
            self.source_manager.global_config = global_config
            self.source_manager.save_config()
            messagebox.showinfo("提示", "保存成功")
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")

if __name__ == "__main__":
    root = tk.Tk()
    root.title("配置管理测试")
    root.geometry("400x300")
    
    def open_config():
        config_gui = ConfigGUI(root)
        config_gui.open_config_window()
    
    btn = tk.Button(root, text="打开配置管理", command=open_config, 
                   bg='#2196F3', fg='white', font=('微软雅黑', 12, 'bold'), padx=20, pady=10)
    btn.pack(expand=True, fill=tk.BOTH, padx=50, pady=50)
    
    root.mainloop()