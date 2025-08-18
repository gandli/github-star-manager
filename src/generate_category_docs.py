#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
按分类生成md文档，替代原来的README.md更新功能
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


def generate_category_content(repos, category, max_items_per_doc=20):
    """
    生成单个分类的文档内容
    
    Args:
        repos: 该分类下的项目列表
        category: 分类名称
        max_items_per_doc: 每个文档最大项目数
        
    Returns:
        list: 文档内容列表（如果项目太多会分成多个文档）
    """
    if not repos:
        return []
    
    # 按star数量降序排序
    repos.sort(key=lambda x: x.get('stargazers_count', 0), reverse=True)
    
    docs = []
    total_repos = len(repos)
    
    # 如果项目数量超过限制，分成多个文档
    for i in range(0, total_repos, max_items_per_doc):
        chunk_repos = repos[i:i + max_items_per_doc]
        doc_num = i // max_items_per_doc + 1
        
        if total_repos > max_items_per_doc:
            title = f"# {category} (第{doc_num}部分)\n\n"
        else:
            title = f"# {category}\n\n"
        
        content = title
        content += f"*更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
        content += f"本分类共有 {total_repos} 个项目"
        
        if total_repos > max_items_per_doc:
            start_idx = i + 1
            end_idx = min(i + max_items_per_doc, total_repos)
            content += f"，当前显示第 {start_idx}-{end_idx} 个项目"
        
        content += "\n\n---\n\n"
        
        for idx, repo in enumerate(chunk_repos, 1):
            global_idx = i + idx
            content += f"## {global_idx}. [{repo['name']}]({repo['html_url']})\n\n"
            
            # 基本信息
            content += f"**仓库:** {repo['full_name']}\n\n"
            if repo.get('description'):
                content += f"**描述:** {repo['description']}\n\n"
            
            # 统计信息
            stars = repo.get('stargazers_count', 0)
            forks = repo.get('forks_count', 0)
            language = repo.get('language', '未知')
            content += f"**Stars:** {stars:,} | **Forks:** {forks:,} | **Language:** {language}\n\n"
            
            # AI生成的摘要和特性
            if repo.get('summary'):
                content += f"**AI摘要:** {repo['summary']}\n\n"
            
            if repo.get('key_features'):
                content += "**主要特性:**\n"
                for feature in repo['key_features']:
                    content += f"- {feature}\n"
                content += "\n"
            
            # 最后更新时间
            if repo.get('updated_at'):
                updated_date = repo['updated_at'][:10]  # 只取日期部分
                content += f"**最后更新:** {updated_date}\n\n"
            
            content += "---\n\n"
        
        docs.append(content)
    
    return docs


def save_category_docs(categories_data, output_dir):
    """
    保存分类文档
    
    Args:
        categories_data: 按分类组织的项目数据
        output_dir: 输出目录
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 清理旧的分类文档
    for file in os.listdir(output_dir):
        if file.startswith('category_') and file.endswith('.md'):
            os.remove(os.path.join(output_dir, file))
            print(f"删除旧文档: {file}")
    
    saved_files = []
    
    for category, repos in categories_data.items():
        if not repos:
            continue
            
        print(f"生成分类 '{category}' 的文档，共 {len(repos)} 个项目")
        
        # 生成该分类的文档内容
        docs = generate_category_content(repos, category)
        
        for doc_idx, content in enumerate(docs, 1):
            if len(docs) > 1:
                filename = f"category_{category.replace('/', '_').replace(' ', '_')}_part{doc_idx}.md"
            else:
                filename = f"category_{category.replace('/', '_').replace(' ', '_')}.md"
            
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            saved_files.append(filename)
            print(f"保存文档: {filename}")
    
    return saved_files


def generate_index_doc(categories_data, saved_files, output_dir):
    """
    生成索引文档
    
    Args:
        categories_data: 按分类组织的项目数据
        saved_files: 已保存的文件列表
        output_dir: 输出目录
    """
    content = "# GitHub Stars 分类索引\n\n"
    content += f"*更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
    
    total_projects = sum(len(repos) for repos in categories_data.values())
    content += f"总计 {len(categories_data)} 个分类，{total_projects} 个项目\n\n"
    content += "---\n\n"
    
    # 按项目数量降序排列分类
    sorted_categories = sorted(categories_data.items(), key=lambda x: len(x[1]), reverse=True)
    
    for category, repos in sorted_categories:
        if not repos:
            continue
            
        content += f"## {category} ({len(repos)} 个项目)\n\n"
        
        # 找到该分类对应的文档文件
        category_files = [f for f in saved_files if f.startswith(f"category_{category.replace('/', '_').replace(' ', '_')}")]
        
        for file in sorted(category_files):
            if '_part' in file:
                part_num = file.split('_part')[1].split('.')[0]
                content += f"- [第{part_num}部分]({file})\n"
            else:
                content += f"- [查看全部]({file})\n"
        
        content += "\n"
    
    # 保存索引文档
    index_file = os.path.join(output_dir, "README.md")
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"保存索引文档: README.md")


def main():
    print("========== 开始执行分类文档生成脚本 ==========")
    
    # 加载配置
    print("正在加载配置文件...")
    config = load_config()
    max_items_per_doc = config.get('max_items_per_doc', 20)  # 每个文档最大项目数
    print(f"配置加载完成，每个文档最大项目数: {max_items_per_doc}")
    
    # 创建输出目录
    print("正在创建输出目录...")
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs')
    os.makedirs(docs_dir, exist_ok=True)
    print(f"文档输出目录已准备: {docs_dir}")
    
    # 加载分类后的项目列表
    print("正在加载分类后的项目列表...")
    input_file = os.path.join(data_dir, 'classified_repos_latest.json')
    if not os.path.exists(input_file):
        print(f"错误: 找不到分类后的项目列表文件 {input_file}")
        sys.exit(1)
    
    repos = load_classified_repos(input_file)
    print(f"已加载{len(repos)}个分类后的项目")
    
    # 按分类组织项目
    print("正在按分类组织项目...")
    categories_data = defaultdict(list)
    for repo in repos:
        category = repo.get('category', '其他')
        categories_data[category].append(repo)
    
    print(f"项目已分为{len(categories_data)}个类别")
    for category, category_repos in categories_data.items():
        print(f"  - {category}: {len(category_repos)}个项目")
    
    # 生成并保存分类文档
    print("正在生成分类文档...")
    saved_files = save_category_docs(categories_data, docs_dir)
    print(f"共生成{len(saved_files)}个分类文档")
    
    # 生成索引文档
    print("正在生成索引文档...")
    generate_index_doc(categories_data, saved_files, docs_dir)
    
    print("========== 分类文档生成脚本执行完成 ==========")


if __name__ == "__main__":
    main()