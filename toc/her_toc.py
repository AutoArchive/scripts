#!/usr/bin/env python3
import os
import yaml
from pathlib import Path
import subprocess
import re
import requests
import json
import argparse
from utils import *

def generate_file_entry(file_info, directory='.'):
    """Generate markdown entry for a file with metadata."""
    name = file_info.get('name', 'Unknown') or 'Unknown'
    filename = file_info.get('filename', 'Unknown') or 'Unknown'
    file_type = file_info.get('type', 'Unknown') or 'Unknown'
    
    page_link = file_info.get('page', filename) if file_type != 'image' else filename
    entry = ""
    
    if file_type == 'image':
        entry = f"\n![{name}]({filename})\n"
    else:
        entry = f"\n\n[{name}]({page_link})"
        
        # Extract metadata if page exists
        if page := file_info.get('page'):
            page_path = os.path.join(directory, page)
            if os.path.exists(page_path):
                year, archived_date, description = extract_metadata_from_markdown(page_path)
                if description:
                    entry += f"<details><summary>查看摘要</summary>\n\n{description}\n</details>\n\n"
                file_info['year'] = year or 'Unknown'
                file_info['archived_date'] = archived_date or '9999-12-31'
                
    return entry

def generate_categorized_file_toc(files, directory='.'):
    """Generate TOC for files, categorized by type and year."""
    categories = {
        'document': {}, 'image': {}, 'video': {},
        'audio': {}, 'webpage': {}, 'other': {}
    }
    
    # Sort and categorize
    for file_info in sorted(files, key=lambda x: natural_sort_key(x['name'])):
        file_type = file_info['type']
        entry = generate_file_entry(file_info, directory, include_wordcloud)
        year = file_info.get('year', '0000') if file_info.get('year') != 'Unknown' else '0000'
        
        if year not in categories[file_type]:
            categories[file_type][year] = []
            
        archived_date = file_info.get('archived_date', '9999-12-31')
        categories[file_type][year].append((entry, archived_date))
    
    # Generate TOC
    toc = []
    type_names = {
        'document': '📄 文档', 'image': '🖼️ 图片',
        'video': '🎬 视频', 'audio': '🎵 音频',
        'webpage': '🌐 网页', 'other': '📎 其他'
    }
    
    # 改进排序逻辑
    def sort_key(entry_tuple):
        entry, date = entry_tuple
        if date is None:
            return '9999-12-31'
        return date
    
    for file_type, years in categories.items():
        if years:
            toc.append(f"\n### {type_names[file_type]}\n")
            for year in sorted(years.keys(), reverse=True):
                if years[year]:
                    display_year = '时间未知，按收录顺序排列' if year == '0000' else year
                    toc.append(f"\n#### {display_year}\n")
                    
                    # 使用新的排序逻辑
                    sorted_entries = sorted(years[year], key=sort_key)
                    toc.extend(entry for entry, _ in sorted_entries)
    
    return "\n".join(toc)

def process_independence_entries(ignore_regexes):
    """Process independence entries from independence_repo.json."""
    entries = []
    json_path = 'independence_repo.json'
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            independence_data = json.loads(f.read())
            
        for entry in independence_data:
            name = entry.get('name', '')
            url = entry.get('url', '')
            size = entry.get('size', 0)
            
            if name and url and size:
                entries.append(f"- [{name}: {url}]({url}) ({size} 篇内容)")
            else:
                print(f"Warning: Invalid entry data in independence_repo.json")
                
        return entries
    except FileNotFoundError:
        print(f"Warning: independence_repo.json not found")
        return []
    except json.JSONDecodeError:
        print(f"Warning: Failed to parse independence_repo.json")
        return []

def process_directory(directory, ignore_regexes, include_wordcloud=False):
    """Process a directory to generate README.md based on config.yml."""
    if is_ignored(directory, ignore_regexes):
        print(f"Skipping ignored directory: {directory}")
        return

    config_path = os.path.join(directory, 'config.yml')
    if not os.path.exists(config_path):
        print(f"Warning: No config.yml found in {directory}")
        return
    
    # Read config
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Generate TOC content
    toc_content = []
    
    # Add description if available
    if 'description' in config:
        toc_content.append(f"{config['description']}\n")
        
    # Add tags if available
    if 'tags' in config and config['tags']:
        toc_content.append("\n标签: " + ", ".join([f"`{tag}`" for tag in config['tags']]) + "\n")

    # Add one line total count
    total_count = count_files_recursive(directory, ignore_regexes)
    toc_content.append(f"\n总计 {total_count} 篇内容\n\n")

    # Add subdirectories section
    if config.get('subdirs'):
        toc_content.append("### 📁 子目录\n")
        for subdir in sorted(config['subdirs']):
            subdir_path = os.path.join(directory, subdir)
            if is_ignored(subdir_path, ignore_regexes):
                continue
            file_count = count_files_recursive(subdir_path, ignore_regexes)
            toc_content.append(f"- [{subdir}]({subdir}) ({file_count} 篇内容)")
        toc_content.append("")

    # Process independence entries (replacing .conf files)
    if directory == '.':  # Only process independence entries in root directory
        independence_entries = process_independence_entries(ignore_regexes)
        if independence_entries:
            toc_content.append("### 📚 独立档案库与网站\n")
            toc_content.extend(independence_entries)
            toc_content.append("")

    # Add files section
    if config.get('files'):
        files_toc = generate_categorized_file_toc(config['files'], directory, include_wordcloud)
        if files_toc:
            toc_content.append(files_toc)
    
    # Add wordcloud if enabled and exists
    if include_wordcloud:
        if os.path.exists(wordcloud_path):
            toc_content.append(f'## 摘要词云图\n\n<iframe src="../abstracts_wordcloud.html" width="100%" height="400px" frameborder="0"></iframe>\n')
    
    # Add auto-generated note
    toc_content.append("\n> 本内容为自动生成，请修改 .github/ 目录下的对应脚本或者模板\n")
    
    toc = "\n".join(toc_content)
    
    exclude_marker = """---
search:
  exclude: true
---


"""

    # Generate README content
    template_path = get_template_path(directory)
    if template_path:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        updated_content = content.replace('{{TABLE_OF_CONTENTS}}', toc)
    else:
        dir_name = config.get('name', os.path.basename(directory))
        updated_content = exclude_marker + f"# {dir_name}\n\n{toc}"
    
    # Write README.md
    readme_path = os.path.join(directory, 'README.md')
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    # Process subdirectories
    for subdir in config.get('subdirs', []):
        subdir_path = os.path.join(directory, subdir)
        process_directory(subdir_path, ignore_regexes, include_wordcloud)

def update_project_readme(include_wordcloud=False):
    """Update README files throughout the project based on config.yml files."""
    ignore_regexes = load_ignore_patterns()
    process_directory('.', ignore_regexes, include_wordcloud)
    print("Table of contents generated successfully!")

def main():
    parser = argparse.ArgumentParser(description='Generate table of contents for the project')
    parser.add_argument('--wordcloud', action='store_true', help='Include wordcloud visualizations in the output')
    args = parser.parse_args()
    
    update_project_readme(include_wordcloud=args.wordcloud)

if __name__ == "__main__":
    main()
