# GitHub Star Manager

一个基于Python和GitHub Actions的自动化GitHub收藏项目管理系统，通过AI技术实现项目智能分类和文档生成。

## 🌟 功能特性

- 🚀 **自动获取GitHub Star项目** - 支持全量和增量更新模式
- 🤖 **AI智能分类** - 使用Cloudflare Workers AI进行项目分类和摘要生成
- 📊 **数据管理** - 统一的数据存储、更新和统计功能
- 📝 **自动文档生成** - 按分类生成独立的Markdown文档
- ⚡ **GitHub Actions自动化** - 定时执行和手动触发支持
- 🔄 **增量更新** - 智能避免重复处理，提高效率
- 📈 **统计分析** - 详细的项目统计和分类概览

## 📋 项目统计

<!-- GITHUB_STAR_MANAGER_START -->
<!-- 此部分内容由GitHub Star Manager自动生成和更新 -->

### 📊 项目统计

- **总项目数**: 10
- **已分类项目**: 10
- **未分类项目**: 0
- **分类完成率**: 100.0%

### 📂 分类概览

| 分类 | 项目数量 | 文档链接 |
|------|----------|----------|
| 前端开发 | 3 | [📖 查看详情](docs/前端开发.md) |
| 机器学习 | 3 | [📖 查看详情](docs/机器学习.md) |
| 后端开发 | 2 | [📖 查看详情](docs/后端开发.md) |
| 网络安全 | 1 | [📖 查看详情](docs/网络安全.md) |
| 开发工具 | 1 | [📖 查看详情](docs/开发工具.md) |

### 💻 主要编程语言

| 语言 | 项目数量 | 占比 |
|------|----------|------|
| TypeScript | 4 | 40.0% |
| Python | 2 | 20.0% |
| Dart | 1 | 10.0% |
| Ruby | 1 | 10.0% |
| Go | 1 | 10.0% |
| C++ | 1 | 10.0% |

### 🕒 更新信息

