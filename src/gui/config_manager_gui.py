"""配置管理界面
功能：管理网站配置、采集设置等
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
import sys

# 添加src目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collectors.scrapling_config import ScraplingConfigManager

class ConfigManagerGUI:
    def __init__(self, parent):
        self.parent = parent
        self.config_manager = ScraplingConfigManager()
        self.create_window()
    
    def create_window(self):
        """创建配置管理窗口"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("配置管理")
        self.window.geometry("800x600")
        
        # 创建主框架
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建网站列表
        self.create_website_list(main_frame)
        
        # 创建操作按钮
        self.create_buttons(main_frame)
    
    def create_website_list(self, parent):
        """创建网站列表"""
        # 创建框架
        list_frame = ttk.LabelFrame(parent, text="网站配置", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 创建树状视图
        columns = ("name", "url", "status", "updated")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        # 设置列标题
        self.tree.heading("name", text="网站名称")
        self.tree.heading("url", text="网站URL")
        self.tree.heading("status", text="状态")
        self.tree.heading("updated", text="最后更新")
        
        # 设置列宽
        self.tree.column("name", width=150)
        self.tree.column("url", width=300)
        self.tree.column("status", width=80)
        self.tree.column("updated", width=150)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # 加载网站列表
        self.load_website_list()
    
    def load_website_list(self):
        """加载网站列表"""
        # 清空树状视图
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 加载网站配置
        websites = self.config_manager.list_websites()
        for website in websites:
            config = self.config_manager.get_website_config(website)
            status = "启用" if config.get('enabled', True) else "禁用"
            updated = config.get('last_updated', '')
            url = config.get('url', '')
            
            self.tree.insert("", tk.END, values=(website, url, status, updated))
    
    def create_buttons(self, parent):
        """创建操作按钮"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=10)
        
        # 添加网站按钮
        add_button = ttk.Button(button_frame, text="添加网站", command=self.add_website)
        add_button.pack(side=tk.LEFT, padx=5)
        
        # 编辑网站按钮
        edit_button = ttk.Button(button_frame, text="编辑网站", command=self.edit_website)
        edit_button.pack(side=tk.LEFT, padx=5)
        
        # 删除网站按钮
        delete_button = ttk.Button(button_frame, text="删除网站", command=self.delete_website)
        delete_button.pack(side=tk.LEFT, padx=5)
        
        # 刷新按钮
        refresh_button = ttk.Button(button_frame, text="刷新", command=self.load_website_list)
        refresh_button.pack(side=tk.LEFT, padx=5)
        
        # 关闭按钮
        close_button = ttk.Button(button_frame, text="关闭", command=self.window.destroy)
        close_button.pack(side=tk.RIGHT, padx=5)
    
    def add_website(self):
        """添加网站"""
        # 获取网站名称和URL
        name = simpledialog.askstring("添加网站", "请输入网站名称:")
        if not name:
            return
        
        url = simpledialog.askstring("添加网站", "请输入网站URL:")
        if not url:
            return
        
        # 添加网站
        try:
            selectors = self.config_manager.add_website(name, url)
            messagebox.showinfo("成功", f"网站添加成功！\n提取的选择器已保存。")
            self.load_website_list()
        except Exception as e:
            messagebox.showerror("错误", f"添加网站失败: {str(e)}")
    
    def edit_website(self):
        """编辑网站"""
        # 获取选中的网站
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请选择一个网站进行编辑")
            return
        
        # 获取网站信息
        item = selected_item[0]
        values = self.tree.item(item, "values")
        name = values[0]
        url = values[1]
        
        # 编辑网站信息
        new_url = simpledialog.askstring("编辑网站", "请输入新的网站URL:", initialvalue=url)
        if new_url is not None:
            try:
                # 更新网站配置
                self.config_manager.update_website_config(name, {'url': new_url})
                
                # 询问是否重新分析
                if messagebox.askyesno("重新分析", "是否重新分析网站结构？"):
                    selectors = self.config_manager.analyze_website(new_url)
                    self.config_manager.update_website_config(name, {'selectors': selectors})
                    messagebox.showinfo("成功", "网站分析完成，选择器已更新。")
                
                messagebox.showinfo("成功", "网站更新成功！")
                self.load_website_list()
            except Exception as e:
                messagebox.showerror("错误", f"更新网站失败: {str(e)}")
    
    def delete_website(self):
        """删除网站"""
        # 获取选中的网站
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请选择一个网站进行删除")
            return
        
        # 获取网站信息
        item = selected_item[0]
        values = self.tree.item(item, "values")
        name = values[0]
        
        # 确认删除
        if messagebox.askyesno("删除网站", f"确定要删除网站 '{name}' 吗？"):
            try:
                success = self.config_manager.remove_website(name)
                if success:
                    messagebox.showinfo("成功", "网站删除成功！")
                    self.load_website_list()
                else:
                    messagebox.showerror("错误", "删除网站失败")
            except Exception as e:
                messagebox.showerror("错误", f"删除网站失败: {str(e)}")
