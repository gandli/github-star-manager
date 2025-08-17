#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
更新README.md文件，将分类后的Star项目列表添加到文档中
"""

import os
import sys
import json
import yaml
from datetime import datetime
from collections import defaultdict


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


def load_classified_repos(input_file):
    """
    加载分类后的项目列表
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载分类后的项目列表失败: {e}")
        sys.exit(1)


def generate_readme_content(repos, username):
    """
    生成README内容
    """
    # 按分类组织项目
    categories = defaultdict(list)
    for repo in repos:
        categories[repo['category']].append(repo)
    
    # 生成README内容
    content = f"# GitHub Star Manager

自动化管理和分类您的GitHub Star项目，通过AI生成摘要和分类，帮助您更好地管理和利用已收藏的项目。

## 功能特点

- 自动获取您的GitHub Star项目列表
- 使用AI对项目进行智能分类
- 生成项目摘要和关键特性
- 定期更新README文件，保持项目列表最新
- 完全基于GitHub Actions自动化运行

## 使用方法

1. Fork本仓库
2. 在仓库设置中添加以下Secrets:
   - `GH_PAT`: GitHub个人访问令牌，需要有`repo`和`user`权限
   - `AI_API_KEY`: AI API密钥（用于智能分类和摘要生成）
3. 修改配置文件中的用户名为您的GitHub用户名
4. 启用GitHub Actions

## 项目结构

```
.
├── .github/workflows/  # GitHub Actions工作流配置
├── src/                # 源代码
│   ├── fetch_stars.py  # 获取Star项目列表
│   ├── classify.py     # 项目分类和摘要生成
│   └── update_readme.py # 更新README文件
├── config.yaml         # 配置文件
└── README.md           # 项目说明文档
```

## 配置选项

在`config.yaml`文件中，您可以自定义以下选项：

- `username`: 您的GitHub用户名
- `update_interval`: 更新频率（天）
- `categories`: 自定义分类类别
- `max_stars`: 最大获取的Star项目数量

## Star项目列表

*最后更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

用户: [{username}](https://github.com/{username})

"""
    
    # 添加分类项目列表
    for category, repos_in_category in sorted(categories.items()):
        content += f"### {category}\n\n"
        
        # 按Star数量排序
        repos_in_category.sort(key=lambda x: x['stargazers_count'], reverse=True)
        
        for repo in repos_in_category:
            content += f"#### [{repo['full_name']}]({repo['html_url']})\n\n"
            content += f"⭐ {repo['stargazers_count']} | 🔄 {repo['forks_count']} | 🔤 {repo['language'] or '未知'}\n\n"
            content += f"{repo['summary']}\n\n"
            
            # 添加主要特点
            content += "**主要特点:**\n\n"
            for feature in repo['key_features']:
                content += f"- {feature}\n"
            content += "\n"
    
    content += "\n## 许可证\n\nMIT\n"
    
    return content


def update_readme(content, readme_file):
    """
    更新README文件
    """
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"已更新README文件: {readme_file}")


def main():
    # 加载配置
    config = load_config()
    username = config.get('username')
    
    if username == "USERNAME":
        print("错误: 请在config.yaml中设置您的GitHub用户名")
        sys.exit(1)
    
    # 加载分类后的项目列表
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    input_file = os.path.join(data_dir, 'classified_repos_latest.json')
    
    if not os.path.exists(input_file):
        print(f"错误: 找不到分类后的项目列表文件 {input_file}")
        sys.exit(1)
    
    repos = load_classified_repos(input_file)
    print(f"已加载{len(repos)}个分类后的项目")
    
    # 生成README内容
    content = generate_readme_content(repos, username)
    
    # 更新README文件
    readme_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'README.md')
    update_readme(content, readme_file)


if __name__ == "__main__":
    main()