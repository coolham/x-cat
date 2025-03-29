# -*- coding: utf-8 -*-
"""
分类定义转换器
用于在Markdown和结构化格式之间转换分类定义
"""
from typing import Dict, List, Optional, Any
import re
import hashlib
from pathlib import Path
from loguru import logger
import yaml
from datetime import datetime

class CategoryConverter:
    """分类定义转换器，用于在Markdown和结构化格式之间转换分类定义"""
    
    def __init__(self):
        self.version = '1.0'
        
    def calculate_hash(self, content: str) -> str:
        """计算内容哈希值
        
        Args:
            content: 要计算哈希值的内容
            
        Returns:
            str: MD5哈希值
        """
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def markdown_to_structured(self, markdown_content: str) -> Dict:
        """将Markdown格式转换为结构化格式
        
        Args:
            markdown_content: Markdown格式的分类定义
            
        Returns:
            Dict: 结构化格式的分类定义
        """
        try:
            # 计算内容哈希值
            content_hash = self.calculate_hash(markdown_content)
            
            # 初始化结果字典
            result = {
                'version': self.version,
                'last_updated': datetime.now().strftime('%Y-%m-%d'),
                'content_hash': content_hash,
                'categories': {}
            }
            
            # 解析主分类
            primary_pattern = r'##\s*(\d+)\.\s*([^(]+)\s*\(([^)]+)\)'
            primary_matches = re.finditer(primary_pattern, markdown_content)
            
            for match in primary_matches:
                order = int(match.group(1))
                name = match.group(2).strip()
                category_id = match.group(3).strip()
                
                # 获取主分类下的二级分类
                subcategories = {}
                sub_pattern = r'-\s*([^(]+)\s*\(([^)]+)\)'
                sub_matches = re.finditer(sub_pattern, markdown_content[match.end():])
                
                for sub_match in sub_matches:
                    sub_name = sub_match.group(1).strip()
                    sub_id = sub_match.group(2).strip()
                    
                    subcategories[sub_id] = {
                        'id': f'subcat_{category_id}_{sub_id}',
                        'name': sub_name,
                        'description': f'{name}下的{sub_name}相关内容',
                        'order': len(subcategories) + 1
                    }
                
                # 添加主分类
                result['categories'][category_id] = {
                    'id': f'cat_{category_id}',
                    'name': name,
                    'description': f'{name}相关技术、应用和发展',
                    'order': order,
                    'subcategories': subcategories
                }
            
            return result
            
        except Exception as e:
            raise ValueError(f"转换Markdown格式失败: {str(e)}")
    
    def structured_to_markdown(self, structured_data: Dict) -> str:
        """将结构化格式转换为Markdown格式
        
        Args:
            structured_data: 结构化格式的分类定义
            
        Returns:
            str: Markdown格式的分类定义
        """
        try:
            markdown = ["# 内容分类系统\n"]
            
            # 按order排序主分类
            sorted_categories = sorted(
                structured_data['categories'].items(),
                key=lambda x: x[1]['order']
            )
            
            # 生成主分类
            for cat_id, cat in sorted_categories:
                markdown.append(f"\n## {cat['order']}. {cat['name']} ({cat_id})")
                
                # 按order排序二级分类
                sorted_subcats = sorted(
                    cat['subcategories'].items(),
                    key=lambda x: x[1]['order']
                )
                
                # 生成二级分类
                for sub_id, subcat in sorted_subcats:
                    markdown.append(f"- {subcat['name']} ({sub_id})")
            
            return "\n".join(markdown)
            
        except Exception as e:
            raise ValueError(f"转换结构化格式失败: {str(e)}")
    
    def create_ai_prompt(self, structured_data: Dict, language: str = 'zh') -> str:
        """创建AI分类提示词
        
        Args:
            structured_data: 结构化格式的分类定义
            language: 语言代码，默认'zh'
            
        Returns:
            str: AI分类提示词
        """
        try:
            if language == 'zh':
                prompt = ["请根据以下分类体系对内容进行分类：\n"]
            else:
                prompt = ["Please classify the content according to the following category system:\n"]
            
            # 添加主分类
            for cat_id, cat in structured_data['categories'].items():
                if language == 'zh':
                    prompt.append(f"\n{cat['order']}. {cat['name']}")
                else:
                    prompt.append(f"\n{cat['order']}. {cat['name']}")
                
                # 添加二级分类
                for sub_id, subcat in cat['subcategories'].items():
                    if language == 'zh':
                        prompt.append(f"  - {subcat['name']}")
                    else:
                        prompt.append(f"  - {subcat['name']}")
            
            # 添加分类要求
            if language == 'zh':
                prompt.extend([
                    "\n分类要求：",
                    "1. 选择最合适的一级分类和二级分类",
                    "2. 如果内容不适合任何二级分类，只需选择一级分类",
                    "3. 返回JSON格式的分类结果，包含以下字段：",
                    "   - primary_category: 选择的一级分类名称",
                    "   - secondary_category: 选择的二级分类名称（如果适用）",
                    "   - confidence: 分类置信度（0.0-1.0）",
                    "   - reasoning: 分类理由（50字以内）"
                ])
            else:
                prompt.extend([
                    "\nClassification requirements:",
                    "1. Select the most appropriate primary and secondary categories",
                    "2. If the content doesn't fit any secondary category, only select primary category",
                    "3. Return classification result in JSON format with the following fields:",
                    "   - primary_category: selected primary category name",
                    "   - secondary_category: selected secondary category name (if applicable)",
                    "   - confidence: classification confidence (0.0-1.0)",
                    "   - reasoning: classification reasoning (within 50 characters)"
                ])
            
            return "\n".join(prompt)
            
        except Exception as e:
            raise ValueError(f"创建AI提示词失败: {str(e)}") 