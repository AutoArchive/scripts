# 文件处理模块

File processing utilities for archive management.

## 目录结构

```
file/
├── __init__.py
├── add_config_from_page.py    # 从页面提取配置
├── add_config.py              # 添加文件到配置
├── encoding/                  # 编码处理
│   ├── encoding.py
│   ├── encoding_simple.py
│   └── fix_encoding.sh
├── gen_search_index.py        # 生成搜索索引
├── ignore.py                  # 文件忽略规则
├── notice/                    # 通知处理
│   ├── add_notice_txt.py
│   └── notice.py
├── rename.py                  # 文件重命名
└── translate/                 # 翻译工具
    └── translate.py
```

## 核心功能

### 1. add_config.py / add_config_from_page.py

将新文件添加到目录的 `config.yml` 中。

**功能:**
- 扫描目录中的新文件
- 自动提取文件元数据（大小、MD5、类型）
- 更新 config.yml

**使用方法:**
```bash
python -m file.add_config
```

### 2. encoding/ - 编码处理

处理各种文本编码问题。

#### encoding.py / encoding_simple.py
自动检测和转换文件编码。

#### fix_encoding.sh
批量修复编码的 shell 脚本。

**使用方法:**
```bash
bash file/encoding/fix_encoding.sh
```

### 3. gen_search_index.py

生成全站搜索索引。

**功能:**
- 遍历所有 config.yml
- 提取文件元数据和内容摘要
- 生成搜索索引文件

**输出:** 搜索索引 JSON

### 4. ignore.py

管理需要忽略的文件列表。

**默认忽略:**
- 临时文件
- 系统文件
- 已处理文件

### 5. notice/ - 通知系统

#### notice.py
发送处理通知。

#### add_notice_txt.py
添加通知文本到文件。

### 6. rename.py

批量重命名文件，统一命名规范。

### 7. translate/translate.py

文档翻译工具。

**功能:**
- 调用翻译 API
- 保持格式不变
- 生成双语对照

## 文件类型识别

| 扩展名 | 类型 | 处理方式 |
|--------|------|----------|
| .pdf | document | 生成页面 |
| .md | markdown | 直接处理 |
| .txt | text | 编码转换 |
| .epub | ebook | 转换处理 |
| .doc/.docx | document | 转换处理 |

## 工作流程

```
新文件加入
    ↓
[add_config.py] 提取元数据
    ↓
[encoding/*] 编码检查/修复
    ↓
更新 config.yml
    ↓
[gen_search_index.py] 更新搜索索引
    ↓
[notice/*] 发送通知
```

## 依赖

- pyyaml
- chardet (编码检测)
- requests (翻译 API)
