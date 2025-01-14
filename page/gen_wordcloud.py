import os
import re
import jieba
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import yaml
import requests

def extract_abstract(md_content):
    """提取被注释包含的abstract内容"""
    pattern = r'<!-- tcd_abstract -->(.*?)<!-- tcd_abstract_end -->'
    match = re.search(pattern, md_content, re.DOTALL)
    abstract = match.group(1).strip() if match else ""
    return abstract

def get_stopwords():
    """获取停用词列表"""
    # 默认的停用词列表作为备选
    default_stopwords = set(['的', '了', '和', '是', '与', '以', '及', '等', '对', '在', '中', '或', '由', '上', '下', 
                           '而', '到', '为', '与', '则', '等', '这', '那', '你', '我', '他', '她', '它', '们', '个',
                           '之', '也', '就', '但', '还', '有', '着', '去', '又', '来', '做', '被', '将', '向', '从',
                           '此', '时', '要', '于', '已', '所', '如', '这个', '那个', '什么', '哪', '那里', '很', '啊',
                           '吗', '呢', '了', '的话', '让', '使', '给', '但是', '因为', '所以', '如果', '虽然', '这样',
                           '那样', '只', '都', '把', '可以', '这些', '那些', '没有', '看', '说', '地'])
    
    try:
        stopwords_file = os.path.join(os.path.dirname(__file__), 'chinese_stopwords.txt')
        if os.path.exists(stopwords_file):
            with open(stopwords_file, 'r', encoding='utf-8') as f:
                stopwords = set([line.strip() for line in f.readlines()])
            return stopwords
    except Exception as e:
        print(f"Warning: Could not load stopwords file, using default stopwords. Error: {e}")
    
    return default_stopwords

def generate_wordcloud(text, output_path):
    """生成词云图片文件"""
    # 分词
    words = jieba.cut(text)
    # 去除停用词
    stopwords = get_stopwords()
    words = [word for word in words if word not in stopwords and len(word) > 1]
    
    # 将分词结果组合成文本
    text = ' '.join(words)
    
    # Try different font paths
    possible_font_paths = [
        '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
        '/usr/share/fonts/wqy-microhei/wqy-microhei.ttc',
        '/usr/share/fonts/truetype/wqy-microhei/wqy-microhei.ttc',
        '/usr/share/fonts/wqy/wqy-microhei.ttc',
        'wqy-microhei.ttc',  # If font is in current directory
        'SimHei.ttf',        # Windows font
        'msyh.ttc'          # Windows font
    ]
    
    font_path = None
    for path in possible_font_paths:
        if os.path.exists(path):
            font_path = path
            break
    
    if not font_path:
        print("Warning: Could not find a suitable font. Downloading WQY-Microhei...")
        # Download the font if not found
        font_url = "https://github.com/anthonyfok/fonts-wqy-microhei/raw/master/wqy-microhei.ttc"
        response = requests.get(font_url)
        font_path = "wqy-microhei.ttc"
        with open(font_path, "wb") as f:
            f.write(response.content)
    
    # 创建词云对象
    wc = WordCloud(
        font_path=font_path,
        width=1200,
        height=800,
        background_color='white',
        max_words=100,
        max_font_size=150,
        random_state=42
    )
    
    # 生成词云
    wc.generate(text)
    
    # 保存图片
    output_path = output_path.replace('.html', '.png')
    wc.to_file(output_path)
    plt.close()

def extract_tags(md_content):
    """从 markdown 表格中提取 Tags"""
    pattern = r'\|\s*Tags\s*\|\s*([^|]+?)\s*\|'
    match = re.search(pattern, md_content)
    if match:
        tags = match.group(1).strip()
        # 将逗号分隔的标签转换为空格分隔
        return tags.replace('，', ' ').replace(',', ' ')
    return ""

def collect_abstracts(dir_path):
    """递归收集指定目录及其子目录中的所有摘要和标签"""
    abstracts = []
    
    for root, dirs, files in os.walk(dir_path):
        if 'config.yml' in files:
            # rm abstracts_wordcloud.html
            if os.path.exists(os.path.join(root, 'abstracts_wordcloud.html')):
                os.remove(os.path.join(root, 'abstracts_wordcloud.html'))
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            abstract = extract_abstract(content)
                            tags = extract_tags(content)
                            if abstract:
                                # 将标签和摘要组合在一起
                                combined_text = f"{abstract} {tags} {file}"
                                abstracts.append(combined_text)
                    except Exception as e:
                        print(f"Error processing {file_path}: {e}")
    
    return abstracts

def process_directory(base_path):
    """处理目录及其子目录"""
    for root, dirs, files in os.walk(base_path):
        if 'config.yml' in files:
            print(f"Processing directory: {root}")
            abstracts = collect_abstracts(root)
            
            if abstracts:
                combined_text = ' '.join(abstracts)
                output_path = os.path.join(root, 'abstracts_wordcloud.html')  # 保持原文件名，在generate_wordcloud中会改为.png
                generate_wordcloud(combined_text, output_path)
                print(f"Generated wordcloud at: {output_path.replace('.html', '.png')}")
            else:
                print(f"No abstracts found in {root} or its subdirectories")

if __name__ == "__main__":
    process_directory("./")
