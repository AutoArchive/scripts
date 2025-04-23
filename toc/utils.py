import re
import os
import yaml
import json
import requests
import subprocess
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
    numeral_map = {
        '①': '1', '②': '2', '③': '3', '④': '4', '⑤': '5',
        '⑥': '6', '⑦': '7', '⑧': '8', '⑨': '9', '⑩': '10'
    }
    
    def convert(text):
        if text in numeral_map:
            return int(numeral_map[text])
        return int(text) if text.isdigit() else text.lower()
    
    pattern = '([0-9]+|[①②③④⑤⑥⑦⑧⑨⑩])'
    return [convert(c) for c in re.split(pattern, s)]


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


def extract_metadata_from_markdown(file_path):
    """Extract year, archived_date and description from markdown file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Extract description from abstract
        desc_match = re.search(
            r'<!-- tcd_abstract -->\n(.*?)\n<!-- tcd_abstract_end -->',
            content, re.DOTALL)
        description = desc_match.group(1).strip() if desc_match else None
        
        # Extract year from date in metadata table
        date_match = re.search(r'\|\s*Date\s*\|\s*(\d{4})[^|]*\|', content)
        year = date_match.group(1) if date_match else None

        # Extract archived date from metadata table
        archived_match = re.search(r'\|\s*Archived Date\s*\|\s*([^|]+)\|', content)
        archived_date = archived_match.group(1).strip() if archived_match else '0000-01-01'

        return year, archived_date, description
    except:
        return None, '0000-01-01', None
