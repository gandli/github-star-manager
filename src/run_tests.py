#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
运行所有测试的脚本
"""

import os
import sys
import time
from logging_config import setup_logging
import logging
import argparse

# 设置日志
setup_logging()
logger = logging.getLogger(__name__)

def run_test(test_module_name):
    """运行指定的测试模块"""
    try:
        logger.info(f"运行测试: {test_module_name}")
        start_time = time.time()
        
        # 导入测试模块
        test_module = __import__(test_module_name)
        
        # 运行测试
        result = test_module.main()
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result is None or result is True:
            logger.info(f"测试 {test_module_name} 成功完成，耗时: {duration:.2f} 秒")
            return True
        else:
            logger.error(f"测试 {test_module_name} 失败，耗时: {duration:.2f} 秒")
            return False
    except Exception as e:
        logger.error(f"运行测试 {test_module_name} 时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """运行所有测试"""
    # 测试模块列表
    test_modules = [
        "test_config",
        "test_ai_processor",
        "test_github_api",
        "test_readme_generator",
        "test_workflow"
    ]
    
    # 运行所有测试
    success_count = 0
    failure_count = 0
    
    for test_module in test_modules:
        if run_test(test_module):
            success_count += 1
        else:
            failure_count += 1
    
    # 打印测试结果摘要
    logger.info("测试完成")
    logger.info(f"成功: {success_count}")
    logger.info(f"失败: {failure_count}")
    
    return failure_count == 0

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="运行测试")
    parser.add_argument("--test", "-t", help="要运行的测试模块名称，不指定则运行所有测试")
    args = parser.parse_args()
    
    logger.info("开始运行测试")
    
    if args.test:
        # 运行指定的测试
        success = run_test(args.test)
    else:
        # 运行所有测试
        success = run_all_tests()
    
    # 设置退出码
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()