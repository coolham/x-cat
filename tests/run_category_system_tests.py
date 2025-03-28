#!/usr/bin/env python
# -*- coding: utf-8 -*-
# tests/run_category_system_tests.py

import pytest
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def run_tests():
    """运行分类系统的集成测试"""
    print("=====================================================")
    print("运行智能分类系统集成测试")
    print("=====================================================")
    
    # 仅运行集成测试
    test_file = "tests/integration/test_category_system_integration.py"
    
    # 运行测试
    exit_code = pytest.main(["-v", test_file])
    
    # 输出结果
    if exit_code == 0:
        print("\n集成测试通过！")
    else:
        print(f"\n测试失败，退出代码: {exit_code}")
    
    return exit_code

if __name__ == "__main__":
    sys.exit(run_tests())
