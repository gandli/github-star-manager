from github import Github
import os
import sys
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
        token = os.getenv('GH_PAT')
    if not token:
        logger.error("未设置GH_TOKEN或GH_PAT环境变量")
        raise ValueError("未设置GH_TOKEN或GH_PAT环境变量")
    return Github(token)

# 获取用户star的项目
def get_starred_repos(g):
    try:
        from config import config
        import time
        user = g.get_user()
        
        # 获取配置参数
        per_page = config["github"]["per_page"]
        max_retries = config["github"]["max_retries"]
        retry_delay = config["github"]["retry_delay"]
        
        # 使用分页参数获取star项目
        try:
            # PyGithub的get_starred()方法不支持sort和direction参数
            # 直接使用基本方法获取star项目
            starred = user.get_starred()
            logger.info(f"成功获取star项目列表")
        except Exception as e:
            logger.error(f"获取star项目失败: {str(e)}")
            raise
        
        # 记录总数
        # PyGithub的PaginatedList对象没有totalCount属性，需要手动计算
        total_count = len(list(starred))
        logger.info(f"共找到 {total_count} 个star项目")
        # 重新获取starred列表，因为上面的操作已经遍历了整个列表
        starred = user.get_starred()
        
        # 分页获取所有项目
        repos = []
        retry_count = 0
        page = 0
        
        # 如果配置了只获取部分项目
        max_repos = config["github"].get("max_repos", 0)
        if max_repos > 0:
            logger.info(f"将只获取最新的 {max_repos} 个star项目")
        
        while True:
            try:
                # 获取当前页的项目
                page_items = starred.get_page(page)
                page_repos = list(page_items)
                
                if not page_repos:
                    # 没有更多项目，退出循环
                    break
                
                # 添加到结果列表
                repos.extend(page_repos)
                logger.info(f"已获取第 {page+1} 页，{len(repos)}/{total_count} 个项目")
                
                # 如果达到最大获取数量，退出循环
                if max_repos > 0 and len(repos) >= max_repos:
                    logger.info(f"已达到最大获取数量 {max_repos}，停止获取")
                    repos = repos[:max_repos]  # 确保不超过最大数量
                    break
                
                # 继续下一页
                page += 1
                retry_count = 0  # 重置重试计数
                
            except Exception as e:
                error_message = str(e)
                retry_count += 1
                
                # 检查是否是API速率限制错误
                if "API rate limit exceeded" in error_message:
                    # 计算更智能的等待时间
                    wait_time = retry_delay * (2 ** (retry_count - 1))  # 指数退避策略
                    wait_time = min(wait_time, 120)  # 最长等待2分钟
                    
                    logger.warning(f"API速率限制，等待 {wait_time} 秒后重试")
                    time.sleep(wait_time)
                    continue
                
                if retry_count > max_retries:
                    logger.error(f"获取第 {page+1} 页star项目失败，已达到最大重试次数: {error_message}")
                    break
                
                logger.warning(f"获取第 {page+1} 页star项目失败，第 {retry_count} 次重试: {error_message}")
                time.sleep(retry_delay * retry_count)  # 递增等待时间
        
        logger.info(f"获取到 {len(repos)} 个star项目")
        return repos
    except Exception as e:
        logger.error(f"获取star项目失败: {str(e)}")
        raise

