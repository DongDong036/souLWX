"""
股票识别与映射模块
提供股票代码和名称的双向映射功能
"""

import re
import requests
from difflib import get_close_matches

class StockRecognizer:
    def __init__(self):
        # 初始化股票映射数据
        self.stock_mapping = self._load_stock_mapping()
        self.code_to_name_mapping = {v: k for k, v in self.stock_mapping.items()}
    
    def _load_stock_mapping(self):
        """加载股票映射数据"""
        # 基础股票映射
        stock_mapping = {
            # 算力相关
            '奥瑞德': '600666',
            '昆仑万维': '300418',
            '泰豪科技': '600590',
            '东方国信': '300166',
            '利通电子': '603629',
            '中国能建': '601868',
            '宁波建工': '601789',
            '豫能控股': '001896',
            '中电鑫龙': '002298',
            
            # 科技相关
            '沪电股份': '002463',
            '金安国纪': '002636',
            '佰维存储': '688525',
            '德明利': '001309',
            '凯德石英': '688553',
            '思源电气': '002028',
            '中新集团': '601512',
            '大连电瓷': '002606',
            
            # 能源相关
            '金开新能': '600821',
            '首航新能': '300665',
            '铁龙物流': '600125',
            '协鑫能科': '002015',
            '华电能源': '600726',
            '粤电力A': '000539',
            
            # 新增常用股票
            '银之杰': '300085',
            '赢时胜': '300377',
            '中信证券': '600030',
            '同花顺': '300033',
            '东方财富': '300059',
            '迈为股份': '300751',
            '捷佳伟创': '300724',
            '上能电气': '300827',
            '美埃科技': '688376',
            '美光科技': 'MU',
            '英伟达': 'NVDA',
            '特斯拉': 'TSLA',
            '苹果': 'AAPL',
            '微软': 'MSFT',
            '亚马逊': 'AMZN',
            '谷歌': 'GOOGL',
            '脸书': 'META',
            '阿里巴巴': 'BABA',
            '腾讯控股': '0700',
            '台积电': '2330',
            '三星电子': '005930',
            '宁德时代': '300750',
            '比亚迪': '002594',
            '隆基绿能': '601012',
            '阳光电源': '300274',
            '通威股份': '600438',
            '中环股份': '002129',
            '晶澳科技': '002459',
            '天合光能': '688599',
            '福斯特': '603806',
            '福莱特': '601865',
            '信义光能': '0968',
            '先导智能': '300450',
            '杭可科技': '688006',
            '赢合科技': '300457',
            '科达利': '002850',
            '恩捷股份': '002812',
            '璞泰来': '603659',
            '杉杉股份': '600884',
            '宁德时代': '300750',
            '比亚迪': '002594',
            '亿纬锂能': '300014',
            '国轩高科': '002074',
            '孚能科技': '688567',
            '容百科技': '688005',
            '当升科技': '300073',
            '杉杉股份': '600884',
            '科达利': '002850',
            '先导智能': '300450',
            '杭可科技': '688006',
            '赢合科技': '300457',
            '宁德时代': '300750',
            '比亚迪': '002594',
            '亿纬锂能': '300014',
            '国轩高科': '002074',
            '孚能科技': '688567',
            '容百科技': '688005',
            '当升科技': '300073',
            '杉杉股份': '600884',
            '科达利': '002850',
            '先导智能': '300450',
            '杭可科技': '688006',
            '赢合科技': '300457',
            '宁德时代': '300750',
            '比亚迪': '002594',
            '亿纬锂能': '300014',
            '国轩高科': '002074',
            '孚能科技': '688567',
            '容百科技': '688005',
            '当升科技': '300073',
            '杉杉股份': '600884',
            '科达利': '002850',
            '先导智能': '300450',
            '杭可科技': '688006',
            '赢合科技': '300457',
            '宁德时代': '300750',
            '比亚迪': '002594',
            '亿纬锂能': '300014',
            '国轩高科': '002074',
            '孚能科技': '688567',
            '容百科技': '688005',
            '当升科技': '300073',
            '杉杉股份': '600884',
            '科达利': '002850',
            '先导智能': '300450',
            '杭可科技': '688006',
            '赢合科技': '300457',
            '宁德时代': '300750',
            '比亚迪': '002594',
            '亿纬锂能': '300014',
            '国轩高科': '002074',
            '孚能科技': '688567',
            '容百科技': '688005',
            '当升科技': '300073',
            '杉杉股份': '600884',
            '科达利': '002850',
            '先导智能': '300450',
            '杭可科技': '688006',
            '赢合科技': '300457'
        }
        return stock_mapping
    
    def recognize_stocks(self, content):
        """识别文章中的股票"""
        stocks = []
        code_set = set()
        
        # 1. 识别股票代码
        stock_codes = self._extract_stock_codes(content)
        for code in stock_codes:
            stock_info = self._get_stock_by_code(code)
            if stock_info and stock_info['code'] not in code_set:
                code_set.add(stock_info['code'])
                stocks.append(stock_info)
        
        # 2. 识别股票名称
        stock_names = self._extract_stock_names(content)
        for name in stock_names:
            stock_info = self._get_stock_by_name(name)
            if stock_info and stock_info['code'] not in code_set:
                code_set.add(stock_info['code'])
                stocks.append(stock_info)
        
        return stocks
    
    def _extract_stock_codes(self, content):
        """提取股票代码"""
        # 匹配6位数字的股票代码，可能带有SH/SZ前缀
        pattern = r'(?:SH|SZ)?\d{6}'
        codes = re.findall(pattern, content)
        
        # 标准化代码
        standardized_codes = []
        for code in codes:
            # 移除前缀，只保留数字
            code = code.upper().replace('SH', '').replace('SZ', '')
            if len(code) == 6 and code.isdigit():
                standardized_codes.append(code)
        
        return list(set(standardized_codes))
    
    def _extract_stock_names(self, content):
        """提取股票名称"""
        found_names = []
        
        # 直接匹配
        for stock_name in self.stock_mapping:
            if stock_name in content:
                found_names.append(stock_name)
        
        # 模糊匹配（处理可能的错别字或简称）
        content_words = re.findall(r'[\u4e00-\u9fa5]{2,8}', content)
        for word in content_words:
            if len(word) >= 2:
                matches = get_close_matches(word, self.stock_mapping.keys(), n=3, cutoff=0.7)
                for match in matches:
                    if match not in found_names:
                        found_names.append(match)
        
        return found_names
    
    def _get_stock_by_code(self, code):
        """通过代码获取股票信息"""
        if code in self.code_to_name_mapping:
            return {
                'name': self.code_to_name_mapping[code],
                'code': code
            }
        
        # 尝试通过API查询
        try:
            stock_info = self._query_stock_by_code(code)
            if stock_info:
                return stock_info
        except Exception:
            pass
        
        return None
    
    def _get_stock_by_name(self, name):
        """通过名称获取股票信息"""
        if name in self.stock_mapping:
            return {
                'name': name,
                'code': self.stock_mapping[name]
            }
        
        # 尝试通过API查询
        try:
            stock_info = self._query_stock_by_name(name)
            if stock_info:
                return stock_info
        except Exception:
            pass
        
        return None
    
    def _query_stock_by_code(self, code):
        """通过API查询股票信息"""
        # 腾讯证券API
        try:
            url = f"https://qt.gtimg.cn/q={code}"
            response = requests.get(url, timeout=3)
            response.encoding = 'gbk'
            
            content = response.text
            if content.startswith('v_') and '~' in content:
                data = content.split('=')[1].strip(';')
                stock_info = data.split('~')
                
                if len(stock_info) > 3 and stock_info[1]:
                    return {
                        'name': stock_info[1],
                        'code': stock_info[2]
                    }
        except Exception:
            pass
        
        return None
    
    def _query_stock_by_name(self, name):
        """通过名称查询股票信息"""
        # 这里可以添加通过名称查询的API
        # 暂时返回None，使用本地映射
        return None
    
    def get_suggestions(self, text):
        """获取股票建议"""
        suggestions = []
        
        # 检查是否是代码
        text = text.strip()
        if re.match(r'^\d{6}$', text):
            stock = self._get_stock_by_code(text)
            if stock:
                suggestions.append(stock)
        
        # 检查是否是名称
        elif re.match(r'^[\u4e00-\u9fa5]+$', text):
            stock = self._get_stock_by_name(text)
            if stock:
                suggestions.append(stock)
            else:
                # 模糊匹配
                matches = get_close_matches(text, self.stock_mapping.keys(), n=5, cutoff=0.6)
                for match in matches:
                    suggestions.append({
                        'name': match,
                        'code': self.stock_mapping[match]
                    })
        
        return suggestions

# 测试
if __name__ == "__main__":
    recognizer = StockRecognizer()
    
    # 测试识别
    test_content = "银之杰（300085）连续走出11根阳线，比亚迪和宁德时代表现不错"
    stocks = recognizer.recognize_stocks(test_content)
    print("识别结果:")
    for stock in stocks:
        print(f"{stock['name']} ({stock['code']})")
    
    # 测试建议
    print("\n建议测试:")
    suggestions = recognizer.get_suggestions("银之杰")
    for suggestion in suggestions:
        print(f"{suggestion['name']} ({suggestion['code']})")
    
    suggestions = recognizer.get_suggestions("300085")
    for suggestion in suggestions:
        print(f"{suggestion['name']} ({suggestion['code']})")
    
    suggestions = recognizer.get_suggestions("比亚迪")
    for suggestion in suggestions:
        print(f"{suggestion['name']} ({suggestion['code']})")