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
from data_manager import data_manager


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


def fetch_starred_repos(username, token, max_stars=100, incremental=True, request_timeout=30, max_retries=3, retry_delay=5):
    """
    获取用户的Star项目列表
    
    Args:
        username: GitHub用户名
        token: GitHub访问令牌
        max_stars: 最大获取数量
        incremental: 是否增量更新（只获取最新的Star项目）
        request_timeout: 请求超时时间（秒）
        max_retries: 最大重试次数
        retry_delay: 初始重试延迟（秒）
        
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
    
    print(f"开始获取GitHub Star项目列表...")
    
    # 如果是增量更新，先加载现有的项目列表
    existing_repos = []
    existing_repo_urls = set()
    if incremental:
        try:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
            latest_file = os.path.join(data_dir, 'starred_repos_latest.json')
            if os.path.exists(latest_file):
                print(f"增量更新模式：正在加载现有项目列表 {latest_file}")
                with open(latest_file, 'r', encoding='utf-8') as f:
                    existing_repos = json.load(f)
                existing_repo_urls = {repo['html_url'] for repo in existing_repos}
                print(f"已加载{len(existing_repos)}个现有项目")
        except Exception as e:
            print(f"加载现有项目列表失败，将执行全量更新: {e}")
            incremental = False
    
    while len(all_repos) < max_stars:
        print(f"正在获取第{page}页数据 (每页{per_page}条)...")
        url = f"https://api.github.com/users/{username}/starred?page={page}&per_page={per_page}"
        
        # 添加重试机制
        for retry in range(max_retries):
            try:
                response = requests.get(url, headers=headers, timeout=request_timeout)  # 使用配置的超时时间
                
                if response.status_code == 200:
                    break  # 请求成功，跳出重试循环
                elif response.status_code == 504 or response.status_code >= 500:  # 服务器错误，可以重试
                    if retry < max_retries - 1:  # 如果不是最后一次重试
                        print(f"获取第{page}页数据失败: {response.status_code} - 服务器错误，{retry_delay}秒后重试({retry+1}/{max_retries})")
                        import time
                        time.sleep(retry_delay)  # 等待一段时间后重试
                        retry_delay *= 2  # 指数退避策略，每次重试延迟时间翻倍
                        continue
                # 其他错误或最后一次重试失败
                print(f"获取Star项目失败: {response.status_code} - {response.text}")
                break
            except requests.exceptions.RequestException as e:
                if retry < max_retries - 1:  # 如果不是最后一次重试
                    print(f"请求异常: {e}，{retry_delay}秒后重试({retry+1}/{max_retries})")
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避策略
                    continue
                print(f"请求异常: {e}，重试次数已用完")
                break
        
        # 检查是否成功获取数据
        if response.status_code != 200:
            print(f"获取第{page}页数据失败，跳过此页继续获取下一页")
            page += 1
            continue  # 跳过此页，继续获取下一页
            
        repos = response.json()
        if not repos:  # 没有更多项目
            print(f"没有更多项目，获取完成")
            break
            
        print(f"成功获取第{page}页数据，共{len(repos)}个项目")
        
        # 如果是增量更新，检查是否已经获取到所有新项目
        if incremental:
            new_repos = []
            for repo in repos:
                if repo['html_url'] not in existing_repo_urls:
                    new_repos.append(repo)
                else:
                    print(f"已找到现有项目，增量更新完成")
                    break
            
            if len(new_repos) < len(repos):  # 说明找到了已存在的项目
                all_repos.extend(new_repos)
                break
            
            all_repos.extend(new_repos)
        else:
            all_repos.extend(repos)
        
        page += 1
        
        # 达到最大数量后停止
        if len(all_repos) >= max_stars:
            print(f"已达到最大获取数量({max_stars})，停止获取")
            all_repos = all_repos[:max_stars]
            break
    
    # 提取需要的信息
    print(f"开始处理获取到的{len(all_repos)}个项目数据...")
    result = []
    for i, repo in enumerate(all_repos, 1):
        if i % 20 == 0:  # 每处理20个项目打印一次进度
            print(f"正在处理项目数据: {i}/{len(all_repos)}")
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
    
    print(f"项目数据处理完成，共{len(result)}个项目")
    return result


def save_repos_to_file(repos, output_file):
    """将仓库信息保存到JSON文件"""
    print(f"正在保存{len(repos)}个项目到文件: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(repos, f, ensure_ascii=False, indent=2)
    print(f"文件保存成功: {output_file}")
    print(f"已保存{len(repos)}个Star项目到{output_file}")


def main():
    print("========== 开始执行获取GitHub Star项目列表脚本 ==========")
    # 获取GitHub Token
    github_token = os.environ.get('GH_PAT')
    if not github_token:
        print("错误: 未设置GH_PAT环境变量")
        sys.exit(1)
    
    print("正在加载配置文件...")
    # 加载配置
    config = load_config()
    max_stars = config.get('max_stars', 100)
    # 默认使用增量更新模式
    incremental_update = config.get('incremental_update', True)
    print(f"配置加载完成，最大获取Star数量: {max_stars}，增量更新模式: {incremental_update}")
    
    print("正在获取GitHub用户名...")
    # 首先检查是否设置了GITHUB_USERNAME环境变量（优先级最高）
    # 在GitHub Actions工作流中，这个变量通常设置为github.repository_owner
    username = os.environ.get('GITHUB_USERNAME')
    if username:
        print(f"使用环境变量中的用户名: {username}")
    # 如果没有设置GITHUB_USERNAME，则在GitHub Actions环境中自动获取仓库所有者用户名
    elif os.environ.get('GITHUB_ACTIONS') == 'true':
        # 从GITHUB_REPOSITORY环境变量中提取用户名 (格式: owner/repo)
        # 这是GitHub Actions的标准上下文变量
        # 注意：在工作流中我们已经通过github.repository_owner设置了GITHUB_USERNAME，
        # 所以这部分代码主要作为备用逻辑
        github_repository = os.environ.get('GITHUB_REPOSITORY', '')
        if '/' in github_repository:
            username = github_repository.split('/')[0]
            print(f"在GitHub Actions中自动获取用户名: {username}")
        else:
            # 如果无法从GITHUB_REPOSITORY获取，则使用配置文件中的用户名
            username = config.get('username')
            print(f"使用配置文件中的用户名: {username}")
    else:
        # 本地运行时使用配置文件中的用户名
        username = config.get('username')
        print(f"使用配置文件中的用户名: {username}")
    
    if not username:
        print("错误: 无法获取GitHub用户名，请在config.yaml中设置username或确保在GitHub Actions环境中运行")
        sys.exit(1)
    
    # 创建输出目录
    print("正在创建输出目录...")
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    os.makedirs(data_dir, exist_ok=True)
    print(f"输出目录已准备: {data_dir}")
    
    # 获取Star项目
    print(f"正在获取用户 {username} 的Star项目...")
    if incremental_update:
        print("使用增量更新模式，只获取最新的Star项目")
    else:
        print("使用全量更新模式，获取所有Star项目")
    
    # 从配置文件中读取网络请求相关的配置
    request_timeout = config.get('request_timeout', 30)
    max_retries = config.get('max_retries', 3)
    retry_delay = config.get('retry_delay', 5)
    print(f"网络请求配置：超时时间={request_timeout}秒，最大重试次数={max_retries}，初始重试延迟={retry_delay}秒")
    
    repos = fetch_starred_repos(
        username, 
        github_token, 
        max_stars, 
        incremental_update,
        request_timeout,
        max_retries,
        retry_delay
    )
    
    # 如果是增量更新且有新项目，则合并新旧项目列表
    if incremental_update and repos:
        latest_file = os.path.join(data_dir, 'starred_repos_latest.json')
        if os.path.exists(latest_file):
            try:
                with open(latest_file, 'r', encoding='utf-8') as f:
                    existing_repos = json.load(f)
                
                # 合并新旧项目列表，确保没有重复
                existing_urls = {repo['html_url'] for repo in existing_repos}
                merged_repos = existing_repos.copy()
                
                new_count = 0
                for repo in repos:
                    if repo['html_url'] not in existing_urls:
                        merged_repos.append(repo)
                        new_count += 1
                
                print(f"合并项目列表：{len(existing_repos)}个现有项目 + {new_count}个新项目 = {len(merged_repos)}个总项目")
                repos = merged_repos
            except Exception as e:
                print(f"合并项目列表失败: {e}，将只使用新获取的项目")
    
    print(f"成功获取 {len(repos)} 个Star项目")
    
    # 保存结果
    print("正在保存项目数据...")
    timestamp = datetime.now().strftime('%Y%m%d')
    output_file = os.path.join(data_dir, f'starred_repos_{timestamp}.json')
    save_repos_to_file(repos, output_file)
    
    # 同时保存一个最新版本
    latest_file = os.path.join(data_dir, 'starred_repos_latest.json')
    save_repos_to_file(repos, latest_file)
    
    # 将项目数据保存到JSON数据管理器中
    print("正在将项目数据保存到数据管理器...")
    for repo in repos:
        try:
            data_manager.add_or_update_star(repo)
        except Exception as e:
            print(f"保存项目 {repo.get('full_name', 'unknown')} 到数据管理器失败: {e}")
    
    # 显示统计信息
    stats = data_manager.get_statistics()
    print(f"数据管理器统计信息:")
    print(f"  总项目数: {stats.get('total_stars', 0)}")
    print(f"  已分类项目数: {stats.get('classified_count', 0)}")
    print(f"  未分类项目数: {stats.get('unclassified_count', 0)}")
    print(f"  最后更新时间: {stats.get('last_updated', 'unknown')}")
    
    print("========== 获取GitHub Star项目列表脚本执行完成 ==========")


if __name__ == "__main__":
    main()