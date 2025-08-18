#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Star Manager - 数据获取模块

功能：
- 通过GitHub API获取用户Star项目列表
- 支持全量获取和增量更新两种模式
- 实现API请求重试机制和超时处理
"""

import os
import json
import time
import logging
import requests
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
import yaml


class GitHubStarFetcher:
    """GitHub星标项目获取器"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """初始化获取器
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.github_token = os.getenv(self.config['env_vars']['github_token'])
        self.username = os.getenv(self.config['env_vars']['github_username'])
        self.fetch_mode = os.getenv(self.config['env_vars']['fetch_mode'], 'incremental')
        
        if not self.github_token:
            raise ValueError("GitHub token not found in environment variables")
        if not self.username:
            raise ValueError("GitHub username not found in environment variables")
            
        self.session = self._setup_session()
        self.logger = self._setup_logger()
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置字典
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration: {e}")
    
    def _setup_session(self) -> requests.Session:
        """设置HTTP会话
        
        Returns:
            配置好的requests会话
        """
        session = requests.Session()
        session.headers.update({
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': f'GitHub-Star-Manager/{self.username}'
        })
        return session
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器
        
        Returns:
            配置好的日志记录器
        """
        logger = logging.getLogger(__name__)
        logger.setLevel(getattr(logging, self.config['logging']['level']))
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(self.config['logging']['format'])
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def _make_request(self, url: str, params: Optional[Dict] = None) -> Optional[requests.Response]:
        """发送HTTP请求，包含重试机制
        
        Args:
            url: 请求URL
            params: 请求参数
            
        Returns:
            响应对象或None
        """
        github_config = self.config['github']
        
        for attempt in range(github_config['max_retries'] + 1):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=github_config['timeout']
                )
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 403:
                    # 检查是否是API限制
                    if 'X-RateLimit-Remaining' in response.headers:
                        remaining = int(response.headers['X-RateLimit-Remaining'])
                        if remaining == 0:
                            reset_time = int(response.headers['X-RateLimit-Reset'])
                            wait_time = reset_time - int(time.time()) + 60
                            self.logger.warning(f"API rate limit exceeded. Waiting {wait_time} seconds...")
                            time.sleep(wait_time)
                            continue
                    
                    self.logger.error(f"Access forbidden: {response.text}")
                    return None
                elif response.status_code == 404:
                    self.logger.error(f"Resource not found: {url}")
                    return None
                else:
                    self.logger.warning(f"Request failed with status {response.status_code}: {response.text}")
                    
            except requests.exceptions.Timeout:
                self.logger.warning(f"Request timeout (attempt {attempt + 1})")
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Request error (attempt {attempt + 1}): {e}")
            
            if attempt < github_config['max_retries']:
                wait_time = github_config['retry_delay'] * (2 ** attempt)
                self.logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
        
        self.logger.error(f"Failed to fetch data after {github_config['max_retries']} retries")
        return None
    
    def _get_last_fetch_time(self) -> Optional[str]:
        """获取上次获取时间
        
        Returns:
            上次获取时间的ISO格式字符串或None
        """
        data_file = self.config['data']['stars_data_file']
        
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('metadata', {}).get('last_fetch_time')
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return None
    
    def fetch_starred_repos(self, mode: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取星标仓库列表
        
        Args:
            mode: 获取模式 ('full' 或 'incremental')，默认使用环境变量
            
        Returns:
            星标仓库列表
        """
        fetch_mode = mode or self.fetch_mode
        github_config = self.config['github']
        
        self.logger.info(f"Starting to fetch starred repositories in {fetch_mode} mode")
        
        # 确定获取参数
        if fetch_mode == 'full':
            max_repos = github_config['max_full_fetch']
            since_param = None
        else:
            max_repos = github_config['max_incremental_fetch']
            last_fetch_time = self._get_last_fetch_time()
            since_param = last_fetch_time
        
        repos = []
        page = 1
        per_page = 100  # GitHub API最大值
        
        while len(repos) < max_repos:
            # 构建请求参数
            params = {
                'page': page,
                'per_page': min(per_page, max_repos - len(repos)),
                'sort': 'created',
                'direction': 'desc'
            }
            
            if since_param:
                params['since'] = since_param
            
            # 发送请求
            url = f"{github_config['api_base_url']}/users/{self.username}/starred"
            response = self._make_request(url, params)
            
            if not response:
                break
            
            page_repos = response.json()
            
            if not page_repos:
                self.logger.info("No more repositories to fetch")
                break
            
            # 处理仓库数据
            for repo in page_repos:
                if len(repos) >= max_repos:
                    break
                    
                processed_repo = self._process_repo_data(repo)
                repos.append(processed_repo)
            
            self.logger.info(f"Fetched page {page}, total repos: {len(repos)}")
            page += 1
            
            # 添加请求间隔
            time.sleep(self.config['performance']['request_interval'])
        
        self.logger.info(f"Successfully fetched {len(repos)} repositories")
        return repos
    
    def _process_repo_data(self, repo: Dict[str, Any]) -> Dict[str, Any]:
        """处理仓库数据，提取需要的字段
        
        Args:
            repo: GitHub API返回的仓库数据
            
        Returns:
            处理后的仓库数据
        """
        return {
            'id': repo['id'],
            'name': repo['name'],
            'full_name': repo['full_name'],
            'description': repo.get('description', ''),
            'html_url': repo['html_url'],
            'clone_url': repo['clone_url'],
            'language': repo.get('language'),
            'stargazers_count': repo['stargazers_count'],
            'forks_count': repo['forks_count'],
            'open_issues_count': repo['open_issues_count'],
            'topics': repo.get('topics', []),
            'created_at': repo['created_at'],
            'updated_at': repo['updated_at'],
            'pushed_at': repo.get('pushed_at'),
            'size': repo['size'],
            'default_branch': repo['default_branch'],
            'archived': repo.get('archived', False),
            'disabled': repo.get('disabled', False),
            'private': repo['private'],
            'fork': repo['fork'],
            'owner': {
                'login': repo['owner']['login'],
                'type': repo['owner']['type']
            },
            'license': repo['license']['name'] if repo.get('license') else None,
            'starred_at': datetime.now(timezone.utc).isoformat(),
            'is_classified': False,
            'category': None,
            'summary': None,
            'key_features': []
        }
    
    def save_repos_data(self, repos: List[Dict[str, Any]], output_file: Optional[str] = None) -> str:
        """保存仓库数据到文件
        
        Args:
            repos: 仓库数据列表
            output_file: 输出文件路径，默认使用配置文件中的路径
            
        Returns:
            保存的文件路径
        """
        output_path = output_file or self.config['data']['stars_data_file']
        
        # 确保目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 准备数据
        data = {
            'metadata': {
                'total_count': len(repos),
                'fetch_mode': self.fetch_mode,
                'last_fetch_time': datetime.now(timezone.utc).isoformat(),
                'username': self.username
            },
            'repositories': repos
        }
        
        # 保存数据
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Saved {len(repos)} repositories to {output_path}")
        return output_path


def main():
    """主函数"""
    try:
        # 初始化获取器
        fetcher = GitHubStarFetcher()
        
        # 获取星标仓库
        repos = fetcher.fetch_starred_repos()
        
        # 保存数据
        output_file = fetcher.save_repos_data(repos)
        
        print(f"Successfully fetched and saved {len(repos)} repositories to {output_file}")
        
    except Exception as e:
        logging.error(f"Error in main execution: {e}")
        raise


if __name__ == "__main__":
    main()