# GitHub Star 项目管理

> 自动更新于: {{update_time}}

这个仓库使用GitHub Actions自动获取我Star的项目，并使用AI进行分类和生成摘要。

## 项目分类

{% for category, repos in categories.items() %}
### {{category}}

{% if repos %}
{% for repo in repos %}
- [{{repo.name}}]({{repo.html_url}}) - {{repo.summary}} ![Stars](https://img.shields.io/github/stars/{{repo.full_name}}?style=social)
{% endfor %}
{% else %}
*暂无项目*
{% endif %}

{% endfor %}

## 统计信息

- 总计: {{total_count}} 个项目
- 最近更新: {{update_time}}

## 关于

本项目使用 [GitHub Star Manager](https://github.com/yourusername/github-star-manager) 自动生成