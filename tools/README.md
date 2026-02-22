# 工具模块

Miscellaneous tools and utilities for archive maintenance.

## 目录结构

```
tools/
├── __init__.py
├── analysis_search_index.py     # 搜索索引分析
├── ci-sample/
│   └── publish.yml              # CI 发布示例
├── clean_markdown.py            # Markdown 清理
├── convert_doc.py               # 文档转换
├── epub2txt.py                  # EPUB 转文本
├── merge_files.py               # 文件合并
├── movefile_for_size.py         # 按大小移动文件
├── moveoutdir.py                # 移出目录
├── publish.py                   # 发布工具
├── recover_deleted_files.py     # 恢复删除文件
├── split_pdf.py                 # PDF 分割
└── workspace/                   # 工作空间工具
    ├── extract_visited_links.py
    ├── md5_check_global.py
    ├── md5_check.py
    ├── name_check_global.py
    ├── organize_files.py
    ├── rename_files.py
    ├── seperate_classify.py
    ├── workspace_classify.py
    ├── workspace_merge.py
    └── workspace_rename.py
```

## 核心工具

### 1. clean_markdown.py

清理和规范化 Markdown 文件。

**功能:**
- 修复格式问题
- 统一标题层级
- 清理多余空行
- 规范化链接

### 2. convert_doc.py

文档格式转换。

**支持转换:**
- DOC/DOCX → Markdown
- PDF → Markdown (提取文本)
- EPUB → Markdown

### 3. epub2txt.py

EPUB 电子书转纯文本。

### 4. split_pdf.py

PDF 文件分割工具。

**使用场景:**
- 分割大 PDF 便于阅读
- 提取特定页面

### 5. merge_files.py

合并多个文件为一个。

### 6. publish.py

发布工具，将内容推送到各个平台。

### 7. analysis_search_index.py

分析搜索索引的使用情况。

**功能:**
- 统计热门搜索
- 分析未命中查询
- 优化建议

## 工作空间工具 (workspace/)

用于本地文件整理和预处理。

### md5_check.py / md5_check_global.py

MD5 校验工具。
- 本地: 检查单个目录
- 全局: 检查所有仓库

### organize_files.py

自动整理文件到正确位置。

### rename_files.py / workspace_rename.py

批量重命名文件。

### workspace_classify.py / seperate_classify.py

文件自动分类。

### workspace_merge.py

工作空间合并工具。

### extract_visited_links.py

提取已访问的链接列表。

### name_check_global.py

全局文件名规范检查。

## CI 示例

`ci-sample/publish.yml` 提供了 GitHub Actions 工作流示例。

## 使用示例

```bash
# 清理 Markdown
python tools/clean_markdown.py file.md

# 转换文档
python tools/convert_doc.py input.docx output.md

# 检查 MD5
python tools/workspace/md5_check.py

# 整理文件
python tools/workspace/organize_files.py
```

## 依赖

各工具依赖不同，详见各自文件头部导入。
常用依赖:
- pyyaml
- requests
- beautifulsoup4 (HTML处理)
- PyPDF2 (PDF处理)
- python-docx (DOCX处理)
- ebooklib (EPUB处理)
