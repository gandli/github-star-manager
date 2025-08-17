#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
工作流程测试脚本
用于测试整个 GitHub Star 管理工作流程
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

def test_workflow():
    """测试完整工作流程"""
    try:
        # 检查环境变量
        github_token = os.getenv("GH_TOKEN")
        if not github_token:
            logger.error("未设置 GH_TOKEN 环境变量")
            return False
        
        ai_token = os.getenv("GITHUB_AI_TOKEN")
        if not ai_token:
            logger.warning("未设置 GITHUB_AI_TOKEN 环境变量，将使用启发式分类")
        
        # 导入必要的模块
        from github import Github
        from ai_processor import AIProcessor
        from update_stars import get_starred_repos, repo_to_dict, update_readme, save_repos_data
        
        # 创建临时输出文件
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.md', delete=False) as temp_readme_file:
            temp_readme_path = temp_readme_file.name
        
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as temp_data_file:
            temp_data_path = temp_data_file.name
        
        # 保存原始配置
        original_readme_output_path = config["readme"]["output_path"]
        original_data_output_path = config["data"]["output_path"]
        original_max_repos = config["github"].get("max_repos", None)
        
        try:
            # 修改配置以使用临时输出文件和限制仓库数量
            config["readme"]["output_path"] = temp_readme_path
            config["data"]["output_path"] = temp_data_path
            config["github"]["max_repos"] = 10  # 只获取前 10 个仓库进行测试
            
            # 初始化 GitHub 客户端
            logger.info("初始化 GitHub 客户端")
            g = Github(github_token)
            
            # 初始化 AI 处理器
            logger.info("初始化 AI 处理器")
            ai_processor = AIProcessor(ai_token)
            
            # 获取 star 项目
            logger.info("获取 star 项目")
            start_time = time.time()
            starred_repos = get_starred_repos(g)
            logger.info(f"获取到 {len(starred_repos)} 个 star 项目，耗时: {time.time() - start_time:.2f} 秒")
            
            # 处理仓库数据
            logger.info("处理仓库数据")
            repos_data = []
            processed_count = 0
            error_count = 0
            
            for repo in starred_repos:
                try:
                    # 转换仓库为字典
                    repo_dict = repo_to_dict(repo)
                    
                    # 使用 AI 处理器分类和生成摘要
                    repo_dict["category"] = ai_processor.classify_repository(repo_dict)
                    repo_dict["ai_summary"] = ai_processor.generate_summary(repo_dict)
                    
                    repos_data.append(repo_dict)
                    processed_count += 1
                    
                    # 打印进度
                    if processed_count % 2 == 0 or processed_count == len(starred_repos):
                        logger.info(f"处理进度: {processed_count}/{len(starred_repos)} ({processed_count/len(starred_repos)*100:.1f}%)")
                except Exception as e:
                    logger.error(f"处理仓库 {repo.full_name if hasattr(repo, 'full_name') else 'unknown'} 失败: {str(e)}")
                    error_count += 1
            
            logger.info(f"处理完成: 成功 {processed_count} 个，失败 {error_count} 个")
            
            # 获取 AI 处理器缓存统计
            cache_stats = ai_processor.get_cache_stats()
            logger.info(f"AI 处理器缓存统计: {cache_stats}")
            
            # 更新 README
            logger.info("更新 README")
            update_readme(repos_data)
            
            # 保存仓库数据
            logger.info("保存仓库数据")
            save_repos_data(repos_data)
            
            # 检查生成的文件
            if os.path.exists(temp_readme_path):
                readme_size = os.path.getsize(temp_readme_path)
                logger.info(f"生成的 README 文件大小: {readme_size} 字节")
            else:
                logger.error("README 文件未生成")
            
            if os.path.exists(temp_data_path):
                data_size = os.path.getsize(temp_data_path)
                logger.info(f"生成的数据文件大小: {data_size} 字节")
                
                # 读取数据文件内容
                with open(temp_data_path, 'r', encoding='utf-8') as f:
                    data_content = json.load(f)
                
                logger.info(f"数据文件包含 {len(data_content)} 个仓库")
            else:
                logger.error("数据文件未生成")
            
            return True
        finally:
            # 恢复原始配置
            config["readme"]["output_path"] = original_readme_output_path
            config["data"]["output_path"] = original_data_output_path
            if original_max_repos is not None:
                config["github"]["max_repos"] = original_max_repos
            else:
                config["github"].pop("max_repos", None)
            
            # 删除临时文件
            try:
                if os.path.exists(temp_readme_path):
                    os.unlink(temp_readme_path)
                if os.path.exists(temp_data_path):
                    os.unlink(temp_data_path)
                logger.info("已删除临时文件")
            except Exception as e:
                logger.warning(f"删除临时文件失败: {str(e)}")
    
    except Exception as e:
        logger.error(f"测试工作流程失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    logger.info("开始测试工作流程")
    
    # 测试工作流程
    if not test_workflow():
        logger.error("工作流程测试失败")
        return
    
    logger.info("工作流程测试完成")

if __name__ == "__main__":
    main()