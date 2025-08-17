from github import Github
import os
import json
import logging
import traceback
from datetime import datetime
from typing import Dict, List, Any
from ai_processor import AIProcessor
from logging_config import setup_logging

# 配置日志
logger = setup_logging()

# 初始化GitHub客户端
def init_github_client():
    token = os.getenv('GH_TOKEN') 
    if not token:
        logger.error("未设置GH_TOKEN或GH_PAT环境变量")
        raise ValueError("未设置GH_TOKEN或GH_PAT环境变量")
    return Github(token)

# 获取用户star的项目
def get_starred_repos(g):
    try:
        user = g.get_user()
        starred = user.get_starred()
        logger.info(f"成功获取star项目列表")
        return starred
    except Exception as e:
        logger.error(f"获取star项目失败: {str(e)}")
        raise

# 将PyGithub对象转换为字典
def repo_to_dict(repo) -> Dict[str, Any]:
    """将PyGithub仓库对象转换为字典"""
    return {
        "name": repo.name,
        "full_name": repo.full_name,
        "description": repo.description,
        "language": repo.language,
        "stargazers_count": repo.stargazers_count,
        "forks_count": repo.forks_count,
        "updated_at": repo.updated_at,
        "html_url": repo.html_url,
        "topics": repo.get_topics() if hasattr(repo, 'get_topics') else []
    }

# 使用AI生成项目分类和摘要
def generate_summary(repo, ai_processor):
    # 转换为字典
    repo_dict = repo_to_dict(repo)
    
    # 使用AI处理器进行分类和摘要生成
    category = ai_processor.classify_repository(repo_dict)
    summary = ai_processor.generate_summary(repo_dict)
    
    # 基础项目信息
    base_info = f"""
## [{repo.name}]({repo.html_url})
- **描述**: {repo.description or '无描述'}
- **语言**: {repo.language or '未知'}
- **星数**: {repo.stargazers_count}
- **最后更新**: {repo.updated_at.strftime('%Y-%m-%d')}
- **分类**: {category}
"""
    
    # 添加AI生成的摘要
    if summary:
        base_info += f"- **摘要**: {summary}\n"
    
    return base_info

# 按分类组织仓库
def organize_by_category(repos_data):
    """将仓库按分类组织"""
    categories = {}
    
    for repo_data in repos_data:
        category = repo_data.get("category", "其他")
        if category not in categories:
            categories[category] = []
        categories[category].append(repo_data)
    
    return categories

# 更新README.md
def update_readme(repos, ai_processor):
    logger.info("开始更新README.md")
    
    # 收集所有仓库数据
    repos_data = []
    for repo in repos:
        try:
            repo_dict = repo_to_dict(repo)
            repo_dict["category"] = ai_processor.classify_repository(repo_dict)
            repo_dict["summary"] = ai_processor.generate_summary(repo_dict)
            repo_dict["markdown"] = generate_summary(repo, ai_processor)
            repos_data.append(repo_dict)
        except Exception as e:
            logger.error(f"处理仓库 {repo.name} 时出错: {str(e)}")
    
    # 按分类组织
    categories = organize_by_category(repos_data)
    
    # 写入README
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write("# 我的GitHub Star项目 [![Update Starred Repos](https://github.com/gandli/github-star-manager/actions/workflows/update_stars.yml/badge.svg)](https://github.com/gandli/github-star-manager/actions/workflows/update_stars.yml)\n\n")
        f.write(f"最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # 添加项目简介
        f.write("## GitHub Star项目自动管理系统\n\n")
        f.write("这是一个自动化的GitHub Star项目管理系统，通过GitHub Actions定期更新我的star项目列表。\n\n")
        
        # 添加功能介绍
        f.write("### 功能\n")
        f.write("- 自动获取我的GitHub star项目\n")
        f.write("- 使用AI进行项目分类和摘要生成\n")
        f.write("- 自动更新项目信息到本README\n")
        f.write("- 每天自动运行更新\n\n")
        
        # 添加分类统计
        f.write("### 分类统计\n\n")
        f.write("| 分类 | 数量 |\n")
        f.write("| --- | --- |\n")
        for category, repos in sorted(categories.items()):
            f.write(f"| {category} | {len(repos)} |\n")
        f.write("\n")
        
        # 按分类展示项目
        f.write("### 项目列表\n\n")
        
        # 创建分类目录
        f.write("#### 目录\n\n")
        for category in sorted(categories.keys()):
            f.write(f"- [{category}](#user-content-{category.lower().replace('/', '').replace(' ', '-')})\n")
        f.write("\n")
        
        # 按分类展示项目
        for category, repos in sorted(categories.items()):
            f.write(f"#### {category}\n\n")
            for repo_data in repos:
                f.write(repo_data["markdown"])
            f.write("\n")
        
    logger.info("README.md更新完成")

# 保存仓库数据到JSON文件
def save_repos_data(repos_data, filename="repos_data.json"):
    """保存仓库数据到JSON文件，用于缓存和分析"""
    try:
        # 转换datetime对象为字符串
        for repo in repos_data:
            if "updated_at" in repo and hasattr(repo["updated_at"], "strftime"):
                repo["updated_at"] = repo["updated_at"].strftime("%Y-%m-%d %H:%M:%S")
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(repos_data, f, ensure_ascii=False, indent=2)
        logger.info(f"仓库数据已保存到 {filename}")
    except Exception as e:
        logger.error(f"保存仓库数据失败: {str(e)}")

if __name__ == "__main__":
    try:
        logger.info("开始执行GitHub Star项目自动管理系统")
        
        # 初始化AI处理器
        logger.info("初始化AI处理器")
        ai_processor = AIProcessor()
        
        # 初始化GitHub客户端并获取star项目
        logger.info("初始化GitHub客户端")
        g = init_github_client()
        
        logger.info("获取star项目列表")
        starred_repos = get_starred_repos(g)
        
        # 收集仓库数据
        repos_data = []
        total_repos = 0
        
        # 计算总数
        try:
            total_repos = starred_repos.totalCount
            logger.info(f"共找到 {total_repos} 个star项目")
        except:
            logger.warning("无法获取star项目总数")
        
        # 更新README
        logger.info("开始更新README")
        update_readme(starred_repos, ai_processor)
        
        # 保存仓库数据
        try:
            # 收集所有仓库数据用于保存
            repos_data = []
            for repo in starred_repos:
                try:
                    repo_dict = repo_to_dict(repo)
                    repo_dict["category"] = ai_processor.classify_repository(repo_dict)
                    repo_dict["summary"] = ai_processor.generate_summary(repo_dict)
                    repos_data.append(repo_dict)
                except Exception as e:
                    logger.error(f"处理仓库 {repo.name} 数据时出错: {str(e)}")
            
            # 保存数据到JSON文件
            save_repos_data(repos_data)
        except Exception as e:
            logger.error(f"保存仓库数据时出错: {str(e)}")
        
        logger.info("处理完成")
    except Exception as e:
        logger.error(f"程序执行出错: {str(e)}")
        logger.error(traceback.format_exc())
        raise