# 工作流模块

GitHub Actions workflow automation and document building.

## 目录结构

```
workflows/
├── __init__.py
└── build_documents.py    # 文档构建工作流脚本
```

## 核心功能

### build_documents.py

GitHub Actions 调用的主要构建脚本。

**功能:**
- 协调各模块完成文档构建
- 生成目录、页面、索引
- 触发部署流程

**典型工作流:**

```yaml
# .github/workflows/build.yml
name: Build Documents

on:
  push:
    branches: [ main ]
  schedule:
    - cron: '0 */6 * * *'  # 每6小时
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          submodules: recursive
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Build documents
        run: |
          python -m workflows.build_documents
      
      - name: Deploy
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./site
```

**构建流程:**

```python
def main():
    # 1. 更新子模块
    update_submodules()
    
    # 2. 生成目录索引
    catalog_main()
    
    # 3. 生成文件页面
    gen_page_main()
    
    # 4. 生成完整目录
    full_toc_main()
    
    # 5. 生成搜索索引
    gen_search_index()
    
    # 6. 构建站点
    build_site()
```

## 与其他模块的关系

```
workflows/build_documents.py
    ├── calls config/catalog.py
    ├── calls page/gen_page.py
    ├── calls toc/full_toc.py
    ├── calls file/gen_search_index.py
    └── triggers GitHub Pages deployment
```

## 环境变量

| 变量 | 说明 |
|------|------|
| `GITHUB_TOKEN` | GitHub API Token |
| `OPENAI_API_KEY` | OpenAI API Key (用于AI摘要) |
| `GA_ID` | Google Analytics ID |

## 输出

构建完成后生成:
- 静态网站文件 (HTML/CSS/JS)
- 搜索索引 (JSON)
- 目录页面 (Markdown/HTML)
- 文件展示页面

## 依赖

- 所有其他模块的依赖
- GitPython (子模块操作)
