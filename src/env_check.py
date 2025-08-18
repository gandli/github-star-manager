#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境检查模块
用于验证GitHub Actions运行环境和必需的配置
"""

import os
import sys
import subprocess
import requests
from typing import Dict, List, Tuple


class EnvironmentChecker:
    """环境检查器"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def check_secrets(self, skip_classification: bool = False) -> bool:
        """检查必需的secrets"""
        print("🔧 检查必需的环境变量...")
        
        success = True
        
        # 检查GitHub相关变量
        if not os.getenv('GH_PAT'):
            print("❌ GH_PAT secret is not set")
            print("💡 请在仓库设置中添加 GH_PAT secret")
            self.errors.append("GH_PAT secret 未设置")
            success = False
        else:
            print("✅ GH_PAT secret 已配置")
        
        # GITHUB_USERNAME 可以通过 github.actor 自动获取
        github_username = os.getenv('GITHUB_USERNAME')
        if github_username:
            print(f"✅ GITHUB_USERNAME 已设置: {github_username}")
        else:
            print("⚠️ GITHUB_USERNAME 未设置，将使用默认值")
            self.warnings.append("GITHUB_USERNAME 未设置")
        
        # 检查AI相关变量（如果不跳过分类）
        if not skip_classification:
            if not os.getenv('AI_API_KEY'):
                print("❌ AI_API_KEY secret is not set")
                print("💡 请在仓库设置中添加 AI_API_KEY secret，或使用 skip_classification 参数跳过AI分类")
                self.errors.append("AI_API_KEY secret 未设置")
                success = False
            else:
                print("✅ AI_API_KEY secret 已配置")
            
            if not os.getenv('AI_ACCOUNT_ID'):
                print("❌ AI_ACCOUNT_ID secret is not set")
                print("💡 请在仓库设置中添加 AI_ACCOUNT_ID secret，或使用 skip_classification 参数跳过AI分类")
                self.errors.append("AI_ACCOUNT_ID secret 未设置")
                success = False
            else:
                print("✅ AI_ACCOUNT_ID secret 已配置")
        else:
            print("⏭️ 跳过AI分类，无需验证AI相关secrets")
        
        if success:
            print("✅ 环境变量验证通过")
        
        return success
    
    def check_disk_space(self, min_space_gb: float = 1.0) -> bool:
        """检查磁盘空间"""
        try:
            # 获取当前目录的磁盘使用情况
            result = subprocess.run(['df', '.'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    # 解析df输出
                    fields = lines[1].split()
                    available_kb = int(fields[3])  # 可用空间（KB）
                    available_gb = available_kb / (1024 * 1024)
                    
                    if available_gb < min_space_gb:
                        print(f"⚠️ 磁盘空间不足: {available_gb:.2f}GB 可用")
                        self.warnings.append(f"磁盘空间不足: {available_gb:.2f}GB")
                        return False
                    else:
                        print(f"✅ 磁盘空间充足: {available_gb:.2f}GB 可用")
                        return True
        except Exception as e:
            print(f"⚠️ 无法检查磁盘空间: {e}")
            self.warnings.append(f"磁盘空间检查失败: {e}")
        
        return True
    
    def check_network_connectivity(self) -> bool:
        """检查网络连接"""
        try:
            response = requests.get('https://api.github.com/rate_limit', timeout=10)
            if response.status_code == 200:
                print("✅ GitHub API 连接正常")
                return True
            else:
                print(f"❌ GitHub API 连接异常: HTTP {response.status_code}")
                self.errors.append(f"GitHub API 连接异常: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ GitHub API 连接失败: {e}")
            self.errors.append(f"GitHub API 连接失败: {e}")
            return False
    
    def check_python_environment(self) -> bool:
        """检查Python环境"""
        try:
            python_version = sys.version
            print(f"✅ Python环境: {python_version.split()[0]}")
            
            # 检查关键依赖
            required_packages = ['requests', 'yaml']
            missing_packages = []
            
            for package in required_packages:
                try:
                    __import__(package)
                except ImportError:
                    missing_packages.append(package)
            
            if missing_packages:
                print(f"❌ 缺少必需的包: {', '.join(missing_packages)}")
                self.errors.append(f"缺少必需的包: {', '.join(missing_packages)}")
                return False
            else:
                print("✅ 核心依赖验证通过")
                return True
                
        except Exception as e:
            print(f"❌ Python环境检查失败: {e}")
            self.errors.append(f"Python环境检查失败: {e}")
            return False
    
    def run_health_check(self, skip_classification: bool = False) -> bool:
        """运行完整的健康检查"""
        print("🏥 执行系统健康检查...")
        
        checks = [
            self.check_disk_space(),
            self.check_network_connectivity(),
            self.check_python_environment()
        ]
        
        all_passed = all(checks)
        
        if all_passed:
            print("✅ 系统健康检查通过")
        else:
            print("❌ 系统健康检查发现问题")
        
        return all_passed
    
    def get_system_info(self) -> Dict[str, str]:
        """获取系统信息"""
        info = {}
        
        try:
            # 系统信息
            result = subprocess.run(['uname', '-s'], capture_output=True, text=True)
            if result.returncode == 0:
                info['system'] = result.stdout.strip()
            
            result = subprocess.run(['uname', '-r'], capture_output=True, text=True)
            if result.returncode == 0:
                info['kernel'] = result.stdout.strip()
            
            # Python版本
            info['python_version'] = sys.version.split()[0]
            
            # 磁盘空间
            result = subprocess.run(['df', '-h', '.'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    fields = lines[1].split()
                    info['disk_available'] = fields[3]
            
            # 内存信息（Linux）
            try:
                with open('/proc/meminfo', 'r') as f:
                    meminfo = f.read()
                    for line in meminfo.split('\n'):
                        if line.startswith('MemAvailable:'):
                            mem_kb = int(line.split()[1])
                            mem_gb = mem_kb / (1024 * 1024)
                            info['memory_available'] = f"{mem_gb:.1f}GB"
                            break
            except:
                pass
                
        except Exception as e:
            info['error'] = str(e)
        
        return info
    
    def print_system_info(self) -> None:
        """打印系统信息"""
        info = self.get_system_info()
        
        print("💻 系统信息:")
        if 'system' in info and 'kernel' in info:
            print(f"  - 系统: {info['system']} {info['kernel']}")
        if 'python_version' in info:
            print(f"  - Python: {info['python_version']}")
        if 'disk_available' in info:
            print(f"  - 磁盘空间: {info['disk_available']} 可用")
        if 'memory_available' in info:
            print(f"  - 内存: {info['memory_available']} 可用")
        if 'error' in info:
            print(f"  - 错误: {info['error']}")


def main():
    """主函数 - 用于命令行调用"""
    import argparse
    
    parser = argparse.ArgumentParser(description='环境检查工具')
    parser.add_argument('--skip-classification', action='store_true',
                       help='跳过AI分类相关的环境检查')
    parser.add_argument('--secrets-only', action='store_true',
                       help='仅检查secrets配置')
    parser.add_argument('--health-check', action='store_true',
                       help='执行完整的健康检查')
    parser.add_argument('--system-info', action='store_true',
                       help='显示系统信息')
    
    args = parser.parse_args()
    
    checker = EnvironmentChecker()
    
    if args.system_info:
        checker.print_system_info()
        return
    
    if args.secrets_only:
        success = checker.check_secrets(args.skip_classification)
        sys.exit(0 if success else 1)
    
    if args.health_check:
        success = checker.run_health_check(args.skip_classification)
        sys.exit(0 if success else 1)
    
    # 默认执行secrets检查
    success = checker.check_secrets(args.skip_classification)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()