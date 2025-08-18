#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流辅助工具模块
用于GitHub Actions工作流中的各种辅助功能
"""

import os
import subprocess
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class WorkflowUtils:
    """工作流辅助工具"""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
    
    def create_directories(self, dirs: List[str] = None) -> bool:
        """创建必要的目录结构"""
        if dirs is None:
            dirs = ['data', 'docs', 'logs']
        
        print("📁 创建项目目录结构...")
        
        try:
            for dir_name in dirs:
                os.makedirs(dir_name, mode=0o755, exist_ok=True)
                print(f"  ✅ {dir_name}/")
            
            print("✅ 目录结构创建完成")
            
            # 显示目录列表
            print("📋 目录列表:")
            result = subprocess.run(['ls', '-la'], capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.startswith('d'):
                        print(f"  {line}")
            
            return True
            
        except Exception as e:
            print(f"❌ 目录创建失败: {e}")
            return False
    
    def check_file_changes(self) -> Tuple[bool, List[str]]:
        """检查Git文件变更"""
        print("🔍 检查文件变更...")
        
        try:
            # 检查工作区变更
            result1 = subprocess.run(['git', 'diff', '--quiet'], capture_output=True)
            # 检查暂存区变更
            result2 = subprocess.run(['git', 'diff', '--cached', '--quiet'], capture_output=True)
            
            has_changes = result1.returncode != 0 or result2.returncode != 0
            
            changed_files = []
            
            if has_changes:
                print("📝 检测到文件变更")
                
                # 获取变更的文件列表
                result = subprocess.run(['git', 'diff', '--name-only'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    changed_files.extend(result.stdout.strip().split('\n'))
                
                result = subprocess.run(['git', 'diff', '--cached', '--name-only'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    cached_files = result.stdout.strip().split('\n')
                    changed_files.extend([f for f in cached_files if f not in changed_files])
                
                # 过滤空字符串
                changed_files = [f for f in changed_files if f.strip()]
                
                if changed_files:
                    print("📋 变更的文件:")
                    for file in changed_files:
                        print(f"  - {file}")
            else:
                print("📝 没有检测到文件变更")
            
            return has_changes, changed_files
            
        except Exception as e:
            print(f"❌ 检查文件变更失败: {e}")
            return False, []
    
    def commit_and_push_changes(self, run_number: str, fetch_mode: str = "incremental", 
                               event_name: str = "manual", skip_classification: str = "false") -> bool:
        """提交并推送变更到Git仓库"""
        print("💾 提交文件变更...")
        
        try:
            # 配置Git用户信息
            subprocess.run(['git', 'config', '--local', 'user.email', 'action@github.com'], 
                         check=True)
            subprocess.run(['git', 'config', '--local', 'user.name', 'GitHub Action'], 
                         check=True)
            
            # 添加变更的文件
            files_to_add = ['data/', 'docs/', 'README.md']
            for file_pattern in files_to_add:
                subprocess.run(['git', 'add', file_pattern], check=False)
            
            # 检查是否有文件被添加到暂存区
            result = subprocess.run(['git', 'diff', '--cached', '--quiet'], capture_output=True)
            if result.returncode == 0:
                print("⚠️ 没有文件被添加到暂存区")
                return True
            
            # 生成详细的提交信息
            commit_msg = "🤖 自动更新GitHub Star项目数据"
            
            if fetch_mode == "full":
                commit_msg += " (全量更新)"
            else:
                commit_msg += " (增量更新)"
            
            # 获取统计信息
            if os.path.exists("data/stars_data.json"):
                try:
                    with open("data/stars_data.json", "r", encoding="utf-8") as f:
                        data = json.load(f)
                    repos = data.get("repositories", [])
                    classified = sum(1 for r in repos if r.get("is_classified", False))
                    stats = f"{len(repos)} 个项目，{classified} 个已分类"
                    commit_msg += f"\n\n📊 统计信息: {stats}"
                except Exception as e:
                    print(f"⚠️ 获取统计信息失败: {e}")
            
            commit_msg += f"\n- 获取模式: {fetch_mode}"
            commit_msg += f"\n- 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
            commit_msg += f"\n- 触发方式: {event_name}"
            commit_msg += f"\n- 工作流运行: {run_number}"
            
            if skip_classification == "true":
                commit_msg += "\n- 跳过AI分类: 是"
            
            # 提交变更
            subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
            print("✅ 变更提交成功")
            
            # 推送变更
            print("🚀 推送变更到远程仓库...")
            subprocess.run(['git', 'push'], check=True)
            print("✅ 变更推送成功")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Git操作失败: {e}")
            return False
        except Exception as e:
            print(f"❌ 提交推送失败: {e}")
            return False
    
    def generate_execution_summary(self, fetch_mode: str, workflow_run: str, 
                                 github_event: str, skip_classification: bool = False,
                                 workflow_url: str = "") -> None:
        """生成执行摘要"""
        print("📊 ===== 执行摘要 =====")
        
        end_time = datetime.utcnow()
        
        print(f"🕐 开始时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"🕐 结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"⏱️ 执行时长: {(end_time - self.start_time).total_seconds():.1f} 秒")
        print(f"🔧 获取模式: {fetch_mode}")
        print(f"🎯 触发方式: {github_event}")
        print(f"🏃 运行编号: {workflow_run}")
        
        if workflow_url:
            print(f"🔗 工作流链接: {workflow_url}")
        
        if skip_classification:
            print("🤖 AI分类: 跳过")
        else:
            print("🤖 AI分类: 执行")
        
        # 使用统计模块获取详细信息
        try:
            from .stats import StatsReporter
            reporter = StatsReporter()
            reporter.print_project_stats()
            reporter.print_doc_stats()
        except Exception as e:
            print(f"⚠️ 统计信息获取失败: {e}")
        
        # 性能统计
        self._print_performance_stats()
        
        print("========================")
    
    def _print_performance_stats(self) -> None:
        """打印性能统计"""
        print("⚡ 性能统计:")
        
        try:
            # 磁盘使用
            result = subprocess.run(['df', '-h', '.'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    fields = lines[1].split()
                    print(f"  - 磁盘使用: {fields[4]} (已用)")
            
            # 内存使用（Linux）
            try:
                result = subprocess.run(['free', '-h'], capture_output=True, text=True)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if line.startswith('Mem:'):
                            fields = line.split()
                            print(f"  - 内存使用: {fields[2]}/{fields[1]} (已用/总计)")
                            break
            except:
                pass
                
        except Exception as e:
            print(f"  - 性能统计获取失败: {e}")
    
    def cleanup_temp_files(self) -> None:
        """清理临时文件"""
        print("🧹 清理临时文件...")
        
        try:
            # 清理各种临时文件
            temp_patterns = [
                ('*.tmp', '临时文件'),
                ('*.pyc', 'Python字节码文件'),
                ('__pycache__', 'Python缓存目录')
            ]
            
            for pattern, description in temp_patterns:
                if pattern == '__pycache__':
                    # 清理__pycache__目录
                    result = subprocess.run(['find', '.', '-name', pattern, '-type', 'd', 
                                           '-exec', 'rm', '-rf', '{}', '+'], 
                                          capture_output=True)
                else:
                    # 清理文件
                    result = subprocess.run(['find', '.', '-name', pattern, '-type', 'f', 
                                           '-delete'], capture_output=True)
                
                if result.returncode == 0:
                    print(f"  ✅ 已清理 {description}")
            
            print("🧹 清理完成")
            
        except Exception as e:
            print(f"⚠️ 清理过程中出现错误: {e}")
    
    def handle_failure_diagnostics(self, workflow_run: str, github_event: str) -> None:
        """处理失败诊断"""
        print("❌ 工作流执行失败，开始诊断和清理...")
        
        # 显示失败信息
        print("🔍 失败诊断:")
        print(f"  - 失败时间: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"  - 运行编号: {workflow_run}")
        print(f"  - 触发方式: {github_event}")
        
        # 检查应用日志
        self._check_application_logs()
        
        # 检查数据文件状态
        self._check_data_files()
        
        # 网络连接测试
        self._test_network_connectivity()
        
        # 显示Python环境信息
        self._show_python_environment()
        
        # 显示系统资源信息
        from .env_check import EnvironmentChecker
        checker = EnvironmentChecker()
        checker.print_system_info()
        
        # 清理临时文件
        self.cleanup_temp_files()
    
    def _check_application_logs(self) -> None:
        """检查应用日志"""
        print("📋 应用错误日志:")
        
        if os.path.exists('logs'):
            try:
                result = subprocess.run(['find', 'logs', '-name', '*.log', '-type', 'f'], 
                                      capture_output=True, text=True)
                if result.returncode == 0 and result.stdout.strip():
                    log_files = result.stdout.strip().split('\n')
                    for log_file in log_files:
                        print(f"=== {log_file} ===")
                        subprocess.run(['head', '-50', log_file])
                else:
                    print("  - 没有找到日志文件")
            except Exception as e:
                print(f"  - 日志检查失败: {e}")
        else:
            print("  - 没有找到应用日志目录")
    
    def _check_data_files(self) -> None:
        """检查数据文件状态"""
        print("📊 数据文件状态:")
        
        data_file = "data/stars_data.json"
        if os.path.exists(data_file):
            try:
                file_size = os.path.getsize(data_file)
                print(f"  - stars_data.json: 存在 ({file_size} bytes)")
            except Exception as e:
                print(f"  - stars_data.json: 存在但无法获取大小 ({e})")
        else:
            print("  - stars_data.json: 不存在")
    
    def _test_network_connectivity(self) -> None:
        """测试网络连接"""
        print("🌐 网络连接测试:")
        
        try:
            import requests
            response = requests.get('https://api.github.com', timeout=10)
            if response.status_code == 200:
                print("  - GitHub API: ✅ 可访问")
            else:
                print(f"  - GitHub API: ❌ HTTP {response.status_code}")
        except Exception as e:
            print(f"  - GitHub API: ❌ 无法访问 ({e})")
    
    def _show_python_environment(self) -> None:
        """显示Python环境信息"""
        print("🐍 Python环境信息:")
        
        try:
            import sys
            print(f"  - Python版本: {sys.version.split()[0]}")
            
            # 显示已安装的包（前20个）
            result = subprocess.run(['pip', 'list'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                print("  - 已安装包:")
                for line in lines[:20]:
                    print(f"    {line}")
                if len(lines) > 20:
                    print(f"    ... 还有 {len(lines) - 20} 个包")
        except Exception as e:
            print(f"  - 环境信息获取失败: {e}")


def main():
    """主函数 - 用于命令行调用"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python workflow_utils.py <command> [args...]")
        print("Commands:")
        print("  create-dirs - Create necessary directories")
        print("  check-changes - Check for git changes")
        print("  commit-push <fetch_mode> <workflow_run> <skip_classification> - Commit and push changes")
        print("  summary <fetch_mode> <workflow_run> <github_event> <skip_classification> <workflow_url> - Generate execution summary")
        print("  cleanup - Clean temporary files")
        print("  diagnostics <workflow_run> <github_event> - Run failure diagnosis")
        sys.exit(1)
    
    utils = WorkflowUtils()
    command = sys.argv[1]
    
    if command == "create-dirs":
        success = utils.create_directories()
        exit(0 if success else 1)
    
    elif command == "check-changes":
        has_changes, files = utils.check_file_changes()
        print(f"has_changes={str(has_changes).lower()}")
        if files:
            print(f"changed_files={','.join(files)}")
    
    elif command == "commit-push" and len(sys.argv) >= 5:
        fetch_mode = sys.argv[2]
        workflow_run = sys.argv[3]
        skip_classification = sys.argv[4].lower() == 'true'
        success = utils.commit_and_push_changes(
            fetch_mode, workflow_run, skip_classification
        )
        exit(0 if success else 1)
    
    elif command == "summary" and len(sys.argv) >= 7:
        fetch_mode = sys.argv[2]
        workflow_run = sys.argv[3]
        github_event = sys.argv[4]
        skip_classification = sys.argv[5].lower() == 'true'
        workflow_url = sys.argv[6] if len(sys.argv) > 6 else ""
        utils.generate_execution_summary(
            fetch_mode, workflow_run, github_event,
            skip_classification, workflow_url
        )
    
    elif command == "cleanup":
        utils.cleanup_temp_files()
    
    elif command == "diagnostics" and len(sys.argv) >= 4:
        workflow_run = sys.argv[2]
        github_event = sys.argv[3]
        utils.handle_failure_diagnostics(workflow_run, github_event)
    
    else:
        print(f"Unknown command or insufficient arguments: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()