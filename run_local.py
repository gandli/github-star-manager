#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
本地运行GitHub Star Manager

使用方法：
1. 设置环境变量GH_PAT和AI_API_KEY
2. 运行此脚本
"""

import os
import sys
import subprocess


def check_env_vars():
    """
    检查必要的环境变量
    """
    missing_vars = []
    
    if not os.environ.get('GH_PAT'):
        missing_vars.append('GH_PAT')
    
    if not os.environ.get('AI_API_KEY'):
        missing_vars.append('AI_API_KEY')
    
    return missing_vars


def run_script(script_path):
    """
    运行Python脚本
    """
    try:
        subprocess.run([sys.executable, script_path], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"运行脚本失败: {e}")
        return False


def main():
    # 检查环境变量
    missing_vars = check_env_vars()
    if missing_vars:
        print(f"错误: 缺少以下环境变量: {', '.join(missing_vars)}")
        print("请设置这些环境变量后再运行此脚本")
        sys.exit(1)
    
    # 获取脚本路径
    base_dir = os.path.dirname(os.path.abspath(__file__))
    fetch_script = os.path.join(base_dir, 'src', 'fetch_stars.py')
    classify_script = os.path.join(base_dir, 'src', 'classify.py')
    update_script = os.path.join(base_dir, 'src', 'update_readme.py')
    
    # 创建数据目录
    os.makedirs(os.path.join(base_dir, 'data'), exist_ok=True)
    
    # 运行脚本
    print("=== 开始获取Star项目列表 ===")
    if not run_script(fetch_script):
        sys.exit(1)
    
    print("\n=== 开始项目分类和摘要生成 ===")
    if not run_script(classify_script):
        sys.exit(1)
    
    print("\n=== 开始更新README ===")
    if not run_script(update_script):
        sys.exit(1)
    
    print("\n=== 全部完成! ===")
    print(f"请查看更新后的README文件: {os.path.join(base_dir, 'README.md')}")


if __name__ == "__main__":
    main()