# GitHub Star Manager

自动化管理和分类您的GitHub Star项目，通过AI生成摘要和分类，帮助您更好地管理和利用已收藏的项目。

## 功能特点

- 自动获取您的GitHub Star项目列表
- 支持增量更新模式，只获取最新的Star项目
- 内置请求重试机制，解决GitHub API偶尔超时问题
- 使用AI对项目进行智能分类
- 生成项目摘要和关键特性
- 定期更新README文件，保持项目列表最新
- 完全基于GitHub Actions自动化运行

## 工作原理

1. 通过GitHub API获取用户的Star项目列表（默认使用增量更新模式，只获取最新的Star项目）
2. 使用AI模型（默认为智谱AI的GLM-4.5-Flash）对项目进行分类和摘要生成
3. 将分类结果更新到README.md文件中
4. 通过GitHub Actions定期自动运行，保持项目列表最新

## 使用方法

### 在GitHub上部署

1. Fork本仓库
2. 在仓库设置中添加以下Secrets:
   - `GH_PAT`: GitHub个人访问令牌，需要有`repo`和`user`权限
   - `AI_API_KEY`: AI API密钥（用于智能分类和摘要生成）
3. 启用GitHub Actions

> **注意**: 在GitHub Actions环境中，系统会自动获取仓库所有者的用户名，无需手动修改`config.yaml`文件中的`username`字段。默认情况下，工作流使用`${{ github.repository_owner }}`（仓库所有者）作为用户名。如果您需要管理其他用户的Star项目，可以通过以下两种方式：
> 1. 在GitHub Actions工作流中设置`GITHUB_USERNAME`环境变量为其他值（例如使用`${{ github.actor }}`获取当前触发工作流的用户名）
> 2. 手动修改`config.yaml`文件中的`username`字段

### 本地运行

1. 克隆仓库
   ```bash
   git clone https://github.com/YOUR_USERNAME/github-star-manager.git
   cd github-star-manager
   ```

2. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

3. 设置环境变量（两种方式）

   **方式一：使用.env文件（推荐）**
   
   复制`.env.example`文件为`.env`并填入您的信息：
   ```
   # 必需的环境变量
   GH_PAT=your_github_token
   AI_API_KEY=your_ai_api_key
   
   # 可选的环境变量
   GITHUB_USERNAME=your_github_username  # 覆盖config.yaml中的设置
   ```
   
   **方式二：直接设置系统环境变量**
   ```bash
   # Linux/macOS
   export GH_PAT=your_github_token
   export AI_API_KEY=your_ai_api_key
   export GITHUB_USERNAME=your_github_username  # 可选，覆盖config.yaml中的设置
   
   # Windows (PowerShell)
   $env:GH_PAT="your_github_token"
   $env:AI_API_KEY="your_ai_api_key"
   $env:GITHUB_USERNAME="your_github_username"  # 可选，覆盖config.yaml中的设置
   ```

4. 运行脚本
   ```bash
   python run_local.py
   ```

## 项目结构

```
.
├── .github/workflows/  # GitHub Actions工作流配置
├── data/               # 数据存储目录
├── src/                # 源代码
│   ├── fetch_stars.py  # 获取Star项目列表
│   ├── classify.py     # 项目分类和摘要生成
│   └── update_readme.py # 更新README文件
├── .env.example        # 环境变量示例文件
├── config.yaml         # 配置文件
├── requirements.txt    # 项目依赖
├── run_local.py        # 本地运行脚本
└── README.md           # 项目说明文档
```

## 配置选项

在`config.yaml`文件中，您可以自定义以下选项：

- `username`: 您的GitHub用户名
- `update_interval`: 更新频率（天）
- `categories`: 自定义分类类别
- `max_stars`: 最大获取的Star项目数量（默认为5000）。如果您的Star项目数量超过此值，请增加此配置以获取所有项目。例如，对于有4000多个Star项目的用户，建议设置为5000或更高
- `incremental_update`: 是否启用增量更新模式（默认为true）。启用后，每次更新只获取最新的Star项目，而不是全量更新

### 网络请求配置
- `request_timeout`: 请求超时时间（秒），默认为30秒
- `max_retries`: 最大重试次数，默认为3次
- `retry_delay`: 初始重试延迟（秒），默认为5秒。每次重试失败后，延迟时间会翻倍（指数退避策略）

### AI配置
- `ai_model`: 使用的AI模型
- `ai_api_url`: AI API地址

## 自定义AI模型

默认使用智谱AI的GLM-4.5-Flash模型，您可以在`config.yaml`中修改`ai_model`和`ai_api_url`来使用其他AI模型。

如果您想使用其他AI服务，需要修改`src/classify.py`中的`call_ai_api`函数，以适配不同的API格式。

## 故障排除

### 常见问题

1. **获取Star项目失败**
   - 检查GitHub Token是否有效
   - 确认Token有`repo`和`user`权限
   - 检查GitHub API限流情况
   - 如果遇到504超时错误，可以尝试以下解决方案：
     - 在`config.yaml`中增加`request_timeout`值（例如60秒）
     - 增加`max_retries`值（例如5次）
     - 减小`max_stars`值，分批获取项目

2. **AI分类失败**
   - 检查AI API密钥是否有效
   - 确认API URL是否正确
   - 查看API调用日志获取详细错误信息

3. **GitHub Actions未运行**
   - 检查是否启用了GitHub Actions
   - 确认Secrets是否正确设置
   - 查看Actions日志获取详细错误信息

## 贡献指南

欢迎贡献代码、报告问题或提出改进建议！

1. Fork本仓库
2. 创建您的特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交您的更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建一个Pull Request

## Star项目列表

*此部分将由自动化脚本更新*

## 许可证

MIT