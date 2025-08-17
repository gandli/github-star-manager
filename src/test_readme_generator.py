#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
README 生成器测试脚本
用于测试 README 生成功能
"""

import os
import sys
import json
import time
from datetime import datetime
from logging_config import setup_logging
import logging
import tempfile
from config import config

# 设置日志
setup_logging()
logger = logging.getLogger(__name__)

def test_readme_generation():
    """测试 README 生成"""
    try:
        # 导入更新 README 函数
        from update_stars import update_readme
        
        # 创建测试数据
        test_repos = [
            {
                "name": "tensorflow",
                "full_name": "tensorflow/tensorflow",
                "html_url": "https://github.com/tensorflow/tensorflow",
                "description": "An Open Source Machine Learning Framework for Everyone",
                "language": "C++",
                "stargazers_count": 178000,
                "updated_at": "2023-01-01T00:00:00Z",
                "category": "机器学习",
                "ai_summary": "TensorFlow 是一个开源机器学习框架，支持深度学习和神经网络模型的训练和部署。",
                "topics": ["machine-learning", "deep-learning", "neural-networks", "python"]
            },
            {
                "name": "vue",
                "full_name": "vuejs/vue",
                "html_url": "https://github.com/vuejs/vue",
                "description": "🖖 Vue.js is a progressive, incrementally-adoptable JavaScript framework for building UI on the web.",
                "language": "JavaScript",
                "stargazers_count": 205000,
                "updated_at": "2023-02-01T00:00:00Z",
                "category": "前端框架",
                "ai_summary": "Vue.js 是一个渐进式 JavaScript 框架，用于构建用户界面，易于上手且灵活。",
                "topics": ["javascript", "frontend", "framework", "vue"]
            },
            {
                "name": "awesome-python",
                "full_name": "vinta/awesome-python",
                "html_url": "https://github.com/vinta/awesome-python",
                "description": "A curated list of awesome Python frameworks, libraries, software and resources",
                "language": "Python",
                "stargazers_count": 145000,
                "updated_at": "2023-03-01T00:00:00Z",
                "category": "学习资源",
                "ai_summary": "精选的 Python 框架、库、软件和资源列表，是学习 Python 的宝贵参考。",
                "topics": ["awesome", "python", "resources", "list"]
            },
            {
                "name": "linux",
                "full_name": "torvalds/linux",
                "html_url": "https://github.com/torvalds/linux",
                "description": "Linux kernel source tree",
                "language": "C",
                "stargazers_count": 154000,
                "updated_at": "2023-04-01T00:00:00Z",
                "category": "操作系统",
                "ai_summary": "Linux 内核源代码，是开源操作系统的核心组件。",
                "topics": ["linux", "kernel", "operating-system"]
            },
            {
                "name": "free-programming-books",
                "full_name": "EbookFoundation/free-programming-books",
                "html_url": "https://github.com/EbookFoundation/free-programming-books",
                "description": "📚 Freely available programming books",
                "language": None,
                "stargazers_count": 270000,
                "updated_at": "2023-05-01T00:00:00Z",
                "category": "学习资源",
                "ai_summary": "免费提供的编程书籍集合，涵盖多种编程语言和技术。",
                "topics": ["books", "education", "programming", "resources"]
            }
        ]
        
        # 创建临时输出文件
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.md', delete=False) as temp_file:
            temp_output_path = temp_file.name
        
        # 保存原始配置
        original_readme_output_path = config["readme"]["output_path"]
        
        try:
            # 修改配置以使用临时输出文件
            config["readme"]["output_path"] = temp_output_path
            
            # 测试 README 生成
            logger.info("测试 README 生成")
            update_readme(test_repos)
            
            # 读取生成的 README 文件
            with open(temp_output_path, 'r', encoding='utf-8') as f:
                readme_content = f.read()
            
            # 检查生成的 README 内容
            logger.info(f"生成的 README 文件大小: {len(readme_content)} 字节")
            
            # 检查是否包含所有分类
            categories = set(repo["category"] for repo in test_repos)
            for category in categories:
                if category in readme_content:
                    logger.info(f"README 包含分类: {category}")
                else:
                    logger.error(f"README 缺少分类: {category}")
            
            # 检查是否包含所有仓库
            for repo in test_repos:
                if repo["name"] in readme_content:
                    logger.info(f"README 包含仓库: {repo['name']}")
                else:
                    logger.error(f"README 缺少仓库: {repo['name']}")
            
            # 检查是否包含 AI 摘要
            ai_summaries_found = 0
            for repo in test_repos:
                if repo["ai_summary"] in readme_content:
                    ai_summaries_found += 1
            
            logger.info(f"README 包含 {ai_summaries_found}/{len(test_repos)} 个 AI 摘要")
            
            return True
        finally:
            # 恢复原始配置
            config["readme"]["output_path"] = original_readme_output_path
            
            # 删除临时文件
            try:
                os.unlink(temp_output_path)
                logger.info("已删除临时 README 文件")
            except Exception as e:
                logger.warning(f"删除临时 README 文件失败: {str(e)}")
    
    except Exception as e:
        logger.error(f"测试 README 生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    logger.info("开始测试 README 生成器")
    
    # 测试 README 生成
    if not test_readme_generation():
        logger.error("README 生成器测试失败")
        return
    
    logger.info("README 生成器测试完成")

if __name__ == "__main__":
    main()