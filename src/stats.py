#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统计和报告模块
用于生成项目统计信息和执行摘要
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional


class StatsReporter:
    """统计报告生成器"""
    
    def __init__(self, data_file: str = "data/stars_data.json"):
        self.data_file = data_file
    
    def get_project_stats(self) -> Dict[str, Any]:
        """获取项目统计信息"""
        stats = {
            'total_projects': 0,
            'classified_projects': 0,
            'unclassified_projects': 0,
            'classification_rate': 0.0,
            'file_size_kb': 0.0,
            'last_updated': 'Unknown',
            'file_exists': False
        }
        
        try:
            if os.path.exists(self.data_file):
                stats['file_exists'] = True
                
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                repos = data.get('repositories', [])
                stats['total_projects'] = len(repos)
                stats['classified_projects'] = sum(1 for r in repos if r.get('is_classified', False))
                stats['unclassified_projects'] = stats['total_projects'] - stats['classified_projects']
                
                if stats['total_projects'] > 0:
                    stats['classification_rate'] = (stats['classified_projects'] / stats['total_projects']) * 100
                
                # 文件大小
                file_size = os.path.getsize(self.data_file)
                stats['file_size_kb'] = file_size / 1024
                
                # 最后更新时间
                stats['last_updated'] = data.get('metadata', {}).get('last_updated', 'Unknown')
                
        except Exception as e:
            print(f"获取统计信息时出错: {e}")
        
        return stats
    
    def get_unclassified_count(self) -> int:
        """获取未分类项目数量"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                repos = data.get('repositories', [])
                return sum(1 for r in repos if not r.get('is_classified', False))
        except Exception:
            pass
        
        return 0
    
    def get_doc_stats(self, docs_dir: str = "docs") -> Dict[str, Any]:
        """获取文档统计信息"""
        stats = {
            'doc_count': 0,
            'doc_files': [],
            'docs_exist': False
        }
        
        try:
            if os.path.exists(docs_dir):
                stats['docs_exist'] = True
                doc_files = []
                
                for root, dirs, files in os.walk(docs_dir):
                    for file in files:
                        if file.endswith('.md'):
                            doc_files.append(file)
                
                stats['doc_count'] = len(doc_files)
                stats['doc_files'] = sorted(doc_files)
                
        except Exception as e:
            print(f"获取文档统计信息时出错: {e}")
        
        return stats
    
    def print_project_stats(self) -> None:
        """打印项目统计信息"""
        stats = self.get_project_stats()
        
        if stats['file_exists']:
            print(f"📊 当前总项目数: {stats['total_projects']}")
            print(f"📈 数据统计:")
            print(f"  - 总项目数: {stats['total_projects']}")
            print(f"  - 已分类: {stats['classified_projects']}")
            print(f"  - 未分类: {stats['unclassified_projects']}")
            if stats['total_projects'] > 0:
                print(f"  - 分类率: {stats['classification_rate']:.1f}%")
            print(f"  - 数据文件大小: {stats['file_size_kb']:.1f} KB")
            print(f"  - 最后更新: {stats['last_updated']}")
        else:
            print("  - ⚠️ 数据文件不存在")
    
    def print_classification_stats(self) -> None:
        """打印分类统计信息"""
        stats = self.get_project_stats()
        
        if stats['file_exists']:
            print(f"📊 已分类项目: {stats['classified_projects']}/{stats['total_projects']}")
        else:
            print("❌ 数据文件不存在，无法获取分类统计")
    
    def print_doc_stats(self, docs_dir: str = "docs") -> None:
        """打印文档统计信息"""
        stats = self.get_doc_stats(docs_dir)
        
        print(f"📚 生成文档: {stats['doc_count']} 个")
        
        if stats['doc_count'] > 0:
            print("📋 文档列表:")
            for doc in stats['doc_files']:
                print(f"  - {doc}")
    
    def generate_commit_message(self, fetch_mode: str, workflow_run: str, 
                              skip_classification: bool = False) -> str:
        """生成提交信息"""
        commit_msg = "🤖 自动更新GitHub Star项目数据"
        
        if fetch_mode == "full":
            commit_msg += " (全量更新)"
        else:
            commit_msg += " (增量更新)"
        
        # 获取统计信息
        stats = self.get_project_stats()
        if stats['file_exists']:
            commit_msg += f"\n\n📊 统计信息: {stats['total_projects']} 个项目，{stats['classified_projects']} 个已分类"
        
        commit_msg += f"\n- 获取模式: {fetch_mode}"
        commit_msg += f"\n- 更新时间: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
        commit_msg += f"\n- 工作流运行: {workflow_run}"
        
        if skip_classification:
            commit_msg += "\n- 跳过AI分类: 是"
        
        return commit_msg


def main():
    """主函数 - 用于命令行调用"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python stats.py <command>")
        print("Commands:")
        print("  project_stats - Show project statistics")
        print("  classification - Show classification statistics")
        print("  unclassified - Show number of unclassified projects")
        print("  file_info - Show file information")
        print("  doc_stats - Show documentation statistics")
        print("  commit_message <run_number> - Generate commit message")
        return
    
    reporter = StatsReporter()
    command = sys.argv[1]
    
    if command == "project_stats":
        stats = reporter.get_project_stats()
        print(f"📊 当前总项目数: {stats['total_projects']}")
        if stats['total_projects'] > 0:
            print(f"📊 已分类项目: {stats['classified_projects']}/{stats['total_projects']}")
            print(f"📊 分类率: {stats['classification_rate']:.1f}%")
    
    elif command == "classification":
        reporter.print_classification_stats()
    
    elif command == "unclassified":
        count = reporter.get_unclassified_count()
        print(count)
    
    elif command == "file_info":
        stats = reporter.get_project_stats()
        if stats['file_exists']:
            print(f"📁 数据文件大小: {stats['file_size_kb']:.1f} KB")
            print(f"🕒 最后更新: {stats['last_updated']}")
        else:
            print("❌ 数据文件不存在")
    
    elif command == "doc_stats":
        reporter.print_doc_stats()
    
    elif command == "commit_message" and len(sys.argv) >= 3:
        run_number = sys.argv[2]
        fetch_mode = sys.argv[3] if len(sys.argv) > 3 else "incremental"
        skip_classification = sys.argv[4] if len(sys.argv) > 4 else "false"
        message = reporter.generate_commit_message(fetch_mode, run_number, skip_classification == "true")
        print(message)
    
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()