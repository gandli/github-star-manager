# 我的GitHub Star项目 [![Update Starred Repos](https://github.com/gandli/github-star-manager/actions/workflows/update_stars.yml/badge.svg)](https://github.com/gandli/github-star-manager/actions/workflows/update_stars.yml)

最后更新: 未更新

## GitHub Star项目自动管理系统

这是一个自动化的GitHub Star项目管理系统，通过GitHub Actions定期获取用户的GitHub star项目列表，利用GitHub Models的AI能力对项目进行智能分类和摘要生成，并将结构化结果自动更新到README.md文件中，实现star项目的自动化管理和知识沉淀。

### 功能特点

- **自动获取**: 自动获取用户的GitHub star项目列表
- **AI分类**: 利用GitHub Models的AI能力对项目进行智能分类
- **摘要生成**: 自动生成项目摘要，提取核心价值
- **分类展示**: 按分类组织和展示项目，便于查找
- **统计分析**: 提供分类统计，了解兴趣分布
- **定时更新**: 通过GitHub Actions定期自动更新
- **错误处理**: 完善的错误处理和日志记录

### 使用指南

#### 1. 配置环境

1. Fork本仓库到你的GitHub账号
2. 在仓库设置中添加以下Secrets:
   - `GH_TOKEN`: GitHub个人访问令牌，用于访问GitHub API
   - `GITHUB_AI_TOKEN`: (可选) GitHub AI API密钥，用于AI分类和摘要生成

#### 2. 自定义配置

你可以根据需要修改以下文件：

- `.github/workflows/update_stars.yml`: 调整自动更新的时间和频率
- `src/ai_processor.py`: 自定义分类规则和摘要生成逻辑
- `src/update_stars.py`: 调整README生成格式和内容

#### 3. 手动触发更新

1. 在GitHub仓库页面，点击Actions标签
2. 选择"Update Starred Repos"工作流
3. 点击"Run workflow"按钮手动触发更新

### 技术实现

- **Python**: 核心逻辑实现
- **PyGithub**: GitHub API交互
- **GitHub Models**: AI分类和摘要生成
- **GitHub Actions**: 自动化运行
- **Markdown**: 结构化展示

### 项目结构

```
├── .github/workflows/    # GitHub Actions工作流配置
├── logs/                 # 日志文件目录
├── src/                  # 源代码
│   ├── ai_processor.py   # AI处理模块
│   ├── logging_config.py # 日志配置
│   └── update_stars.py   # 主程序
├── .env.example          # 环境变量示例
├── .gitignore            # Git忽略文件
└── README.md             # 项目文档
```

### 项目分类

[项目列表将在这里自动生成]