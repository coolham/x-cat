"""
分析器模块包
提供不同类型的内容分析功能
"""

from app.analyzers.base import ContentAnalyzer as BaseContentAnalyzer
from app.analyzers.ai_client import AIClient

try:
    from app.analyzers.content_analyzer import ContentAnalyzer
    from app.analyzers.content_analyzer_module import ContentAnalyzerModule
except ImportError:
    ContentAnalyzer = None
    ContentAnalyzerModule = None 