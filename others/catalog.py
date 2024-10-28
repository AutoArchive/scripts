import os
import yaml
from pathlib import Path

def find_config_files(root_dir):
    """
    Recursively find all config.yml files in the given directory
    """
    catalog = {}
    
    for root, dirs, files in os.walk(root_dir):
        if 'config.yml' in files:
            try:
                config_path = os.path.join(root, 'config.yml')
                print(f"Reading {config_path}")
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    
                # Get relative path from root directory
                rel_path = os.path.relpath(root, root_dir)
                # Store path and description from config if available
                catalog[rel_path] = config.get('description', 'No description available')
            except Exception as e:
                print(f"Error reading {config_path}: {e}")
    
    return catalog

def generate_catalog(catalog, output_file):
    """
    Generate catalog.yml file with paths and descriptions
    """
    # Sort paths for consistent output
    sorted_catalog = dict(sorted(catalog.items()))
    
    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.dump(sorted_catalog, f, allow_unicode=True, sort_keys=False)

def main():
    # Get the project root directory (assuming script is in project/scripts)
    root_dir = "./"
    output_file = os.path.join(root_dir, '.github', 'catalog.yml')
    
    # Find all config files and their descriptions
    catalog = find_config_files(root_dir)
    
    # Generate the catalog file
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    generate_catalog(catalog, output_file)
    
    print(f"Catalog generated successfully at {output_file}")
    print(f"Found {len(catalog)} directories with config files")

if __name__ == "__main__":
    main()
