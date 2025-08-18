#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据管理模块
负责管理star项目的JSON数据存储
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StarDataManager:
    """Star项目数据管理器"""
    
    def __init__(self, data_file_path: str = "data/stars_data.json"):
        """
        初始化数据管理器
        
        Args:
            data_file_path: JSON数据文件路径
        """
        self.data_file_path = data_file_path
        self.ensure_data_file_exists()
    
    def ensure_data_file_exists(self):
        """确保数据文件存在，如果不存在则创建"""
        if not os.path.exists(self.data_file_path):
            os.makedirs(os.path.dirname(self.data_file_path), exist_ok=True)
            initial_data = {
                "metadata": {
                    "last_updated": datetime.now().isoformat(),
                    "total_stars": 0,
                    "classified_count": 0,
                    "unclassified_count": 0
                },
                "stars": {}
            }
            self.save_data(initial_data)
    
    def load_data(self) -> Dict[str, Any]:
        """
        加载JSON数据
        
        Returns:
            包含所有star数据的字典
        """
        try:
            with open(self.data_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"加载数据文件失败: {e}")
            return {
                "metadata": {
                    "last_updated": datetime.now().isoformat(),
                    "total_stars": 0,
                    "classified_count": 0,
                    "unclassified_count": 0
                },
                "stars": {}
            }
    
    def save_data(self, data: Optional[Dict[str, Any]] = None):
        """
        保存数据到JSON文件
        
        Args:
            data: 要保存的数据字典，如果为None则保存当前加载的数据
        """
        try:
            if data is None:
                data = self.load_data()
            
            # 更新元数据
            self.update_metadata(data)
            
            os.makedirs(os.path.dirname(self.data_file_path), exist_ok=True)
            with open(self.data_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"数据已保存到 {self.data_file_path}")
        except Exception as e:
            logger.error(f"保存数据失败: {e}")
            raise
    
    def add_or_update_star(self, star_info: Dict[str, Any]):
        """
        添加或更新star项目信息
        
        Args:
            star_info: 包含star项目信息的字典
        """
        data = self.load_data()
        
        # 构建star项目的完整信息
        star_id = star_info.get('id') or star_info.get('full_name', '').replace('/', '_')
        
        star_data = {
            "id": star_info.get('id'),
            "name": star_info.get('name', ''),
            "full_name": star_info.get('full_name', ''),
            "description": star_info.get('description', ''),
            "html_url": star_info.get('html_url', ''),
            "language": star_info.get('language', ''),
            "stargazers_count": star_info.get('stargazers_count', 0),
            "forks_count": star_info.get('forks_count', 0),
            "created_at": star_info.get('created_at', ''),
            "updated_at": star_info.get('updated_at', ''),
            "pushed_at": star_info.get('pushed_at', ''),
            "topics": star_info.get('topics', []),
            "license": star_info.get('license', {}).get('name', '') if star_info.get('license') else '',
            "archived": star_info.get('archived', False),
            "fork": star_info.get('fork', False),
            "size": star_info.get('size', 0),
            "open_issues_count": star_info.get('open_issues_count', 0),
            "default_branch": star_info.get('default_branch', 'main'),
            # 分类相关字段
            "is_classified": False,
            "category": "",
            "classification_date": "",
            "classification_confidence": 0.0,
            "classification_reason": "",
            # 数据管理字段
            "added_date": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
        
        # 如果项目已存在，保留分类信息
        if star_id in data["stars"]:
            existing_star = data["stars"][star_id]
            star_data["is_classified"] = existing_star.get("is_classified", False)
            star_data["category"] = existing_star.get("category", "")
            star_data["classification_date"] = existing_star.get("classification_date", "")
            star_data["classification_confidence"] = existing_star.get("classification_confidence", 0.0)
            star_data["classification_reason"] = existing_star.get("classification_reason", "")
            star_data["added_date"] = existing_star.get("added_date", star_data["added_date"])
        
        data["stars"][star_id] = star_data
        
        # 更新统计信息
        self.update_metadata(data)
        
        # 保存数据
        self.save_data(data)
        
        logger.info(f"已添加/更新star项目: {star_info.get('full_name', star_id)}")
    
    def update_classification(self, star_id: str, category: str, confidence: float = 0.0, reason: str = ""):
        """
        更新项目的分类信息
        
        Args:
            star_id: 项目ID或full_name
            category: 分类名称
            confidence: 分类置信度
            reason: 分类原因
        """
        data = self.load_data()
        
        # 查找项目（支持通过ID或full_name查找）
        target_star_id = None
        for sid, star_data in data["stars"].items():
            if sid == star_id or star_data.get("full_name") == star_id or star_data.get("id") == star_id:
                target_star_id = sid
                break
        
        if target_star_id is None:
            logger.warning(f"未找到项目: {star_id}")
            return False
        
        # 更新分类信息
        data["stars"][target_star_id]["is_classified"] = True
        data["stars"][target_star_id]["category"] = category
        data["stars"][target_star_id]["classification_date"] = datetime.now().isoformat()
        data["stars"][target_star_id]["classification_confidence"] = confidence
        data["stars"][target_star_id]["classification_reason"] = reason
        data["stars"][target_star_id]["last_updated"] = datetime.now().isoformat()
        
        # 更新统计信息
        self.update_metadata(data)
        
        # 保存数据
        self.save_data(data)
        
        logger.info(f"已更新项目分类: {data['stars'][target_star_id]['full_name']} -> {category}")
        return True
    
    def get_star_by_id(self, star_id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID获取star项目信息
        
        Args:
            star_id: 项目ID或full_name
            
        Returns:
            项目信息字典，如果不存在返回None
        """
        data = self.load_data()
        
        # 查找项目
        for sid, star_data in data["stars"].items():
            if sid == star_id or star_data.get("full_name") == star_id or star_data.get("id") == star_id:
                return star_data
        
        return None
    
    def get_all_stars(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有star项目
        
        Returns:
            所有项目的字典
        """
        data = self.load_data()
        return data.get("stars", {})
    
    def get_unclassified_stars(self) -> Dict[str, Dict[str, Any]]:
        """
        获取未分类的star项目
        
        Returns:
            未分类项目的字典
        """
        data = self.load_data()
        unclassified = {}
        
        for star_id, star_data in data.get("stars", {}).items():
            if not star_data.get("is_classified", False):
                unclassified[star_id] = star_data
        
        return unclassified
    
    def get_classified_stars(self) -> Dict[str, Dict[str, Any]]:
        """
        获取已分类的star项目
        
        Returns:
            已分类项目的字典
        """
        data = self.load_data()
        classified = {}
        
        for star_id, star_data in data.get("stars", {}).items():
            if star_data.get("is_classified", False):
                classified[star_id] = star_data
        
        return classified
    
    def get_stars_by_category(self, category: str) -> Dict[str, Dict[str, Any]]:
        """
        根据分类获取star项目
        
        Args:
            category: 分类名称
            
        Returns:
            指定分类的项目字典
        """
        data = self.load_data()
        category_stars = {}
        
        for star_id, star_data in data.get("stars", {}).items():
            if star_data.get("category") == category:
                category_stars[star_id] = star_data
        
        return category_stars
    
    def update_metadata(self, data: Dict[str, Any]):
        """
        更新元数据统计信息
        
        Args:
            data: 数据字典
        """
        stars = data.get("stars", {})
        total_stars = len(stars)
        classified_count = sum(1 for star in stars.values() if star.get("is_classified", False))
        unclassified_count = total_stars - classified_count
        
        data["metadata"].update({
            "total_stars": total_stars,
            "classified_count": classified_count,
            "unclassified_count": unclassified_count
        })
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            包含统计信息的字典
        """
        data = self.load_data()
        return data.get("metadata", {})
    
    def export_to_csv(self, output_path: str):
        """
        导出数据到CSV文件
        
        Args:
            output_path: CSV文件输出路径
        """
        import csv
        
        data = self.load_data()
        stars = data.get("stars", {})
        
        if not stars:
            logger.warning("没有数据可导出")
            return
        
        # 获取所有字段名
        fieldnames = set()
        for star_data in stars.values():
            fieldnames.update(star_data.keys())
        fieldnames = sorted(list(fieldnames))
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for star_data in stars.values():
                writer.writerow(star_data)
        
        logger.info(f"数据已导出到 {output_path}")


# 创建全局数据管理器实例
data_manager = StarDataManager()