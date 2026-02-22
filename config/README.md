# 配置管理模块

Configuration and catalog management utilities for archive repositories.

## 目录结构

```
config/
├── __init__.py
├── catalog.py          # 目录索引生成器
├── get_md5_list.py     # MD5 校验列表生成
├── hierarchy/          # 层级结构检测
│   ├── __init__.py
│   └── detect_entry.py
├── repo/               # 仓库配置管理
│   ├── __init__.py
│   ├── add_to_config.py
│   └── keywords.py
└── visitor.py          # 访问统计处理
```

## 核心功能

### 1. catalog.py - 目录索引生成器

递归扫描目录结构，生成 `catalog.yml` 索引文件。

**功能:**
- 扫描指定深度内的所有 `config.yml` 文件
- 提取目录名称和描述
- 生成统一的目录索引

**使用方法:**
```bash
python -m config.catalog --max-depth 2
```

**输出:** `.github/catalog.yml`

**示例输出:**
```yaml
学术文献:
  name: 学术文献
  description: 此目录包含关于跨性别议题的学术文献...
文学作品:
  name: 文学作品
  description: 小说、散文等文学创作...
```

### 2. get_md5_list.py

生成文件的 MD5 校验列表，用于完整性检查。

### 3. hierarchy/detect_entry.py

自动检测目录的层级结构入口点。

### 4. repo/ - 仓库配置管理

#### add_to_config.py
将新文件添加到 `config.yml` 中。

#### keywords.py
关键词管理和提取。

### 5. visitor.py - 访问统计处理

处理 Google Analytics 访问数据。

**功能:**
- 从 data-analysis 仓库获取 GA 数据
- 归一化页面路径
- 生成访问量映射

**数据来源:**
```
https://raw.githubusercontent.com/project-polymorph/data-analysis/main/ga_visitor/google_analysis.csv
```

**使用方法:**
```python
from config.visitor import load_ga_data
path_map = load_ga_data()
# 返回: {normalized_path: views}
```

## 配置文件格式

### config.yml

每个目录下的配置文件，描述该目录的内容：

```yaml
name: '目录名称'
description: '目录描述'
curator: '维护者'
source: '来源'
tags:
  - 标签1
  - 标签2
license: '许可证'
files:
  - name: '文件名'
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

```
目录结构
    ↓
[catalog.py] 扫描 config.yml
    ↓
生成 catalog.yml 索引
    ↓
[visitor.py] 添加访问统计
    ↓
[page/gen_page.py] 生成页面
```

## 依赖

- pyyaml
- pandas (for visitor.py)
- requests
