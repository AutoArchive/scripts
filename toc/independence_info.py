#! /usr/bin/env python3
import os
import yaml
import json
import re
import requests
from pathlib import Path

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

def load_independence_entries():
    """Load independence entries from digital.yml."""
    digital_yml_path = 'digital.yml'
    if os.path.exists(digital_yml_path):
        with open(digital_yml_path, 'r', encoding='utf-8') as f:
            digital_config = yaml.safe_load(f)
            return digital_config.get('independence', [])
    return []

def process_independence_to_json():
    """Process independence entries and generate JSON files for each entry."""
    entries = load_independence_entries()
    output_dir = Path('.github/data/independence')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    all_entries = []
    
    for entry in entries:
        path = entry.get('path', '')
        url = entry.get('url', '')
        name = entry.get('name', '')
        
        if not all([url, path, name]):
            print(f"Warning: Missing required fields for entry {name}")
            continue

        content = read_file_content(path)
        if content:
            match = re.search(r'总计\s+(\d+)\s+篇内容', content)
            size = int(match.group(1)) if match else 0
            
            entry_data = {
                'name': name,
                'url': url,
                'path': path,
                'size': size,
                'last_updated': None  # 可以在这里添加更新时间
            }
            
            # 为每个条目生成单独的 JSON 文件
            # safe_name = re.sub(r'[^\w\-_]', '_', name)
            # entry_file = output_dir / f'{safe_name}.json'
            # with open(entry_file, 'w', encoding='utf-8') as f:
            #     json.dump(entry_data, f, ensure_ascii=False, indent=2)
            
            all_entries.append(entry_data)
            print(f"Generated JSON for {name}")
    
    # 生成包含所有条目的总文件
    with open('independence_repo.json', 'w', encoding='utf-8') as f:
        json.dump(all_entries, f, ensure_ascii=False, indent=2)
    
    print(f"Generated JSON files in {output_dir}")

if __name__ == "__main__":
    process_independence_to_json()
