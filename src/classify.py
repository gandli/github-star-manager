#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
使用AI对GitHub Star项目进行分类和摘要生成
"""

import os
import sys
import json
import yaml
import requests
from datetime import datetime
from data_manager import data_manager


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


def load_repos(input_file):
    """
    加载项目列表
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载项目列表失败: {e}")
        sys.exit(1)


def call_ai_api(api_key, api_url, model, prompt, max_retries=3, retry_delay=5):
    """
    调用Cloudflare Workers AI API进行项目分类和摘要生成
    
    Args:
        api_key: Cloudflare Workers AI API密钥
        api_url: API地址
        model: 模型名称（用于Cloudflare Workers AI）
        prompt: 提示词
        max_retries: 最大重试次数
        retry_delay: 重试间隔（秒）
        
    Returns:
        str: AI生成的回复
    """
    import time
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Cloudflare Workers AI API格式 - 使用input字段
    system_prompt = "你是一个专业的GitHub项目分析助手，擅长对项目进行分类和生成摘要。"
    full_prompt = f"{system_prompt}\n\n{prompt}"
    
    data = {
        "input": full_prompt
    }
    
    for attempt in range(max_retries):
        try:
            # 添加请求间隔，避免并发过高
            if attempt > 0:
                print(f"等待{retry_delay}秒后进行第{attempt+1}次重试...")
                time.sleep(retry_delay)
                # 每次重试增加等待时间，避免连续失败
                retry_delay *= 1.5
            
            response = requests.post(api_url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            # 处理Cloudflare Workers AI响应格式
            if 'result' in result and 'result' in result and 'output' in result['result']:
                # Cloudflare Workers AI格式: result.result.output[1].content[0].text
                output = result['result']['output']
                if len(output) > 1 and 'content' in output[1] and len(output[1]['content']) > 0:
                    return output[1]['content'][0]['text']
                else:
                    print(f"Cloudflare Workers AI响应格式异常: {result}")
                    return None
            elif 'choices' in result:
                # OpenAI格式（兼容性）
                return result['choices'][0]['message']['content']
            else:
                print(f"未知的API响应格式: {result}")
                return None
        except requests.exceptions.HTTPError as e:
            # 特别处理429错误（请求过多）
            if hasattr(e, 'response') and e.response.status_code == 429:
                print(f"API请求过多(429)，第{attempt+1}次重试...")
                if attempt == max_retries - 1:  # 最后一次重试
                    print(f"达到最大重试次数({max_retries})，放弃请求")
                    if hasattr(e, 'response') and hasattr(e.response, 'text'):
                        print(f"响应内容: {e.response.text}")
                    return None
                # 对于429错误，增加更长的等待时间
                time.sleep(retry_delay * 2)
            else:
                print(f"调用AI API失败: {e}")
                if hasattr(e, 'response') and hasattr(e.response, 'text'):
                    print(f"响应内容: {e.response.text}")
                return None
        except Exception as e:
            print(f"调用AI API失败: {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                print(f"响应内容: {e.response.text}")
            return None
    
    return None


def generate_repo_prompt(repo, categories):
    """
    生成项目分析提示词
    """
    prompt = f"""请分析以下GitHub项目，并提供分类和摘要：

项目名称: {repo['name']}
项目描述: {repo['description'] or '无描述'}
主要语言: {repo['language'] or '未知'}
项目主题: {', '.join(repo['topics']) if repo['topics'] else '无'}
Star数量: {repo['stargazers_count']}
Fork数量: {repo['forks_count']}
项目URL: {repo['html_url']}

请从以下类别中选择最合适的一个：{', '.join(categories)}

请以JSON格式返回以下内容：
1. category: 从上述类别中选择的最合适分类
2. summary: 项目的简短摘要（不超过100字）
3. key_features: 项目的主要特点（列出3-5点）

只返回JSON格式的结果，不要有其他文字。"""
    return prompt


def parse_ai_response(response):
    """
    解析AI返回的结果
    """
    try:
        # 尝试直接解析JSON
        return json.loads(response)
    except json.JSONDecodeError:
        # 如果直接解析失败，尝试提取JSON部分
        try:
            # 查找可能的JSON部分（通常在```json和```之间）
            if '```json' in response and '```' in response.split('```json', 1)[1]:
                json_part = response.split('```json', 1)[1].split('```', 1)[0]
                return json.loads(json_part)
            # 或者尝试查找{和}之间的内容
            elif '{' in response and '}' in response:
                json_part = response[response.find('{'):response.rfind('}')+1]
                return json.loads(json_part)
        except (json.JSONDecodeError, IndexError):
            pass
    
    # 如果无法解析，返回一个默认结果
    print(f"无法解析AI响应为JSON: {response}")
    return {
        "category": "其他",
        "summary": "无法生成摘要",
        "key_features": ["无法识别特点"]
    }


def process_repo(repo, api_key, api_url, model, categories, request_interval=3):
    """
    处理单个项目
    """
    import time
    
    # 生成提示词
    prompt = generate_repo_prompt(repo, categories)
    
    # 调用AI API
    response = call_ai_api(api_key, api_url, model, prompt)
    
    if response:
        # 解析结果
        result = parse_ai_response(response)
        
        # 添加分类和摘要到项目信息中
        repo_with_analysis = repo.copy()
        category = result.get('category', '其他')
        repo_with_analysis['category'] = category
        repo_with_analysis['summary'] = result.get('summary', '无摘要')
        repo_with_analysis['key_features'] = result.get('key_features', ['无特点'])
        
        # 更新数据管理器中的分类信息
        try:
            confidence = result.get('confidence', 0.8)  # 默认置信度
            reason = f"AI分类结果: {result.get('summary', '无摘要')}"
            data_manager.update_classification(
                repo['full_name'], 
                category, 
                confidence, 
                reason
            )
        except Exception as e:
            print(f"更新数据管理器失败: {repo['full_name']} - {e}")
        
        print(f"成功处理: {repo['full_name']}")
    else:
        # 如果AI调用失败，使用默认值
        repo_with_analysis = repo.copy()
        category = '其他'
        repo_with_analysis['category'] = category
        repo_with_analysis['summary'] = '无法生成摘要'
        repo_with_analysis['key_features'] = ['无法识别特点']
        
        # 更新数据管理器中的分类信息（失败情况）
        try:
            data_manager.update_classification(
                repo['full_name'], 
                category, 
                0.1,  # 低置信度
                "AI分类失败，使用默认分类"
            )
        except Exception as e:
            print(f"更新数据管理器失败: {repo['full_name']} - {e}")
        
        print(f"处理失败: {repo['full_name']}，使用默认值")
    
    # 添加请求间隔，避免API并发过高
    time.sleep(request_interval)
    
    return repo_with_analysis


def classify_repos(repos, api_key, api_url, model, categories, request_interval=3, max_concurrent=2):
    """
    对项目列表进行分类和摘要生成
    
    Args:
        repos: 项目列表
        api_key: AI API密钥
        api_url: API地址
        model: 模型名称
        categories: 分类列表
        request_interval: 请求间隔（秒），避免API并发过高
        max_concurrent: 最大并发数，限制同时处理的项目数量
    """
    import time
    import concurrent.futures
    from threading import Lock
    
    classified_repos = []
    total = len(repos)
    print(f"开始处理{total}个项目，最大并发数: {max_concurrent}")
    
    # 使用线程池限制并发数
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent) as executor:
        # 提交所有任务
        future_to_repo = {executor.submit(process_repo, repo, api_key, api_url, model, categories, request_interval): repo 
                         for repo in repos}
        
        # 收集结果
        for i, future in enumerate(concurrent.futures.as_completed(future_to_repo)):
            repo = future_to_repo[future]
            try:
                repo_with_analysis = future.result()
                classified_repos.append(repo_with_analysis)
                print(f"完成 [{i+1}/{total}]: {repo['full_name']}")
            except Exception as e:
                print(f"处理 {repo['full_name']} 时发生错误: {e}")
                # 如果处理失败，使用默认值
                repo_with_analysis = repo.copy()
                repo_with_analysis['category'] = '其他'
                repo_with_analysis['summary'] = '处理出错'
                repo_with_analysis['key_features'] = ['处理过程中出错']
                classified_repos.append(repo_with_analysis)
    
    return classified_repos


def save_classified_repos(repos, output_file):
    """
    保存分类后的项目列表到文件
    """
    print(f"正在保存{len(repos)}个分类后的项目到文件: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(repos, f, ensure_ascii=False, indent=2)
    print(f"文件保存成功: {output_file}")


def main():
    print("========== 开始执行项目分类和摘要生成脚本 ==========")
    # 获取AI API密钥
    print("正在获取AI API密钥...")
    ai_api_key = os.environ.get('AI_API_KEY')
    if not ai_api_key:
        print("错误: 未设置AI_API_KEY环境变量")
        sys.exit(1)
    print("成功获取AI API密钥")
    
    # 获取AI账户ID
    print("正在获取AI账户ID...")
    ai_account_id = os.environ.get('AI_ACCOUNT_ID')
    if not ai_account_id:
        print("错误: 未设置AI_ACCOUNT_ID环境变量")
        sys.exit(1)
    print("成功获取AI账户ID")
    
    # 加载配置
    print("正在加载配置文件...")
    config = load_config()
    ai_model = config.get('ai_model', '@cf/openai/gpt-oss-20b')
    # 动态构建API URL
    ai_api_url = f"https://api.cloudflare.com/client/v4/accounts/{ai_account_id}/ai/run/{ai_model}"
    categories = config.get('categories', ['其他'])
    incremental_update = config.get('incremental_update', True)
    max_process_count = config.get('max_stars', 50)  # 每次最多处理的项目数
    print(f"配置加载完成，使用模型: {ai_model}")
    print(f"API地址: {ai_api_url}")
    print(f"可用分类: {', '.join(categories)}")
    print(f"增量更新模式: {incremental_update}")
    print(f"每次最多处理项目数: {max_process_count}")
    
    # 获取分类进度统计
    stats = data_manager.get_statistics()
    print(f"当前分类进度: 总计{stats['total_stars']}个项目，已分类{stats['classified_count']}个，未分类{stats['unclassified_count']}个")
    
    # 创建输出目录
    print("正在创建输出目录...")
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    os.makedirs(data_dir, exist_ok=True)
    print(f"输出目录已准备: {data_dir}")
    
    # 加载最新的项目列表
    print("正在加载最新的项目列表...")
    input_file = os.path.join(data_dir, 'starred_repos_latest.json')
    if not os.path.exists(input_file):
        print(f"错误: 找不到项目列表文件 {input_file}")
        sys.exit(1)
    
    repos = load_repos(input_file)
    print(f"已加载{len(repos)}个Star项目")
    
    # 确保所有项目都已添加到数据管理器中
    print("正在同步项目数据到数据管理器...")
    for repo in repos:
        data_manager.add_or_update_star(repo)
    print("项目数据同步完成")
    
    # 如果是增量更新，只处理未分类的项目
    if incremental_update:
        print("增量更新模式：正在获取未分类的项目...")
        
        # 获取未分类的项目
        unclassified_stars = data_manager.get_unclassified_stars()
        print(f"发现{len(unclassified_stars)}个未分类项目")
        
        if not unclassified_stars:
            print("没有未分类项目，跳过AI分类步骤")
            # 获取所有已分类项目用于生成文档
            classified_stars = data_manager.get_classified_stars()
            classified_repos = []
            for star_id, star_data in classified_stars.items():
                classified_repos.append(star_data)
            print(f"使用现有{len(classified_repos)}个已分类项目生成文档")
        else:
            # 将未分类的star数据转换为repos格式
            unclassified_repos = []
            for star_id, star_data in unclassified_stars.items():
                unclassified_repos.append(star_data)
            
            # 按时间升序排序未分类项目（最早添加的项目优先处理）
            unclassified_repos.sort(key=lambda x: x.get('added_date', '1970-01-01T00:00:00Z'), reverse=False)
            print(f"已按项目添加时间升序排序未分类项目")
            
            # 限制处理数量
            if len(unclassified_repos) > max_process_count:
                unclassified_repos = unclassified_repos[:max_process_count]
                print(f"限制处理数量为{max_process_count}个项目（按时间升序选择最早的项目）")
            
            # 只对未分类项目进行分类
            print(f"开始对{len(unclassified_repos)}个未分类项目进行AI分类和摘要生成...")
            print(f"设置请求间隔为5秒，最大并发数为2，以避免API并发限制")
            new_classified_repos = classify_repos(unclassified_repos, ai_api_key, ai_api_url, ai_model, categories, 
                                                request_interval=5, max_concurrent=2)
            print(f"未分类项目AI分类完成，共处理{len(new_classified_repos)}个项目")
            
            # 获取所有已分类项目（包括新分类的）
            all_classified_stars = data_manager.get_classified_stars()
            classified_repos = []
            for star_id, star_data in all_classified_stars.items():
                classified_repos.append(star_data)
            print(f"总计{len(classified_repos)}个已分类项目将用于生成文档")
    
    # 如果不是增量更新，对所有项目进行分类
    if not incremental_update or 'classified_repos' not in locals():
        print("全量更新模式：开始对所有项目进行分类和摘要生成...")
        
        # 按时间升序排序项目（最早添加的项目优先处理）
        repos.sort(key=lambda x: x.get('created_at', '1970-01-01T00:00:00Z'), reverse=False)
        print(f"已按项目创建时间升序排序项目")
        
        # 限制处理数量
        if len(repos) > max_process_count:
            repos = repos[:max_process_count]
            print(f"限制处理数量为{max_process_count}个项目（按时间升序选择最早的项目）")
        
        print(f"设置请求间隔为5秒，最大并发数为2，以避免API并发限制")
        # 设置较长的请求间隔和最大并发数为2，避免API并发限制
        new_classified_repos = classify_repos(repos, ai_api_key, ai_api_url, ai_model, categories, 
                                        request_interval=5, max_concurrent=2)
        print(f"项目分类和摘要生成完成，共处理{len(new_classified_repos)}个项目")
        
        # 获取所有已分类项目
        all_classified_stars = data_manager.get_classified_stars()
        classified_repos = []
        for star_id, star_data in all_classified_stars.items():
            classified_repos.append(star_data)
        print(f"总计{len(classified_repos)}个已分类项目将用于生成文档")
    
    # 保存结果
    print("正在保存分类结果...")
    timestamp = datetime.now().strftime('%Y%m%d')
    output_file = os.path.join(data_dir, f'classified_repos_{timestamp}.json')
    save_classified_repos(classified_repos, output_file)
    
    # 同时保存一个最新版本
    latest_file = os.path.join(data_dir, 'classified_repos_latest.json')
    save_classified_repos(classified_repos, latest_file)
    
    # 保存数据管理器的数据
    try:
        data_manager.save_data()
        print("数据管理器数据保存成功")
    except Exception as e:
        print(f"保存数据管理器数据失败: {e}")
    
    print("========== 项目分类和摘要生成脚本执行完成 ==========")


if __name__ == "__main__":
    main()