"""
DEEPSEEK API交互模块
功能：
- DEEPSEEK API调用
- 文章分析
- 股票识别
- API配置管理
"""

import requests
import json
import os
from logger import log_app, log_error
from config_manager import load_config, save_config

class DeepSeekAPI:
    def __init__(self):
        """初始化DEEPSEEK API客户端"""
        self.api_key = self._load_api_key()
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        log_app("DEEPSEEK API客户端初始化完成")
    
    def _load_api_key(self):
        """
        加载API Key
        
        Returns:
            str: API Key
        """
        # 尝试从配置文件加载
        api_key_file = 'config/deepseek_api_key.json'
        if os.path.exists(api_key_file):
            try:
                with open(api_key_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('api_key', '')
            except Exception as e:
                log_error(f"加载API Key失败：{str(e)}")
        return ''
    
    def set_api_key(self, api_key):
        """
        设置API Key
        
        Args:
            api_key: API Key
        
        Returns:
            bool: 是否成功
        """
        try:
            self.api_key = api_key
            self.headers['Authorization'] = f"Bearer {api_key}"
            
            # 保存到配置文件
            api_key_file = 'config/deepseek_api_key.json'
            os.makedirs('config', exist_ok=True)
            with open(api_key_file, 'w', encoding='utf-8') as f:
                json.dump({'api_key': api_key}, f, ensure_ascii=False, indent=2)
            
            # 添加到.gitignore
            self._add_to_gitignore()
            
            log_app("API Key设置成功")
            return True
        except Exception as e:
            log_error(f"设置API Key失败：{str(e)}")
            return False
    
    def _add_to_gitignore(self):
        """
        将API Key文件添加到.gitignore
        """
        gitignore_path = '.gitignore'
        api_key_file = 'config/deepseek_api_key.json'
        
        if os.path.exists(gitignore_path):
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if api_key_file not in content:
                with open(gitignore_path, 'a', encoding='utf-8') as f:
                    f.write(f'\n{api_key_file}\n')
        else:
            with open(gitignore_path, 'w', encoding='utf-8') as f:
                f.write(f'{api_key_file}\n')
    
    def test_api_connection(self):
        """
        测试API连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            test_message = "测试API连接"
            response = self.chat_completion(test_message)
            return response is not None
        except Exception as e:
            log_error(f"API连接测试失败：{str(e)}")
            return False
    
    def chat_completion(self, message, model="deepseek-chat", max_tokens=1000, temperature=0.7):
        """
        调用Chat Completion API
        
        Args:
            message: 消息内容
            model: 模型名称
            max_tokens: 最大 tokens
            temperature: 温度
        
        Returns:
            str: 响应内容
        """
        try:
            payload = {
                "model": model,
                "messages": [
                    {"role": "user", "content": message}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            response.raise_for_status()
            data = response.json()
            
            if 'choices' in data and len(data['choices']) > 0:
                return data['choices'][0]['message']['content']
            return None
            
        except Exception as e:
            log_error(f"API调用失败：{str(e)}")
            return None
    
    def analyze_article(self, article_content):
        """
        分析文章内容
        
        Args:
            article_content: 文章内容
        
        Returns:
            dict: 分析结果
        """
        try:
            prompt = f"""请分析以下文章内容，提供：
1. 文章主题和核心观点
2. 关键信息提取
3. 相关股票识别（如果有）
4. 内容摘要

文章内容：
{article_content[:3000]}..."""
            
            response = self.chat_completion(prompt, max_tokens=2000)
            
            if response:
                # 解析响应
                analysis_result = self._parse_analysis_response(response)
                return analysis_result
            return None
            
        except Exception as e:
            log_error(f"文章分析失败：{str(e)}")
            return None
    
    def _parse_analysis_response(self, response):
        """
        解析分析响应
        
        Args:
            response: API响应内容
        
        Returns:
            dict: 解析结果
        """
        # 简单解析，实际应用中可以使用更复杂的解析逻辑
        lines = response.split('\n')
        result = {
            'topic': '',
            'key_points': [],
            'stocks': [],
            'summary': ''
        }
        
        current_section = None
        for line in lines:
            line = line.strip()
            if '主题' in line or '核心观点' in line:
                current_section = 'topic'
            elif '关键信息' in line:
                current_section = 'key_points'
            elif '股票' in line:
                current_section = 'stocks'
            elif '摘要' in line:
                current_section = 'summary'
            elif line and current_section:
                if current_section == 'key_points':
                    result['key_points'].append(line)
                elif current_section == 'stocks':
                    # 提取股票代码
                    import re
                    stock_codes = re.findall(r'(?:SZ|SH)?\d{6}', line)
                    for code in stock_codes:
                        code = code.upper()
                        if len(code) == 6:
                            if code.startswith('6'):
                                result['stocks'].append(f'SH{code}')
                            else:
                                result['stocks'].append(f'SZ{code}')
                        else:
                            result['stocks'].append(code)
                elif current_section == 'summary':
                    result['summary'] += line + ' '
                elif current_section == 'topic':
                    result['topic'] += line + ' '
        
        # 去重股票
        result['stocks'] = list(set(result['stocks']))
        
        return result
    
    def identify_stocks(self, content):
        """
        从内容中识别股票
        
        Args:
            content: 文本内容
        
        Returns:
            list: 识别的股票代码
        """
        try:
            prompt = f"""请从以下内容中识别出所有股票代码，并以JSON格式返回：
{content[:2000]}..."""
            
            response = self.chat_completion(prompt, max_tokens=500)
            
            if response:
                # 尝试解析JSON
                try:
                    import re
                    # 提取JSON部分
                    json_match = re.search(r'\{[^}]*\}', response)
                    if json_match:
                        stock_data = json.loads(json_match.group(0))
                        return stock_data.get('stocks', [])
                except Exception:
                    # 如果JSON解析失败，使用正则提取
                    stock_codes = re.findall(r'(?:SZ|SH)?\d{6}', response)
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
                    return list(set(standardized_codes))
            return []
            
        except Exception as e:
            log_error(f"股票识别失败：{str(e)}")
            return []

# 全局实例
deepseek_api = DeepSeekAPI()

if __name__ == '__main__':
    # 测试DEEPSEEK API
    api = DeepSeekAPI()
    
    # 测试API连接
    print("测试API连接...")
    connected = api.test_api_connection()
    print(f"API连接状态：{connected}")
    
    # 测试文章分析
    test_content = """近日，人工智能概念股持续走强，其中昆仑万维（300418）、佰维存储（688525）等个股表现突出。分析师认为，随着AI技术的不断发展，相关产业链公司有望持续受益。"""
    
    print("\n测试文章分析...")
    analysis = api.analyze_article(test_content)
    if analysis:
        print(f"主题：{analysis['topic']}")
        print(f"关键信息：{analysis['key_points']}")
        print(f"识别的股票：{analysis['stocks']}")
        print(f"摘要：{analysis['summary']}")
    else:
        print("文章分析失败")
    
    # 测试股票识别
    print("\n测试股票识别...")
    stocks = api.identify_stocks(test_content)
    print(f"识别的股票：{stocks}")