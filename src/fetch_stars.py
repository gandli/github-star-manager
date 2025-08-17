#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
获取GitHub用户的Star项目列表
"""

import os
import sys
import yaml
import json
import requests
from datetime import datetime


def load_config():
    """
    加载配置文件
    """
    try:
        with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml'), 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        sys.exit(1)


def fetch_starred_repos(username, token, max_stars=100):
    """
    获取用户的Star项目列表
    
    Args:
        username: GitHub用户名
        token: GitHub访问令牌
        max_stars: 最大获取数量
        
    Returns:
        list: 项目列表
    """
    all_repos = []
    page = 1
    per_page = 100  # GitHub API每页最大100条
    
    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': f'Bearer {token}',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    
    while len(all_repos) < max_stars:
        url = f"https://api.github.com/users/{username}/starred?page={page}&per_page={per_page}"
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"获取Star项目失败: {response.status_code} - {response.text}")
            break
            
        repos = response.json()
        if not repos:  # 没有更多项目
            break
            
        all_repos.extend(repos)
        page += 1
        
        # 达到最大数量后停止
        if len(all_repos) >= max_stars:
            all_repos = all_repos[:max_stars]
            break
    
    # 提取需要的信息
    result = []
    for repo in all_repos:
        result.append({
            'name': repo['name'],
            'full_name': repo['full_name'],
            'html_url': repo['html_url'],
            'description': repo['description'],
            'language': repo['language'],
            'stargazers_count': repo['stargazers_count'],
            'forks_count': repo['forks_count'],
            'topics': repo.get('topics', []),
            'created_at': repo['created_at'],
            'updated_at': repo['updated_at'],
            'starred_at': None  # GitHub API不直接提供此信息
        })
    
    return result


def save_repos_to_file(repos, output_file):
    """
    保存项目列表到文件
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(repos, f, ensure_ascii=False, indent=2)
    print(f"已保存{len(repos)}个Star项目到{output_file}")


def main():
    # 获取GitHub Token
    github_token = os.environ.get('GH_PAT')
    if not github_token:
        print("错误: 未设置GH_PAT环境变量")
        sys.exit(1)
    
    # 加载配置
    config = load_config()
    max_stars = config.get('max_stars', 100)
    
    # 首先检查是否设置了GITHUB_USERNAME环境变量（优先级最高）
    username = os.environ.get('GITHUB_USERNAME')
    if username:
        print(f"使用环境变量中的用户名: {username}")
    # 如果没有设置GITHUB_USERNAME，则在GitHub Actions环境中自动获取仓库所有者用户名
    elif os.environ.get('GITHUB_ACTIONS') == 'true':
        # 从GITHUB_REPOSITORY环境变量中提取用户名 (格式: owner/repo)
        # 这是GitHub Actions的标准上下文变量
        github_repository = os.environ.get('GITHUB_REPOSITORY', '')
        if '/' in github_repository:
            username = github_repository.split('/')[0]
            print(f"在GitHub Actions中自动获取用户名: {username}")
        else:
            # 如果无法从GITHUB_REPOSITORY获取，则使用配置文件中的用户名
            username = config.get('username')
    else:
        # 本地运行时使用配置文件中的用户名
        username = config.get('username')
    
    if not username:
        print("错误: 无法获取GitHub用户名，请在config.yaml中设置username或确保在GitHub Actions环境中运行")
        sys.exit(1)
    
    # 创建输出目录
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # 获取Star项目
    print(f"正在获取用户 {username} 的Star项目...")
    repos = fetch_starred_repos(username, github_token, max_stars)
    
    # 保存结果
    timestamp = datetime.now().strftime('%Y%m%d')
    output_file = os.path.join(data_dir, f'starred_repos_{timestamp}.json')
    save_repos_to_file(repos, output_file)
    
    # 同时保存一个最新版本
    latest_file = os.path.join(data_dir, 'starred_repos_latest.json')
    save_repos_to_file(repos, latest_file)


if __name__ == "__main__":
    main()