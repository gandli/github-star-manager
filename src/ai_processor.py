import os
import requests
import json
import logging
import traceback
from typing import Dict, List, Any, Optional
from logging_config import setup_logging

# 配置日志
logger = setup_logging()


class AIProcessor:
    """使用GitHub Models的AI能力处理GitHub仓库信息"""

    def __init__(self, api_key: Optional[str] = None):
        """初始化AI处理器

        Args:
            api_key: GitHub API密钥，如果为None则从环境变量获取
        """
        self.api_key = api_key or os.getenv("GH_TOKEN")
        if not self.api_key:
            logger.warning("未设置GitHub AI API密钥，将使用启发式方法进行分类")

    def classify_repository(self, repo_data: Dict[str, Any]) -> str:
        """对仓库进行分类

        Args:
            repo_data: 仓库数据，包含name, description, language等字段

        Returns:
            分类结果
        """
        if not self.api_key:
            return self._heuristic_classify(repo_data)

        try:
            # 准备请求数据
            prompt = self._generate_classification_prompt(repo_data)
            classification = self._call_github_ai(prompt)
            return classification.strip()
        except Exception as e:
            logger.error(f"AI分类失败: {str(e)}")
            # 失败时回退到启发式方法
            return self._heuristic_classify(repo_data)

    def generate_summary(self, repo_data: Dict[str, Any]) -> str:
        """生成仓库摘要

        Args:
            repo_data: 仓库数据

        Returns:
            生成的摘要
        """
        if not self.api_key:
            return self._generate_basic_summary(repo_data)

        try:
            # 准备请求数据
            prompt = self._generate_summary_prompt(repo_data)
            summary = self._call_github_ai(prompt)
            return summary.strip()
        except Exception as e:
            logger.error(f"AI摘要生成失败: {str(e)}")
            # 失败时回退到基础摘要
            return self._generate_basic_summary(repo_data)

    def _call_github_ai(self, prompt: str) -> str:
        """调用GitHub AI API
        
        Args:
            prompt: 提示词
            
        Returns:
            AI响应
        """
        if not self.api_key:
            logger.warning("未设置API密钥，无法调用AI服务")
            return ""
            
        try:
            logger.debug(f"准备调用AI API，提示词长度: {len(prompt)}")
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            data = {
                "model": "github-copilot",  # 使用GitHub Copilot模型
                "prompt": prompt,
                "max_tokens": 300,
                "temperature": 0.5
            }
            
            logger.debug("发送API请求")
            response = requests.post(
                "https://api.github.com/copilot/completions",
                headers=headers,
                json=data,
                timeout=30  # 设置超时时间
            )
            
            if response.status_code != 200:
                logger.error(f"API调用失败: {response.status_code} - {response.text}")
                raise Exception(f"API调用失败: {response.status_code}")
            
            result = response.json()
            response_text = result.get("choices", [{}])[0].get("text", "")
            logger.debug(f"API调用成功，响应长度: {len(response_text)}")
            return response_text
        except requests.exceptions.Timeout:
            logger.error("API调用超时")
            raise Exception("API调用超时")
        except requests.exceptions.RequestException as e:
            logger.error(f"API请求异常: {str(e)}")
            logger.error(traceback.format_exc())
            raise Exception(f"API请求异常: {str(e)}")
        except Exception as e:
            logger.error(f"调用AI API时发生未知错误: {str(e)}")
            logger.error(traceback.format_exc())
            raise

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

        # 默认分类
        return "其他"

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

        # 格式化更新时间
        if updated_at and hasattr(updated_at, "strftime"):
            updated_at = updated_at.strftime("%Y-%m-%d")

        return f"{description}"
