# -*- coding: utf-8 -*-
"""
分类系统管理器
负责加载、更新和管理分类定义
"""
from typing import Dict, List, Optional, Any
import yaml
import time
from pathlib import Path
from loguru import logger
import os
from datetime import datetime
import traceback

from .category_converter import CategoryConverter

class CategoryManager:
    """分类系统管理器"""
    
    def __init__(self):
        """初始化分类管理器"""
        self.categories = {}
        self.rules = {}
        self.markdown_path = Path("config/category_definitions.md")
        self.structured_path = Path("config/category_definitions.yaml")
        
        # 确保配置目录存在
        self.markdown_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 延迟加载分类定义
        self._categories_loaded = False
        
        # 创建转换器
        self.converter = CategoryConverter()
        
        # 初始化内容哈希
        self.content_hash = None
        
    async def initialize(self) -> bool:
        """初始化分类管理器
        
        Returns:
            bool: 是否初始化成功
        """
        try:
            # 加载分类定义
            self._load_categories()
            
            # 如果没有分类定义，创建默认分类
            if not self.categories:
                self._create_default_categories()
                
            logger.info("分类管理器初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"分类管理器初始化失败: {str(e)}")
            logger.debug(traceback.format_exc())
            return False
            
    def _create_default_categories(self):
        """创建默认分类"""
        try:
            default_categories = {
                'general': {
                    'id': 'general',
                    'name': '通用',
                    'description': '通用分类',
                    'order': 1,
                    'subcategories': {
                        'news': {
                            'id': 'news',
                            'name': '新闻',
                            'description': '新闻资讯',
                            'order': 1
                        },
                        'tech': {
                            'id': 'tech',
                            'name': '科技',
                            'description': '科技资讯',
                            'order': 2
                        },
                        'entertainment': {
                            'id': 'entertainment',
                            'name': '娱乐',
                            'description': '娱乐资讯',
                            'order': 3
                        }
                    }
                }
            }
            
            # 更新分类定义
            self.categories = default_categories
            
            # 保存分类定义
            self._save_categories()
            
            logger.info("已创建默认分类")
            
        except Exception as e:
            logger.error(f"创建默认分类失败: {str(e)}")
            logger.debug(traceback.format_exc())
            raise
        
    def _load_categories(self):
        """加载分类定义"""
        if self._categories_loaded:
            return
            
        try:
            # 检查文件是否存在
            if not self.markdown_path.exists():
                logger.warning(f"分类定义文件不存在: {self.markdown_path}")
                return
                
            # 检查文件修改时间
            if self.structured_path.exists():
                markdown_mtime = self.markdown_path.stat().st_mtime
                structured_mtime = self.structured_path.stat().st_mtime
                
                if markdown_mtime > structured_mtime:
                    logger.info("检测到分类定义文件变更，正在更新...")
                    try:
                        self._update_from_markdown()
                    except Exception as e:
                        logger.error(f"更新分类定义失败: {str(e)}")
                        # 如果更新失败，尝试加载现有的结构化配置
                        if self.structured_path.exists():
                            self._load_structured_config()
            else:
                # 如果结构化配置不存在，从Markdown创建
                self._update_from_markdown()
                
            self._categories_loaded = True
            
        except Exception as e:
            logger.error(f"加载分类定义失败: {str(e)}")
            logger.debug(traceback.format_exc())
            
    def _save_structured_config(self, data: Dict[str, Any]):
        """保存结构化配置
        
        Args:
            data: 结构化数据
        """
        try:
            # 创建临时文件
            temp_path = self.structured_path.with_suffix('.yaml.tmp')
            
            # 写入临时文件
            with open(temp_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True, sort_keys=False)
                
            # 如果原文件存在，尝试删除
            if self.structured_path.exists():
                try:
                    self.structured_path.unlink()
                except Exception as e:
                    logger.warning(f"删除原配置文件失败: {str(e)}")
                    
            # 重命名临时文件
            temp_path.rename(self.structured_path)
            
        except Exception as e:
            logger.error(f"保存结构化配置失败: {str(e)}")
            logger.debug(traceback.format_exc())
            raise
            
    def _update_from_markdown(self):
        """从Markdown更新分类定义"""
        try:
            # 读取Markdown文件
            with open(self.markdown_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 解析分类定义
            structured_data = self._parse_markdown(content)
            
            # 保存结构化配置
            self._save_structured_config(structured_data)
            
            # 更新内存中的分类定义
            self.categories = structured_data.get('categories', {})
            self.rules = structured_data.get('rules', {})
            
        except Exception as e:
            logger.error(f"更新分类定义失败: {str(e)}")
            logger.debug(traceback.format_exc())
            raise
            
    def _load_structured_config(self):
        """加载结构化配置"""
        try:
            with open(self.structured_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                
            self.categories = data.get('categories', {})
            self.rules = data.get('rules', {})
            
        except Exception as e:
            logger.error(f"加载结构化配置失败: {str(e)}")
            logger.debug(traceback.format_exc())
            raise
    
    def check_and_update(self) -> bool:
        """检查并更新分类定义
        
        Returns:
            bool: 是否进行了更新
        """
        try:
            if not self.markdown_path.exists():
                return False
                
            current_hash = self.converter.calculate_hash(
                self.markdown_path.read_text(encoding='utf-8')
            )
            
            if current_hash != self.content_hash:
                self._update_from_markdown()
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"检查更新失败: {str(e)}")
            return False
    
    def get_primary_categories(self, language: str = 'zh') -> List[Dict]:
        """获取一级分类列表
        
        Args:
            language: 语言代码，默认'zh'
            
        Returns:
            List[Dict]: 一级分类列表
        """
        try:
            return sorted(
                [
                    {
                        'id': cat['id'],
                        'name': cat['name'],
                        'description': cat['description'],
                        'order': cat['order']
                    }
                    for cat in self.categories.values()
                ],
                key=lambda x: x['order']
            )
            
        except Exception as e:
            logger.error(f"获取一级分类失败: {str(e)}")
            return []
    
    def get_secondary_categories(self, primary_id: str, language: str = 'zh') -> List[Dict]:
        """获取二级分类列表
        
        Args:
            primary_id: 一级分类ID
            language: 语言代码，默认'zh'
            
        Returns:
            List[Dict]: 二级分类列表
        """
        try:
            if primary_id not in self.categories:
                return []
                
            return sorted(
                [
                    {
                        'id': subcat['id'],
                        'name': subcat['name'],
                        'description': subcat['description'],
                        'order': subcat['order']
                    }
                    for subcat in self.categories[primary_id]['subcategories'].values()
                ],
                key=lambda x: x['order']
            )
            
        except Exception as e:
            logger.error(f"获取二级分类失败: {str(e)}")
            return []
    
    def get_category_by_id(self, category_id: str, language: str = 'zh') -> Optional[Dict]:
        """根据ID获取分类信息
        
        Args:
            category_id: 分类ID
            language: 语言代码，默认'zh'
            
        Returns:
            Optional[Dict]: 分类信息，如果不存在则返回None
        """
        try:
            # 检查一级分类
            if category_id in self.categories:
                return self.categories[category_id]
                
            # 检查二级分类
            for primary_cat in self.categories.values():
                if category_id in primary_cat['subcategories']:
                    return primary_cat['subcategories'][category_id]
                    
            return None
            
        except Exception as e:
            logger.error(f"获取分类信息失败: {str(e)}")
            return None
    
    def get_category_path(self, category_id: str, language: str = 'zh') -> List[Dict]:
        """获取分类完整路径
        
        Args:
            category_id: 分类ID
            language: 语言代码，默认'zh'
            
        Returns:
            List[Dict]: 分类路径列表，从根到目标分类
        """
        try:
            path = []
            
            # 检查一级分类
            if category_id in self.categories:
                path.append(self.categories[category_id])
                return path
                
            # 检查二级分类
            for primary_id, primary_cat in self.categories.items():
                if category_id in primary_cat['subcategories']:
                    path.append(primary_cat)
                    path.append(primary_cat['subcategories'][category_id])
                    return path
                    
            return []
            
        except Exception as e:
            logger.error(f"获取分类路径失败: {str(e)}")
            return []
    
    def update_category(self, category_id: str, data: Dict) -> bool:
        """更新分类信息
        
        Args:
            category_id: 分类ID
            data: 更新数据
            
        Returns:
            bool: 是否更新成功
        """
        try:
            # 检查一级分类
            if category_id in self.categories:
                self.categories[category_id].update(data)
                self._save_categories()
                return True
                
            # 检查二级分类
            for primary_cat in self.categories.values():
                if category_id in primary_cat['subcategories']:
                    primary_cat['subcategories'][category_id].update(data)
                    self._save_categories()
                    return True
                    
            return False
            
        except Exception as e:
            logger.error(f"更新分类失败: {str(e)}")
            return False
    
    def get_ai_prompt(self, language: str = 'zh') -> str:
        """获取AI分类提示词
        
        Args:
            language: 语言代码，默认'zh'
            
        Returns:
            str: AI分类提示词
        """
        try:
            return self.converter.create_ai_prompt(
                {'categories': self.categories},
                language
            )
            
        except Exception as e:
            logger.error(f"获取AI提示词失败: {str(e)}")
            return ""
    
    def _save_categories(self) -> None:
        """保存分类定义"""
        try:
            # 准备结构化数据
            data = {
                'version': self.converter.version,
                'last_updated': datetime.now().strftime('%Y-%m-%d'),
                'content_hash': self.content_hash,
                'categories': self.categories
            }
            
            # 保存结构化配置
            self._save_structured_config(data)
            
            # 保存Markdown配置
            self._save_markdown_config()
            
        except Exception as e:
            logger.error(f"保存分类定义失败: {str(e)}")
            raise
    
    def _save_markdown_config(self) -> None:
        """保存Markdown格式配置"""
        try:
            # 准备结构化数据
            data = {
                'version': self.converter.version,
                'last_updated': datetime.now().strftime('%Y-%m-%d'),
                'content_hash': self.content_hash,
                'categories': self.categories
            }
            
            # 转换为Markdown格式
            markdown_content = self.converter.structured_to_markdown(data)
            
            # 创建备份
            if self.markdown_path.exists():
                backup_path = self.markdown_path.with_suffix('.md.bak')
                self.markdown_path.rename(backup_path)
            
            # 保存新配置
            self.markdown_path.write_text(markdown_content, encoding='utf-8')
            
            # 删除备份
            if backup_path.exists():
                backup_path.unlink()
                
        except Exception as e:
            logger.error(f"保存Markdown配置失败: {str(e)}")
            # 恢复备份
            if backup_path.exists():
                backup_path.rename(self.markdown_path)
            raise

    def _parse_markdown(self, content: str) -> Dict[str, Any]:
        """解析Markdown内容
        
        Args:
            content: Markdown内容
            
        Returns:
            Dict[str, Any]: 结构化数据
        """
        try:
            # 使用转换器解析Markdown
            structured_data = self.converter.markdown_to_structured(content)
            
            # 验证数据结构
            if not isinstance(structured_data, dict):
                raise ValueError("解析结果必须是字典类型")
                
            if 'categories' not in structured_data:
                raise ValueError("解析结果必须包含categories字段")
                
            return structured_data
            
        except Exception as e:
            logger.error(f"解析Markdown失败: {str(e)}")
            logger.debug(traceback.format_exc())
            raise 