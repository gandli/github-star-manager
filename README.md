# GitHub Star Manager

自动化管理和分类您的GitHub Star项目，通过AI生成摘要和分类，帮助您更好地管理和利用已收藏的项目。

## 功能特点

- 自动获取您的GitHub Star项目列表
- 使用AI对项目进行智能分类
- 生成项目摘要和关键特性
- 定期更新README文件，保持项目列表最新
- 完全基于GitHub Actions自动化运行

## 使用方法

1. Fork本仓库
2. 在仓库设置中添加以下Secrets:
   - `GH_TOKEN`: GitHub个人访问令牌，需要有`repo`和`user`权限
   - `AI_API_KEY`: AI API密钥（用于智能分类和摘要生成）
3. 修改配置文件中的用户名为您的GitHub用户名
4. 启用GitHub Actions

## 项目结构

```
.
├── .github/workflows/  # GitHub Actions工作流配置
├── src/                # 源代码
│   ├── fetch_stars.py  # 获取Star项目列表
│   ├── classify.py     # 项目分类和摘要生成
│   └── update_readme.py # 更新README文件
├── config.yaml         # 配置文件
└── README.md           # 项目说明文档
```

## 配置选项

在`config.yaml`文件中，您可以自定义以下选项：

- `username`: 您的GitHub用户名
- `update_interval`: 更新频率（天）
- `categories`: 自定义分类类别
- `max_stars`: 最大获取的Star项目数量

## Star项目列表

*此部分将由自动化脚本更新*

## 许可证

MIT