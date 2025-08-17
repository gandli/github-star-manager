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
    
    # 读取现有的README文件
    readme_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'README.md')
    try:
        with open(readme_file, 'r', encoding='utf-8') as f:
            readme_content = f.read()
    except Exception as e:
        print(f"读取README文件失败: {e}")
        # 如果无法读取现有文件，则创建一个新的README
        readme_content = "# GitHub Star Manager\n\n自动化管理和分类您的GitHub Star项目，通过AI生成摘要和分类，帮助您更好地管理和利用已收藏的项目。\n\n## 功能特点\n\n- 自动获取您的GitHub Star项目列表\n- 使用AI对项目进行智能分类\n- 生成项目摘要和关键特性\n- 定期更新README文件，保持项目列表最新\n- 完全基于GitHub Actions自动化运行\n\n## Star项目列表\n\n*此部分将由自动化脚本更新*\n\n## 许可证\n\nMIT"
    
    # 生成Star项目列表内容
    star_list_content = f"*最后更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n用户: [{username}](https://github.com/{username})\n\n"
    
    # 添加分类项目列表
    for category, repos_in_category in sorted(categories.items()):
        star_list_content += f"### {category}\n\n"
        
        # 按Star数量排序
        repos_in_category.sort(key=lambda x: x['stargazers_count'], reverse=True)
        
        for repo in repos_in_category:
            star_list_content += f"#### [{repo['full_name']}]({repo['html_url']})\n\n"
            star_list_content += f"⭐ {repo['stargazers_count']} | 🔄 {repo['forks_count']} | 🔤 {repo['language'] or '未知'}\n\n"
            star_list_content += f"{repo['summary']}\n\n"
            
            # 添加主要特点
            star_list_content += "**主要特点:**\n\n"
            for feature in repo['key_features']:
                star_list_content += f"- {feature}\n"
            star_list_content += "\n"
    
    # 在README中查找并替换"*此部分将由自动化脚本更新*"标记
    if "*此部分将由自动化脚本更新*" in readme_content:
        content = readme_content.replace("*此部分将由自动化脚本更新*", star_list_content)
    else:
        # 如果找不到标记，则查找"## Star项目列表"部分
        star_section_index = readme_content.find("## Star项目列表")
        if star_section_index != -1:
            # 查找下一个标题的位置
            next_section_index = readme_content.find("##", star_section_index + 1)
            if next_section_index != -1:
                # 替换Star项目列表部分
                content = readme_content[:star_section_index] + "## Star项目列表\n\n" + star_list_content + "\n" + readme_content[next_section_index:]
            else:
                # 如果没有下一个标题，则添加到文件末尾
                content = readme_content[:star_section_index] + "## Star项目列表\n\n" + star_list_content
        else:
            # 如果找不到Star项目列表部分，则添加到文件末尾
            content = readme_content + "\n\n## Star项目列表\n\n" + star_list_content
    
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
    username = config.get('GITHUB_USERNAME')
    
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