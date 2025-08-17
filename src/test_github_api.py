#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GitHub API 测试脚本
用于测试 GitHub API 的连接和获取 star 项目的功能
"""

import os
import sys
import json
import time
from datetime import datetime
from github import Github, GithubException
from logging_config import setup_logging
import logging
import requests
from config import config

# 设置日志
setup_logging()
logger = logging.getLogger(__name__)

def test_github_connection():
    """测试 GitHub API 连接"""
    # 获取 GitHub Token
    github_token = os.getenv("GH_TOKEN")
    if not github_token:
        logger.error("未设置 GH_TOKEN 环境变量")
        return False
    
    try:
        # 初始化 GitHub 客户端
        g = Github(github_token)
        
        # 获取用户信息
        user = g.get_user()
        logger.info(f"成功连接到 GitHub，用户: {user.login}")
        
        # 获取 API 速率限制信息
        rate_limit = g.get_rate_limit()
        logger.info(f"API 速率限制: {rate_limit.core.limit}")
        logger.info(f"API 剩余请求数: {rate_limit.core.remaining}")
        logger.info(f"API 重置时间: {rate_limit.core.reset}")
        
        return True
    except Exception as e:
        logger.error(f"连接 GitHub API 失败: {str(e)}")
        return False

def test_get_starred_repos():
    """测试获取 star 项目"""
    # 获取 GitHub Token
    github_token = os.getenv("GH_TOKEN")
    if not github_token:
        logger.error("未设置 GH_TOKEN 环境变量")
        return False
    
    try:
        # 初始化 GitHub 客户端
        g = Github(github_token)
        user = g.get_user()
        
        # 尝试使用不同的排序方式获取 star 项目
        logger.info("测试不同排序方式获取 star 项目")
        
        # 1. 默认方式
        logger.info("1. 使用默认方式获取 star 项目")
        start_time = time.time()
        starred_default = user.get_starred()
        try:
            total_count = starred_default.totalCount
            logger.info(f"总共有 {total_count} 个 star 项目")
        except Exception as e:
            logger.warning(f"获取 star 项目总数失败: {str(e)}")
        
        # 只获取前 5 个项目进行测试
        repos_default = list(starred_default[:5])
        logger.info(f"获取到 {len(repos_default)} 个 star 项目，耗时: {time.time() - start_time:.2f} 秒")
        
        # 2. 按创建时间排序
        logger.info("2. 按创建时间排序获取 star 项目")
        try:
            start_time = time.time()
            starred_created = user.get_starred(sort="created", direction="desc")
            repos_created = list(starred_created[:5])
            logger.info(f"获取到 {len(repos_created)} 个 star 项目，耗时: {time.time() - start_time:.2f} 秒")
        except Exception as e:
            logger.error(f"按创建时间排序获取 star 项目失败: {str(e)}")
        
        # 3. 按更新时间排序
        logger.info("3. 按更新时间排序获取 star 项目")
        try:
            start_time = time.time()
            starred_updated = user.get_starred(sort="updated", direction="desc")
            repos_updated = list(starred_updated[:5])
            logger.info(f"获取到 {len(repos_updated)} 个 star 项目，耗时: {time.time() - start_time:.2f} 秒")
        except Exception as e:
            logger.error(f"按更新时间排序获取 star 项目失败: {str(e)}")
        
        # 测试分页获取
        logger.info("测试分页获取 star 项目")
        start_time = time.time()
        repos_paged = []
        for i in range(2):  # 只获取前 2 页进行测试
            page_items = starred_default.get_page(i)
            page_repos = list(page_items)
            repos_paged.extend(page_repos)
            logger.info(f"获取第 {i+1} 页，共 {len(page_repos)} 个项目")
        
        logger.info(f"分页获取到 {len(repos_paged)} 个 star 项目，耗时: {time.time() - start_time:.2f} 秒")
        
        return True
    except Exception as e:
        logger.error(f"测试获取 star 项目失败: {str(e)}")
        return False

def test_get_starred_at():
    """测试获取 starred_at 时间戳"""
    # 获取 GitHub Token
    github_token = os.getenv("GH_TOKEN")
    if not github_token:
        logger.error("未设置 GH_TOKEN 环境变量")
        return False
    
    try:
        # 初始化 GitHub 客户端
        g = Github(github_token, per_page=5)
        user = g.get_user()
        
        # 获取 star 项目
        logger.info("测试获取 starred_at 时间戳")
        starred = user.get_starred()
        
        # 获取前 5 个项目
        count = 0
        for repo in starred:
            if count >= 5:
                break
            
            logger.info(f"仓库: {repo.full_name}")
            logger.info(f"  - 创建时间: {repo.created_at}")
            logger.info(f"  - 更新时间: {repo.updated_at}")
            
            # 尝试获取 starred_at 时间戳
            try:
                # 使用 PyGithub 的 _rawData 属性获取原始数据
                if hasattr(repo, '_rawData') and 'starred_at' in repo._rawData:
                    starred_at = repo._rawData['starred_at']
                    logger.info(f"  - Star 时间 (从 _rawData): {starred_at}")
                else:
                    logger.warning(f"  - 仓库 {repo.full_name} 的 _rawData 中没有 starred_at 属性")
            except Exception as e:
                logger.warning(f"  - 获取仓库 {repo.full_name} 的 starred_at 失败: {str(e)}")
            
            count += 1
        
        # 测试直接使用 requests 获取 starred_at
        logger.info("测试使用 requests 直接获取 starred_at")
        
        headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3.star+json',  # 关键是使用这个 Accept 头
        }
        
        api_base_url = config.get("github", {}).get("api_base_url", "https://api.github.com")
        
        response = requests.get(
            f'{api_base_url}/user/starred',
            headers=headers,
            params={'per_page': 5}
        )
        
        if response.status_code == 200:
            repos = response.json()
            for repo in repos:
                starred_at = repo.get('starred_at')
                repo_name = repo.get('repo', {}).get('full_name')
                logger.info(f"  - {repo_name} (starred_at: {starred_at})")
        else:
            logger.error(f"请求失败: {response.status_code} - {response.text}")
        
        return True
    except Exception as e:
        logger.error(f"测试获取 starred_at 时间戳失败: {str(e)}")
        return False

def main():
    """主函数"""
    logger.info("开始测试 GitHub API")
    
    # 测试 GitHub 连接
    if not test_github_connection():
        logger.error("GitHub API 连接测试失败")
        return
    
    # 测试获取 star 项目
    if not test_get_starred_repos():
        logger.error("获取 star 项目测试失败")
        return
    
    # 测试获取 starred_at 时间戳
    if not test_get_starred_at():
        logger.error("获取 starred_at 时间戳测试失败")
        return
    
    logger.info("GitHub API 测试完成")

if __name__ == "__main__":
    main()