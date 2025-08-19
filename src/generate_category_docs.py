#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Star Manager - 分类文档生成模块

功能：
- 按分类生成独立的Markdown文档
- 每个分类最多显示指定数量的项目
- 自动更新项目统计信息
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Any
import yaml
from .data_manager import DataManager


class CategoryDocGenerator:
    """分类文档生成器"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """初始化文档生成器
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.data_manager = DataManager(config_path)
        self.output_dir = self.config['docs']['output_dir']
        self.max_projects = self.config['docs']['max_projects_per_category']
        self.logger = self._setup_logger()
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置字典
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration: {e}")
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器
        
        Returns:
            配置好的日志记录器
        """
        logger = logging.getLogger(__name__)
        logger.setLevel(getattr(logging, self.config['logging']['level']))
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(self.config['logging']['format'])
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def _format_repo_entry(self, repo: Dict[str, Any]) -> str:
        """格式化单个仓库条目
        
        Args:
            repo: 仓库信息
            
        Returns:
            格式化的Markdown字符串
        """
        name = repo.get('name', '')
        full_name = repo.get('full_name', '')
        description = repo.get('description', '暂无描述')
        html_url = repo.get('html_url', '')
        language = repo.get('language', '未知')
        stars = repo.get('stargazers_count', 0)
        summary = repo.get('summary', description)
        key_features = repo.get('key_features', [])
        
        # 构建条目
        entry = f"### [{name}]({html_url})\n\n"
        entry += f"**仓库**: {full_name}\n\n"
        entry += f"**描述**: {description}\n\n"
        
        if summary and summary != description:
            entry += f"**AI摘要**: {summary}\n\n"
        
        if key_features:
            entry += "**关键特性**:\n"
            for feature in key_features:
                entry += f"- {feature}\n"
            entry += "\n"
        
        entry += f"**语言**: {language} | **星数**: ⭐ {stars:,}\n\n"
        entry += "---\n\n"
        
        return entry
    
    def _generate_category_header(self, category: str, repos: List[Dict[str, Any]], total_in_category: int) -> str:
        """生成分类文档头部
        
        Args:
            category: 分类名称
            repos: 显示的仓库列表
            total_in_category: 该分类的总项目数
            
        Returns:
            头部Markdown字符串
        """
        header = f"# {category}\n\n"
        header += f"本分类共有 **{total_in_category}** 个项目"
        
        if len(repos) < total_in_category:
            header += f"，当前显示前 **{len(repos)}** 个项目"
        
        header += f"。\n\n"
        header += f"*最后更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
        
        return header
    
    def _generate_category_toc(self, repos: List[Dict[str, Any]]) -> str:
        """生成分类目录
        
        Args:
            repos: 仓库列表
            
        Returns:
            目录Markdown字符串
        """
        if not repos:
            return ""
        
        toc = "## 目录\n\n"
        for i, repo in enumerate(repos, 1):
            name = repo.get('name', '')
            # 生成锚点链接
            anchor = name.lower().replace(' ', '-').replace('_', '-')
            toc += f"{i}. [{name}](#{anchor})\n"
        
        toc += "\n---\n\n"
        return toc
    
    def _check_document_needs_update(self, category: str, repos: List[Dict[str, Any]]) -> bool:
        """检查分类文档是否需要更新
        
        Args:
            category: 分类名称
            repos: 仓库列表
            
        Returns:
            是否需要更新
        """
        filename = f"{category.replace('/', '_')}.md"
        filepath = os.path.join(self.output_dir, filename)
        
        # 如果文件不存在，需要创建
        if not os.path.exists(filepath):
            self.logger.info(f"Document does not exist, creating new: {filepath}")
            return True
        
        try:
            # 读取现有文档
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查仓库数量是否变化
            import re
            total_pattern = re.compile(r'本分类共有 \*\*(\d+)\*\* 个项目')
            match = total_pattern.search(content)
            if not match:
                return True
            
            old_total = int(match.group(1))
            new_total = len(repos)
            
            if old_total != new_total:
                self.logger.info(f"Repository count changed for {category}: {old_total} -> {new_total}")
                return True
            
            # 检查仓库列表是否变化（通过检查仓库名称和星数）
            repo_pattern = re.compile(r'### \[([^\]]+)\]\([^\)]+\).*?\*\*星数\*\*: ⭐ ([\d,]+)', re.DOTALL)
            repo_matches = repo_pattern.findall(content)
            
            if len(repo_matches) != min(len(repos), self.max_projects):
                self.logger.info(f"Displayed repository count changed for {category}")
                return True
            
            # 创建现有文档中的仓库映射
            existing_repos = {}
            for name, stars_str in repo_matches:
                stars = int(stars_str.replace(',', ''))
                existing_repos[name] = stars
            
            # 检查前N个仓库是否有变化
            sorted_repos = sorted(repos, key=lambda x: x.get('stargazers_count', 0), reverse=True)
            display_repos = sorted_repos[:self.max_projects]
            
            for repo in display_repos:
                name = repo.get('name', '')
                stars = repo.get('stargazers_count', 0)
                
                if name not in existing_repos or existing_repos[name] != stars:
                    self.logger.info(f"Repository {name} changed or new in {category}")
                    return True
            
            self.logger.info(f"No changes detected for category: {category}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking document update for {category}: {e}")
            return True  # 出错时默认更新
    
    def generate_category_document(self, category: str) -> bool:
        """生成单个分类的文档
        
        Args:
            category: 分类名称
            
        Returns:
            是否生成成功
        """
        try:
            # 获取该分类的所有仓库
            all_repos = self.data_manager.get_repositories_by_category(category)
            
            if not all_repos:
                self.logger.warning(f"No repositories found for category: {category}")
                return False
            
            # 检查文档是否需要更新
            if not self._check_document_needs_update(category, all_repos):
                self.logger.info(f"Skipping unchanged category document: {category}")
                return True
            
            # 按星数排序并限制数量
            sorted_repos = sorted(all_repos, key=lambda x: x.get('stargazers_count', 0), reverse=True)
            display_repos = sorted_repos[:self.max_projects]
            
            # 生成文档内容
            content = self._generate_category_header(category, display_repos, len(all_repos))
            content += self._generate_category_toc(display_repos)
            content += "## 项目列表\n\n"
            
            for repo in display_repos:
                content += self._format_repo_entry(repo)
            
            # 添加页脚
            content += self._generate_footer(category, len(all_repos), len(display_repos))
            
            # 保存文档
            filename = f"{category.replace('/', '_')}.md"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info(f"Generated category document: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error generating category document for {category}: {e}")
            return False
    
    def _generate_footer(self, category: str, total_count: int, displayed_count: int) -> str:
        """生成文档页脚
        
        Args:
            category: 分类名称
            total_count: 总项目数
            displayed_count: 显示的项目数
            
        Returns:
            页脚Markdown字符串
        """
        footer = "## 统计信息\n\n"
        footer += f"- **分类**: {category}\n"
        footer += f"- **总项目数**: {total_count}\n"
        footer += f"- **显示项目数**: {displayed_count}\n"
        
        if displayed_count < total_count:
            footer += f"- **未显示项目数**: {total_count - displayed_count}\n"
        
        footer += f"- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        footer += "---\n\n"
        footer += "*本文档由 [GitHub Star Manager](https://github.com/your-username/github-star-manager) 自动生成*\n"
        
        return footer
    
    def generate_all_category_documents(self) -> Dict[str, bool]:
        """生成所有分类的文档
        
        Returns:
            各分类的生成结果字典
        """
        results = {}
        
        # 获取所有分类
        data = self.data_manager.load_data()
        stats = self.data_manager.get_statistics(data)
        categories = stats.get('categories', {})
        
        self.logger.info(f"Generating documents for {len(categories)} categories")
        
        for category in categories.keys():
            if categories[category] > 0:  # 只为有项目的分类生成文档
                results[category] = self.generate_category_document(category)
            else:
                self.logger.info(f"Skipping empty category: {category}")
                results[category] = False
        
        successful_count = sum(1 for success in results.values() if success)
        self.logger.info(f"Generated {successful_count}/{len(results)} category documents")
        
        return results
    
    def _check_index_needs_update(self, stats: Dict[str, Any]) -> bool:
        """检查索引文档是否需要更新
        
        Args:
            stats: 统计信息
            
        Returns:
            是否需要更新
        """
        index_path = os.path.join(self.output_dir, "index.md")
        
        # 如果文件不存在，需要创建
        if not os.path.exists(index_path):
            self.logger.info(f"Index document does not exist, creating new: {index_path}")
            return True
        
        try:
            # 读取现有索引文档
            with open(index_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查分类数量和项目总数是否变化
            import re
            stats_pattern = re.compile(r'总共有 \*\*(\d+)\*\* 个分类，包含 \*\*(\d+)\*\* 个项目')
            match = stats_pattern.search(content)
            if not match:
                return True
            
            old_category_count = int(match.group(1))
            old_repo_count = int(match.group(2))
            
            new_category_count = len(stats.get('categories', {}))
            new_repo_count = stats['basic']['total_repositories']
            
            if old_category_count != new_category_count or old_repo_count != new_repo_count:
                self.logger.info(f"Stats changed: categories {old_category_count}->{new_category_count}, repos {old_repo_count}->{new_repo_count}")
                return True
            
            # 检查分类列表是否变化
            category_pattern = re.compile(r'\| ([^|]+) \| (\d+) \|')
            category_matches = category_pattern.findall(content)
            
            if len(category_matches) != new_category_count:
                self.logger.info(f"Category count mismatch in index: {len(category_matches)} vs {new_category_count}")
                return True
            
            # 检查每个分类的项目数量是否变化
            categories = stats.get('categories', {})
            for category_name, count_str in category_matches:
                category_name = category_name.strip()
                old_count = int(count_str)
                new_count = categories.get(category_name, 0)
                
                if old_count != new_count:
                    self.logger.info(f"Category count changed: {category_name} {old_count}->{new_count}")
                    return True
            
            # 检查分类完成率是否变化
            completion_pattern = re.compile(r'\*\*分类完成率\*\*: ([\d\.]+)%')
            completion_match = completion_pattern.search(content)
            if completion_match:
                old_rate = float(completion_match.group(1))
                new_rate = stats['basic']['classification_rate']
                
                if abs(old_rate - new_rate) > 0.1:  # 允许0.1%的误差
                    self.logger.info(f"Classification rate changed: {old_rate}%->{new_rate}%")
                    return True
            
            self.logger.info("No changes detected for index document")
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking index update: {e}")
            return True  # 出错时默认更新
    
    def generate_category_index(self) -> bool:
        """生成分类索引文档
        
        Returns:
            是否生成成功
        """
        try:
            data = self.data_manager.load_data()
            stats = self.data_manager.get_statistics(data)
            
            # 检查索引是否需要更新
            if not self._check_index_needs_update(stats):
                self.logger.info("Skipping unchanged index document")
                return True
            
            categories = stats.get('categories', {})
            
            # 生成索引内容
            content = "# 项目分类索引\n\n"
            content += f"总共有 **{len(categories)}** 个分类，包含 **{stats['basic']['total_repositories']}** 个项目。\n\n"
            content += f"*最后更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
            
            # 按项目数量排序
            sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
            
            content += "## 分类列表\n\n"
            content += "| 分类 | 项目数量 | 文档链接 |\n"
            content += "|------|----------|----------|\n"
            
            for category, count in sorted_categories:
                if count > 0:
                    filename = f"{category.replace('/', '_')}.md"
                    content += f"| {category} | {count} | [{category}]({filename}) |\n"
            
            content += "\n"
            
            # 添加统计信息
            content += "## 统计概览\n\n"
            basic_stats = stats['basic']
            content += f"- **总项目数**: {basic_stats['total_repositories']}\n"
            content += f"- **已分类项目**: {basic_stats['classified_repositories']}\n"
            content += f"- **未分类项目**: {basic_stats['unclassified_repositories']}\n"
            content += f"- **分类完成率**: {basic_stats['classification_rate']:.1f}%\n\n"
            
            # 添加语言统计
            languages = stats.get('languages', {})
            if languages:
                content += "## 主要编程语言\n\n"
                content += "| 语言 | 项目数量 |\n"
                content += "|------|----------|\n"
                
                for language, count in list(languages.items())[:10]:
                    content += f"| {language} | {count} |\n"
                
                content += "\n"
            
            # 保存索引文档
            index_path = os.path.join(self.output_dir, "index.md")
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info(f"Generated category index: {index_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error generating category index: {e}")
            return False
    
    def clean_old_documents(self) -> None:
        """清理旧的文档文件"""
        try:
            if not os.path.exists(self.output_dir):
                return
            
            # 获取当前所有分类
            data = self.data_manager.load_data()
            stats = self.data_manager.get_statistics(data)
            current_categories = set(stats.get('categories', {}).keys())
            
            # 检查现有文档文件
            for filename in os.listdir(self.output_dir):
                if filename.endswith('.md') and filename != 'index.md':
                    category = filename[:-3].replace('_', '/')
                    
                    if category not in current_categories:
                        file_path = os.path.join(self.output_dir, filename)
                        os.remove(file_path)
                        self.logger.info(f"Removed obsolete document: {file_path}")
                        
        except Exception as e:
            self.logger.error(f"Error cleaning old documents: {e}")


def main():
    """主函数"""
    import sys
    import argparse
    
    try:
        # 创建命令行参数解析器
        parser = argparse.ArgumentParser(description='GitHub Star Manager - 分类文档生成工具')
        subparsers = parser.add_subparsers(dest='command', help='命令')
        
        # 生成所有文档的命令
        all_parser = subparsers.add_parser('all', help='生成所有分类文档')
        all_parser.add_argument('--force', action='store_true', help='强制全量更新所有文档')
        
        # 生成单个分类文档的命令
        category_parser = subparsers.add_parser('category', help='生成指定分类的文档')
        category_parser.add_argument('name', help='分类名称')
        category_parser.add_argument('--force', action='store_true', help='强制更新文档')
        
        # 生成索引文档的命令
        index_parser = subparsers.add_parser('index', help='生成索引文档')
        index_parser.add_argument('--force', action='store_true', help='强制更新索引')
        
        # 清理旧文档的命令
        subparsers.add_parser('clean', help='清理旧文档')
        
        # 解析命令行参数
        if len(sys.argv) > 1:
            args = parser.parse_args()
        else:
            # 默认生成所有文档
            args = parser.parse_args(['all'])
        
        # 创建文档生成器
        generator = CategoryDocGenerator()
        
        # 根据命令执行相应操作
        if args.command == 'category':
            # 如果指定了强制更新，临时修改检查方法
            if args.force:
                generator._check_document_needs_update = lambda category, repos: True
            
            # 生成指定分类的文档
            success = generator.generate_category_document(args.name)
            print(f"Category document generation {'successful' if success else 'failed'}")
            
        elif args.command == 'index':
            # 如果指定了强制更新，临时修改检查方法
            if args.force:
                generator._check_index_needs_update = lambda stats: True
            
            # 生成索引文档
            success = generator.generate_category_index()
            print(f"Index generation {'successful' if success else 'failed'}")
            
        elif args.command == 'clean':
            # 清理旧文档
            generator.clean_old_documents()
            print("Document cleanup completed")
            
        else:  # 'all' 命令或默认情况
            # 如果指定了强制更新，临时修改检查方法
            if hasattr(args, 'force') and args.force:
                generator._check_document_needs_update = lambda category, repos: True
                generator._check_index_needs_update = lambda stats: True
                print("Forcing full update of all documents")
            
            # 生成所有文档
            results = generator.generate_all_category_documents()
            generator.generate_category_index()
            generator.clean_old_documents()
            
            successful_count = sum(1 for success in results.values() if success)
            print(f"Generated {successful_count}/{len(results)} category documents")
            
    except Exception as e:
        logging.error(f"Error in main execution: {e}")
        raise


if __name__ == "__main__":
    main()