- **最后更新时间**: 2025-08-19 03:41:14
- **最近添加的项目**:
  - [keepassxc](https://github.com/keepassxreboot/keepassxc)
  - [FerretDB](https://github.com/FerretDB/FerretDB)
  - [discourse](https://github.com/discourse/discourse)
  - [vite](https://github.com/vitejs/vite)
  - [ente](https://github.com/ente-io/ente)

📋 [查看完整分类索引](docs/index.md)

<!-- GITHUB_STAR_MANAGER_END -->

## 🚀 快速开始

### 环境要求

- Python 3.8+
- GitHub个人访问令牌 (PAT)
- Cloudflare Workers AI API密钥

### 安装步骤

1. **克隆项目**
   ```bash
   git clone https://github.com/your-username/github-star-manager.git
   cd github-star-manager
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置环境变量**
   
   创建 `.env` 文件或设置以下环境变量：
   ```bash
   export GH_PAT="your_github_personal_access_token"
   export AI_API_KEY="your_cloudflare_ai_api_key"
   export AI_ACCOUNT_ID="your_cloudflare_account_id"
   export GITHUB_USERNAME="your_github_username"
   ```

4. **配置参数**
   
   根据需要修改 `config.yaml` 文件中的配置参数。

### 使用方法

#### 手动运行

```bash
# 1. 获取星标项目（增量模式）
FETCH_MODE=incremental python src/fetch_stars.py

# 2. AI分类
python src/classify.py

# 3. 生成文档
python src/generate_category_docs.py
python src/update_readme.py
```

#### 全量更新

```bash
# 获取所有星标项目（全量模式）
FETCH_MODE=full python src/fetch_stars.py

# 后续步骤相同
python src/classify.py
python src/generate_category_docs.py
python src/update_readme.py
```

#### GitHub Actions自动化

项目配置了GitHub Actions工作流，支持：

- **定时执行**：每天UTC时间3点自动运行（增量模式）
- **手动触发**：在Actions页面手动触发，可选择更新模式
- **参数配置**：支持获取模式、强制全量、跳过分类等选项

## 📁 项目结构

```
github-star-manager/
├── src/                           # 源代码目录
│   ├── fetch_stars.py            # 数据获取模块
│   ├── classify.py               # AI分类模块
│   ├── data_manager.py           # 数据管理模块
│   ├── generate_category_docs.py # 分类文档生成
│   └── update_readme.py          # README更新模块
├── data/                          # 数据存储目录
│   └── stars_data.json           # 项目数据文件
├── docs/                          # 文档输出目录
│   ├── index.md                  # 分类索引
│   └── *.md                      # 各分类文档
├── .github/workflows/             # GitHub Actions工作流
│   └── update_stars.yml          # 自动化工作流配置
├── logs/                          # 日志文件目录
├── config.yaml                   # 配置文件
├── requirements.txt              # Python依赖
└── README.md                     # 项目说明文档
```

## ⚙️ 配置说明

### 环境变量

| 变量名 | 描述 | 必需 |
|--------|------|------|
| `GH_PAT` | GitHub个人访问令牌 | ✅ |
| `AI_API_KEY` | Cloudflare Workers AI API密钥 | ✅ |
| `AI_ACCOUNT_ID` | Cloudflare账户ID | ✅ |
| `FETCH_MODE` | 获取模式 (full/incremental) | ❌ |

### 配置文件 (config.yaml)

主要配置项包括：

- **GitHub API配置**：请求超时、重试次数、获取数量限制
- **AI分类配置**：模型选择、并发控制、分类定义
- **数据管理配置**：文件路径、备份设置
- **文档生成配置**：输出目录、每分类最大显示数量
- **日志配置**：日志级别、格式设置

## 🤖 AI分类系统

### 预定义分类

系统预设了10个主要分类：

1. **前端开发** - Web前端、UI/UX、JavaScript框架等
2. **后端开发** - 服务器端、API、数据库等
3. **机器学习** - ML算法、深度学习、AI工具等
4. **数据科学** - 数据分析、可视化、统计工具等
5. **开发工具** - IDE、构建工具、调试工具等
6. **网络安全** - 安全工具、加密、渗透测试等
7. **云计算** - 云服务、容器化、微服务等
8. **桌面应用** - 桌面软件、GUI框架等
9. **移动应用** - 移动开发、跨平台框架等
10. **系统工具** - 系统管理、运维、监控等

### AI处理流程

1. **数据预处理** - 提取项目关键信息
2. **智能分类** - 基于项目描述、语言、标签等进行分类
3. **摘要生成** - 生成项目的简洁摘要
4. **特性提取** - 识别项目的关键特性
5. **结果验证** - 确保分类结果的准确性

## 📊 数据管理

### 数据结构

```json
{
  "metadata": {
    "last_updated": "2024-01-01T00:00:00Z",
    "total_repositories": 1000,
    "fetch_mode": "incremental"
  },
  "repositories": [
    {
      "id": 123456,
      "name": "project-name",
      "full_name": "owner/project-name",
      "description": "Project description",
      "html_url": "https://github.com/owner/project-name",
      "language": "Python",
      "stargazers_count": 1000,
      "is_classified": true,
      "category": "机器学习",
      "summary": "AI generated summary",
      "key_features": ["feature1", "feature2"]
    }
  ]
}
```

### 增量更新机制

- **智能检测** - 自动识别新增和更新的项目
- **状态跟踪** - 维护分类状态，避免重复处理
- **数据合并** - 安全地合并新旧数据
- **备份机制** - 自动备份重要数据

## 🔧 高级功能

### 自定义分类

可以在 `config.yaml` 中添加自定义分类：

```yaml
ai_classification:
  categories:
    - "自定义分类1"
    - "自定义分类2"
```

### 批量操作

```bash
# 生成特定分类的文档
python src/generate_category_docs.py category "机器学习"

# 生成分类索引
python src/generate_category_docs.py index

# 清理旧文档
python src/generate_category_docs.py clean
```

### 数据导出

```python
from src.data_manager import DataManager

dm = DataManager()

# 导出特定分类的数据
ml_repos = dm.get_repositories_by_category("机器学习")

# 获取统计信息
stats = dm.get_statistics()
```

## 🐛 故障排除

### 常见问题

1. **API限流**
   - 检查GitHub API配额
   - 调整请求间隔和重试策略

2. **AI分类失败**
   - 验证Cloudflare API密钥
   - 检查网络连接
   - 查看错误日志

3. **数据文件损坏**
   - 使用备份文件恢复
   - 重新执行全量获取

### 日志查看

```bash
# 查看最新日志
tail -f logs/github_star_manager.log

# 查看错误日志
grep "ERROR" logs/github_star_manager.log
```

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 开发环境设置

```bash
# 安装开发依赖
pip install -r requirements.txt

# 运行测试
python -m pytest tests/

# 代码格式化
black src/

# 代码检查
flake8 src/
```

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [GitHub API](https://docs.github.com/en/rest) - 提供项目数据
- [Cloudflare Workers AI](https://developers.cloudflare.com/workers-ai/) - AI分类服务
- [GitHub Actions](https://github.com/features/actions) - 自动化执行

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 [Issue](https://github.com/your-username/github-star-manager/issues)
- 发起 [Discussion](https://github.com/your-username/github-star-manager/discussions)
- 邮件：gandli@qq.com

---

⭐ 如果这个项目对你有帮助，请给它一个星标！