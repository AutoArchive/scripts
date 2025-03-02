#!/usr/bin/env python3
import os
import yaml
import sys
import argparse
import subprocess  # For git check-ignore
import re  # For regex
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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

def is_ignored(path, ignore_regexes):
    """
    Check if a path matches any ignore pattern or is git-ignored.
    """
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

def find_md5_in_config(config_path, ignore_regexes):
    """
    Extract MD5 values from a config file.
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        md5_info = {}
        # Look for MD5 values in the files list
        if isinstance(config, dict) and 'files' in config:
            for file_info in config['files']:
                if 'md5' in file_info and 'filename' in file_info:
                    config_dir = Path(config_path).parent
                    file_path = str(config_dir / file_info['filename'])
                    # Check if the file is ignored
                    if not is_ignored(file_path, ignore_regexes):
                        md5_info[file_info['filename']] = {
                            'name': file_info['filename'],
                            'path': file_path,
                            'md5': file_info['md5']
                        }
                    else:
                        print(f"Ignored file in config: {file_path}")
        return md5_info
    except Exception as e:
        print(f"Error reading {config_path}: {e}")
        return {}

def find_config_files(root_dir, ignore_regexes, max_depth=2):
    """
    Recursively find all config.yml files and extract MD5 information.
    """
    md5_catalog = {}
    md5_to_files = {}
    root_level = root_dir.rstrip('/').count('/')

    for root, dirs, files in os.walk(root_dir):
        normalized_root = os.path.normpath(root)

        # Check if current directory should be ignored
        if is_ignored(normalized_root, ignore_regexes):
            dirs[:] = []  # Don't recurse into subdirectories
            continue

        # Remove ignored directories from dirs
        dirs[:] = [d for d in dirs if not is_ignored(os.path.join(root, d), ignore_regexes)]

        # Check current depth
        current_depth = normalized_root.rstrip('/').count('/') - root_level
        if current_depth > max_depth:
            dirs.clear()
            continue

        if 'config.yml' in files:
            config_path = os.path.join(root, 'config.yml')
            if is_ignored(config_path, ignore_regexes):
                continue
            print(f"Reading {config_path}")
            md5_info = find_md5_in_config(config_path, ignore_regexes)

            # Check for duplicate MD5 values
            for file_info in md5_info.values():
                md5_hash = file_info['md5']
                if md5_hash in md5_to_files:
                    print(f"\nWARNING: Duplicate MD5 hash found: {md5_hash}")
                    print(f"  File 1: {md5_to_files[md5_hash]}")
                    print(f"  File 2: {file_info['path']}\n")
                else:
                    md5_to_files[md5_hash] = file_info['path']

            md5_catalog.update(md5_info)

    return md5_catalog

def generate_md5_catalog(md5_catalog, output_file):
    """
    Generate md5.yml file with file names, paths and MD5 values.
    """
    try:
        # Sort entries for consistent output
        sorted_catalog = dict(sorted(md5_catalog.items()))

        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(sorted_catalog, f, allow_unicode=True, sort_keys=False)
    except Exception as e:
        print(f"Error generating MD5 catalog file: {e}")
        sys.exit(1)

def md5_list_main(
    base_dir: str = '.',
    max_depth: int = 2,
    output_file: Optional[str] = None,
    fail_on_duplicates: bool = False,
    remove_duplicates: bool = False
) -> Tuple[Dict, List[str]]:
    """
    Main function to generate MD5 list from config files.
    
    Args:
        base_dir (str): Base directory to start searching from
        max_depth (int): Maximum directory depth to search
        output_file (Optional[str]): Path to output MD5 list file. If None, uses '.github/md5.yml' in base_dir
        fail_on_duplicates (bool): Whether to exit with error if duplicates are found
        remove_duplicates (bool): Whether to remove duplicate files
        
    Returns:
        Tuple[Dict, List[str]]: (MD5 catalog dictionary, List of removed duplicates)
    """
    try:
        if output_file is None:
            output_file = os.path.join(base_dir, '.github', 'md5.yml')

        # Load ignore patterns and compile regexes
        ignore_regexes = load_ignore_patterns()

        # Find all config files and extract MD5 information
        md5_catalog = find_config_files(base_dir, ignore_regexes, max_depth)

        # Modified duplicate checking and removal logic
        md5_to_files = {}
        duplicates_to_remove = set()
        removed_files = []

        # First pass: collect all files with same MD5
        for filename, info in md5_catalog.items():
            md5_hash = info['md5']
            if md5_hash in md5_to_files:
                md5_to_files[md5_hash].append(filename)
                duplicates_to_remove.add(filename)
            else:
                md5_to_files[md5_hash] = [filename]

        # Remove duplicates if requested
        if remove_duplicates:
            for duplicate in duplicates_to_remove:
                # Remove the duplicate file
                os.remove(md5_catalog[duplicate]['path'])
                removed_files.append(md5_catalog[duplicate]['path'])
                
                # Check and remove associated page.md file
                file_path = md5_catalog[duplicate]['path']
                page_md_path = os.path.splitext(file_path)[0] + '_page.md'
                if os.path.exists(page_md_path):
                    os.remove(page_md_path)
                    removed_files.append(page_md_path)
                    print(f"Removed associated page.md file: {page_md_path}")
                
                del md5_catalog[duplicate]
                print(f"Removed duplicate file: {duplicate}")

        has_duplicates = len(duplicates_to_remove) > 0
        if has_duplicates and fail_on_duplicates and not remove_duplicates:
            print("Error: Duplicate MD5 hashes found. Exiting.")
            sys.exit(1)

        # Generate the catalog file
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        generate_md5_catalog(md5_catalog, output_file)

        print(f"MD5 catalog generated successfully at {output_file}")
        print(f"Found {len(md5_catalog)} files with MD5 values")
        
        return md5_catalog, removed_files
    except Exception as e:
        print(f"Error in MD5 list generation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate catalog of MD5 values from config files')
    parser.add_argument('--max-depth', type=int, default=2,
                      help='Maximum directory depth to search (default: 2)')
    parser.add_argument('--fail-on-duplicates', action='store_true',
                      help='Exit with error if duplicate MD5 hashes are found')
    parser.add_argument('--remove-duplicates', action='store_true',
                      help='Remove duplicate files (keeps the first occurrence)')
    args = parser.parse_args()
    
    md5_list_main(
        max_depth=args.max_depth,
        fail_on_duplicates=args.fail_on_duplicates,
        remove_duplicates=args.remove_duplicates
    )
