import os
import requests
import json
import logging
import traceback
import time
from typing import Dict, List, Any, Optional
from logging_config import setup_logging
from config import config

# 配置日志
logger = setup_logging()


class AIProcessor:
    """使用GitHub Models的AI能力处理GitHub仓库信息"""

    def __init__(self, api_key: Optional[str] = None):
        """初始化AI处理器

        Args:
            api_key: GitHub API密钥，如果为None则从配置获取
        """
        self.api_key = api_key or config["ai"]["token"]
        self.cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
        
        if not self.api_key:
            logger.warning("未设置GitHub AI API密钥，将使用启发式方法进行分类")

    def classify_repository(self, repo_data: Dict[str, Any]) -> str:
        """对仓库进行分类

        Args:
            repo_data: 仓库数据，包含name, description, language等字段

        Returns:
            分类结果
        """
        # 检查缓存
        repo_id = repo_data.get("id") or repo_data.get("full_name")
        cache_key = f"classify_{repo_id}"
        
        if cache_key in self.cache:
            self.cache_hits += 1
            logger.debug(f"缓存命中: {cache_key}")
            return self.cache[cache_key]
            
        self.cache_misses += 1
        
        if not self.api_key:
            result = self._heuristic_classify(repo_data)
            self.cache[cache_key] = result
            return result

        try:
            # 准备请求数据
            prompt = self._generate_classification_prompt(repo_data)
            classification = self._call_github_ai(prompt)
            result = classification.strip()
            
            # 验证分类结果是否在预定义分类中
            if result not in config["categories"]:
                # 尝试查找最接近的分类
                for category in config["categories"]:
                    if result.lower() in category.lower() or category.lower() in result.lower():
                        result = category
                        break
                else:
                    # 如果仍然找不到匹配，使用启发式方法
                    result = self._heuristic_classify(repo_data)
            
            # 保存到缓存
            self.cache[cache_key] = result
            return result
        except Exception as e:
            logger.error(f"AI分类失败: {str(e)}")
            # 失败时回退到启发式方法
            result = self._heuristic_classify(repo_data)
            self.cache[cache_key] = result
            return result

    def generate_summary(self, repo_data: Dict[str, Any]) -> str:
        """生成仓库摘要

        Args:
            repo_data: 仓库数据

        Returns:
            生成的摘要
        """
        # 检查缓存
        repo_id = repo_data.get("id") or repo_data.get("full_name")
        cache_key = f"summary_{repo_id}"
        
        if cache_key in self.cache:
            self.cache_hits += 1
            logger.debug(f"缓存命中: {cache_key}")
            return self.cache[cache_key]
            
        self.cache_misses += 1
        
        if not self.api_key:
            result = self._generate_basic_summary(repo_data)
            self.cache[cache_key] = result
            return result

        try:
            # 准备请求数据
            prompt = self._generate_summary_prompt(repo_data)
            summary = self._call_github_ai(prompt)
            result = summary.strip()
            
            # 验证摘要长度，如果太短则使用基础摘要
            if len(result) < 10:
                result = self._generate_basic_summary(repo_data)
                
            # 保存到缓存
            self.cache[cache_key] = result
            return result
        except Exception as e:
            logger.error(f"AI摘要生成失败: {str(e)}")
            # 失败时回退到基础摘要
            result = self._generate_basic_summary(repo_data)
            self.cache[cache_key] = result
            return result

    def _call_github_ai(self, prompt: str) -> str:
        """调用GitHub AI API，包含重试机制

        Args:
            prompt: 提示词

        Returns:
            AI响应
        """
        if not self.api_key:
            logger.warning("未设置API密钥，无法调用AI服务")
            return ""

        max_retries = config["ai"].get("max_retries", 3)
        retry_delay = config["ai"].get("retry_delay", 5)
        timeout = config["ai"].get("timeout", 30)
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"准备调用AI API，提示词长度: {len(prompt)}，尝试次数: {attempt + 1}/{max_retries}")

                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                }

                data = {
                    "model": config["ai"]["model"],
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": config["ai"]["max_tokens"],
                    "temperature": config["ai"]["temperature"],
                }

                logger.debug("发送API请求")
                response = requests.post(
                    config["ai"]["api_url"],
                    headers=headers,
                    json=data,
                    timeout=timeout,
                )

                # 处理速率限制
                if response.status_code == 429:
                    # 使用更智能的指数退避策略
                    retry_after = int(response.headers.get("Retry-After", retry_delay))
                    # 使用较小的基数和指数，避免等待时间过长
                    wait_time = min(retry_after * (1.5 ** attempt), 60)  # 指数退避，最长等待60秒
                    logger.warning(f"API速率限制，等待 {wait_time:.1f} 秒后重试 (尝试 {attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                    
                # 处理其他错误
                if response.status_code != 200:
                    error_msg = f"API调用失败: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    
                    if attempt < max_retries - 1:
                        # 使用更短的递增重试延迟
                        current_delay = min(retry_delay * (1.5 ** attempt), 30)  # 最长等待30秒
                        logger.info(f"将在 {current_delay:.1f} 秒后重试，剩余尝试次数: {max_retries - attempt - 1}")
                        time.sleep(current_delay)
                        continue
                    else:
                        # 记录详细错误信息
                        logger.error(f"API调用失败，已达到最大重试次数。状态码: {response.status_code}，响应: {response.text[:200]}...")
                        # 返回空结果而不是抛出异常，避免中断整个流程
                        return ""

                result = response.json()
                response_text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                logger.debug(f"API调用成功，响应长度: {len(response_text)}")
                return response_text
                
            except requests.exceptions.Timeout:
                logger.error(f"API调用超时，尝试次数: {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    # 使用更短的递增重试延迟
                    current_delay = min(retry_delay * (1.5 ** attempt), 20)  # 最长等待20秒
                    logger.info(f"将在 {current_delay:.1f} 秒后重试")
                    time.sleep(current_delay)
                else:
                    logger.error("API调用超时，已达到最大重试次数")
                    # 返回空结果而不是抛出异常，避免中断整个流程
                    return ""
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"API请求异常: {str(e)}，尝试次数: {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    # 使用更短的递增重试延迟
                    current_delay = min(retry_delay * (1.5 ** attempt), 20)  # 最长等待20秒
                    logger.info(f"将在 {current_delay:.1f} 秒后重试")
                    time.sleep(current_delay)
                else:
                    logger.error(traceback.format_exc())
                    # 返回空结果而不是抛出异常，避免中断整个流程
                    return ""
                    
            except Exception as e:
                logger.error(f"调用AI API时发生未知错误: {str(e)}，尝试次数: {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    # 使用更短的递增重试延迟
                    current_delay = min(retry_delay * (1.5 ** attempt), 20)  # 最长等待20秒
                    logger.info(f"将在 {current_delay:.1f} 秒后重试")
                    time.sleep(current_delay)
                else:
                    logger.error(traceback.format_exc())
                    # 返回空结果而不是抛出异常，避免中断整个流程
                    return ""

    def _generate_classification_prompt(self, repo_data: Dict[str, Any]) -> str:
        """生成分类提示词

        Args:
            repo_data: 仓库数据

        Returns:
            提示词
        """
        name = repo_data.get("name", "")
        description = repo_data.get("description", "")
        language = repo_data.get("language", "")
        topics = repo_data.get("topics", [])

        prompt = f"""请根据以下GitHub仓库信息，将其分类到最合适的一个类别中：
        
仓库名称: {name}
描述: {description}
主要语言: {language}
主题标签: {", ".join(topics)}

请从以下类别中选择一个最合适的（如果都不合适，可以提供一个新的合适分类）：
- 前端开发
- 后端开发
- 全栈开发
- 移动应用开发
- 人工智能/机器学习
- 数据科学/分析
- DevOps/基础设施
- 安全工具
- 开发工具
- 学习资源
- 区块链/Web3
- 游戏开发
- 物联网
- 其他

只需回复分类名称，不要包含其他内容。"""

        return prompt

    def _generate_summary_prompt(self, repo_data: Dict[str, Any]) -> str:
        """生成摘要提示词

        Args:
            repo_data: 仓库数据

        Returns:
            提示词
        """
        name = repo_data.get("name", "")
        description = repo_data.get("description", "")
        language = repo_data.get("language", "")
        topics = repo_data.get("topics", [])
        stars = repo_data.get("stargazers_count", 0)

        prompt = f"""请根据以下GitHub仓库信息，生成一个简短的中文摘要（不超过100字），突出其主要功能和价值：
        
仓库名称: {name}
描述: {description}
主要语言: {language}
主题标签: {", ".join(topics)}
星标数: {stars}

摘要应该简洁明了地说明这个项目是什么，能做什么，为什么值得关注。
只需回复摘要内容，不要包含其他内容。"""

        return prompt

    def _heuristic_classify(self, repo_data: Dict[str, Any]) -> str:
        """使用启发式方法进行分类
        
        基于仓库的描述、语言和主题标签，使用关键词匹配进行分类

        Args:
            repo_data: 仓库数据

        Returns:
            分类结果
        """
        description = (
            repo_data.get("description", "").lower()
            if repo_data.get("description")
            else ""
        )
        language = (
            repo_data.get("language", "").lower() if repo_data.get("language") else ""
        )
        topics = [t.lower() for t in repo_data.get("topics", [])]

        # 合并所有文本以进行分类
        all_text = description + " " + language + " " + " ".join(topics)

        # 前端开发
        if any(
            keyword in all_text
            for keyword in [
                "frontend",
                "front-end",
                "react",
                "vue",
                "angular",
                "javascript",
                "typescript",
                "html",
                "css",
                "ui",
                "ux",
            ]
        ):
            return "前端开发"

        # 后端开发
        if any(
            keyword in all_text
            for keyword in [
                "backend",
                "back-end",
                "api",
                "server",
                "database",
                "django",
                "flask",
                "express",
                "spring",
                "node.js",
            ]
        ):
            return "后端开发"

        # 全栈开发
        if any(
            keyword in all_text
            for keyword in ["fullstack", "full-stack", "web app", "webapp"]
        ):
            return "全栈开发"

        # 移动应用开发
        if any(
            keyword in all_text
            for keyword in [
                "mobile",
                "android",
                "ios",
                "flutter",
                "react native",
                "swift",
                "kotlin",
            ]
        ):
            return "移动应用开发"

        # 人工智能/机器学习
        if any(
            keyword in all_text
            for keyword in [
                "ai",
                "artificial intelligence",
                "machine learning",
                "ml",
                "deep learning",
                "neural",
                "tensorflow",
                "pytorch",
                "nlp",
            ]
        ):
            return "人工智能/机器学习"

        # 数据科学/分析
        if any(
            keyword in all_text
            for keyword in [
                "data science",
                "data analysis",
                "analytics",
                "visualization",
                "pandas",
                "jupyter",
                "statistics",
            ]
        ):
            return "数据科学/分析"

        # DevOps/基础设施
        if any(
            keyword in all_text
            for keyword in [
                "devops",
                "ci/cd",
                "pipeline",
                "docker",
                "kubernetes",
                "k8s",
                "infrastructure",
                "deploy",
                "aws",
                "cloud",
            ]
        ):
            return "DevOps/基础设施"

        # 安全工具
        if any(
            keyword in all_text
            for keyword in [
                "security",
                "pentest",
                "penetration",
                "hacking",
                "vulnerability",
                "encryption",
                "crypto",
            ]
        ):
            return "安全工具"

        # 开发工具
        if any(
            keyword in all_text
            for keyword in [
                "tool",
                "utility",
                "plugin",
                "extension",
                "ide",
                "editor",
                "development tool",
            ]
        ):
            return "开发工具"

        # 学习资源
        if any(
            keyword in all_text
            for keyword in [
                "tutorial",
                "course",
                "learning",
                "education",
                "book",
                "guide",
                "example",
                "awesome",
            ]
        ):
            return "学习资源"

        # 区块链/Web3
        if any(
            keyword in all_text
            for keyword in [
                "blockchain",
                "web3",
                "crypto",
                "nft",
                "token",
                "ethereum",
                "bitcoin",
                "solidity",
            ]
        ):
            return "区块链/Web3"

        # 游戏开发
        if any(
            keyword in all_text for keyword in ["game", "unity", "unreal", "gaming"]
        ):
            return "游戏开发"

        # 物联网
        if any(
            keyword in all_text
            for keyword in [
                "iot",
                "internet of things",
                "embedded",
                "arduino",
                "raspberry pi",
            ]
        ):
            return "物联网"

        # 检查是否有README或文档相关的关键词
        if any(
            keyword in all_text
            for keyword in [
                "awesome",
                "list",
                "resource",
                "collection",
                "tutorial",
                "guide",
                "book",
                "course",
                "learn",
                "cheatsheet",
                "documentation",
            ]
        ):
            return "学习资源"
            
        # 默认分类
        return "其他"
        
    def get_cache_stats(self) -> Dict[str, int]:
        """获取缓存统计信息
        
        Returns:
            包含缓存命中和未命中次数的字典
        """
        return {
            "hits": self.cache_hits,
            "misses": self.cache_misses,
            "total": self.cache_hits + self.cache_misses,
            "hit_rate": self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0
        }
        
    def clear_cache(self) -> None:
        """清除缓存"""
        self.cache.clear()
        logger.info("缓存已清除")

    def _generate_basic_summary(self, repo_data: Dict[str, Any]) -> str:
        """生成基础摘要

        Args:
            repo_data: 仓库数据

        Returns:
            基础摘要
        """
        name = repo_data.get("name", "")
        description = repo_data.get("description", "无描述")
        language = repo_data.get("language", "未知")
        stars = repo_data.get("stargazers_count", 0)
        updated_at = repo_data.get("updated_at", "")
        topics = repo_data.get("topics", [])

        # 格式化更新时间
        if updated_at and hasattr(updated_at, "strftime"):
            updated_at = updated_at.strftime("%Y-%m-%d")

        # 如果描述为空，尝试使用其他信息构建摘要
        if description == "无描述" or not description:
            if topics:
                return f"一个{language}项目，主题包括: {', '.join(topics[:3])}"
            else:
                return f"一个{language}项目，已获得{stars}个星标"
        
        return f"{description}"