# 将PyGithub对象转换为字典
def repo_to_dict(repo) -> Dict[str, Any]:
    """将PyGithub仓库对象转换为字典
    
    Args:
        repo: PyGithub仓库对象
        
    Returns:
        包含仓库信息的字典
    """
    try:
        # 基本信息
        repo_dict = {
            "name": repo.name,
            "full_name": repo.full_name,
            "description": repo.description or "",
            "language": repo.language or "未知",
            "stargazers_count": repo.stargazers_count,
            "forks_count": repo.forks_count,
            "updated_at": repo.updated_at,
            "html_url": repo.html_url,
            "created_at": repo.created_at,
            "pushed_at": repo.pushed_at,
            "size": repo.size,
            "default_branch": repo.default_branch,
            "open_issues_count": repo.open_issues_count,
            "is_fork": repo.fork
        }
        
        # 获取主题标签
        try:
            repo_dict["topics"] = repo.get_topics() if hasattr(repo, 'get_topics') else []
        except Exception as e:
            logger.warning(f"获取仓库 {repo.name} 的主题标签失败: {str(e)}")
            repo_dict["topics"] = []
        
        # 尝试获取starred_at时间戳（如果可用）
        try:
            if hasattr(repo, 'starred_at'):
                repo_dict["starred_at"] = repo.starred_at
            # 如果使用特殊API获取starred_at
            elif hasattr(repo, '_starred_at'):
                repo_dict["starred_at"] = repo._starred_at
        except Exception as e:
            logger.warning(f"获取仓库 {repo.name} 的starred_at时间戳失败: {str(e)}")
            # 如果无法获取，使用updated_at作为回退
            repo_dict["starred_at"] = repo_dict["updated_at"]
        
        return repo_dict
    except Exception as e:
        logger.error(f"转换仓库 {repo.name if hasattr(repo, 'name') else 'unknown'} 为字典时出错: {str(e)}")
        # 返回基本信息，确保不会因为单个字段错误导致整个处理失败
        return {
            "name": repo.name if hasattr(repo, 'name') else "未知",
            "full_name": repo.full_name if hasattr(repo, 'full_name') else "未知",
            "html_url": repo.html_url if hasattr(repo, 'html_url') else "",
            "description": "获取详细信息时出错"
        }

