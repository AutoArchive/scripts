#!/usr/bin/env python3
import os
import yaml
import pandas as pd
import requests
from io import StringIO
from datetime import datetime
from typing import Dict, Optional

def load_ga_data():
    """Load Google Analytics data from GitHub"""
    try:
        print("Fetching GA data from GitHub...")
        url = "https://raw.githubusercontent.com/project-polymorph/data-analysis/refs/heads/main/ga_visitor/google_analysis.csv"
        response = requests.get(url)
        response.raise_for_status()
        
        # Read CSV data
        content = response.text
        lines = content.split('\n')
        print(f"Retrieved {len(lines)} lines of data")
        
        # Find the actual data start (after metadata)
        start_idx = 0
        for i, line in enumerate(lines):
            if line.startswith('Page path and screen class,Views,'):
                start_idx = i
                break
        
        print(f"Data starts at line {start_idx}")
        
        # Create DataFrame from the actual data
        data = '\n'.join(lines[start_idx:])
        df = pd.read_csv(StringIO(data))
        
        # Create a map of normalized paths to views
        path_map = {}
        for _, row in df.iterrows():
            path = row['Page path and screen class']
            if isinstance(path, str):
                clean_path = normalize_path(path)
                views = int(row['Views'])
                path_map[clean_path] = views
                # Also add index variant
                path_map[f"{clean_path}/index"] = views
        
        print(f"Processed {len(path_map)} GA entries")
            
        return path_map
    except Exception as e:
        print(f"Warning: Failed to load GA data: {e}")
        return None

def normalize_path(path):
    """Normalize path for comparison"""
    # Remove leading/trailing slashes
    path = path.strip('/')
    # Remove .md or .html extension
    if path.endswith('.md') or path.endswith('.html'):
        path = os.path.splitext(path)[0]
    # Replace backslashes with forward slashes
    path = path.replace('\\', '/')
    # remove ./ at the beginning of the path
    path = path.lstrip('./')
    return path

def update_file_entry(file_entry, views):
    """Update file entry with visitor count while preserving structure"""
    if isinstance(file_entry, dict):
        file_entry['visitors'] = views
        return file_entry
    else:
        # For string entries, preserve as string and add visitor count in comment
        return f"{file_entry}  # visitors: {views}"

def process_directory(directory, ga_map):
    """Process a directory to update config.yml files with visitor data"""
    config_path = os.path.join(directory, 'config.yml')
    if not os.path.exists(config_path):
        print(f"No config.yml found in {directory}")
        return
        
    print(f"\nProcessing directory: {directory}")
    
    # Read config file content as string to preserve formatting
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Load config
    config = yaml.safe_load(content)
    
    # Process files in config
    if 'files' in config:
        modified = False
        for i, file_entry in enumerate(config['files']):
            file_path = file_entry.get('page', '')  # Try filename if link not found
                
            if file_path:
                # Calculate full path relative to root
                rel_path = os.path.join(directory, file_path).replace(os.sep, '/')
                rel_path = rel_path.strip('/')
                
                # Normalize path for comparison
                compare_path = normalize_path(rel_path)
                print(f"  Checking path: {compare_path}")
                # print(f"  GA map: {ga_map}")
                # Look for match in GA map
                views = ga_map.get(compare_path)
                if views:
                    print(f"  Found match for {rel_path}: {views} views")
                    print(f"    Compare path: {compare_path}")
                    
                    # Update file entry with visitor count
                    config['files'][i] = update_file_entry(file_entry, views)
                    modified = True
        
        # Only write if modifications were made
        if modified:
            # Update the visitor counts in the original content
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True, sort_keys=False)
    
    # Process subdirectories
    if 'subdirs' in config:
        for subdir in config['subdirs']:
            subdir_path = os.path.join(directory, subdir)
            process_directory(subdir_path, ga_map)
    
    if modified:
        print(f"Updated {config_path}")

def visitor_main(base_dir: str = '.', ga_data_url: Optional[str] = None) -> Dict:
    """
    Main function to update visitor counts in config files.
    
    Args:
        base_dir (str): Base directory to start processing from
        ga_data_url (Optional[str]): URL to Google Analytics data. If None, uses default URL
        
    Returns:
        Dict: Google Analytics data mapping
    """
    # Load GA data
    ga_map = load_ga_data()
    if ga_map is None:
        print("Failed to load GA data")
        return {}
    
    # Start processing from root directory
    os.chdir(base_dir)  # Change to base directory
    process_directory('.', ga_map)
    
    print("\nFinished updating visitor data in config files")
    return ga_map

if __name__ == "__main__":
    visitor_main() 