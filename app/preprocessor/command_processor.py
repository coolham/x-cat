# -*- coding: utf-8 -*-
"""
命令处理器
负责处理各种命令
"""
from typing import Dict, Optional
from loguru import logger

class CommandProcessor:
    """命令处理器"""
    
    def __init__(self):
        """初始化命令处理器"""
        # 注册命令处理器
        self._handlers = {
            '/test': self._handle_test,
            '/abc': self._handle_abc,
            '/help': self._handle_help
        }
        logger.info("命令处理器初始化成功")
    
    def process(self, command: str, metadata: Dict) -> Dict:
        """处理命令
        
        Args:
            command: 命令文本
            metadata: 元数据
            
        Returns:
            Dict: 处理结果，包含：
                {
                    'success': bool,      # 是否成功
                    'content': str,       # 处理结果
                    'errors': List[str]   # 错误信息
                }
        """
        try:
            # 解析命令
            parts = command.split()
            cmd = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []
            
            # 查找命令处理器
            handler = self._handlers.get(cmd)
            if not handler:
                return {
                    'success': False,
                    'content': f'未知命令: {cmd}',
                    'errors': [f'未知命令: {cmd}']
                }
            
            # 执行命令
            return handler(args, metadata)
            
        except Exception as e:
            logger.error(f"命令处理失败: {str(e)}")
            return {
                'success': False,
                'content': f'命令处理失败: {str(e)}',
                'errors': [str(e)]
            }
    
    def _handle_test(self, args: list, metadata: Dict) -> Dict:
        """处理 /test 命令
        
        Args:
            args: 命令参数
            metadata: 元数据
            
        Returns:
            Dict: 处理结果
        """
        return {
            'success': True,
            'content': '测试命令执行成功',
            'errors': []
        }
    
    def _handle_abc(self, args: list, metadata: Dict) -> Dict:
        """处理 /abc 命令
        
        Args:
            args: 命令参数
            metadata: 元数据
            
        Returns:
            Dict: 处理结果
        """
        return {
            'success': True,
            'content': 'ABC命令执行成功',
            'errors': []
        }
    
    def _handle_help(self, args: list, metadata: Dict) -> Dict:
        """处理 /help 命令
        
        Args:
            args: 命令参数
            metadata: 元数据
            
        Returns:
            Dict: 处理结果
        """
        help_text = """可用命令列表：
/test - 测试命令
/abc - ABC命令
/help - 显示帮助信息"""
        
        return {
            'success': True,
            'content': help_text,
            'errors': []
        } 