#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Star Manager - README更新模块

功能：
- 自动更新主README文件
- 插入项目统计信息
- 生成分类概览
- 保持README的其他内容不变
"""

import os
import re
import logging
from datetime import datetime
from typing import Dict, Any, List, Tuple
import yaml
from data_manager import DataManager


class ReadmeUpdater:
    """README更新器"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """初始化README更新器
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.data_manager = DataManager(config_path)
        self.readme_path = self.config['docs']['readme_path']
        self.docs_dir = self.config['docs']['output_dir']
        self.logger = self._setup_logger()
        
        # 标记注释
        self.start_marker = "<!-- GITHUB_STAR_MANAGER_START -->"
        self.end_marker = "<!-- GITHUB_STAR_MANAGER_END -->"
        
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
    
    def _read_readme(self) -> str:
        """读取README文件内容
        
        Returns:
            README文件内容
        """
        try:
            if os.path.exists(self.readme_path):
                with open(self.readme_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                # 如果README不存在，创建基础模板
                return self._create_basic_readme_template()
        except Exception as e:
            self.logger.error(f"Error reading README file: {e}")
            return self._create_basic_readme_template()
    
    def _create_basic_readme_template(self) -> str:
        """创建基础README模板
        
        Returns:
            基础README内容
        """
        template = """# GitHub Star Manager

一个基于Python和GitHub Actions的自动化GitHub收藏项目管理系统，通过AI技术实现项目智能分类和文档生成。

## 功能特性

- 🚀 自动获取GitHub Star项目
- 🤖 AI智能分类和摘要生成
- 📊 项目统计和数据管理
- 📝 自动生成分类文档
- ⚡ GitHub Actions自动化执行

## 项目统计

<!-- GITHUB_STAR_MANAGER_START -->
<!-- 此部分内容由GitHub Star Manager自动生成和更新 -->
<!-- GITHUB_STAR_MANAGER_END -->

## 使用说明

### 环境配置

1. 设置环境变量：
   - `GH_PAT`: GitHub个人访问令牌
   - `AI_API_KEY`: AI API密钥
   - `AI_ACCOUNT_ID`: AI账户ID
   - `GITHUB_USERNAME`: GitHub用户名

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

### 运行方式

#### 手动运行

```bash
# 获取星标项目
python src/fetch_stars.py

# AI分类
python src/classify.py

# 生成文档
python src/generate_category_docs.py
python src/update_readme.py
```

#### 自动化运行

项目配置了GitHub Actions工作流，支持：
- 定时执行（每天UTC 3点）
- 手动触发
- 增量和全量更新模式

## 项目结构

```
github-star-manager/
├── src/                    # 源代码目录
│   ├── fetch_stars.py     # 数据获取模块
│   ├── classify.py        # AI分类模块
│   ├── data_manager.py    # 数据管理模块
│   ├── generate_category_docs.py  # 分类文档生成
│   └── update_readme.py   # README更新模块
├── data/                  # 数据存储目录
│   └── stars_data.json   # 项目数据文件
├── docs/                  # 文档输出目录
├── .github/workflows/     # GitHub Actions工作流
├── config.yaml           # 配置文件
├── requirements.txt      # Python依赖
└── README.md            # 项目说明文档
```

## 许可证

MIT License
"""
        return template
    
    def _generate_statistics_section(self) -> str:
        """生成统计信息部分
        
        Returns:
            统计信息的Markdown内容
        """
        try:
            data = self.data_manager.load_data()
            stats = self.data_manager.get_statistics(data)
            
            content = "### 📊 项目统计\n\n"
            
            # 基础统计
            basic_stats = stats['basic']
            content += f"- **总项目数**: {basic_stats['total_repositories']:,}\n"
            content += f"- **已分类项目**: {basic_stats['classified_repositories']:,}\n"
            content += f"- **未分类项目**: {basic_stats['unclassified_repositories']:,}\n"
            content += f"- **分类完成率**: {basic_stats['classification_rate']:.1f}%\n\n"
            
            # 分类统计
            categories = stats.get('categories', {})
            if categories:
                content += "### 📂 分类概览\n\n"
                content += "| 分类 | 项目数量 | 文档链接 |\n"
                content += "|------|----------|----------|\n"
                
                # 按项目数量排序
                sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
                
                for category, count in sorted_categories:
                    if count > 0:
                        # 生成文档链接
                        doc_filename = f"{category.replace('/', '_')}.md"
                        doc_path = f"{self.docs_dir}/{doc_filename}"
                        
                        if os.path.exists(doc_path):
                            link = f"[📖 查看详情]({self.docs_dir}/{doc_filename})"
                        else:
                            link = "文档生成中..."
                        
                        content += f"| {category} | {count:,} | {link} |\n"
                
                content += "\n"
            
            # 语言统计（显示前10个）
            languages = stats.get('languages', {})
            if languages:
                content += "### 💻 主要编程语言\n\n"
                content += "| 语言 | 项目数量 | 占比 |\n"
                content += "|------|----------|------|\n"
                
                total_repos = basic_stats['total_repositories']
                top_languages = list(languages.items())[:10]
                
                for language, count in top_languages:
                    percentage = (count / total_repos * 100) if total_repos > 0 else 0
                    content += f"| {language} | {count:,} | {percentage:.1f}% |\n"
                
                content += "\n"
            
            # 最近更新信息
            content += "### 🕒 更新信息\n\n"
            content += f"- **最后更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            # 获取最近添加的项目
            recent_repos = self._get_recent_repositories(data, limit=5)
            if recent_repos:
                content += "- **最近添加的项目**:\n"
                for repo in recent_repos:
                    name = repo.get('name', '')
                    url = repo.get('html_url', '')
                    content += f"  - [{name}]({url})\n"
            
            content += "\n"
            
            # 添加索引链接
            index_path = os.path.join(self.docs_dir, "index.md")
            if os.path.exists(index_path):
                content += f"📋 [查看完整分类索引]({self.docs_dir}/index.md)\n\n"
            
            return content
            
        except Exception as e:
            self.logger.error(f"Error generating statistics section: {e}")
            return "### 📊 项目统计\n\n统计信息生成失败，请检查数据文件。\n\n"
    
    def _get_recent_repositories(self, data: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
        """获取最近添加的仓库
        
        Args:
            data: 项目数据
            limit: 返回数量限制
            
        Returns:
            最近添加的仓库列表
        """
        try:
            repositories = data.get('repositories', [])
            
            # 按starred_at时间排序（如果有的话）
            sorted_repos = sorted(
                repositories,
                key=lambda x: x.get('starred_at', x.get('created_at', '')),
                reverse=True
            )
            
            return sorted_repos[:limit]
            
        except Exception as e:
            self.logger.error(f"Error getting recent repositories: {e}")
            return []
    
    def _find_update_section(self, content: str) -> Tuple[int, int]:
        """查找需要更新的部分
        
        Args:
            content: README内容
            
        Returns:
            (开始位置, 结束位置) 的元组，如果未找到返回 (-1, -1)
        """
        start_pos = content.find(self.start_marker)
        end_pos = content.find(self.end_marker)
        
        if start_pos != -1 and end_pos != -1 and end_pos > start_pos:
            return start_pos, end_pos + len(self.end_marker)
        
        return -1, -1
    
    def update_readme(self) -> bool:
        """更新README文件
        
        Returns:
            是否更新成功
        """
        try:
            # 读取当前README内容
            current_content = self._read_readme()
            
            # 生成新的统计信息部分
            stats_section = self._generate_statistics_section()
            
            # 构建完整的更新内容
            update_content = f"{self.start_marker}\n"
            update_content += "<!-- 此部分内容由GitHub Star Manager自动生成和更新 -->\n\n"
            update_content += stats_section
            update_content += self.end_marker
            
            # 查找现有的更新部分
            start_pos, end_pos = self._find_update_section(current_content)
            
            if start_pos != -1 and end_pos != -1:
                # 替换现有内容
                new_content = (
                    current_content[:start_pos] +
                    update_content +
                    current_content[end_pos:]
                )
            else:
                # 如果没有找到标记，在文件末尾添加
                if not current_content.endswith('\n'):
                    current_content += '\n'
                new_content = current_content + '\n' + update_content + '\n'
            
            # 确保目录存在
            readme_dir = os.path.dirname(self.readme_path)
            if readme_dir:
                os.makedirs(readme_dir, exist_ok=True)
            
            # 写入更新后的内容
            with open(self.readme_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            self.logger.info(f"Successfully updated README: {self.readme_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating README: {e}")
            return False
    
    def validate_readme(self) -> Dict[str, Any]:
        """验证README文件
        
        Returns:
            验证结果字典
        """
        result = {
            'exists': False,
            'has_markers': False,
            'content_length': 0,
            'last_modified': None,
            'issues': []
        }
        
        try:
            if os.path.exists(self.readme_path):
                result['exists'] = True
                
                # 获取文件信息
                stat = os.stat(self.readme_path)
                result['last_modified'] = datetime.fromtimestamp(stat.st_mtime)
                
                # 读取内容
                content = self._read_readme()
                result['content_length'] = len(content)
                
                # 检查标记
                if self.start_marker in content and self.end_marker in content:
                    result['has_markers'] = True
                else:
                    result['issues'].append("Missing update markers")
                
                # 检查基本结构
                if '# ' not in content:
                    result['issues'].append("No main heading found")
                
                if len(content.strip()) < 100:
                    result['issues'].append("Content seems too short")
                    
            else:
                result['issues'].append("README file does not exist")
                
        except Exception as e:
            result['issues'].append(f"Error validating README: {e}")
            
        return result
    
    def backup_readme(self) -> str:
        """备份当前README文件
        
        Returns:
            备份文件路径
        """
        try:
            if not os.path.exists(self.readme_path):
                raise FileNotFoundError("README file does not exist")
            
            # 生成备份文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"README_backup_{timestamp}.md"
            backup_path = os.path.join(os.path.dirname(self.readme_path), backup_filename)
            
            # 复制文件
            with open(self.readme_path, 'r', encoding='utf-8') as src:
                content = src.read()
            
            with open(backup_path, 'w', encoding='utf-8') as dst:
                dst.write(content)
            
            self.logger.info(f"README backed up to: {backup_path}")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Error backing up README: {e}")
            raise


def main():
    """主函数"""
    import sys
    
    try:
        updater = ReadmeUpdater()
        
        if len(sys.argv) > 1:
            command = sys.argv[1]
            
            if command == 'update':
                # 更新README
                success = updater.update_readme()
                print(f"README update {'successful' if success else 'failed'}")
                
            elif command == 'validate':
                # 验证README
                result = updater.validate_readme()
                print(f"README validation result: {result}")
                
            elif command == 'backup':
                # 备份README
                backup_path = updater.backup_readme()
                print(f"README backed up to: {backup_path}")
                
            else:
                print("Unknown command. Available: update, validate, backup")
        else:
            # 默认执行更新
            success = updater.update_readme()
            print(f"README update {'successful' if success else 'failed'}")
            
    except Exception as e:
        logging.error(f"Error in main execution: {e}")
        raise


if __name__ == "__main__":
    main()