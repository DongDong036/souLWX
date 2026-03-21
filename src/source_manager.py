"""
信息源管理模块
用于管理不同的信息源配置
"""

import json
import os
from pathlib import Path

class SourceManager:
    def __init__(self, config_file='config/sources_config.json'):
        self.config_file = config_file
        self.sources = []
        self.global_config = {}
        self.load_config()
    
    def load_config(self):
        """加载信息源配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.sources = config.get('sources', [])
                self.global_config = config.get('global', {})
                print(f"[OK] 已加载 {len(self.sources)} 个信息源")
            else:
                self.create_default_config()
        except Exception as e:
            print(f"[ERROR] 加载配置失败：{e}")
            self.create_default_config()
    
    def create_default_config(self):
        """创建默认配置"""
        default_config = {
            "version": "1.0",
            "sources": [
                {
                    "id": "jiuyangongshe",
                    "name": "韭研公社",
                    "url": "https://www.jiuyangongshe.com/",
                    "enabled": True,
                    "type": "community",
                    "selectors": {
                        "article_links": [
                            '.jc-home-main .module',
                            '.action-main .module',
                            '.tab-content .item',
                            '.time-article-item',
                            '.community-bar li',
                            '.broadcast-list li',
                            '.message-list li'
                        ],
                        "title": "inner_text",
                        "content": [
                            '.text-box.text-justify.fsDetail',
                            '.text-box',
                            '.fsDetail',
                            '.pre',
                            '.expound',
                            '.article-content',
                            '.article-detail',
                            'section .text-box',
                            'section'
                        ],
                        "author": [
                            '.username-box .fs16-bold',
                            '.username-box .name .fs16-bold',
                            '.detail-container .fs16-bold',
                            '[data-v-234fd4b4].fs16-bold',
                            '.user-info .name',
                            '.author-name',
                            '.username',
                            '.user-name'
                        ],
                        "publish_time": [
                            '.username-box .date',
                            '.detail-container .date',
                            '[data-v-234fd4b4].date',
                            '.username-box .fs14',
                            '.publish-time',
                            '.time',
                            '.post-time'
                        ]
                    },
                    "max_articles": 10,
                    "interval": 30
                }
            ],
            "global": {
                "default_interval": 30,
                "max_concurrent": 3,
                "timeout": 60
            }
        }
        
        # 确保目录存在
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        
        self.sources = default_config['sources']
        self.global_config = default_config['global']
        print(f"[OK] 创建默认配置，包含 {len(self.sources)} 个信息源")
    
    def get_enabled_sources(self):
        """获取启用的信息源"""
        return [source for source in self.sources if source.get('enabled', True)]
    
    def add_source(self, source_config):
        """添加新的信息源"""
        # 生成唯一ID
        source_id = source_config.get('id') or self._generate_source_id(source_config.get('name', 'new_source'))
        source_config['id'] = source_id
        
        # 验证必填字段
        required_fields = ['name', 'url', 'type']
        for field in required_fields:
            if field not in source_config:
                raise ValueError(f"缺少必填字段：{field}")
        
        # 添加默认值
        source_config.setdefault('enabled', True)
        source_config.setdefault('selectors', {})
        source_config.setdefault('max_articles', 10)
        source_config.setdefault('interval', self.global_config.get('default_interval', 30))
        
        # 检查是否已存在
        existing_ids = [s['id'] for s in self.sources]
        if source_id in existing_ids:
            # 更新现有源
            for i, source in enumerate(self.sources):
                if source['id'] == source_id:
                    self.sources[i] = source_config
                    break
        else:
            # 添加新源
            self.sources.append(source_config)
        
        self.save_config()
        return source_id
    
    def remove_source(self, source_id):
        """移除信息源"""
        self.sources = [s for s in self.sources if s.get('id') != source_id]
        self.save_config()
    
    def update_source(self, source_id, updates):
        """更新信息源配置"""
        for i, source in enumerate(self.sources):
            if source.get('id') == source_id:
                source.update(updates)
                self.save_config()
                return True
        return False
    
    def save_config(self):
        """保存配置"""
        config = {
            "version": "1.0",
            "sources": self.sources,
            "global": self.global_config
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"[OK] 保存配置成功，共 {len(self.sources)} 个信息源")
    
    def _generate_source_id(self, name):
        """生成唯一的信息源ID"""
        import re
        # 生成基于名称的ID
        source_id = re.sub(r'[^a-zA-Z0-9]', '_', name.lower())
        
        # 确保唯一性
        existing_ids = [s['id'] for s in self.sources]
        counter = 1
        original_id = source_id
        
        while source_id in existing_ids:
            source_id = f"{original_id}_{counter}"
            counter += 1
        
        return source_id
    
    def get_source_by_id(self, source_id):
        """根据ID获取信息源"""
        for source in self.sources:
            if source.get('id') == source_id:
                return source
        return None
    
    def get_source_by_name(self, name):
        """根据名称获取信息源"""
        for source in self.sources:
            if source.get('name') == name:
                return source
        return None
    
    def validate_source(self, source_config):
        """验证信息源配置"""
        errors = []
        
        # 检查必填字段
        required = ['name', 'url', 'type']
        for field in required:
            if not source_config.get(field):
                errors.append(f"缺少必填字段：{field}")
        
        # 检查URL格式
        if 'url' in source_config:
            url = source_config['url']
            if not (url.startswith('http://') or url.startswith('https://')):
                errors.append("URL格式不正确，必须以 http:// 或 https:// 开头")
        
        # 检查选择器
        selectors = source_config.get('selectors', {})
        if not selectors.get('article_links'):
            errors.append("缺少文章链接选择器")
        
        return errors

# 测试
if __name__ == "__main__":
    manager = SourceManager()
    print("当前信息源:")
    for source in manager.sources:
        print(f"- {source['name']} ({source['id']}) - {'启用' if source.get('enabled', True) else '禁用'}")
    
    # 测试添加新源
    test_source = {
        "name": "测试源",
        "url": "https://example.com",
        "type": "news",
        "enabled": True,
        "max_articles": 5,
        "interval": 60
    }
    
    try:
        source_id = manager.add_source(test_source)
        print(f"\n添加测试源成功：{source_id}")
    except Exception as e:
        print(f"添加测试源失败：{e}")
    
    # 测试移除
    if manager.get_source_by_id('test_source'):
        manager.remove_source('test_source')
        print("移除测试源成功")
    
    print("\n最终信息源:")
    for source in manager.sources:
        print(f"- {source['name']} ({source['id']}) - {'启用' if source.get('enabled', True) else '禁用'}")