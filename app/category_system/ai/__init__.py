# -*- coding: utf-8 -*-
"""
AI Classification Module
Provides AI-based content classification functionality
"""

from .classifier import AIClassifier
from .prompts import get_classification_prompt

__all__ = ['AIClassifier', 'get_classification_prompt']