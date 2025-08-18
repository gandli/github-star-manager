#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Star Manager - 数据管理模块

功能：
- 统一管理项目数据的存储和更新
- 实现增量更新逻辑，避免重复分类
- 维护分类状态跟踪
- 提供统计信息
"""

import os
import json
import shutil
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Tuple
import yaml


class DataManager:
    """数据管理器"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """初始化数据管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.data_file = self.config['data']['stars_data_file']
        self.backup_file = self.config['data']['backup_file']
        self.auto_backup = self.config['data']['auto_backup']
        self.logger = self._setup_logger()
        
        # 确保数据目录存在
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        
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
    
    def load_data(self) -> Dict[str, Any]:
        """加载数据文件
        
        Returns:
            数据字典
        """
        if not os.path.exists(self.data_file):
            self.logger.info("Data file not found, creating new data structure")
            return self._create_empty_data_structure()
        
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.logger.info(f"Loaded data from {self.data_file}")
                return data
        except (json.JSONDecodeError, FileNotFoundError) as e:
            self.logger.error(f"Error loading data file: {e}")
            # 尝试从备份恢复
            return self._restore_from_backup()
    
    def _create_empty_data_structure(self) -> Dict[str, Any]:
        """创建空的数据结构
        
        Returns:
            空的数据字典
        """
        return {
            'metadata': {
                'total_count': 0,
                'classified_count': 0,
                'unclassified_count': 0,
                'last_fetch_time': None,
                'last_classification_time': None,
                'fetch_mode': 'incremental',
                'username': None,
                'version': '1.0.0'
            },
            'repositories': []
        }
    
    def _restore_from_backup(self) -> Dict[str, Any]:
        """从备份文件恢复数据
        
        Returns:
            恢复的数据字典
        """
        if os.path.exists(self.backup_file):
            try:
                with open(self.backup_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.logger.info(f"Restored data from backup: {self.backup_file}")
                    return data
            except (json.JSONDecodeError, FileNotFoundError) as e:
                self.logger.error(f"Error loading backup file: {e}")
        
        self.logger.warning("No valid backup found, creating new data structure")
        return self._create_empty_data_structure()
    
    def save_data(self, data: Dict[str, Any]) -> bool:
        """保存数据到文件
        
        Args:
            data: 要保存的数据
            
        Returns:
            是否保存成功
        """
        try:
            # 创建备份
            if self.auto_backup and os.path.exists(self.data_file):
                self._create_backup()
            
            # 更新元数据
            self._update_metadata(data)
            
            # 保存数据
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Data saved successfully to {self.data_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving data: {e}")
            return False
    
    def _create_backup(self) -> bool:
        """创建数据备份
        
        Returns:
            是否备份成功
        """
        try:
            # 确保备份目录存在
            os.makedirs(os.path.dirname(self.backup_file), exist_ok=True)
            
            # 复制文件
            shutil.copy2(self.data_file, self.backup_file)
            self.logger.info(f"Backup created: {self.backup_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            return False
    
    def _update_metadata(self, data: Dict[str, Any]) -> None:
        """更新元数据
        
        Args:
            data: 数据字典
        """
        repos = data.get('repositories', [])
        
        # 计算统计信息
        total_count = len(repos)
        classified_count = sum(1 for repo in repos if repo.get('is_classified', False))
        unclassified_count = total_count - classified_count
        
        # 更新元数据
        metadata = data.setdefault('metadata', {})
        metadata.update({
            'total_count': total_count,
            'classified_count': classified_count,
            'unclassified_count': unclassified_count,
            'last_update_time': datetime.now(timezone.utc).isoformat()
        })
    
    def merge_repositories(self, existing_repos: List[Dict[str, Any]], new_repos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """合并仓库列表，避免重复
        
        Args:
            existing_repos: 现有仓库列表
            new_repos: 新仓库列表
            
        Returns:
            合并后的仓库列表
        """
        # 创建现有仓库的ID映射
        existing_ids = {repo['id']: i for i, repo in enumerate(existing_repos)}
        
        merged_repos = existing_repos.copy()
        new_count = 0
        updated_count = 0
        
        for new_repo in new_repos:
            repo_id = new_repo['id']
            
            if repo_id in existing_ids:
                # 更新现有仓库（保留分类信息）
                existing_index = existing_ids[repo_id]
                existing_repo = merged_repos[existing_index]
                
                # 保留分类相关字段
                classification_fields = {
                    'is_classified': existing_repo.get('is_classified', False),
                    'category': existing_repo.get('category'),
                    'summary': existing_repo.get('summary'),
                    'key_features': existing_repo.get('key_features', [])
                }
                
                # 更新仓库信息
                merged_repos[existing_index] = {**new_repo, **classification_fields}
                updated_count += 1
                
            else:
                # 添加新仓库
                merged_repos.append(new_repo)
                new_count += 1
        
        self.logger.info(f"Repository merge completed: {new_count} new, {updated_count} updated")
        return merged_repos
    
    def get_statistics(self, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """获取统计信息
        
        Args:
            data: 数据字典，如果为None则从文件加载
            
        Returns:
            统计信息字典
        """
        if data is None:
            data = self.load_data()
        
        repos = data.get('repositories', [])
        metadata = data.get('metadata', {})
        
        # 基础统计
        total_count = len(repos)
        classified_count = sum(1 for repo in repos if repo.get('is_classified', False))
        unclassified_count = total_count - classified_count
        
        # 分类统计
        category_stats = {}
        for repo in repos:
            if repo.get('is_classified', False):
                category = repo.get('category', '未分类')
                category_stats[category] = category_stats.get(category, 0) + 1
        
        # 语言统计
        language_stats = {}
        for repo in repos:
            language = repo.get('language') or '未知'
            language_stats[language] = language_stats.get(language, 0) + 1
        
        # 星数统计
        star_counts = [repo.get('stargazers_count', 0) for repo in repos]
        avg_stars = sum(star_counts) / len(star_counts) if star_counts else 0
        max_stars = max(star_counts) if star_counts else 0
        min_stars = min(star_counts) if star_counts else 0
        
        return {
            'basic': {
                'total_repositories': total_count,
                'classified_repositories': classified_count,
                'unclassified_repositories': unclassified_count,
                'classification_rate': (classified_count / total_count * 100) if total_count > 0 else 0
            },
            'categories': category_stats,
            'languages': dict(sorted(language_stats.items(), key=lambda x: x[1], reverse=True)[:10]),
            'stars': {
                'average': round(avg_stars, 2),
                'maximum': max_stars,
                'minimum': min_stars,
                'total': sum(star_counts)
            },
            'metadata': {
                'last_fetch_time': metadata.get('last_fetch_time'),
                'last_classification_time': metadata.get('last_classification_time'),
                'last_update_time': metadata.get('last_update_time'),
                'fetch_mode': metadata.get('fetch_mode'),
                'username': metadata.get('username')
            }
        }
    
    def get_repositories_by_category(self, category: str, data: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """根据分类获取仓库列表
        
        Args:
            category: 分类名称
            data: 数据字典，如果为None则从文件加载
            
        Returns:
            指定分类的仓库列表
        """
        if data is None:
            data = self.load_data()
        
        repos = data.get('repositories', [])
        return [repo for repo in repos if repo.get('category') == category and repo.get('is_classified', False)]
    
    def get_unclassified_repositories(self, data: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """获取未分类的仓库列表
        
        Args:
            data: 数据字典，如果为None则从文件加载
            
        Returns:
            未分类的仓库列表
        """
        if data is None:
            data = self.load_data()
        
        repos = data.get('repositories', [])
        return [repo for repo in repos if not repo.get('is_classified', False)]
    
    def update_repository_classification(self, repo_id: int, classification: Dict[str, Any], data: Optional[Dict[str, Any]] = None) -> bool:
        """更新单个仓库的分类信息
        
        Args:
            repo_id: 仓库ID
            classification: 分类信息
            data: 数据字典，如果为None则从文件加载
            
        Returns:
            是否更新成功
        """
        if data is None:
            data = self.load_data()
        
        repos = data.get('repositories', [])
        
        for repo in repos:
            if repo['id'] == repo_id:
                repo.update({
                    'is_classified': True,
                    'category': classification.get('category'),
                    'summary': classification.get('summary'),
                    'key_features': classification.get('key_features', [])
                })
                
                # 更新分类时间
                metadata = data.setdefault('metadata', {})
                metadata['last_classification_time'] = datetime.now(timezone.utc).isoformat()
                
                self.save_data(data)
                self.logger.info(f"Updated classification for repository {repo_id}")
                return True
        
        self.logger.warning(f"Repository {repo_id} not found")
        return False
    
    def export_data(self, output_file: str, format_type: str = 'json', category: Optional[str] = None) -> bool:
        """导出数据
        
        Args:
            output_file: 输出文件路径
            format_type: 导出格式 ('json' 或 'csv')
            category: 指定分类，如果为None则导出所有数据
            
        Returns:
            是否导出成功
        """
        try:
            data = self.load_data()
            
            if category:
                repos = self.get_repositories_by_category(category, data)
                export_data = {
                    'metadata': data.get('metadata', {}),
                    'repositories': repos
                }
            else:
                export_data = data
            
            if format_type.lower() == 'json':
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
            elif format_type.lower() == 'csv':
                import csv
                repos = export_data.get('repositories', [])
                
                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    if repos:
                        writer = csv.DictWriter(f, fieldnames=repos[0].keys())
                        writer.writeheader()
                        writer.writerows(repos)
            else:
                raise ValueError(f"Unsupported format: {format_type}")
            
            self.logger.info(f"Data exported to {output_file} in {format_type} format")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting data: {e}")
            return False
    
    def cleanup_old_backups(self, keep_count: int = 5) -> None:
        """清理旧的备份文件
        
        Args:
            keep_count: 保留的备份文件数量
        """
        try:
            backup_dir = os.path.dirname(self.backup_file)
            if not os.path.exists(backup_dir):
                return
            
            # 获取所有备份文件
            backup_files = []
            for file in os.listdir(backup_dir):
                if file.startswith('stars_data_backup') and file.endswith('.json'):
                    file_path = os.path.join(backup_dir, file)
                    backup_files.append((file_path, os.path.getmtime(file_path)))
            
            # 按修改时间排序
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # 删除多余的备份文件
            for file_path, _ in backup_files[keep_count:]:
                os.remove(file_path)
                self.logger.info(f"Removed old backup: {file_path}")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up backups: {e}")


def main():
    """主函数"""
    import sys
    
    # 创建数据管理器
    manager = DataManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'stats':
            # 显示统计信息
            stats = manager.get_statistics()
            print(json.dumps(stats, ensure_ascii=False, indent=2))
            
        elif command == 'export' and len(sys.argv) > 2:
            # 导出数据
            output_file = sys.argv[2]
            format_type = sys.argv[3] if len(sys.argv) > 3 else 'json'
            category = sys.argv[4] if len(sys.argv) > 4 else None
            
            success = manager.export_data(output_file, format_type, category)
            print(f"Export {'successful' if success else 'failed'}")
            
        elif command == 'cleanup':
            # 清理备份
            manager.cleanup_old_backups()
            print("Backup cleanup completed")
            
        else:
            print("Unknown command")
    else:
        # 显示基本信息
        stats = manager.get_statistics()
        basic = stats['basic']
        print(f"Total repositories: {basic['total_repositories']}")
        print(f"Classified: {basic['classified_repositories']}")
        print(f"Unclassified: {basic['unclassified_repositories']}")
        print(f"Classification rate: {basic['classification_rate']:.1f}%")


if __name__ == "__main__":
    main()