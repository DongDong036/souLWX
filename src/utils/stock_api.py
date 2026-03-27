"""
股票API模块
功能：
- 通过股票名称查询股票代码
- 股票代码验证和标准化
- 股票信息缓存
"""

import requests
import json
import os
from datetime import datetime, timedelta

# 简单的日志函数
def log_app(message):
    print(f"[INFO] {message}")

def log_error(message):
    print(f"[ERROR] {message}")

class StockAPI:
    def __init__(self):
        """初始化股票API"""
        self.cache_file = 'data/cache/stock_cache.json'
        self.cache = {}
        self.cache_expiry = 7  # 缓存过期时间（天）
        self._load_cache()
        log_app("股票API初始化完成")
    
    def _load_cache(self):
        """
        加载股票缓存
        """
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 检查缓存是否过期
                    if 'last_update' in data:
                        last_update = datetime.fromisoformat(data['last_update'])
                        if datetime.now() - last_update < timedelta(days=self.cache_expiry):
                            self.cache = data.get('cache', {})
                            log_app(f"已加载股票缓存，共 {len(self.cache)} 条记录")
        except Exception as e:
            log_error(f"加载股票缓存失败：{str(e)}")
            self.cache = {}
    
    def _save_cache(self):
        """
        保存股票缓存
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            
            data = {
                'last_update': datetime.now().isoformat(),
                'cache': self.cache
            }
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            log_app(f"已保存股票缓存，共 {len(self.cache)} 条记录")
        except Exception as e:
            log_error(f"保存股票缓存失败：{str(e)}")
    
    def get_stock_code(self, stock_name):
        """
        通过股票名称查询股票代码
        
        Args:
            stock_name: 股票名称
        
        Returns:
            str: 股票代码，如 'SH600000'，如果未找到返回 None
        """
        # 先检查缓存
        if stock_name in self.cache:
            log_app(f"从缓存获取股票代码：{stock_name} -> {self.cache[stock_name]}")
            return self.cache[stock_name]
        
        # 尝试使用新浪财经API
        try:
            code = self._query_sina_finance(stock_name)
            if code:
                self.cache[stock_name] = code
                self._save_cache()
                log_app(f"查询到股票代码：{stock_name} -> {code}")
                return code
        except Exception as e:
            log_error(f"新浪财经API查询失败：{str(e)}")
        
        # 尝试使用东方财富API
        try:
            code = self._query_eastmoney(stock_name)
            if code:
                self.cache[stock_name] = code
                self._save_cache()
                log_app(f"查询到股票代码：{stock_name} -> {code}")
                return code
        except Exception as e:
            log_error(f"东方财富API查询失败：{str(e)}")
        
        # 尝试使用和讯财经API
        try:
            code = self._query_hexun(stock_name)
            if code:
                self.cache[stock_name] = code
                self._save_cache()
                log_app(f"查询到股票代码：{stock_name} -> {code}")
                return code
        except Exception as e:
            log_error(f"和讯财经API查询失败：{str(e)}")
        
        # 内置股票代码映射
        stock_mapping = {
            '浦发银行': 'SH600000',
            '贵州茅台': 'SH600519',
            '宁德时代': 'SZ300750',
            '比亚迪': 'SZ002594',
            '中国平安': 'SH601318',
            '招商银行': 'SH600036',
            '工商银行': 'SH601398',
            '中国石油': 'SH601857',
            '腾讯控股': 'HK00700',
            '阿里巴巴': 'HK09988',
            '中超控股': 'SZ002471',
            '再升科技': 'SH603601',
            '西测测试': 'SZ301306',
            '西部材料': 'SZ002149',
            '铖昌科技': 'SZ001270',
            '*ST铖昌': 'SZ001270'
        }
        
        if stock_name in stock_mapping:
            code = stock_mapping[stock_name]
            self.cache[stock_name] = code
            self._save_cache()
            log_app(f"从内置映射获取股票代码：{stock_name} -> {code}")
            return code
        
        log_app(f"未找到股票代码：{stock_name}")
        return None
    
    def _query_sina_finance(self, stock_name):
        """
        使用新浪财经API查询股票代码
        
        Args:
            stock_name: 股票名称
        
        Returns:
            str: 股票代码，如 'SH600000'，如果未找到返回 None
        """
        import urllib.parse
        url = f"http://suggest3.sinajs.cn/suggest/type=11&key={urllib.parse.quote(stock_name)}"
        try:
            response = requests.get(url, timeout=5, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.encoding = 'gbk'
            content = response.text
            
            # 解析响应
            if 'result' in content:
                import re
                match = re.search(r'result":\[\[("[^"]*"),"[^"]*","([^"]*)"\]\]', content)
                if match:
                    code = match.group(1).strip('"')
                    market = match.group(2)
                    if market == 'sh':
                        return f'SH{code}'
                    elif market == 'sz':
                        return f'SZ{code}'
        except Exception as e:
            log_error(f"新浪财经API查询失败：{str(e)}")
        return None
    
    def _query_eastmoney(self, stock_name):
        """
        使用东方财富API查询股票代码
        
        Args:
            stock_name: 股票名称
        
        Returns:
            str: 股票代码，如 'SH600000'，如果未找到返回 None
        """
        url = "http://nufm.dfcfw.com/EM_Finance2014NumericApplication/JS.aspx"
        params = {
            'type': 'CT',
            'st': '1',
            'sr': '1',
            'p': '1',
            'ps': '10',
            'js': 'var _nt={pages:(pc),data:[(x)]}',
            'token': '4f1862fc3b5e77c150a2b985b12db0fd',
            'cmd': f'C.{stock_name}',
            'sty': 'FCOI'
        }
        
        try:
            response = requests.get(url, params=params, timeout=5, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.encoding = 'utf-8'
            content = response.text
            
            # 解析响应
            import re
            match = re.search(r'data:\[(.*?)\]', content)
            if match:
                data_str = match.group(1)
                items = data_str.split('","')
                if items:
                    # 格式："600000|浦发银行|SH"
                    item = items[0].strip('"')
                    parts = item.split('|')
                    if len(parts) >= 3:
                        code = parts[0]
                        market = parts[2]
                        if market == 'SH':
                            return f'SH{code}'
                        elif market == 'SZ':
                            return f'SZ{code}'
        except Exception as e:
            log_error(f"东方财富API查询失败：{str(e)}")
        return None
    
    def _query_hexun(self, stock_name):
        """
        使用和讯财经API查询股票代码
        
        Args:
            stock_name: 股票名称
        
        Returns:
            str: 股票代码，如 'SH600000'，如果未找到返回 None
        """
        import urllib.parse
        url = f"http://so.hexun.com/suggest/?q={urllib.parse.quote(stock_name)}&t=1"
        try:
            response = requests.get(url, timeout=5, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.encoding = 'utf-8'
            content = response.text
            
            # 解析响应
            import re
            match = re.search(r'"code":"(\d{6})"', content)
            if match:
                code = match.group(1)
                if code.startswith('6'):
                    return f'SH{code}'
                else:
                    return f'SZ{code}'
        except Exception as e:
            log_error(f"和讯财经API查询失败：{str(e)}")
        return None
    
    def normalize_stock_code(self, code):
        """
        标准化股票代码
        
        Args:
            code: 股票代码，如 '600000' 或 'SH600000'
        
        Returns:
            str: 标准化的股票代码，如 'SH600000'
        """
        code = code.strip().upper()
        
        # 已经是标准化格式
        if code.startswith('SH') or code.startswith('SZ'):
            return code
        
        # 纯数字代码
        if code.isdigit() and len(code) == 6:
            if code.startswith('6'):
                return f'SH{code}'
            else:
                return f'SZ{code}'
        
        return code
    
    def validate_stock_code(self, code):
        """
        验证股票代码是否有效
        
        Args:
            code: 股票代码
        
        Returns:
            bool: 是否有效
        """
        code = self.normalize_stock_code(code)
        return (code.startswith('SH') or code.startswith('SZ')) and len(code) == 8 and code[2:].isdigit()

# 全局实例
stock_api = StockAPI()

if __name__ == '__main__':
    # 测试股票API
    api = StockAPI()
    
    test_stocks = ['浦发银行', '腾讯控股', '阿里巴巴', '贵州茅台', '宁德时代']
    
    print("测试股票API...")
    for stock_name in test_stocks:
        code = api.get_stock_code(stock_name)
        print(f"{stock_name}: {code}")
    
    # 测试缓存
    print("\n测试缓存...")
    for stock_name in test_stocks:
        code = api.get_stock_code(stock_name)
        print(f"{stock_name}: {code}")
    
    # 测试标准化
    print("\n测试代码标准化...")
    test_codes = ['600000', '000001', 'SH600000', 'SZ000001']
    for code in test_codes:
        normalized = api.normalize_stock_code(code)
        print(f"{code} -> {normalized}")
    
    # 测试验证
    print("\n测试代码验证...")
    test_codes = ['SH600000', 'SZ000001', '600000', '000001', 'invalid']
    for code in test_codes:
        valid = api.validate_stock_code(code)
        print(f"{code}: {valid}")
