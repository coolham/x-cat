#!/usr/bin/env python
"""
X-Cat 测试运行器
直接运行指定的测试文件，无需依赖pytest
"""
import os
import sys
import importlib.util
import argparse
import traceback
import asyncio
from pathlib import Path


def import_module_from_file(file_path):
    """从文件路径导入模块"""
    module_name = os.path.basename(file_path).replace('.py', '')
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def find_test_functions(module):
    """查找模块中的测试函数"""
    test_functions = []
    
    # 查找所有以test_开头的函数
    for name in dir(module):
        if name.startswith('test_'):
            item = getattr(module, name)
            if callable(item):
                test_functions.append((name, item))
    
    # 查找测试类中的测试方法
    for name in dir(module):
        if name.startswith('Test'):
            test_class = getattr(module, name)
            if isinstance(test_class, type):
                for method_name in dir(test_class):
                    if method_name.startswith('test_'):
                        # 忽略setup和teardown方法
                        if method_name not in ('setup_method', 'teardown_method'):
                            test_functions.append((f"{name}.{method_name}", None))
    
    return test_functions


async def run_test_functions(test_file, test_names=None):
    """运行指定测试文件中的测试函数"""
    try:
        # 导入测试模块
        module = import_module_from_file(test_file)
        
        # 查找测试函数
        test_functions = find_test_functions(module)
        if not test_functions:
            print(f"警告: 在文件 {test_file} 中未找到测试函数")
            return False
        
        # 确定要运行的测试
        tests_to_run = []
        if test_names:
            for name, func in test_functions:
                if any(test_name in name for test_name in test_names):
                    tests_to_run.append((name, func))
        else:
            tests_to_run = test_functions
        
        if not tests_to_run:
            print(f"警告: 未找到匹配的测试函数: {test_names}")
            print(f"可用的测试函数: {[name for name, _ in test_functions]}")
            return False
        
        # 运行测试
        success = True
        for name, func in tests_to_run:
            print(f"\n----- 运行测试: {name} -----")
            try:
                if func:
                    # 直接运行函数
                    if asyncio.iscoroutinefunction(func):
                        await func()
                    else:
                        func()
                else:
                    # 运行类中的方法
                    class_name, method_name = name.split('.')
                    test_class = getattr(module, class_name)
                    test_instance = test_class()
                    
                    # 调用setup方法(如果存在)
                    if hasattr(test_instance, 'setup_method'):
                        test_instance.setup_method()
                    
                    # 运行测试方法
                    test_method = getattr(test_instance, method_name)
                    if asyncio.iscoroutinefunction(test_method):
                        await test_method()
                    else:
                        test_method()
                    
                    # 调用teardown方法(如果存在)
                    if hasattr(test_instance, 'teardown_method'):
                        test_instance.teardown_method()
                
                print(f"✓ 测试通过: {name}")
            except Exception as e:
                success = False
                print(f"✗ 测试失败: {name}")
                print(f"  错误: {str(e)}")
                traceback.print_exc()
        
        return success
    except Exception as e:
        print(f"运行测试文件 {test_file} 时出错: {str(e)}")
        traceback.print_exc()
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="X-Cat 测试运行器")
    parser.add_argument("file", help="要运行的测试文件路径")
    parser.add_argument("--test", "-t", action="append", help="要运行的特定测试名称")
    args = parser.parse_args()
    
    # 检查文件是否存在
    test_file = Path(args.file)
    if not test_file.exists():
        print(f"错误: 测试文件 {test_file} 不存在")
        return 1
    
    # 将项目根目录添加到Python路径
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)
    
    # 运行测试
    print(f"===== 运行测试文件: {test_file} =====")
    success = asyncio.run(run_test_functions(test_file, args.test))
    
    if success:
        print("\n===== 所有测试通过 =====")
        return 0
    else:
        print("\n===== 测试失败 =====")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 