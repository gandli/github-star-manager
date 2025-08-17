from github import Github
import os
from datetime import datetime

# 初始化GitHub客户端
def init_github_client():
    token = os.getenv('GH_TOKEN')
    return Github(token)

# 获取用户star的项目
def get_starred_repos(g):
    user = g.get_user()
    return user.get_starred()

# 使用AI生成项目分类和摘要
def generate_summary(repo):
    # 基础项目信息
    base_info = f"""
## {repo.name}
- **描述**: {repo.description or '无描述'}
- **语言**: {repo.language or '未知'}
- **星数**: {repo.stargazers_count}
- **最后更新**: {repo.updated_at.strftime('%Y-%m-%d')}
"""
    
    # 使用启发式方法进行简单分类
    category = classify_repo(repo)
    
    return f"{base_info}- **分类**: {category}\n"

def classify_repo(repo):
    """启发式分类方法（后续可替换为AI模型）"""
    if not repo.description:
        return "未分类"
        
    description = repo.description.lower()
    
    if any(keyword in description for keyword in ['web', 'frontend', 'react', 'vue']):
        return "前端开发"
    elif any(keyword in description for keyword in ['api', 'backend', 'server', 'database']):
        return "后端开发"
    elif any(keyword in description for keyword in ['machine learning', 'ai', 'deep learning']):
        return "人工智能"
    elif any(keyword in description for keyword in ['devops', 'deploy', 'ci/cd']):
        return "DevOps"
    else:
        return "其他"

# 更新README.md
def update_readme(repos):
    with open('README.md', 'w') as f:
        f.write("# 我的GitHub Star项目\n\n")
        f.write(f"最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for repo in repos:
            f.write(generate_summary(repo))

if __name__ == "__main__":
    g = init_github_client()
    starred_repos = get_starred_repos(g)
    update_readme(starred_repos)