#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Star Manager - AI分类模块

功能：
- 使用AI模型对项目进行智能分类和摘要生成
- 集成Cloudflare Workers AI API
- 支持多种JSON响应格式解析
- 实现并发处理控制
"""

import os
import json
import time
import logging
import asyncio
import aiohttp
import re
from typing import List, Dict, Optional, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import yaml


class AIClassifier:
    """AI项目分类器"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """初始化分类器
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.api_key = os.getenv(self.config['env_vars']['ai_api_key'])
        self.account_id = os.getenv(self.config['env_vars']['ai_account_id'])
        
        if not self.api_key:
            raise ValueError("AI API key not found in environment variables")
        if not self.account_id:
            raise ValueError("AI account ID not found in environment variables")
            
        self.api_url = self.config['ai']['api_base_url'].format(account_id=self.account_id)
        self.logger = self._setup_logger()
        
        # 构建分类提示词
        self.categories = self.config['categories']
        self.classification_prompt = self._build_classification_prompt()
        
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
    
    def _build_classification_prompt(self) -> str:
        """构建分类提示词
        
        Returns:
            分类提示词字符串
        """
        categories_str = "、".join(self.categories)
        
        prompt = f"""
你是一个专业的GitHub项目分类专家。请根据项目信息对GitHub项目进行分类和分析。

可选分类：{categories_str}

请严格按照以下JSON格式返回结果，不要包含任何其他文本或代码块标记：

{{
  "category": "选择最合适的分类",
  "summary": "项目的简洁中文摘要（50-100字）",
  "key_features": ["关键特性1", "关键特性2", "关键特性3"]
}}

分类规则：
1. 根据项目的主要功能和技术栈选择最合适的分类
2. 如果项目涉及多个领域，选择最主要的那个
3. 摘要要简洁明了，突出项目的核心价值
4. 关键特性要具体且有价值，最多3个
5. 必须严格按照JSON格式返回，不要添加任何额外的文本

项目信息：
名称：{{}}
描述：{{}}
语言：{{}}
主题：{{}}
星数：{{}}
URL：{{}}
"""
        return prompt
    
    async def _make_ai_request(self, session: aiohttp.ClientSession, prompt: str) -> Optional[Dict[str, Any]]:
        """发送AI分类请求
        
        Args:
            session: aiohttp会话
            prompt: 提示词
            
        Returns:
            AI响应结果或None
        """
        ai_config = self.config['ai']
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'max_tokens': 512,
            'temperature': 0.1
        }
        
        for attempt in range(ai_config['max_retries']):
            try:
                async with session.post(
                    f"{self.api_url}/{ai_config['model']}",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=ai_config['timeout'])
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result
                    else:
                        error_text = await response.text()
                        self.logger.warning(f"AI request failed with status {response.status}: {error_text}")
                        
            except asyncio.TimeoutError:
                self.logger.warning(f"AI request timeout (attempt {attempt + 1})")
            except Exception as e:
                self.logger.warning(f"AI request error (attempt {attempt + 1}): {e}")
            
            if attempt < ai_config['max_retries'] - 1:
                await asyncio.sleep(ai_config['retry_delay'])
        
        return None
    
    def _extract_json_from_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """从AI响应中提取JSON数据
        
        Args:
            response_text: AI响应文本
            
        Returns:
            提取的JSON数据或None
        """
        # 尝试直接解析JSON
        try:
            return json.loads(response_text.strip())
        except json.JSONDecodeError:
            pass
        
        # 尝试从代码块中提取JSON
        json_pattern = r'```(?:json)?\s*({.*?})\s*```'
        match = re.search(json_pattern, response_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        
        # 尝试提取花括号内的内容
        brace_pattern = r'{[^{}]*(?:{[^{}]*}[^{}]*)*}'
        matches = re.findall(brace_pattern, response_text, re.DOTALL)
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        
        self.logger.warning(f"Failed to extract JSON from response: {response_text[:200]}...")
        return None
    
    def _validate_classification_result(self, result: Dict[str, Any]) -> bool:
        """验证分类结果的有效性
        
        Args:
            result: 分类结果
            
        Returns:
            是否有效
        """
        required_fields = ['category', 'summary', 'key_features']
        
        # 检查必需字段
        for field in required_fields:
            if field not in result:
                return False
        
        # 检查分类是否在预定义列表中
        if result['category'] not in self.categories:
            return False
        
        # 检查关键特性是否为列表
        if not isinstance(result['key_features'], list):
            return False
        
        # 检查字符串字段是否为空
        if not result['summary'] or not isinstance(result['summary'], str):
            return False
        
        return True
    
    async def classify_repository(self, repo: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """分类单个仓库
        
        Args:
            repo: 仓库信息
            
        Returns:
            分类结果或None
        """
        # 构建项目信息
        project_info = {
            'name': repo.get('name', ''),
            'description': repo.get('description', ''),
            'language': repo.get('language', ''),
            'topics': ', '.join(repo.get('topics', [])),
            'stars': repo.get('stargazers_count', 0),
            'url': repo.get('html_url', '')
        }
        
        # 格式化提示词
        prompt = self.classification_prompt.format(
            project_info['name'],
            project_info['description'],
            project_info['language'],
            project_info['topics'],
            project_info['stars'],
            project_info['url']
        )
        
        # 发送AI请求
        async with aiohttp.ClientSession() as session:
            ai_response = await self._make_ai_request(session, prompt)
        
        if not ai_response:
            return None
        
        # 提取响应内容
        response_content = ai_response.get('result', {}).get('response', '')
        if not response_content:
            self.logger.warning("Empty response from AI")
            return None
        
        # 解析JSON响应
        classification_result = self._extract_json_from_response(response_content)
        if not classification_result:
            return None
        
        # 验证结果
        if not self._validate_classification_result(classification_result):
            self.logger.warning(f"Invalid classification result: {classification_result}")
            return None
        
        self.logger.info(f"Successfully classified {repo['name']} as {classification_result['category']}")
        return classification_result
    
    def classify_repositories_batch(self, repos: List[Dict[str, Any]]) -> List[Tuple[int, Optional[Dict[str, Any]]]]:
        """批量分类仓库
        
        Args:
            repos: 仓库列表
            
        Returns:
            分类结果列表，每个元素为(索引, 分类结果)的元组
        """
        max_workers = self.config['ai']['max_concurrent_requests']
        results = []
        
        self.logger.info(f"Starting batch classification of {len(repos)} repositories")
        
        # 使用线程池执行异步任务
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_index = {
                executor.submit(self._run_async_classification, repo): i
                for i, repo in enumerate(repos)
            }
            
            # 收集结果
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    result = future.result()
                    results.append((index, result))
                    
                    if result:
                        self.logger.info(f"Classified repository {index + 1}/{len(repos)}")
                    else:
                        self.logger.warning(f"Failed to classify repository {index + 1}/{len(repos)}")
                        
                except Exception as e:
                    self.logger.error(f"Error classifying repository {index + 1}: {e}")
                    results.append((index, None))
        
        # 按索引排序
        results.sort(key=lambda x: x[0])
        
        successful_classifications = sum(1 for _, result in results if result is not None)
        self.logger.info(f"Batch classification completed: {successful_classifications}/{len(repos)} successful")
        
        return results
    
    def _run_async_classification(self, repo: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """在新的事件循环中运行异步分类
        
        Args:
            repo: 仓库信息
            
        Returns:
            分类结果或None
        """
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self.classify_repository(repo))
        finally:
            loop.close()
    
    def update_repositories_with_classification(self, repos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """更新仓库列表，添加分类信息
        
        Args:
            repos: 仓库列表
            
        Returns:
            更新后的仓库列表
        """
        # 过滤出未分类的仓库
        unclassified_repos = []
        unclassified_indices = []
        
        for i, repo in enumerate(repos):
            if not repo.get('is_classified', False):
                unclassified_repos.append(repo)
                unclassified_indices.append(i)
        
        if not unclassified_repos:
            self.logger.info("All repositories are already classified")
            return repos
        
        self.logger.info(f"Found {len(unclassified_repos)} unclassified repositories")
        
        # 批量分类
        classification_results = self.classify_repositories_batch(unclassified_repos)
        
        # 更新仓库信息
        updated_repos = repos.copy()
        
        for (local_index, classification_result) in classification_results:
            global_index = unclassified_indices[local_index]
            
            if classification_result:
                updated_repos[global_index].update({
                    'is_classified': True,
                    'category': classification_result['category'],
                    'summary': classification_result['summary'],
                    'key_features': classification_result['key_features']
                })
            else:
                # 标记为分类失败，但设置默认值
                updated_repos[global_index].update({
                    'is_classified': False,
                    'category': '系统工具',  # 默认分类
                    'summary': updated_repos[global_index].get('description', '暂无描述'),
                    'key_features': []
                })
        
        return updated_repos


def main():
    """主函数"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python classify.py <data_file>")
        sys.exit(1)
    
    data_file = sys.argv[1]
    
    try:
        # 加载数据
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        repos = data.get('repositories', [])
        
        # 初始化分类器
        classifier = AIClassifier()
        
        # 执行分类
        updated_repos = classifier.update_repositories_with_classification(repos)
        
        # 更新数据
        data['repositories'] = updated_repos
        
        # 保存结果
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        classified_count = sum(1 for repo in updated_repos if repo.get('is_classified', False))
        print(f"Classification completed: {classified_count}/{len(updated_repos)} repositories classified")
        
    except Exception as e:
        logging.error(f"Error in main execution: {e}")
        raise


if __name__ == "__main__":
    main()