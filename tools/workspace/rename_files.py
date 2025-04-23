#!/usr/bin/env python3
import os
import re
import argparse
from pathlib import Path

def rename_files(directory, patterns=None, dry_run=False):
    """
    Rename files in the given directory by removing specified patterns from filenames.
    
    Args:
        directory (str): Path to the directory to process
        patterns (list): List of patterns to remove from filenames
        dry_run (bool): If True, only print what would be done without making changes
    """
    if patterns is None:
        patterns = [
            'soushu2025_com@', 
            '搜书吧', 
            '_Unicode', 
            r'\(1\)', r'\(2\)', r'\(3\)',
            'zh_Ysgyb_',
            r'NovelSeries_\d+_Chapter_[\d~]+_'
        ]
    
    directory = Path(directory)
    if not directory.exists() or not directory.is_dir():
        print(f"Error: {directory} is not a valid directory")
        return
    
    renamed_count = 0
    unchanged_count = 0
    
    for root, _, files in os.walk(directory):
        for filename in files:
            old_path = os.path.join(root, filename)
            
            # Skip hidden files (starting with .)
            if filename.startswith('.'):
                continue
                
            # Create a new filename by removing all patterns
            new_filename = filename
            for pattern in patterns:
                new_filename = re.sub(pattern, '', new_filename)
            
            # Handle multiple spaces (replace with single space)
            new_filename = re.sub(r'\s+', ' ', new_filename)
            
            # Trim leading/trailing spaces
            new_filename = new_filename.strip()
            
            # If filename didn't change, skip
            if new_filename == filename:
                unchanged_count += 1
                continue
            
            # Check for empty filename
            if not new_filename:
                print(f"Warning: {old_path} would have empty filename after processing. Skipping.")
                continue
                
            # If filename has no extension but original did, preserve extension
            if '.' in filename and '.' not in new_filename:
                extension = os.path.splitext(filename)[1]
                new_filename += extension
            
            new_path = os.path.join(root, new_filename)
            
            # Check for duplicate filename
            if os.path.exists(new_path) and old_path != new_path:
                print(f"Warning: Cannot rename {old_path} to {new_path} - destination already exists.")
                continue
            
            if dry_run:
                print(f"Would rename: {old_path} -> {new_path}")
            else:
                try:
                    os.rename(old_path, new_path)
                    print(f"Renamed: {old_path} -> {new_path}")
                    renamed_count += 1
                except Exception as e:
                    print(f"Error renaming {old_path}: {e}")
    
    print(f"\nSummary:")
    print(f"  Files renamed: {renamed_count}")
    print(f"  Files unchanged: {unchanged_count}")

def main():
    parser = argparse.ArgumentParser(description='Rename files by removing specific patterns from filenames')
    parser.add_argument('--directory', help='Directory to process', default='workspace')
    parser.add_argument('--patterns', nargs='+', help='Additional patterns to remove')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    
    args = parser.parse_args()
    
    # Default patterns to remove
    patterns = [
        'soushu2025_com@', 
        '搜书吧', 
        '_Unicode', 
        r'\(1\)', r'\(2\)', r'\(3\)',
        'zh_Ysgyb_',
        r'NovelSeries_\d+_Chapter_[\d~]+_'
    ]
    
    # Add user-specified patterns if provided
    if args.patterns:
        patterns.extend(args.patterns)
    
    rename_files(args.directory, patterns, args.dry_run)

if __name__ == "__main__":
    main() 
