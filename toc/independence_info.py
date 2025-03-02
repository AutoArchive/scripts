#! /usr/bin/env python3
import os
import yaml
import json
import re
import requests
from pathlib import Path
from typing import List, Dict, Optional

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
    return None  # Remove local file reading since we only want remote files

def load_independence_entries():
    """Load independence entries from digital.yml."""
    digital_yml_path = 'digital.yml'
    if os.path.exists(digital_yml_path):
        with open(digital_yml_path, 'r', encoding='utf-8') as f:
            digital_config = yaml.safe_load(f)
            return digital_config.get('independence', [])
    return []

def get_search_index_count(base_url):
    """Get entry count from search_index.yml at the given base URL and save locally."""
    search_index_url = f"{base_url.rstrip('/')}/search_index.yml"
    content = read_file_content(search_index_url)
    print(f"Search index content: {search_index_url}")
    if content:
        try:
            # Create directory if it doesn't exist
            save_dir = Path('.search_index')
            save_dir.mkdir(exist_ok=True)
            
            # Extract domain name from URL
            domain = re.search(r'https?://([^/]+)', base_url).group(1)
            save_path = save_dir / f"{domain}.yml"
            
            # Save the content
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            index_data = yaml.safe_load(content)
            return len(index_data.keys())
        except yaml.YAMLError as e:
            print(f"Warning: Failed to parse search_index.yml from {search_index_url}: {e}")
    return 0

def process_independence_to_json():
    """Process independence entries and generate JSON files for each entry."""
    entries = load_independence_entries()
    output_dir = Path('.github/data/independence')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    all_entries = []
    
    for entry in entries:
        url = entry.get('url', '')
        name = entry.get('name', '')
        
        if not all([url, name]):
            print(f"Warning: Missing required fields for entry {name}")
            continue

        # Get count from search_index.yml instead of local file
        size = get_search_index_count(url)
            
        # Start with all fields from the original entry
        entry_data = entry.copy()
        # Add or update specific fields
        entry_data.update({
            'size': size,
            'last_updated': None
        })
            
        all_entries.append(entry_data)
        print(f"Generated JSON for {name} with {size} entries")
    
    # Generate the combined JSON file
    with open('independence_repo.json', 'w', encoding='utf-8') as f:
        json.dump(all_entries, f, ensure_ascii=False, indent=2)
    
    print(f"Generated JSON files in {output_dir}")
    return all_entries

def independence_info_main(base_dir: str = '.', output_file: Optional[str] = None) -> List[Dict]:
    """
    Main function to process independence information.
    
    Args:
        base_dir (str): Base directory to process from
        output_file (Optional[str]): Path to output file. If None, uses 'independence_repo.json'
        
    Returns:
        List[Dict]: List of processed independence entries
    """
    try:
        os.chdir(base_dir)  # Change to base directory
        return process_independence_to_json()
    except Exception as e:
        print(f"Error processing independence info: {e}")
        return []

if __name__ == "__main__":
    independence_info_main()
