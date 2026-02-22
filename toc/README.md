# 目录生成模块 (TOC)

Table of Contents generation and content processing utilities.

## 目录结构

```
toc/
├── __init__.py
├── content_processors.py     # 内容处理器
├── entry_generators.py       # 条目生成器
├── full_toc.py               # 完整目录生成
├── her_toc.py                # 特定格式目录
├── independence_info.py      # 独立信息处理
├── toc_formatters.py         # 目录格式化
└── utils.py                  # 工具函数
```

## 核心功能

### 1. full_toc.py - 完整目录生成

生成整个档案库的完整目录结构。

**功能:**
- 递归遍历所有目录
- 读取每个目录的 `config.yml`
- 生成层级目录索引

**输出格式:**
```markdown
# 目录

## 学术文献
- [人文社科](学术文献/人文社科/)
- [医学](学术文献/医学/)
- [法律](学术文献/法律/)

## 文学作品
- [小说](文学作品/小说/)
- [散文](文学作品/散文/)
```

### 2. entry_generators.py

生成目录条目的各种格式。

**支持格式:**
- Markdown 链接
- HTML 链接
- 纯文本列表
- JSON 结构

### 3. content_processors.py

处理目录内容，包括:
- 排序
- 过滤
- 分组
- 摘要提取

### 4. toc_formatters.py

目录格式化工具。

**支持样式:**
- 标准 Markdown
- 带图标的目录
- 带访问量的目录
- 带描述的详细目录

### 5. her_toc.py

特定格式的目录生成（可能是历史遗留或特定项目）。

### 6. independence_info.py

处理独立信息条目，用于特殊内容的目录展示。

### 7. utils.py

工具函数:
- 路径处理
- 名称规范化
- 层级计算

## 目录生成流程

```
根目录
    ↓
[full_toc.py] 递归扫描
    ↓
读取每个 config.yml
    ↓
[entry_generators.py] 生成条目
    ↓
[content_processors.py] 处理排序/过滤
    ↓
[toc_formatters.py] 格式化输出
    ↓
生成 README.md / TOC.md
```

## 使用方法

```bash
# 生成完整目录
python -m toc.full_toc

# 生成特定格式目录
python -m toc.her_toc

# 带访问量的目录
python -m toc.full_toc --with-views
```

## 与其他模块的协作

```
toc/
    ↑
config/catalog.py (提供目录结构)
    ↑
config/visitor.py (提供访问数据)
    ↑
page/gen_page.py (生成页面后更新目录)
```

## 依赖

- pyyaml
- config 模块
