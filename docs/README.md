# 韭研公社文章管理器

## 项目简介
一个自动化的桌面应用程序，用于定时采集、管理和分析韭研公社的文章。

## 核心功能
- ⏰ **定时采集**：每 30 分钟自动采集最新文章
- 💾 **增量存储**：自动去重，只保存新文章
- 🔍 **搜索筛选**：支持关键词和时间范围筛选
- 📤 **导出分享**：支持 JSON、Markdown 格式导出
- 📊 **数据统计**：作者统计、日期统计等分析功能

## 快速开始

### 1. 首次登录
```bash
python login_save_cookies.py
```
手动登录后，Cookie 会自动保存。

### 2. 启动程序
```bash
python article_manager_gui.py
```
程序启动后会自动执行第一次采集，之后每 30 分钟自动采集一次。

## 项目结构
```
JC/
├── article_manager_gui.py      # GUI 主程序
├── collect_broadcast_stable.py # 采集脚本
├── login_save_cookies.py       # 登录工具
├── clean_project.py            # 清理工具
├── cookies.json                # 登录凭证（敏感）
├── articles_database.json      # 文章数据库
├── 使用说明.md                  # 详细使用说明
└── README.md                   # 本文件
```

## 常用命令

### 清理历史数据
```bash
python clean_project.py
```

### 手动采集
在 GUI 界面点击"🔄 采集最新 10 篇"按钮

## 依赖
- Python 3.8+
- Playwright
- Schedule

## 注意事项
- 不要分享 `cookies.json` 文件（包含登录凭证）
- 定期备份 `articles_database.json` 和 `cookies.json`
- 首次启动时会自动执行一次采集

---
**开发时间**：2026-03-19  
**版本**：v1.0
