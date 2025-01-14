import os
import re
import jieba
from collections import Counter
from pyecharts import options as opts
from pyecharts.charts import WordCloud
import yaml

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
        # 尝试从文件加载停用词
        stopwords_file = os.path.join(os.path.dirname(__file__), 'chinese_stopwords.txt')
        if os.path.exists(stopwords_file):
            with open(stopwords_file, 'r', encoding='utf-8') as f:
                stopwords = set([line.strip() for line in f.readlines()])
            return stopwords
    except Exception as e:
        print(f"Warning: Could not load stopwords file, using default stopwords. Error: {e}")
    
    return default_stopwords

def generate_wordcloud(text, output_path):
    """生成词云HTML文件"""
    # 分词
    words = jieba.cut(text)
    # 去除停用词
    stopwords = get_stopwords()
    words = [word for word in words if word not in stopwords and len(word) > 1]
    
    # 统计词频
    word_freq = Counter(words)
    words_list = [(word, freq) for word, freq in word_freq.most_common(100)]
    
    # 创建词云图
    c = (
        WordCloud()
        .add("", words_list, word_size_range=[20, 100])
        .set_global_opts(title_opts=opts.TitleOpts(title="摘要词云图"))
    )
    
    # 保存为HTML文件
    c.render(output_path)

def collect_abstracts(dir_path):
    """递归收集指定目录及其子目录中的所有摘要"""
    abstracts = []
    
    for root, dirs, files in os.walk(dir_path):
        if 'config.yml' in files:
            # 处理当前目录下的md文件
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            abstract = extract_abstract(content)
                            if abstract:
                                # add file name to abstract
                                abstract = abstract + " " + file
                                abstracts.append(abstract)
                    except Exception as e:
                        print(f"Error processing {file_path}: {e}")
    
    return abstracts

def process_directory(base_path):
    """处理目录及其子目录"""
    for root, dirs, files in os.walk(base_path):
        if 'config.yml' in files:
            print(f"Processing directory: {root}")
            # 收集当前目录及其子目录中的所有摘要
            abstracts = collect_abstracts(root)
            
            # 如果找到了摘要，生成词云
            if abstracts:
                combined_text = ' '.join(abstracts)
                output_path = os.path.join(root, 'abstracts_wordcloud.html')
                generate_wordcloud(combined_text, output_path)
                print(f"Generated wordcloud at: {output_path}")
            else:
                print(f"No abstracts found in {root} or its subdirectories")
if __name__ == "__main__":
    # 获取当前脚本所在目录
    process_directory("./")
