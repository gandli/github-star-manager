import os
import json
from typing import Dict, Any, List, Optional

# 基础配置
CONFIG = {
    # GitHub配置
    "github": {
        "token": os.getenv("GH_PAT"),  # 优先使用GH_TOKEN，其次使用GH_PAT
        "username": os.getenv(
            "GITHUB_USERNAME", ""
        ),  # GitHub用户名，如果为空则从token获取
        "api_base_url": "https://api.github.com",
        "per_page": 100,  # 每页获取的仓库数量，最大为100
        "max_retries": 3,  # API调用失败时的最大重试次数
        "retry_delay": 5,  # 重试间隔（秒）
    },
    # AI处理配置
    "ai": {
        "token": os.getenv("GITHUB_TOKEN"),  # AI API令牌
        "api_url": "https://api.github.com/copilot/completions",
        "model": "github-copilot",
        "max_tokens": 300,
        "temperature": 0.5,
        "timeout": 30,  # API调用超时时间（秒）
    },
    # 数据存储配置
    "storage": {
        "data_dir": os.path.join(os.path.dirname(os.path.dirname(__file__)), "data"),
        "repos_file": "repos.json",
        "cache_expiry": 86400,  # 缓存过期时间（秒），默认为1天
    },
    # README配置
    "readme": {
        "template_file": os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "templates",
            "README_template.md",
        ),
        "output_file": os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "README.md"
        ),
        "max_repos_per_category": 0,  # 每个分类最多显示的仓库数量，0表示不限制
        "sort_by": "starred_at",  # 排序方式：starred_at, stars, updated_at
        "sort_order": "desc",  # 排序顺序：asc, desc
    },
    # 分类配置
    "categories": [
        "前端开发",
        "后端开发",
        "全栈开发",
        "移动应用开发",
        "人工智能/机器学习",
        "数据科学/分析",
        "DevOps/基础设施",
        "安全工具",
        "开发工具",
        "学习资源",
        "区块链/Web3",
        "游戏开发",
        "物联网",
        "其他",
    ],
}

# 创建必要的目录
os.makedirs(CONFIG["storage"]["data_dir"], exist_ok=True)


# 加载自定义配置（如果存在）
def load_custom_config() -> Dict[str, Any]:
    """加载自定义配置

    Returns:
        合并后的配置
    """
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "config.json"
    )
    custom_config = {}

    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                custom_config = json.load(f)
        except Exception as e:
            print(f"加载自定义配置失败: {str(e)}")

    # 递归合并配置
    return deep_merge(CONFIG, custom_config)


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """递归合并两个字典

    Args:
        base: 基础字典
        override: 覆盖字典

    Returns:
        合并后的字典
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value

    return result


# 导出合并后的配置
config = load_custom_config()
