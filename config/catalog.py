#!/usr/bin/env python3
import os
import yaml
from pathlib import Path
import sys
import argparse
from typing import Dict, Optional

def find_config_files(root_dir, max_depth=2):
    """
    Recursively find all config.yml files in the given directory up to max_depth
    """
    catalog = {}
    root_level = root_dir.rstrip('/').count('/')
    
    for root, dirs, files in os.walk(root_dir):
        # Skip docs directory
        if 'docs' in dirs:
            dirs.remove('docs')
            
        # Check current depth
        current_depth = root.rstrip('/').count('/') - root_level
        if current_depth > max_depth:
            dirs.clear()  # Stop going deeper
            continue
            
        if 'config.yml' in files:
            try:
                config_path = os.path.join(root, 'config.yml')
                print(f"Reading {config_path}")
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    
                # Get relative path from root directory
                rel_path = os.path.relpath(root, root_dir)
                # Create dictionary with name and description
                catalog[rel_path] = {
                    'name': os.path.basename(rel_path),
                    'description': config.get('description', 'No description available')
                }
            except Exception as e:
                print(f"Error reading {config_path}: {e}")
                sys.exit(1)  # Exit on error
    
    return catalog

def generate_catalog(catalog, output_file):
    """
    Generate catalog.yml file with paths and descriptions
    """
    try:
        # Sort paths for consistent output
        sorted_catalog = dict(sorted(catalog.items()))
        
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(sorted_catalog, f, allow_unicode=True, sort_keys=False)
    except Exception as e:
        print(f"Error generating catalog file: {e}")
        sys.exit(1)  # Exit on error

def catalog_main(base_dir: str = '.', max_depth: int = 2, output_file: Optional[str] = None) -> Dict:
    """
    Main function to generate catalog of config files.
    
    Args:
        base_dir (str): Base directory to start searching from
        max_depth (int): Maximum directory depth to search
        output_file (Optional[str]): Path to output catalog file. If None, uses '.github/catalog.yml' in base_dir
        
    Returns:
        Dict: Generated catalog dictionary
    """
    try:
        if output_file is None:
            output_file = os.path.join(base_dir, '.github', 'catalog.yml')
            
        # Change to base directory
        os.chdir(base_dir)
            
        # Find all config files and their descriptions
        catalog = find_config_files('.', max_depth)
        
        # Generate the catalog file
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        generate_catalog(catalog, output_file)
        
        print(f"Catalog generated successfully at {output_file}")
        print(f"Found {len(catalog)} directories with config files")
        
        return catalog
    except Exception as e:
        print(f"Error in catalog generation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate catalog of config files')
    parser.add_argument('--max-depth', type=int, default=2,
                      help='Maximum directory depth to search (default: 2)')
    args = parser.parse_args()
    catalog_main(max_depth=args.max_depth)
