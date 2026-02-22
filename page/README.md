# 页面生成模块

Page generation and website building utilities.

## 目录结构

```
page/
├── __init__.py
├── add_search_exclude.py    # 添加搜索排除标记
├── embed_text.py            # 文本嵌入处理
├── gen_page.py              # 页面生成器
└── gen_wordcloud.py         # 词云生成
```

## 核心功能

### 1. gen_page.py - 页面生成器

核心页面生成模块，为每个文件生成 Markdown 展示页面。

**功能:**
- 读取 `config.yml` 中的文件信息
- 使用模板生成展示页面
- 支持多种文件类型

**模板:**
- `.github/templates/page.md.template` - 普通文件页面
- `.github/templates/additional.md.template` - Markdown 文件附加信息

**生成的页面包含:**
- 文件基本信息（名称、类型、大小、MD5）
- 下载链接
- AI 生成的摘要
- 元数据表格

**使用方法:**
```bash
python -m page.gen_page
```

**工作流程:**
```
config.yml
    ↓
读取文件列表
    ↓
检查页面是否已存在
    ↓
渲染模板
    ↓
生成 {filename}_page.md
    ↓
更新 config.yml 中的 page 字段
```

### 2. add_search_exclude.py

为特定页面添加搜索排除标记，使其不出现在搜索结果中。

**使用场景:**
- 临时文件
- 重复内容
- 测试页面

### 3. embed_text.py

处理文本嵌入，用于 AI 摘要和搜索优化。

**功能:**
- 提取文档关键内容
- 生成向量嵌入
- 用于相似度搜索

### 4. gen_wordcloud.py

生成词云可视化。

**功能:**
- 分析目录内所有文档
- 提取关键词
- 生成词云图片

**输出:** `abstracts_wordcloud.png`

## 页面模板变量

```
{name} - 文件名称
{filename} - 文件名
{type} - 文件类型
{format} - 文件格式
{size} - 文件大小
{md5} - MD5 校验值
{archived} - 归档日期
{description} - 描述
{tags} - 标签
{date} - 日期
{region} - 地区
{link} - 原始链接
{author} - 作者
```

## 页面结构示例

生成的页面 (`{name}_page.md`):

```markdown
# {name}

<!-- tcd_download_link -->
下载: <a href="../{filename}" download>{filename}</a>
<!-- tcd_download_link_end -->

## 摘要

<!-- tcd_abstract -->
AI 生成的摘要内容...
<!-- tcd_abstract_end -->

## 其他信息 [Processed Page Metadata]

| Attribute | Value |
|-----------|-------|
| 文件名 | {filename} |
| 文件类型 | {type} |
| 文件大小 | {size} |
| MD5 | {md5} |
| 归档日期 | {archived} |
```

## 依赖

- pyyaml
- jieba (中文分词，用于词云)
- wordcloud
- matplotlib
