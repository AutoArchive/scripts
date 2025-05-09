#!/usr/bin/env python3
import os
import subprocess
from datetime import datetime
import re

def decode_filename(filename):
    """Decode escaped unicode filename back to Chinese."""
    try:
        # Remove quotes if present
        filename = filename.strip('"')
        # Convert escaped unicode to actual unicode
        decoded = bytes(filename, 'utf-8').decode('unicode_escape').encode('latin1').decode('utf-8')
        # Ensure .md extension
        if not decoded.endswith('.md'):
            decoded += '.md'
        return decoded
    except Exception as e:
        print(f"Error decoding filename {filename}: {str(e)}")
        return filename

def create_backup_dir():
    """Create a backup directory with timestamp."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = f'backup_deleted_files_{timestamp}'
    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir

def get_tree_entries(commit_hash):
    """Get all entries from a tree object."""
    result = subprocess.run(['git', 'ls-tree', '-r', commit_hash],
                          capture_output=True, text=True)
    entries = []
    for line in result.stdout.splitlines():
        try:
            mode, type_, hash_, path = line.split(None, 3)
            entries.append((mode, type_, hash_, path))
        except ValueError:
            continue
    return entries

def sanitize_path(path):
    """Sanitize path to avoid too long filenames."""
    if len(os.path.basename(path)) > 200:  # Max filename length
        dirname = os.path.dirname(path)
        basename = os.path.basename(path)
        # Keep the first 100 and last 100 chars including extension
        basename = basename[:97] + '...' + basename[-97:]
        return os.path.join(dirname, basename)
    return path

def recover_deleted_files():
    """Recover deleted files from the last commit and move them to backup directory."""
    # Get the last commit hash
    result = subprocess.run(['git', 'rev-parse', 'HEAD~1'], 
                          capture_output=True, text=True)
    last_commit = result.stdout.strip()

    # Create backup directory
    backup_dir = create_backup_dir()
    print(f'Created backup directory: {backup_dir}')

    # Get all files from previous commit
    prev_files = {path: (mode, type_, hash_) 
                 for mode, type_, hash_, path in get_tree_entries(last_commit)}

    # Get all files from current commit
    curr_files = {path: (mode, type_, hash_) 
                 for mode, type_, hash_, path in get_tree_entries('HEAD')}

    # Find deleted files
    deleted_files = set(prev_files.keys()) - set(curr_files.keys())

    for path in deleted_files:
        try:
            mode, type_, hash_ = prev_files[path]
            if type_ == 'blob':  # Only process regular files
                # Decode and sanitize the path
                decoded_path = decode_filename(path)
                safe_path = sanitize_path(decoded_path)
                
                # Create directory structure
                backup_path = os.path.join(backup_dir, safe_path)
                os.makedirs(os.path.dirname(backup_path), exist_ok=True)

                # Get file content using git cat-file
                with open(backup_path, 'wb') as f:
                    subprocess.run(['git', 'cat-file', '-p', hash_],
                                stdout=f, check=True)
                print(f'Recovered: {decoded_path}')

        except Exception as e:
            print(f'Error processing {path}: {str(e)}')

if __name__ == '__main__':
    # Change to the git repository directory
    os.chdir('news-website')
    recover_deleted_files() 