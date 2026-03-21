"""
配置管理界面
包含信息源管理、定时任务设置等功能
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from source_manager import SourceManager

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
        columns = ('id', 'name', 'url', 'type', 'enabled', 'interval')
        self.sources_tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        # 配置列
        self.sources_tree.heading('id', text='ID', anchor=tk.CENTER)
        self.sources_tree.heading('name', text='名称', anchor=tk.W)
        self.sources_tree.heading('url', text='URL', anchor=tk.W)
        self.sources_tree.heading('type', text='类型', anchor=tk.CENTER)
        self.sources_tree.heading('enabled', text='状态', anchor=tk.CENTER)
        self.sources_tree.heading('interval', text='采集间隔(分钟)', anchor=tk.CENTER)
        
        # 设置列宽
        self.sources_tree.column('id', width=100, anchor=tk.CENTER)
        self.sources_tree.column('name', width=120, anchor=tk.W)
        self.sources_tree.column('url', width=300, anchor=tk.W)
        self.sources_tree.column('type', width=80, anchor=tk.CENTER)
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
                source.get('type'),
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
        tk.Entry(form_frame, textvariable=url_var, width=40).grid(row=1, column=1, sticky=tk.W, pady=10)
        
        # 类型
        tk.Label(form_frame, text="类型:", font=('微软雅黑', 10)).grid(row=2, column=0, sticky=tk.W, pady=10)
        type_var = tk.StringVar(value=source.get('type', 'community') if source else 'community')
        type_options = ['community', 'news', 'blog', 'forum']
        ttk.Combobox(form_frame, textvariable=type_var, values=type_options, width=37).grid(row=2, column=1, sticky=tk.W, pady=10)
        
        # 最大文章数
        tk.Label(form_frame, text="最大文章数:", font=('微软雅黑', 10)).grid(row=3, column=0, sticky=tk.W, pady=10)
        max_articles_var = tk.StringVar(value=str(source.get('max_articles', 10)) if source else '10')
        tk.Entry(form_frame, textvariable=max_articles_var, width=10).grid(row=3, column=1, sticky=tk.W, pady=10)
        
        # 采集间隔
        tk.Label(form_frame, text="采集间隔（分钟）:", font=('微软雅黑', 10)).grid(row=4, column=0, sticky=tk.W, pady=10)
        interval_var = tk.StringVar(value=str(source.get('interval', 30)) if source else '30')
        tk.Entry(form_frame, textvariable=interval_var, width=10).grid(row=4, column=1, sticky=tk.W, pady=10)
        
        # 启用状态
        enabled_var = tk.BooleanVar(value=source.get('enabled', True) if source else True)
        tk.Checkbutton(form_frame, text="启用", variable=enabled_var, font=('微软雅黑', 10)).grid(row=5, column=1, sticky=tk.W, pady=10)
        
        # 保存按钮
        def save_source():
            source_config = {
                "name": name_var.get(),
                "url": url_var.get(),
                "type": type_var.get(),
                "max_articles": int(max_articles_var.get()),
                "interval": int(interval_var.get()),
                "enabled": enabled_var.get()
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
            messagebox.showinfo("提示", "保存成功")
        
        save_btn = tk.Button(form_frame, text="💾 保存", command=save_source, 
                           bg='#4CAF50', fg='white', font=('微软雅黑', 10, 'bold'), padx=20, pady=8)
        save_btn.grid(row=6, column=0, columnspan=2, pady=20)
    
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