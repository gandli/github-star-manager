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

*最后更新时间: 2025-08-18 00:01:54*

用户: [None](https://github.com/None)

### machine learning

#### [QwenLM/Qwen3-Coder](https://github.com/QwenLM/Qwen3-Coder)

⭐ 12204 | 🔄 830 | 🔤 Python

Qwen3-Coder is the code version of the large language model developed by Qwen team at Alibaba Cloud, specializing in code generation and understanding as a powerful AI programming assistant.

**主要特点:**

- A large language model specifically optimized for code
- Supports code generation and understanding in multiple programming languages
- Based on the Qwen3 series model architecture
- Provides powerful code completion and functionality implementation capabilities
- Can be used for code review and optimization suggestions

### 其他

#### [yzddmr6/WebCrack](https://github.com/yzddmr6/WebCrack)

⭐ 1976 | 🔄 327 | 🔤 Python

WebCrack是一个Python编写的安全测试工具，用于批量检测网站后台的弱密码和万能密码，通过导入后台地址列表实现自动化检测。

**主要特点:**

- 支持批量检测多个网站后台地址
- 自动化检测弱口令和万能密码
- 使用Python开发，易于扩展和定制
- 提供简单直观的用户界面
- 专注于网站后台安全性测试

#### [sagemath/sage](https://github.com/sagemath/sage)

⭐ 1913 | 🔄 648 | 🔤 Python

SageMath是一个开源的数学软件系统，基于Python构建，整合众多开源数学软件包，提供统一计算环境，支持多领域数学研究和教学。

**主要特点:**

- 集成多种开源数学软件包，提供统一的Python接口
- 支持广泛的数学领域，包括代数、几何、数论、密码学等
- 提供强大的计算能力，包括符号计算、数值计算和可视化
- 开源免费，可自由使用和修改
- 活跃的开发社区，持续更新和改进

#### [Marven11/Fenjing](https://github.com/Marven11/Fenjing)

⭐ 1040 | 🔄 67 | 🔤 Python

Fenjing是一个专为CTF设计的Python工具，用于自动化绕过WAF防护的Jinja2 SSTI漏洞利用，帮助安全研究人员和参赛者测试和利用模板注入漏洞。

**主要特点:**

- 专门针对Jinja2模板引擎的SSTI漏洞
- 自动化绕过WAF防护机制
- 专为CTF比赛场景设计
- 提供多种绕过技术和payload
- 基于Python开发，易于扩展和定制

### 前端开发

#### [nunocoracao/blowfish](https://github.com/nunocoracao/blowfish)

⭐ 2213 | 🔄 578 | 🔤 HTML

Blowfish是一个功能丰富、响应式的Hugo博客主题，适用于个人网站和博客，提供高质量网站设计。

**主要特点:**

- 功能丰富的博客主题
- 响应式设计，适配各种设备
- 详细的文档支持
- MIT许可证，开源免费
- 专为Hugo静态网站生成器设计

#### [mengxi-ream/read-frog](https://github.com/mengxi-ream/read-frog)

⭐ 2004 | 🔄 98 | 🔤 TypeScript

Read Frog是一个开源的浏览器扩展，提供沉浸式翻译体验，支持多语言，集成AI模型，帮助语言学习。

**主要特点:**

- 沉浸式翻译体验，实时翻译外语内容
- 支持多种语言（中文、英文、日文等）
- 集成多种AI模型（GPT、OpenAI、Deepseek等）
- 开源项目，可自由使用和修改
- 专为语言学习设计，提升理解能力

#### [googlefonts/googlesans-code](https://github.com/googlefonts/googlesans-code)

⭐ 1483 | 🔄 31 | 🔤 Python

Google Sans Code是专为代码显示优化的字体家族，提供清晰的字符区分和可读性，适合开发者使用。

**主要特点:**

- 专为代码显示优化的字体设计
- 提高代码可读性的字符区分
- 支持多种编程语言的特殊字符
- 适合长时间编码使用的舒适度
- 开源可自由使用

#### [openai/gpt-5-coding-examples](https://github.com/openai/gpt-5-coding-examples)

⭐ 1317 | 🔄 155 | 🔤 HTML

OpenAI官方创建的GPT-5编码示例项目，展示AI在前端Web开发中的应用能力，主要使用HTML实现，为开发者提供AI辅助编程参考。

**主要特点:**

- 展示GPT-5在前端开发中的应用能力
- 提供实际的HTML编码示例
- 由OpenAI官方创建，具有权威性
- 包含Web开发相关的AI编程案例
- 为开发者提供AI辅助编程的学习资源

#### [carbofish/A1CTF](https://github.com/carbofish/A1CTF)

⭐ 72 | 🔄 9 | 🔤 TypeScript

A1CTF是为A1natas设计的安全竞赛平台，使用TypeScript开发，提供CTF挑战和竞赛环境，帮助参与者提升网络安全技能。

**主要特点:**

- 专为A1natas设计的CTF竞赛平台
- 使用TypeScript开发，确保代码质量
- 提供多种网络安全挑战
- 支持提交和验证CTF旗帜
- 包含用户认证和积分系统

### 学习资源

#### [A-poc/RedTeam-Tools](https://github.com/A-poc/RedTeam-Tools)

⭐ 7147 | 🔄 972 | 🔤 未知

RedTeam-Tools是一个红队和渗透测试的综合资源库，汇集了各种安全工具、技术、备忘录和资源，帮助安全专业人员执行渗透测试和红队操作。

**主要特点:**

- 包含广泛的渗透测试工具和技术
- 提供Linux和Windows平台的资源
- 基于MITRE ATT&CK框架的战术和技术
- 包含各种payload和利用代码
- 提供cheatsheet和实用资源

#### [crypto101/book](https://github.com/crypto101/book)

⭐ 3505 | 🔄 214 | 🔤 Python

这是一本关于密码学基础知识的入门书籍，旨在为读者提供密码学的基本概念和原理。

**主要特点:**

- 以书籍形式呈现密码学基础知识
- 使用Python作为主要语言编写示例
- 适合密码学初学者阅读
- 开源项目，社区贡献
- 包含密码学核心概念的详细解释

#### [ffffffff0x/AboutSecurity](https://github.com/ffffffff0x/AboutSecurity)

⭐ 1048 | 🔄 192 | 🔤 HTML

这是一个关于渗透测试的综合学习资源库，包含各种payload、bypass字典、CTF技巧和安全工具，适合安全研究人员和渗透测试人员参考。

**主要特点:**

- 收集了大量渗透测试相关的payload和bypass字典
- 包含CTF竞赛相关的技巧和资源
- 提供安全测试的方法论和流程
- 涵盖多个安全领域，包括web安全、基础设施安全等
- 以HTML格式组织，便于浏览和查找

#### [mimoo/RSA-and-LLL-attacks](https://github.com/mimoo/RSA-and-LLL-attacks)

⭐ 808 | 🔄 129 | 🔤 TeX

这个项目提供了关于使用格约简技术（特别是LLL算法）攻击RSA加密算法的研究和教育材料，涵盖了Boneh-Durfee攻击等多种密码分析技术。

**主要特点:**

- 使用TeX编写的学术文档，详细解释RSA格约简攻击
- 包含Boneh-Durfee攻击等多种RSA攻击方法的研究
- 结合Sage数学软件实现密码分析算法
- 提供密码学教育和研究资源
- 关注格约简技术在密码分析中的应用

#### [ProbiusOfficial/PHPSerialize-labs](https://github.com/ProbiusOfficial/PHPSerialize-labs)

⭐ 186 | 🔄 16 | 🔤 PHP

PHPSerialize-labs是一个PHP语言编写的CTF靶场，专注于PHP序列化和反序列化学习。它提供实践环境，帮助安全研究人员和开发者深入理解PHP反序列化漏洞原理及利用方法。

**主要特点:**

- 专门针对PHP序列化和反序列化的CTF学习靶场
- 提供多种难度的PHP反序列化挑战
- 帮助理解PHP反序列化漏洞原理和利用方法
- 适合CTF竞赛和安全研究人员学习使用
- 包含实际案例和练习，增强实战能力

#### [mcc0624/php_cmd](https://github.com/mcc0624/php_cmd)

⭐ 24 | 🔄 1 | 🔤 HTML

这是一个PHP命令执行漏洞的实践学习平台，专为CTF竞赛和安全研究人员设计，提供安全漏洞测试环境，帮助学习者理解和防御PHP命令注入攻击。

**主要特点:**

- 提供PHP命令执行漏洞的实践环境
- 专为CTF竞赛和安全研究设计
- 包含多种命令注入场景和挑战
- 帮助学习者理解PHP安全漏洞原理
- 提供安全的测试环境，不影响实际系统

### 开发工具

#### [upx/upx](https://github.com/upx/upx)

⭐ 16330 | 🔄 1445 | 🔤 C++

UPX是一个开源的可执行文件压缩工具，支持多种平台的可执行文件、动态库和目标文件。它能显著减小文件大小，同时保持文件的可执行性。

**主要特点:**

- 支持多种平台和文件格式（Windows、Linux、macOS等）
- 高效的压缩算法，能显著减小文件大小
- 保持压缩后文件的完整性和可执行性
- 开源免费，命令行界面简单易用
- 跨平台支持，可在不同操作系统上运行

#### [mendableai/open-lovable](https://github.com/mendableai/open-lovable)

⭐ 14225 | 🔄 2277 | 🔤 TypeScript

open-lovable是一个强大的开发工具，允许用户快速将任何网站克隆并转换为现代化的React应用程序，只需几秒钟即可完成。

**主要特点:**

- 快速克隆并重建任何网站为React应用
- 使用TypeScript开发，提供类型安全
- 简化前端开发流程，节省大量时间
- 适合学习和研究现有网站的结构和实现
- 开源项目，拥有活跃的社区支持

#### [capstone-engine/capstone](https://github.com/capstone-engine/capstone)

⭐ 8212 | 🔄 1610 | 🔤 C

Capstone是一个轻量级、多架构的反汇编框架，支持ARM、x86、MIPS等多种处理器架构，为逆向工程和安全分析提供指令级反汇编能力。

**主要特点:**

- 支持多种处理器架构，包括ARM、ARM64、x86、MIPS、RISC-V等
- 提供轻量级、快速的反汇编引擎
- 支持多种编程语言的绑定（Python、Java、Ruby等）
- 提供详细的指令信息，包括操作码、操作数等
- 具有模块化设计，易于集成到各种项目中

#### [hugsy/gef](https://github.com/hugsy/gef)

⭐ 7680 | 🔄 784 | 🔤 Python

GEF是GDB的增强功能插件，为Linux上的漏洞开发和逆向工程提供现代化的调试体验，支持多种架构和安全研究专用功能。

**主要特点:**

- 增强GDB调试功能，提供更友好的用户体验
- 支持多种架构（x86, MIPS, PowerPC, SPARC等）
- 为漏洞开发和逆向工程提供专门命令和功能
- 集成Python API，支持自定义脚本和扩展
- 提供内存分析、寄存器检查、反汇编等高级调试功能

#### [d60/twikit](https://github.com/d60/twikit)

⭐ 3412 | 🔄 391 | 🔤 Python

twikit是一个Python编写的Twitter API抓取工具，无需API密钥即可访问Twitter内部API，允许用户免费抓取Twitter数据并可作为Twitter机器人使用。

**主要特点:**

- 无需API密钥即可访问Twitter内部API
- 支持数据抓取和机器人功能
- Python编写，易于集成
- 免费使用
- 绕过官方API限制

#### [google/bindiff](https://github.com/google/bindiff)

⭐ 2668 | 🔄 184 | 🔤 Java

bindiff是Google开发的开源工具，用于快速比较反汇编代码的差异和相似性，支持IDA Pro插件，提高逆向工程效率。

**主要特点:**

- 快速比较反汇编代码的差异和相似性
- 提供IDA Pro插件集成
- 使用vxsig算法实现高效的二进制函数相似性检测
- 支持多种编程语言的反汇编代码比较
- 可视化展示代码差异，便于分析理解

#### [david942j/one_gadget](https://github.com/david942j/one_gadget)

⭐ 2213 | 🔄 145 | 🔤 Ruby

one_gadget是一个Ruby工具，专门用于在glibc库中查找单一的gadget代码片段，可用于CTF竞赛中的漏洞利用和远程代码执行。

**主要特点:**

- 专门查找glibc库中的one gadget RCE
- 支持多种版本的glibc库
- 提供简洁的命令行界面
- 常用于CTF竞赛和pwn挑战
- 帮助安全研究人员快速找到可利用的代码片段

#### [wyzxxz/shiro_rce_tool](https://github.com/wyzxxz/shiro_rce_tool)

⭐ 1517 | 🔄 181 | 🔤 未知

这是一个Apache Shiro反序列化远程代码执行(RCE)漏洞的辅助检测工具，帮助安全研究人员和渗透测试人员检测和利用Shiro框架中的安全漏洞。

**主要特点:**

- 专门针对Apache Shiro框架的反序列化漏洞检测
- 提供命令执行功能，可用于验证漏洞存在性
- 简化漏洞检测流程，提高安全测试效率
- 可能包含多种检测方法和payload
- 可能提供友好的用户界面或命令行操作方式

#### [sky22333/hubproxy](https://github.com/sky22333/hubproxy)

⭐ 1296 | 🔄 126 | 🔤 Go

hubproxy是一个基于Go的自托管轻量级代理加速服务，提供Docker镜像和GitHub加速功能，支持离线镜像下载、仓库审计和流式转发，无需缓存。

**主要特点:**

- 轻量级、高性能的多功能代理加速服务
- 支持Docker镜像加速和GitHub加速
- 单域名实现所有功能
- 支持仓库审计
- 流式转发，无缓存设计

#### [UzJu/Cloud-Bucket-Leak-Detection-Tools](https://github.com/UzJu/Cloud-Bucket-Leak-Detection-Tools)

⭐ 1184 | 🔄 143 | 🔤 Python

一款Python开发的工具，用于检测六大云存储服务中的数据泄露问题，帮助用户及时发现和修复安全漏洞。

**主要特点:**

- 支持六大云存储平台的泄露检测
- 使用Python编写，易于部署和使用
- 能够及时发现云存储桶中的公开访问和敏感信息泄露
- 提供详细的检测结果和修复建议
- 帮助提高云存储安全性和数据保护能力

#### [UfoMiao/zcf](https://github.com/UfoMiao/zcf)

⭐ 641 | 🔄 42 | 🔤 TypeScript

zcf是一个零配置的Claude代码流工具，基于TypeScript开发，简化与Claude AI的代码交互流程，提升开发效率。

**主要特点:**

- 零配置设计，开箱即用
- 基于Claude AI的代码生成和辅助功能
- 支持工作流程自动化
- 提供CLI界面，便于命令行操作
- 集成Claude API，实现智能代码交互

#### [iflow-ai/iflow-cli](https://github.com/iflow-ai/iflow-cli)

⭐ 607 | 🔄 50 | 🔤 Shell

iFlow CLI是一个嵌入终端的智能命令行工具，可分析仓库、执行编码任务、解释需求并自动化工作流程，提高开发效率。

**主要特点:**

- 嵌入终端的智能命令行界面
- 仓库分析和代码任务执行
- 跨上下文需求解释
- 从简单文件操作到复杂工作流程的自动化
- 提高开发效率的综合工具

#### [AmintaCCCP/GithubStarsManager](https://github.com/AmintaCCCP/GithubStarsManager)

⭐ 587 | 🔄 16 | 🔤 TypeScript

GithubStarsManager is an application built with TypeScript for managing GitHub starred repositories, helping users organize and access their favorite projects more efficiently.

**主要特点:**

- Provides visual management and organization of starred repositories
- Supports grouping starred repositories by tags or categories
- Offers search and filter functionality to quickly find specific starred repositories
- Integrates with GitHub API for automatic synchronization of starred information
- Provides local storage or cloud sync functionality to ensure data persistence

#### [Byxs20/PuzzleSolver](https://github.com/Byxs20/PuzzleSolver)

⭐ 503 | 🔄 16 | 🔤 未知

PuzzleSolver是一款专为CTF竞赛MISC类别设计的工具，提供各种谜题解决、密码分析和隐写术功能，帮助参赛者快速解决挑战性问题。

**主要特点:**

- 专为CTF竞赛MISC类别设计
- 支持多种谜题类型和解密方法
- 集成常见隐写术分析工具
- 提供密码学辅助功能
- 可能包含自动化脚本提高解题效率

#### [hemashushu/docker-archlinux-gui](https://github.com/hemashushu/docker-archlinux-gui)

⭐ 291 | 🔄 8 | 🔤 Shell

Docker Arch Linux GUI是一个教程项目，演示如何在Docker和Podman容器中直接运行GUI应用程序，无需额外安装软件，使用Shell脚本实现。

**主要特点:**

- 提供在容器中运行GUI应用的方法
- 支持Docker和Podman容器技术
- 无需额外安装任何软件
- 使用Shell脚本实现
- 包含详细的教程说明

#### [bestK/kiro2cc](https://github.com/bestK/kiro2cc)

⭐ 256 | 🔄 33 | 🔤 Go

kiro2cc是一个Go语言开发的工具，用于将kiro格式的代码转换为Claude兼容的代码格式。它提供API接口，方便开发者在不同代码格式间转换。

**主要特点:**

- 使用Go语言开发，性能高效
- 提供API接口，便于集成
- 支持kiro格式到Claude代码格式的转换
- 专门针对代码格式转换优化
- 可能支持批量处理或自动化转换

#### [PortSwigger/mcp-server](https://github.com/PortSwigger/mcp-server)

⭐ 233 | 🔄 34 | 🔤 Kotlin

这是一个为Burp Suite开发的服务器端扩展，使用Kotlin编写，允许与MCP协议交互，增强Burp的安全测试功能。

**主要特点:**

- 作为Burp Suite的扩展服务器运行
- 支持MCP协议通信
- 使用Kotlin语言开发
- 增强Burp Suite的安全测试能力
- 由PortSwigger官方开发

#### [heimao-box/pwnpasi](https://github.com/heimao-box/pwnpasi)

⭐ 150 | 🔄 15 | 🔤 Python

pwnpasi是一个自动化PWN漏洞利用框架，专为CTF竞赛和二进制漏洞利用设计，支持32位和64位程序的自动分析和利用。

**主要特点:**

- 自动化PWN漏洞利用框架
- 集成多种利用技术（堆栈溢出、格式字符串攻击等）
- 支持32位和64位程序的分析和利用
- 专为CTF竞赛和二进制漏洞利用设计
- 基于Python开发，便于扩展和定制

#### [y-shi23/MeowNocode](https://github.com/y-shi23/MeowNocode)

⭐ 149 | 🔄 21 | 🔤 JavaScript

MeowNocode是一个JavaScript无代码开发工具，提供可视化界面和组件化开发方式，使非开发者无需编程即可快速构建应用。

**主要特点:**

- 可视化界面设计：提供拖放式界面，无需编写代码即可设计应用界面
- 组件化开发：提供预构建组件，用户可以通过组合这些组件来创建功能
- 实时预览：允许用户在开发过程中实时查看应用效果
- 响应式设计支持：确保创建的应用在不同设备上都能良好显示
- 可能集成常见功能：如用户认证、数据库连接等

#### [ngramai/opencodespace](https://github.com/ngramai/opencodespace)

⭐ 24 | 🔄 1 | 🔤 Python

opencodespace提供可丢弃的VS Code容器，用于安全运行Claude Code和Gemini CLI等AI开发工具。

**主要特点:**

- 提供可丢弃的VS Code容器环境
- 支持运行Claude Code和Gemini CLI等AI开发工具
- 使用Python编写，便于定制和扩展
- 为AI工具提供隔离的运行环境
- 简化AI开发工具的部署和使用流程

#### [daodao97/claude-code-proxy](https://github.com/daodao97/claude-code-proxy)

⭐ 21 | 🔄 1 | 🔤 Go

这是一个Go编写的Claude API代理工具，提供友好的请求日志查看功能，增强API请求的稳定性，帮助开发者更好地与Claude交互。

**主要特点:**

- 作为Claude API的代理服务
- 提供友好的请求日志查看界面
- 增强API请求的稳定性
- 使用Go语言编写，具有高性能特点
- 可能包含请求重试、错误处理等稳定性相关功能

### 数据科学

#### [shshemi/tabiew](https://github.com/shshemi/tabiew)

⭐ 2067 | 🔄 55 | 🔤 Rust

Tabiew是一个用Rust编写的轻量级TUI工具，专为查看和查询CSV、TSV和parquet等表格数据文件而设计，提供了高效的数据浏览和分析体验。

**主要特点:**

- 轻量级TUI界面，提供直观的数据浏览体验
- 支持多种表格数据格式（CSV、TSV、parquet）
- 内置查询功能，可过滤和分析数据
- 使用Rust编写，性能高效且内存占用低
- 专为命令行环境优化，适合开发者使用

### 机器学习

#### [browseros-ai/BrowserOS](https://github.com/browseros-ai/BrowserOS)

⭐ 3760 | 🔄 266 | 🔤 Python

BrowserOS是一个开源的智能代理网络浏览器，利用AI技术实现自动化浏览和任务执行。

**主要特点:**

- 基于AI的智能代理功能，能够理解用户意图
- 自动化网络浏览和任务执行能力
- 开源特性，允许社区贡献和改进
- 支持通过自然语言指令进行操作
- 具有记忆和学习能力，能够适应用户习惯

#### [usestrix/strix](https://github.com/usestrix/strix)

⭐ 69 | 🔄 6 | 🔤 Python

Strix是一个开源的AI黑客工具集，使用Python构建，旨在帮助开发者将AI功能集成到他们的应用程序中。

**主要特点:**

- 开源AI工具集，专为应用集成设计
- 提供多种AI黑客功能
- 基于Python实现，便于开发者使用和扩展
- 轻量级且易于集成到现有项目中
- 活跃的开发社区支持

### 系统工具

#### [9001/copyparty](https://github.com/9001/copyparty)

⭐ 24575 | 🔄 883 | 🔤 Python

copyparty是一个便携式文件服务器，支持加速上传、去重、多种传输协议、媒体索引和缩略图等功能，无需依赖，所有功能集成在一个文件中。

**主要特点:**

- 便携式设计 - 所有功能集成在一个文件中，无需安装依赖
- 多协议支持 - 支持WebDAV、FTP、TFTP等多种文件传输协议
- 高级上传功能 - 提供加速可恢复上传和文件去重
- 媒体管理 - 包含媒体索引器和增强的缩略图功能
- 零配置网络 - 支持zeroconf自动发现

#### [phusion/baseimage-docker](https://github.com/phusion/baseimage-docker)

⭐ 9034 | 🔄 1091 | 🔤 Shell

Phusion Baseimage是一个为Docker优化的最小化Ubuntu基础镜像，提供了稳定的运行环境和常用的服务配置，简化了Docker容器的创建和管理。

**主要特点:**

- 最小化Ubuntu系统，减少镜像大小和攻击面
- 包含必要的Docker优化配置和服务
- 提供稳定的初始化系统（类似init.d）
- 包含常用的系统工具和服务
- 支持多阶段构建和高效缓存

#### [knownsec/pocsuite3](https://github.com/knownsec/pocsuite3)

⭐ 3760 | 🔄 785 | 🔤 Python

pocsuite3是一个开源的远程漏洞测试框架，由Knownsec 404团队开发，用于渗透测试和漏洞验证。

**主要特点:**

- 开源的远程漏洞测试框架
- 支持多种漏洞验证模式
- 提供丰富的POC（概念验证）库
- 支持自定义POC编写
- 具有命令行和API接口，便于集成和自动化

#### [KimiNewt/pyshark](https://github.com/KimiNewt/pyshark)

⭐ 2411 | 🔄 441 | 🔤 Python

pyshark是Python封装的Wireshark(tshark)库，允许开发者使用Wireshark强大的解析功能在Python中捕获和分析网络数据包。

**主要特点:**

- 提供Python接口访问Wireshark的解析能力
- 支持多种网络协议的数据包解析
- 可以实时捕获和离线分析网络数据包
- 无需深入了解Wireshark的命令行操作
- 支持数据包过滤和详细分析

#### [Tokeii0/LovelyMem](https://github.com/Tokeii0/LovelyMem)

⭐ 1269 | 🔄 74 | 🔤 Python

LovelyMem是一个基于Memprocfs和Volatility的Python开发的可视化内存取证工具，专为CTF竞赛设计，帮助安全研究人员分析和提取内存中的关键证据。

**主要特点:**

- 基于Memprocfs和Volatility框架，提供强大的内存分析能力
- 可视化界面，使复杂的内存数据更易于理解和分析
- 专为CTF竞赛和内存取证场景设计
- Python开发，易于扩展和定制
- 支持Volatility3，兼容最新的内存分析需求

#### [withneural/neuralagent](https://github.com/withneural/neuralagent)

⭐ 765 | 🔄 91 | 🔤 Python

neuralagent是一个桌面AI代理，能够像人类一样使用计算机，支持跨平台自动化任务，通过本地LLM实现智能交互，提升个人生产力。

**主要特点:**

- 桌面AI代理：能够像人类一样与操作系统交互
- 跨平台支持：兼容Linux、macOS和Windows
- 本地LLM集成：使用本地语言模型进行智能决策
- 自动化任务：执行各种桌面自动化操作
- 个人生产力助手：帮助用户完成日常任务

#### [Arinue/CTF-NetA](https://github.com/Arinue/CTF-NetA)

⭐ 590 | 🔄 18 | 🔤 未知

CTF-NetA是专为CTF比赛设计的网络流量分析工具，能够自动分析常见网络流量并快速提取flag，提高参赛效率。

**主要特点:**

- 专门针对CTF比赛优化
- 自动分析网络流量
- 快速提取flag
- 支持多种常见网络协议分析
- 简化CTF竞赛中的取证过程

#### [Tokeii0/VolatilityPro](https://github.com/Tokeii0/VolatilityPro)

⭐ 332 | 🔄 20 | 🔤 Python

VolatilityPro是一款基于Python的内存取证工具，提供GUI界面，自动化处理内存取证任务，适用于CTF竞赛和数字取证分析。

**主要特点:**

- 基于Volatility框架的内存取证工具
- 提供图形用户界面(GUI)，简化操作流程
- 自动化处理内存取证任务，提高效率
- 适用于CTF竞赛和数字取证分析
- 使用Python开发，便于扩展和定制

#### [scavin/Win11Debloat](https://github.com/scavin/Win11Debloat)

⭐ 262 | 🔄 11 | 🔤 PowerShell

Win11Debloat是一个PowerShell脚本，用于移除Windows预装应用、禁用遥测功能，并执行各种优化操作，帮助用户自定义和清理Windows系统，提升使用体验。

**主要特点:**

- 简单易用的PowerShell脚本
- 移除预安装应用
- 禁用遥测功能
- 自定义Windows设置
- 适用于Windows 10和Windows 11

#### [kenjiaiko/binarybook](https://github.com/kenjiaiko/binarybook)

⭐ 222 | 🔄 200 | 🔤 C

一个用C语言开发的二进制数据处理工具，可能用于电子书格式转换或二进制数据解析。

**主要特点:**

- 处理二进制数据格式
- 可能支持电子书相关功能
- 使用C语言实现，性能高效
- 提供命令行界面
- 包含二进制数据的解析和生成功能

#### [Byxs20/FlowAnalyzer](https://github.com/Byxs20/FlowAnalyzer)

⭐ 76 | 🔄 12 | 🔤 Python

FlowAnalyzer是一个Python工具，专门用于解析和处理tshark导出的JSON格式网络流量数据，帮助用户分析和理解网络通信模式。

**主要特点:**

- 解析tshark导出的JSON数据文件
- Python开发，易于集成和扩展
- 提供网络流量分析和可视化功能
- 帮助识别网络通信模式和行为
- 支持处理大规模网络流量数据



## 许可证

MIT