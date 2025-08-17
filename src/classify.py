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


def call_ai_api(api_key, api_url, model, prompt):
    """
    调用AI API进行项目分类和摘要生成
    
    Args:
        api_key: AI API密钥
        api_url: API地址
        model: 模型名称
        prompt: 提示词
        
    Returns:
        str: AI生成的回复
    """
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    data = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "你是一个专业的GitHub项目分析助手，擅长对项目进行分类和生成摘要。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        print(f"调用AI API失败: {e}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"响应内容: {e.response.text}")
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


def classify_repos(repos, api_key, api_url, model, categories):
    """
    对项目列表进行分类和摘要生成
    """
    classified_repos = []
    total = len(repos)
    
    for i, repo in enumerate(repos):
        print(f"正在处理 [{i+1}/{total}]: {repo['full_name']}")
        
        # 生成提示词
        prompt = generate_repo_prompt(repo, categories)
        
        # 调用AI API
        response = call_ai_api(api_key, api_url, model, prompt)
        
        if response:
            # 解析结果
            result = parse_ai_response(response)
            
            # 添加分类和摘要到项目信息中
            repo_with_analysis = repo.copy()
            repo_with_analysis['category'] = result.get('category', '其他')
            repo_with_analysis['summary'] = result.get('summary', '无摘要')
            repo_with_analysis['key_features'] = result.get('key_features', ['无特点'])
            
            classified_repos.append(repo_with_analysis)
        else:
            # 如果AI调用失败，使用默认值
            repo_with_analysis = repo.copy()
            repo_with_analysis['category'] = '其他'
            repo_with_analysis['summary'] = '无法生成摘要'
            repo_with_analysis['key_features'] = ['无法识别特点']
            
            classified_repos.append(repo_with_analysis)
    
    return classified_repos


def save_classified_repos(repos, output_file):
    """
    保存分类后的项目列表到文件
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(repos, f, ensure_ascii=False, indent=2)
    print(f"已保存{len(repos)}个分类后的项目到{output_file}")


def main():
    # 获取AI API密钥
    ai_api_key = os.environ.get('AI_API_KEY')
    if not ai_api_key:
        print("错误: 未设置AI_API_KEY环境变量")
        sys.exit(1)
    
    # 加载配置
    config = load_config()
    ai_model = config.get('ai_model', 'glm-4.5-flash')
    ai_api_url = config.get('ai_api_url', 'https://open.bigmodel.cn/api/paas/v4/chat/completions')
    categories = config.get('categories', ['其他'])
    
    # 创建输出目录
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # 加载最新的项目列表
    input_file = os.path.join(data_dir, 'starred_repos_latest.json')
    if not os.path.exists(input_file):
        print(f"错误: 找不到项目列表文件 {input_file}")
        sys.exit(1)
    
    repos = load_repos(input_file)
    print(f"已加载{len(repos)}个Star项目")
    
    # 对项目进行分类和摘要生成
    classified_repos = classify_repos(repos, ai_api_key, ai_api_url, ai_model, categories)
    
    # 保存结果
    timestamp = datetime.now().strftime('%Y%m%d')
    output_file = os.path.join(data_dir, f'classified_repos_{timestamp}.json')
    save_classified_repos(classified_repos, output_file)
    
    # 同时保存一个最新版本
    latest_file = os.path.join(data_dir, 'classified_repos_latest.json')
    save_classified_repos(classified_repos, latest_file)


if __name__ == "__main__":
    main()