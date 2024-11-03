import os
import yaml
import sys
import argparse
from pathlib import Path

def find_md5_in_config(config_path):
    """
    Extract MD5 values from a config file
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
                    md5_info[file_info['filename']] = {
                        'name': file_info['filename'],
                        'path': str(config_dir / file_info['filename']),
                        'md5': file_info['md5']
                    }
        return md5_info
    except Exception as e:
        print(f"Error reading {config_path}: {e}")
        return {}

def find_config_files(root_dir, max_depth=2):
    """
    Recursively find all config.yml files and extract MD5 information
    """
    md5_catalog = {}
    md5_to_files = {}  # New dict to track MD5 duplicates
    root_level = root_dir.rstrip('/').count('/')
    
    for root, dirs, files in os.walk(root_dir):
        # Skip docs directory
        if 'docs' in dirs:
            dirs.remove('docs')
            
        # Check current depth
        current_depth = root.rstrip('/').count('/') - root_level
        if current_depth > max_depth:
            dirs.clear()
            continue
            
        if 'config.yml' in files:
            config_path = os.path.join(root, 'config.yml')
            print(f"Reading {config_path}")
            md5_info = find_md5_in_config(config_path)
            
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
    Generate md5.yml file with file names, paths and MD5 values
    """
    try:
        # Sort entries for consistent output
        sorted_catalog = dict(sorted(md5_catalog.items()))
        
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(sorted_catalog, f, allow_unicode=True, sort_keys=False)
    except Exception as e:
        print(f"Error generating MD5 catalog file: {e}")
        sys.exit(1)

def main():
    try:
        parser = argparse.ArgumentParser(description='Generate catalog of MD5 values from config files')
        parser.add_argument('--max-depth', type=int, default=2,
                          help='Maximum directory depth to search (default: 2)')
        parser.add_argument('--fail-on-duplicates', action='store_true',
                          help='Exit with error if duplicate MD5 hashes are found')
        args = parser.parse_args()

        root_dir = "./"
        output_file = os.path.join(root_dir, '.github', 'md5.yml')
        
        # Find all config files and extract MD5 information
        md5_catalog = find_config_files(root_dir, args.max_depth)
        
        # Check for duplicates before generating catalog
        md5_counts = {}
        for info in md5_catalog.values():
            md5_counts[info['md5']] = md5_counts.get(info['md5'], 0) + 1
            
        has_duplicates = any(count > 1 for count in md5_counts.values())
        if has_duplicates and args.fail_on_duplicates:
            print("Error: Duplicate MD5 hashes found. Exiting.")
            sys.exit(1)
        
        # Generate the catalog file
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        generate_md5_catalog(md5_catalog, output_file)
        
        print(f"MD5 catalog generated successfully at {output_file}")
        print(f"Found {len(md5_catalog)} files with MD5 values")
    except Exception as e:
        print(f"Error in main execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
