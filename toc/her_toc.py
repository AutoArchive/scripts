#! /usr/bin/env python3
import os
import yaml
from pathlib import Path

def get_template_path(dir_path):
    """Get template path for a specific directory if it exists."""
    relative_path = os.path.relpath(dir_path, '.')
    template_path = os.path.join('.github/templates', relative_path, 'README.md.template')
    if os.path.exists(template_path):
        return template_path
    return None

def natural_sort_key(s):
    """Natural sort key function for sorting strings with numbers."""
    import re
    def convert(text):
        return int(text) if text.isdigit() else text.lower()
    return [convert(c) for c in re.split('([0-9]+)', s)]

def generate_file_entry(file_info):
    """Generate markdown entry for a file based on its type."""
    name = file_info.get('name', 'Unknown') or 'Unknown'
    filename = file_info.get('filename', 'Unknown') or 'Unknown'
    file_type = file_info.get('type', 'Unknown') or 'Unknown'
    
    # Check if a page entry exists for non-image files
    page_link = file_info.get('page', filename) if file_type != 'image' else filename
    
    if file_type == 'image':
        return f"[{name}]({filename})\n\n![{name}]({filename})\n\n"
    else:
        return f"- [{name}]({page_link})"

def generate_categorized_file_toc(files):
    """Generate TOC for files, categorized by type."""
    categorized_files = {
        'document': [],
        'image': [],
        'video': [],
        'audio': [],
        'webpage': [],
        'other': []
    }
    
    # Sort files by name using natural sort
    sorted_files = sorted(files, key=lambda x: natural_sort_key(x['name']))
    
    # Categorize files
    for file_info in sorted_files:
        file_type = file_info['type']
        entry = generate_file_entry(file_info)
        categorized_files[file_type].append(entry)
    
    # Generate TOC sections
    toc = []
    type_names = {
        'document': '📄 文档',
        'image': '🖼️ 图片',
        'video': '🎬 视频',
        'audio': '🎵 音频',
        'webpage': '🌐 网页',
        'other': '📎 其他'
    }
    
    for file_type, entries in categorized_files.items():
        if entries:  # Only add sections that have files
            toc.append(f"\n### {type_names[file_type]}\n")
            toc.extend(entries)
    
    return "\n".join(toc)

def count_files_recursive(directory):
    """Count files in directory and its subdirectories using config.yml."""
    config_path = os.path.join(directory, 'config.yml')
    if not os.path.exists(config_path):
        return 0
        
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    count = len(config.get('files', []))
    for subdir in config.get('subdirs', []):
        subdir_path = os.path.join(directory, subdir)
        count += count_files_recursive(subdir_path)
    
    return count

def process_directory(directory):
    """Process a directory to generate README.md based on config.yml."""
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
    
    # Add subdirectories section
    if config.get('subdirs'):
        toc_content.append("### 📁 子目录\n")
        for subdir in sorted(config['subdirs']):
            file_count = count_files_recursive(os.path.join(directory, subdir))
            toc_content.append(f"- [{subdir}]({subdir}) ({file_count} 篇内容)")
        toc_content.append("")  # Add empty line after subdirs section
    
    # Add files section
    if config.get('files'):
        files_toc = generate_categorized_file_toc(config['files'])
        if files_toc:
            toc_content.append(files_toc)
    
    # Add auto-generated note
    toc_content.append("\n> 本内容为自动生成，请修改 .github/ 目录下的对应脚本或者模板\n")
    
    toc = "\n".join(toc_content)
    
    # Generate README content
    template_path = get_template_path(directory)
    if template_path:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        updated_content = content.replace('{{TABLE_OF_CONTENTS}}', toc)
    else:
        dir_name = config.get('name', os.path.basename(directory))
        updated_content = f"# {dir_name}\n\n{toc}"
    
    # Write README.md
    readme_path = os.path.join(directory, 'README.md')
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    # Process subdirectories
    for subdir in config.get('subdirs', []):
        subdir_path = os.path.join(directory, subdir)
        process_directory(subdir_path)

def update_project_readme():
    """Update README files throughout the project based on config.yml files."""
    process_directory('.')
    print("Table of contents generated successfully!")

if __name__ == "__main__":
    update_project_readme()
