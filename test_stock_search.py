import json
import re

# 加载文章数据
with open('data/database/broadcast_full.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

articles = data.get('messages', [])
print(f"文章数量: {len(articles)}")

# 测试股票搜索
def standardize_stock_code(code):
    code = code.upper().replace('SH', '').replace('SZ', '')
    if len(code) == 6 and code.isdigit():
        return code
    return code

def test_stock_search(stock_text):
    print(f"\n测试搜索: {stock_text}")
    standardized_stock = standardize_stock_code(stock_text)
    print(f"标准化后: {standardized_stock}")
    
    matching_articles = []
    
    for i, article in enumerate(articles):
        article_stocks = article.get('stocks', [])
        
        # 检查文章中的股票是否匹配
        stock_found = False
        for stock in article_stocks:
            if isinstance(stock, dict):
                # 检查股票代码
                stock_code = standardize_stock_code(stock.get('code', ''))
                if stock_code == standardized_stock:
                    stock_found = True
                    break
                # 检查股票名称
                stock_name = stock.get('name', '').lower()
                if stock_text.lower() in stock_name:
                    stock_found = True
                    break
            else:
                # 旧格式的股票数据
                stock_str = str(stock).lower()
                if standardized_stock.lower() in stock_str or stock_text.lower() in stock_str:
                    stock_found = True
                    break
        
        if stock_found:
            matching_articles.append((i, article.get('title', '')))
    
    print(f"找到 {len(matching_articles)} 篇匹配文章")
    for idx, title in matching_articles:
        print(f"  {idx+1}. {title[:50]}...")

# 测试搜索
test_stock_search('300274')
test_stock_search('阳光电源')
test_stock_search('300085')
test_stock_search('银之杰')

# 检查文章内容中是否提到阳光电源
print('\n检查文章内容中是否提到阳光电源:')
for i, article in enumerate(articles):
    content = article.get('content', '').lower()
    if '阳光电源' in content or '300274' in content:
        print(f"  文章 {i+1} 提到了阳光电源: {article.get('title', '')[:50]}...")
