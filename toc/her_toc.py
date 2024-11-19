#! /usr/bin/env python3
import os
import yaml
from pathlib import Path
import subprocess  # Ensure subprocess is imported
import re
import requests  # Add this import at the top
import json

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
    
    # Map of special numerals to regular numbers
    numeral_map = {
        '①': '1', '②': '2', '③': '3', '④': '4', '⑤': '5',
        '⑥': '6', '⑦': '7', '⑧': '8', '⑨': '9', '⑩': '10'
    }
    
    def convert(text):
        # Convert special numerals if present
        if text in numeral_map:
            return int(numeral_map[text])
        return int(text) if text.isdigit() else text.lower()
    
    # Split on both regular numbers and special numerals
    pattern = '([0-9]+|[①②③④⑤⑥⑦⑧⑨⑩])'
    return [convert(c) for c in re.split(pattern, s)]

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

def load_ignore_patterns():
    """
    Load ignore patterns from digital.yml and compile them into regexes.
    """
    ignore_regexes = []
    digital_yml_path = 'digital.yml'
    if os.path.exists(digital_yml_path):
        with open(digital_yml_path, 'r', encoding='utf-8') as f:
            digital_config = yaml.safe_load(f)
            ignore_patterns = digital_config.get('ignore', [])
            ignore_regexes = [re.compile(pattern) for pattern in ignore_patterns]
    return ignore_regexes

def is_ignored(path: str, ignore_regexes) -> bool:
    """
    Check if a path is ignored by git or matches any ignore pattern.
    """
    if path == '.':
        return False

    normalized_path = os.path.normpath(path)

    # Check if any ignore regex matches the path
    for regex in ignore_regexes:
        if regex.search(normalized_path):
            print(f"Ignore: {path} (matched pattern: {regex.pattern})")
            return True

    # Check if path is git-ignored
    try:
        result = subprocess.run(
            ['git', 'check-ignore', '-q', path],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except subprocess.SubprocessError:
        return False

def load_independence_entries():
    """Load independence entries from digital.yml."""
    digital_yml_path = 'digital.yml'
    if os.path.exists(digital_yml_path):
        with open(digital_yml_path, 'r', encoding='utf-8') as f:
            digital_config = yaml.safe_load(f)
            return digital_config.get('independence', [])
    return []

def read_file_content(path):
    """Read file content from local path or remote URL."""
    if path.startswith(('http://', 'https://')):
        try:
            response = requests.get(path)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Warning: Failed to fetch remote content from {path}: {e}")
            return None
    else:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"Warning: File not found at {path}")
            return None

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

def process_directory(directory, ignore_regexes):
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
        process_directory(subdir_path, ignore_regexes)

def count_files_recursive(directory, ignore_regexes):
    """Count files in directory and its subdirectories using config.yml."""
    if is_ignored(directory, ignore_regexes):
        return 0
        
    config_path = os.path.join(directory, 'config.yml')
    if not os.path.exists(config_path):
        return 0
        
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    count = len(config.get('files', []))
    for subdir in config.get('subdirs', []):
        subdir_path = os.path.join(directory, subdir)
        count += count_files_recursive(subdir_path, ignore_regexes)
    
    # Add counts from independence entries if in root directory
    if directory == '.':
        for entry in load_independence_entries():
            path = entry.get('path', '')
            if path:
                content = read_file_content(path)
                if content:
                    match = re.search(r'总计\s+(\d+)\s+篇内容', content)
                    if match:
                        count += int(match.group(1))
    
    return count

def update_project_readme():
    """Update README files throughout the project based on config.yml files."""
    ignore_regexes = load_ignore_patterns()
    process_directory('.', ignore_regexes)
    print("Table of contents generated successfully!")

if __name__ == "__main__":
    update_project_readme()