# 使用AI生成项目分类和摘要
def generate_summary(repo, ai_processor):
    """生成仓库摘要（已废弃，保留仅为向后兼容）"""
    logger.warning("generate_summary函数已废弃，请直接使用update_readme函数")
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
    
    # 添加主题标签（如果有）
    if hasattr(repo, 'topics') and repo.topics and len(repo.topics) > 0:
        topics_str = ", ".join([f"`{topic}`" for topic in repo.topics])
        base_info += f"- **标签**: {topics_str}\n"
    
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
def update_readme(repos_data, ai_processor):
    """更新README.md文件
    
    Args:
        repos_data: 仓库数据列表
        ai_processor: AI处理器实例
    """
    logger.info("开始更新README.md")
    
    # 导入配置
    from config import config
    
    # 为每个仓库生成markdown内容
    for repo_data in repos_data:
        if "markdown" not in repo_data:
            try:
                # 生成基础项目信息
                base_info = f"""
## [{repo_data['name']}]({repo_data['html_url']})
- **描述**: {repo_data['description'] or '无描述'}
- **语言**: {repo_data['language'] or '未知'}
- **星数**: {repo_data['stargazers_count']}
- **最后更新**: {repo_data['updated_at'].strftime('%Y-%m-%d') if hasattr(repo_data['updated_at'], 'strftime') else repo_data['updated_at']}
- **分类**: {repo_data['category']}
"""
                
                # 添加AI生成的摘要
                if repo_data.get("summary"):
                    base_info += f"- **摘要**: {repo_data['summary']}\n"
                
                # 添加主题标签（如果有）
                if repo_data.get("topics") and len(repo_data["topics"]) > 0:
                    topics_str = ", ".join([f"`{topic}`" for topic in repo_data["topics"]])
                    base_info += f"- **标签**: {topics_str}\n"
                
                repo_data["markdown"] = base_info
            except Exception as e:
                logger.error(f"为仓库 {repo_data.get('name', '未知')} 生成markdown时出错: {str(e)}")
                repo_data["markdown"] = f"\n## [{repo_data.get('name', '未知')}]({repo_data.get('html_url', '#')})\n- 生成详细信息时出错\n"
    
    # 按分类组织
    categories = organize_by_category(repos_data)
    
    # 获取README模板文件路径
    template_file = config["readme"]["template_file"]
    output_file = config["readme"]["output_file"]
    
    # 检查是否存在模板文件
    if os.path.exists(template_file):
        try:
            # 使用模板生成README
            with open(template_file, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # 替换模板变量
            content = template_content
            content = content.replace("{{update_time}}", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            # 生成分类统计表格
            categories_table = "| 分类 | 数量 |\n| --- | --- |\n"
            for category, repos in sorted(categories.items()):
                categories_table += f"| {category} | {len(repos)} |\n"
            content = content.replace("{{categories_table}}", categories_table)
            
            # 生成分类目录
            categories_toc = ""
            for category in sorted(categories.keys()):
                categories_toc += f"- [{category}](#user-content-{category.lower().replace('/', '').replace(' ', '-')})\n"
            content = content.replace("{{categories_toc}}", categories_toc)
            
            # 生成分类内容
            categories_content = ""
            for category, repos in sorted(categories.items()):
                categories_content += f"#### {category}\n\n"
                
                # 排序仓库（如果配置了排序方式）
                sort_by = config["readme"].get("sort_by", "starred_at")
                sort_order = config["readme"].get("sort_order", "desc")
                
                # 根据配置排序仓库
                if sort_by in ["starred_at", "stars", "updated_at"]:
                    if sort_by == "stars":
                        sort_key = "stargazers_count"
                    else:
                        sort_key = sort_by
                    
                    # 排序，处理可能不存在的键
                    sorted_repos = sorted(repos, 
                                          key=lambda x: x.get(sort_key, 0) if sort_key in x else 0, 
                                          reverse=(sort_order == "desc"))
                else:
                    # 默认不排序
                    sorted_repos = repos
                
                # 限制每个分类显示的仓库数量
                max_repos = config["readme"].get("max_repos_per_category", 0)
                if max_repos > 0:
                    sorted_repos = sorted_repos[:max_repos]
                
                # 添加仓库内容
                for repo_data in sorted_repos:
                    categories_content += repo_data["markdown"]
                
                categories_content += "\n"
            
            content = content.replace("{{categories_content}}", categories_content)
            
            # 写入README文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
                
            logger.info(f"使用模板更新README.md完成: {output_file}")
            
        except Exception as e:
            logger.error(f"使用模板更新README.md失败: {str(e)}")
            # 回退到基本方式更新README
            _update_readme_basic(repos_data, categories)
    else:
        logger.warning(f"模板文件不存在: {template_file}，使用基本方式更新README")
        # 使用基本方式更新README
        _update_readme_basic(repos_data, categories)

# 基本方式更新README（不使用模板）
def _update_readme_basic(repos_data, categories):
    """使用基本方式更新README.md（不使用模板）
    
    Args:
        repos_data: 仓库数据列表
        categories: 按分类组织的仓库数据
    """
    try:
        # 导入配置
        from config import config
        output_file = config["readme"]["output_file"]
        
        # 写入README
        with open(output_file, 'w', encoding='utf-8') as f:
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
                
                # 排序仓库（如果配置了排序方式）
                sort_by = config["readme"].get("sort_by", "starred_at")
                sort_order = config["readme"].get("sort_order", "desc")
                
                # 根据配置排序仓库
                if sort_by in ["starred_at", "stars", "updated_at"]:
                    if sort_by == "stars":
                        sort_key = "stargazers_count"
                    else:
                        sort_key = sort_by
                    
                    # 排序，处理可能不存在的键
                    sorted_repos = sorted(repos, 
                                          key=lambda x: x.get(sort_key, 0) if sort_key in x else 0, 
                                          reverse=(sort_order == "desc"))
                else:
                    # 默认不排序
                    sorted_repos = repos
                
                # 限制每个分类显示的仓库数量
                max_repos = config["readme"].get("max_repos_per_category", 0)
                if max_repos > 0:
                    sorted_repos = sorted_repos[:max_repos]
                
                for repo_data in sorted_repos:
                    f.write(repo_data["markdown"])
                f.write("\n")
            
        logger.info(f"基本方式更新README.md完成: {output_file}")
    except Exception as e:
        logger.error(f"基本方式更新README.md失败: {str(e)}")
        raise

# 保存仓库数据到JSON文件
def save_repos_data(repos_data, filename="repos_data.json"):
    """保存仓库数据到JSON文件，用于缓存和分析"""
    try:
        # 导入配置
        from config import config
        
        # 如果未指定输出文件，则使用配置中的路径
        if filename == "repos_data.json":
            filename = os.path.join(config["storage"]["data_dir"], config["storage"]["repos_file"])
        
        # 确保目录存在
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
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
        
        # 导入配置
        from config import config
        
        # 初始化AI处理器
        logger.info("初始化AI处理器")
        ai_token = os.getenv("GH_TOKEN")
        if not ai_token:
            logger.warning("未设置GH_TOKEN环境变量，将使用启发式分类方法")
        
        try:
            ai_processor = AIProcessor(ai_token)
            logger.info("AI处理器初始化成功")
        except Exception as e:
            logger.error(f"AI处理器初始化失败: {str(e)}")
            logger.warning("将使用默认分类方法")
            # 创建一个简单的替代处理器
            class SimpleProcessor:
                def classify_repository(self, repo):
                    return "未分类"
                def generate_summary(self, repo):
                    return repo.get('description', '') or '无描述'
            ai_processor = SimpleProcessor()
        
        # 初始化GitHub客户端并获取star项目
        logger.info("初始化GitHub客户端")
        try:
            g = init_github_client()
            logger.info("GitHub客户端初始化成功")
        except Exception as e:
            logger.error(f"GitHub客户端初始化失败: {str(e)}")
            raise  # GitHub客户端初始化失败是致命错误，无法继续
        
        logger.info("获取star项目列表")
        try:
            starred_repos = get_starred_repos(g)
            logger.info("star项目列表获取成功")
        except Exception as e:
            logger.error(f"获取star项目列表失败: {str(e)}")
            raise  # 获取star项目失败是致命错误，无法继续
        
        # 收集仓库数据
        repos_data = []
        processed_count = 0
        error_count = 0
        
        # 获取总数 - starred_repos 是列表，没有 totalCount 属性
        total_repos = len(starred_repos)
        logger.info(f"共找到 {total_repos} 个star项目")
        
        # 只处理最新的10个仓库数据
        # 按照starred_at时间排序，获取最新的10个
        latest_repos = sorted(starred_repos, key=lambda r: r.updated_at if hasattr(r, 'updated_at') else datetime.now(), reverse=True)[:10]
        logger.info(f"将只处理最新的10个star项目进行测试")
        
        # 处理选定的仓库数据
        logger.info("开始处理仓库数据")
        
        # 设置进度报告间隔
        progress_interval = config.get("processing", {}).get("progress_interval", 10)  # 每处理10个仓库报告一次进度
        
        # 使用分页方式处理最新的10个仓库
        for i, repo in enumerate(latest_repos):
            try:
                # 报告进度
                if i > 0 and i % progress_interval == 0:
                    # 避免除零错误和确保总数是数字
                    latest_total = len(latest_repos)
                    if isinstance(latest_total, (int, float)) and latest_total > 0:
                        percentage = (i / float(latest_total)) * 100
                        logger.info(f"已处理 {i} 个仓库，总计 {latest_total} ({percentage:.1f}%)")
                    else:
                        logger.info(f"已处理 {i} 个仓库")
                
                # 转换为字典并处理
                repo_dict = repo_to_dict(repo)
                
                # 使用AI处理器进行分类和摘要生成，添加错误处理
                # 添加API速率限制处理
                import time
                max_retries = config["github"]["max_retries"]
                retry_count = 0
                
                # 分类仓库
                while retry_count <= max_retries:
                    try:
                        repo_dict["category"] = ai_processor.classify_repository(repo_dict)
                        break  # 成功则跳出循环
                    except Exception as e:
                        error_message = str(e)
                        retry_count += 1
                        
                        # 检查是否是API速率限制错误
                        if "API rate limit exceeded" in error_message or "429" in error_message:
                            # 计算更智能的等待时间
                            wait_time = min(5 * (2 ** (retry_count - 1)), 60)  # 指数退避策略，最长等待60秒
                            
                            logger.warning(f"AI分类API速率限制，等待 {wait_time} 秒后重试 ({retry_count}/{max_retries})")
                            time.sleep(wait_time)
                        else:
                            # 其他错误，记录后继续
                            logger.warning(f"AI分类仓库 {repo_dict.get('name', '未知')} 失败: {error_message}")
                            if retry_count >= max_retries:
                                repo_dict["category"] = "未分类"
                                break
                            time.sleep(2)  # 短暂等待后重试
                
                # 生成摘要
                retry_count = 0
                while retry_count <= max_retries:
                    try:
                        repo_dict["summary"] = ai_processor.generate_summary(repo_dict)
                        break  # 成功则跳出循环
                    except Exception as e:
                        error_message = str(e)
                        retry_count += 1
                        
                        # 检查是否是API速率限制错误
                        if "API rate limit exceeded" in error_message or "429" in error_message:
                            # 计算更智能的等待时间
                            wait_time = min(5 * (2 ** (retry_count - 1)), 60)  # 指数退避策略，最长等待60秒
                            
                            logger.warning(f"AI摘要API速率限制，等待 {wait_time} 秒后重试 ({retry_count}/{max_retries})")
                            time.sleep(wait_time)
                        else:
                            # 其他错误，记录后继续
                            logger.warning(f"AI生成摘要 {repo_dict.get('name', '未知')} 失败: {error_message}")
                            if retry_count >= max_retries:
                                repo_dict["summary"] = repo_dict.get('description', '') or '无描述'
                                break
                            time.sleep(2)  # 短暂等待后重试
                
                # 添加到数据列表
                repos_data.append(repo_dict)
                processed_count += 1
                
            except Exception as e:
                logger.error(f"处理仓库 {repo.name if hasattr(repo, 'name') else '未知'} 数据时出错: {str(e)}")
                error_count += 1
                # 尝试添加基本信息
                try:
                    basic_dict = {
                        "name": repo.name if hasattr(repo, 'name') else "未知",
                        "html_url": repo.html_url if hasattr(repo, 'html_url') else "#",
                        "category": "未分类",
                        "description": "获取信息时出错"
                    }
                    repos_data.append(basic_dict)
                except:
                    pass
        
        logger.info(f"仓库数据处理完成，成功: {processed_count}，失败: {error_count}")
        
        # 保存数据到JSON文件
        try:
            data_file = os.path.join(config["storage"]["data_dir"], config["storage"]["repos_file"])
            save_repos_data(repos_data, data_file)
            logger.info(f"仓库数据已保存到 {data_file}")
        except Exception as e:
            logger.error(f"保存仓库数据时出错: {str(e)}")
            # 继续执行，不中断流程
        
        # 更新README
        logger.info("开始更新README")
        readme_updated = False
        try:
            update_readme(repos_data, ai_processor)
            logger.info("README更新成功")
            readme_updated = True
        except Exception as e:
            logger.error(f"更新README时出错: {str(e)}")
            # 尝试使用基本方式更新
            try:
                logger.info("尝试使用基本方式更新README")
                _update_readme_basic(repos_data)
                logger.info("使用基本方式更新README成功")
                readme_updated = True
            except Exception as e2:
                logger.error(f"基本方式更新README也失败: {str(e2)}")
                # 这里可以添加更多的回退策略
        
        # 报告执行统计
        logger.info("===== 执行统计 =====")
        logger.info(f"仓库总数: {total_repos}")
        logger.info(f"处理最新的仓库数: {len(latest_repos)}")
        logger.info(f"成功处理: {processed_count - error_count}")
        logger.info(f"处理失败: {error_count}")
        logger.info(f"README更新: {'成功' if readme_updated else '失败'}")
        logger.info("===================")
        
        # 报告AI处理器缓存统计
        try:
            if hasattr(ai_processor, 'get_cache_stats'):
                cache_stats = ai_processor.get_cache_stats()
                if cache_stats:
                    logger.info(f"AI处理器缓存统计: {cache_stats}")
        except Exception as e:
            logger.warning(f"获取AI处理器缓存统计失败: {str(e)}")
        
        logger.info("GitHub Star项目自动管理系统执行完成")
    except Exception as e:
        logger.error(f"程序执行出错: {str(e)}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        logger.info("GitHub Star项目自动管理系统异常退出")
        sys.exit(1)  # 返回非零状态码表示错误
    else:
        logger.info("GitHub Star项目自动管理系统正常退出")
        sys.exit(0)  # 返回零状态码表示成功