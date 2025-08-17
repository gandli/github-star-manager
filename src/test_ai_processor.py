#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AI 处理器测试脚本
用于测试 AI 处理器的分类和摘要生成功能
"""

import os
import sys
import json
import time
from datetime import datetime
from logging_config import setup_logging
import logging
from ai_processor import AIProcessor

# 设置日志
setup_logging()
logger = logging.getLogger(__name__)

def test_ai_processor():
    """测试 AI 处理器"""
    # 获取 AI Token
    ai_token = os.getenv("GH_TOKEN")
    if not ai_token:
        logger.warning("未设置 GH_TOKEN 环境变量，将使用启发式分类")
    
    try:
        # 初始化 AI 处理器
        ai_processor = AIProcessor(ai_token)
        logger.info("AI 处理器初始化成功")
        
        # 测试样本仓库
        test_repos = [
            {
                "name": "tensorflow",
                "full_name": "tensorflow/tensorflow",
                "html_url": "https://github.com/tensorflow/tensorflow",
                "description": "An Open Source Machine Learning Framework for Everyone",
                "language": "C++",
                "stargazers_count": 178000,
                "topics": ["machine-learning", "deep-learning", "neural-networks", "python"]
            },
            {
                "name": "vue",
                "full_name": "vuejs/vue",
                "html_url": "https://github.com/vuejs/vue",
                "description": "🖖 Vue.js is a progressive, incrementally-adoptable JavaScript framework for building UI on the web.",
                "language": "JavaScript",
                "stargazers_count": 205000,
                "topics": ["javascript", "frontend", "framework", "vue"]
            },
            {
                "name": "awesome-python",
                "full_name": "vinta/awesome-python",
                "html_url": "https://github.com/vinta/awesome-python",
                "description": "A curated list of awesome Python frameworks, libraries, software and resources",
                "language": "Python",
                "stargazers_count": 145000,
                "topics": ["awesome", "python", "resources", "list"]
            },
            {
                "name": "linux",
                "full_name": "torvalds/linux",
                "html_url": "https://github.com/torvalds/linux",
                "description": "Linux kernel source tree",
                "language": "C",
                "stargazers_count": 154000,
                "topics": ["linux", "kernel", "operating-system"]
            },
            {
                "name": "free-programming-books",
                "full_name": "EbookFoundation/free-programming-books",
                "html_url": "https://github.com/EbookFoundation/free-programming-books",
                "description": "📚 Freely available programming books",
                "language": null,
                "stargazers_count": 270000,
                "topics": ["books", "education", "programming", "resources"]
            }
        ]
        
        # 测试分类和摘要生成
        for repo in test_repos:
            logger.info(f"测试仓库: {repo['name']}")
            
            # 测试分类
            start_time = time.time()
            category = ai_processor.classify_repository(repo)
            logger.info(f"  - 分类: {category} (耗时: {time.time() - start_time:.2f} 秒)")
            
            # 测试摘要生成
            start_time = time.time()
            summary = ai_processor.generate_summary(repo)
            logger.info(f"  - 摘要: {summary} (耗时: {time.time() - start_time:.2f} 秒)")
            
            # 等待一段时间，避免 API 速率限制
            time.sleep(1)
        
        # 测试缓存功能
        logger.info("测试缓存功能")
        logger.info("再次对同一仓库进行分类和摘要生成，应该使用缓存")
        
        # 选择第一个仓库再次测试
        repo = test_repos[0]
        
        # 测试分类缓存
        start_time = time.time()
        category = ai_processor.classify_repository(repo)
        logger.info(f"  - 分类 (缓存): {category} (耗时: {time.time() - start_time:.2f} 秒)")
        
        # 测试摘要缓存
        start_time = time.time()
        summary = ai_processor.generate_summary(repo)
        logger.info(f"  - 摘要 (缓存): {summary} (耗时: {time.time() - start_time:.2f} 秒)")
        
        # 获取缓存统计
        cache_stats = ai_processor.get_cache_stats()
        logger.info(f"缓存统计: {cache_stats}")
        
        # 测试启发式分类
        logger.info("测试启发式分类")
        for repo in test_repos:
            category = ai_processor._heuristic_classify(repo)
            logger.info(f"  - 仓库: {repo['name']}, 启发式分类: {category}")
        
        return True
    except Exception as e:
        logger.error(f"测试 AI 处理器失败: {str(e)}")
        return False

def main():
    """主函数"""
    logger.info("开始测试 AI 处理器")
    
    # 测试 AI 处理器
    if not test_ai_processor():
        logger.error("AI 处理器测试失败")
        return
    
    logger.info("AI 处理器测试完成")

if __name__ == "__main__":
    main()