#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试整个工作流程
"""

import os
import sys
import json
import subprocess
from datetime import datetime


def run_command(cmd, description):
    """
    运行命令并检查结果
    """
    print(f"\n{'='*50}")
    print(f"正在执行: {description}")
    print(f"命令: {cmd}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        if result.stdout:
            print("标准输出:")
            print(result.stdout)
        
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"✅ {description} 执行成功")
            return True
        else:
            print(f"❌ {description} 执行失败，返回码: {result.returncode}")
            return False
            
    except Exception as e:
        print(f"❌ 执行 {description} 时发生异常: {e}")
        return False


def check_file_exists(filepath, description):
    """
    检查文件是否存在
    """
    if os.path.exists(filepath):
        print(f"✅ {description} 存在: {filepath}")
        return True
    else:
        print(f"❌ {description} 不存在: {filepath}")
        return False


def check_json_file(filepath, description):
    """
    检查JSON文件是否有效
    """
    if not check_file_exists(filepath, description):
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ {description} JSON格式有效，包含 {len(data)} 条记录")
        return True
    except Exception as e:
        print(f"❌ {description} JSON格式无效: {e}")
        return False


def main():
    print("========== GitHub Star Manager 工作流程测试 ==========")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查必要的环境变量
    print("\n检查环境变量...")
    required_env_vars = ['GH_PAT', 'AI_API_KEY', 'GITHUB_USERNAME']
    env_check_passed = True
    
    for var in required_env_vars:
        if os.environ.get(var):
            print(f"✅ 环境变量 {var} 已设置")
        else:
            print(f"❌ 环境变量 {var} 未设置")
            env_check_passed = False
    
    if not env_check_passed:
        print("\n⚠️  请设置必要的环境变量后再运行测试")
        print("示例:")
        print("set GH_PAT=your_github_token")
        print("set AI_API_KEY=your_ai_api_key")
        print("set GITHUB_USERNAME=your_github_username")
        return
    
    # 检查配置文件
    print("\n检查配置文件...")
    config_file = "config.yaml"
    if not check_file_exists(config_file, "配置文件"):
        return
    
    # 创建必要的目录
    print("\n创建必要的目录...")
    os.makedirs("data", exist_ok=True)
    os.makedirs("docs", exist_ok=True)
    print("✅ 目录创建完成")
    
    # 测试步骤1: 获取Star项目列表
    success1 = run_command("python src/fetch_stars.py", "获取Star项目列表")
    if success1:
        check_json_file("data/starred_repos_latest.json", "最新Star项目列表")
    
    # 测试步骤2: 项目分类和摘要生成
    if success1:
        success2 = run_command("python src/classify.py", "项目分类和摘要生成")
        if success2:
            check_json_file("data/classified_repos_latest.json", "分类后的项目列表")
    
    # 测试步骤3: 生成分类文档
    if success1 and success2:
        success3 = run_command("python src/generate_category_docs.py", "生成分类文档")
        if success3:
            # 检查生成的文档
            docs_dir = "docs"
            if os.path.exists(docs_dir):
                doc_files = [f for f in os.listdir(docs_dir) if f.endswith('.md')]
                if doc_files:
                    print(f"✅ 生成了 {len(doc_files)} 个文档文件:")
                    for doc_file in doc_files:
                        print(f"   - {doc_file}")
                else:
                    print("❌ 未生成任何文档文件")
    
    # 检查最终结果
    print("\n" + "="*50)
    print("测试结果总结")
    print("="*50)
    
    # 检查关键文件
    key_files = [
        ("data/starred_repos_latest.json", "最新Star项目列表"),
        ("data/classified_repos_latest.json", "分类后的项目列表"),
        ("docs/README.md", "索引文档")
    ]
    
    all_passed = True
    for filepath, description in key_files:
        if not check_file_exists(filepath, description):
            all_passed = False
    
    if all_passed:
        print("\n🎉 所有测试通过！工作流程运行正常。")
    else:
        print("\n⚠️  部分测试失败，请检查上述错误信息。")
    
    print("\n========== 测试完成 ==========")


if __name__ == "__main__":
    main()