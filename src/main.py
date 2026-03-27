"""热点与趋势系统主入口
功能：整合所有模块，提供统一的用户界面
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.article_manager_gui import ArticleManagerApp

def main():
    """主函数"""
    root = tk.Tk()
    app = ArticleManagerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
