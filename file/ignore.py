import os
import re
import subprocess

import yaml

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
