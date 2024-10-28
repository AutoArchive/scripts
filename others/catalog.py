import os
import yaml
from pathlib import Path
import sys
import argparse  # Add this import

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

def main():
    try:
        # Add argument parser
        parser = argparse.ArgumentParser(description='Generate catalog of config files')
        parser.add_argument('--max-depth', type=int, default=2,
                          help='Maximum directory depth to search (default: 2)')
        args = parser.parse_args()

        # Get the project root directory (assuming script is in project/scripts)
        root_dir = "./"
        output_file = os.path.join(root_dir, '.github', 'catalog.yml')
        
        # Find all config files and their descriptions
        catalog = find_config_files(root_dir, args.max_depth)
        
        # Generate the catalog file
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        generate_catalog(catalog, output_file)
        
        print(f"Catalog generated successfully at {output_file}")
        print(f"Found {len(catalog)} directories with config files")
    except Exception as e:
        print(f"Error in main execution: {e}")
        sys.exit(1)  # Exit on error

if __name__ == "__main__":
    main()
