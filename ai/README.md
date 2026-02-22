# AI 处理模块

AI-powered content processing utilities for document archives.

## 目录结构

```
ai/
├── __init__.py
├── gen.py              # 主要内容生成器
├── gen_struct.py       # 结构生成工具
└── archive/            # 档案元数据生成
    ├── __init__.py
    ├── gen_dir_meta.py    # 目录元数据生成
    ├── gen_file_meta.py   # 文件元数据生成
    ├── ignore.py          # 忽略规则处理
    └── utils.py           # 工具函数
```

## 核心功能

### 1. gen.py - AI 内容生成器

使用 OpenAI API 对文本内容进行清理和优化。

**环境变量:**
- `OPENAI_API_KEY` - OpenAI API 密钥
- `OPENAI_MODEL_NAME` - 模型名称 (默认: gpt-4o-mini)
- `OPENAI_TEMPERATURE` - 温度参数 (默认: 0.7)

**使用方法:**
```bash
python ai/gen.py input.txt output.txt
```

**功能:**
- 读取输入文件内容
- 调用 OpenAI API 进行内容清理/优化
- 将结果写入输出文件

### 2. gen_struct.py

生成文档结构信息。

### 3. archive/ - 档案元数据模块

#### gen_dir_meta.py
为目录生成 AI 摘要和元数据。

#### gen_file_meta.py
为单个文件生成 AI 摘要和元数据。

#### ignore.py
处理需要忽略的文件规则。

## 工作流程

```
原始文档
    ↓
[gen.py] AI 清理/优化
    ↓
[archive/gen_file_meta.py] 生成文件元数据
    ↓
[archive/gen_dir_meta.py] 生成目录摘要
    ↓
更新 config.yml
```

## 依赖

- openai
- python-dotenv
- pyyaml

## 注意事项

- 需要设置 OPENAI_API_KEY 环境变量
- 大文件建议分批处理
- API 调用有速率限制
