# AutoArchive Scripts

自动化档案库管理脚本集合，用于跨性别与多元性别数字图书馆的内容处理、页面生成和站点构建。

## 项目概述

本仓库包含一套完整的自动化工具链，用于管理大型文档档案库。它通过 GitHub Actions 实现自动化内容处理、AI 摘要生成、页面构建和站点部署。

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    GitHub Actions                       │
│              (定时触发 / 手动触发 / Push触发)              │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│              workflows/build_documents.py               │
│                    (构建协调器)                          │
└─────────────────────┬───────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
   ┌─────────┐  ┌──────────┐  ┌──────────┐
   │  ai/    │  │ config/  │  │  page/   │
   │AI处理   │  │配置管理  │  │页面生成  │
   └─────────┘  └──────────┘  └──────────┘
        │             │             │
        └─────────────┼─────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
   ┌─────────┐  ┌──────────┐  ┌──────────┐
   │  toc/   │  │  file/   │  │  tools/  │
   │目录生成 │  │文件处理  │  │工具集    │
   └─────────┘  └──────────┘  └──────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                   GitHub Pages                          │
│                 (静态站点部署)                           │
└─────────────────────────────────────────────────────────┘
```

## 目录结构

| 目录 | 功能 | 详细文档 |
|------|------|----------|
| `ai/` | AI 内容处理、摘要生成 | [README](ai/README.md) |
| `config/` | 配置管理、目录索引、访问统计 | [README](config/README.md) |
| `file/` | 文件处理、编码转换、搜索索引 | [README](file/README.md) |
| `page/` | 页面生成、词云、文本嵌入 | [README](page/README.md) |
| `toc/` | 目录生成、内容处理、格式化 | [README](toc/README.md) |
| `tools/` | 文档转换、文件整理、分析工具 | [README](tools/README.md) |
| `workflows/` | GitHub Actions 工作流脚本 | [README](workflows/README.md) |
| `others/` | 其他工具脚本 | [README](others/README.md) |

## 核心功能

### 1. 自动化内容处理
- **AI 摘要生成**: 使用 OpenAI API 自动生成文档摘要
- **元数据提取**: 自动提取文件大小、MD5、格式等信息
- **编码处理**: 自动检测和修复文本编码问题

### 2. 页面生成
- **模板渲染**: 为每个文件生成 Markdown 展示页面
- **目录索引**: 自动生成层级目录结构
- **搜索索引**: 构建全站搜索索引

### 3. 站点构建
- **静态生成**: 构建可部署的静态网站
- **GitHub Pages**: 自动部署到 GitHub Pages
- **增量更新**: 只处理变更内容，提高效率

### 4. 访问统计
- **Google Analytics**: 集成 GA 数据分析
- **热门内容**: 识别高访问量文档
- **使用分析**: 搜索行为分析

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 环境变量

创建 `.env` 文件:

```bash
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL_NAME=gpt-4o-mini
OPENAI_TEMPERATURE=0.7
```

### 基本使用

```bash
# 生成目录索引
python -m config.catalog

# 生成文件页面
python -m page.gen_page

# 生成完整目录
python -m toc.full_toc

# 生成搜索索引
python -m file.gen_search_index

# 完整构建（GitHub Actions 调用）
python -m workflows.build_documents
```

## 配置文件

### config.yml 格式

每个内容目录需要包含 `config.yml`:

```yaml
name: '目录名称'
description: '目录描述'
curator: '维护者'
source: '来源URL'
tags:
  - 标签1
  - 标签2
license: '许可证'
files:
  - name: '文件显示名'
    filename: 'file.pdf'
    type: 'document'
    format: 'pdf'
    size: 1024
    md5: 'abc123...'
    page: 'file_page.md'
subdirs:
  - 子目录1
  - 子目录2
```

## 工作流程

### 内容更新流程

```
1. 新文件加入目录
        ↓
2. file/add_config.py 提取元数据
        ↓
3. ai/gen.py 生成 AI 摘要
        ↓
4. page/gen_page.py 生成展示页面
        ↓
5. config/catalog.py 更新目录索引
        ↓
6. toc/full_toc.py 生成完整目录
        ↓
7. file/gen_search_index.py 更新搜索索引
        ↓
8. 部署到 GitHub Pages
```

## 依赖

### Python 依赖

```
openai>=1.0.0
pyyaml>=6.0
requests>=2.28.0
pandas>=1.5.0
python-dotenv>=0.21.0
```

### 系统依赖

- Python 3.10+
- Git
- Git LFS (推荐，用于大文件)

## 作为 Submodule 使用

本仓库通常作为 submodule 被主仓库引用:

```bash
git submodule add https://github.com/AutoArchive/scripts.git .github/scripts
```

在主仓库的 `.github/workflows` 中调用:

```yaml
- name: Build documents
  run: |
    python -m .github.scripts.workflows.build_documents
```

## 开发指南

### 添加新模块

1. 在对应目录创建 Python 文件
2. 添加 `__init__.py` 暴露接口
3. 编写 README.md 文档
4. 更新主 README 目录说明

### 代码规范

- 使用类型注解
- 添加 docstring
- 处理异常错误
- 支持命令行参数

## 许可证

MIT License

## 维护者

- AutoArchive Team
- 跨性别数字图书馆项目

## 相关项目

- [project-polymorph/trans-digital-cn](https://github.com/project-polymorph/trans-digital-cn) - 主档案库
- [project-polymorph/platform-home](https://github.com/project-polymorph/platform-home) - 平台主页
