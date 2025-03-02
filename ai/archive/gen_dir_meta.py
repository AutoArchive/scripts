#!/usr/bin/env python3
import os
import yaml
import json
import logging
from pathlib import Path
import sys

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from ..gen_struct import generate_structured_content
from .ignore import load_ignore_patterns, is_ignored
from .utils import extract_metadata_from_markdown

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

ignore_patterns = load_ignore_patterns()

def get_directory_files(directory):
    logging.debug(f"Getting files from directory: {directory}")
    files = []
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isfile(item_path):
            files.append(item)
    return "\n".join(files)

def get_content_summary(directory, config, max_files=20):
    logging.debug(f"Generating content summary from config with {len(config.get('files', []))} files")
    content = []
    
    # Get file names and descriptions from config
    if 'files' in config:
        files = config['files'][:max_files] if len(config['files']) > max_files else config['files']
        for file in files:
            if isinstance(file, dict) and 'name' in file:
                file_path = os.path.join(directory, file['page'])
                print(file_path)
                _, _, description = extract_metadata_from_markdown(file_path)
                
                # Add file name and description if available
                if description:
                    content.append(f"{file['name']}\n{description}")
                else:
                    print("no desc")
                    content.append(file['name'])
    
    # Get subdirectory names
    if 'subdirs' in config:
        for subdir in config['subdirs']:
            if isinstance(subdir, str):
                content.append(subdir)
            elif isinstance(subdir, dict) and 'name' in subdir:
                content.append(subdir['name'])
    
    # Add ellipsis if files were truncated
    if 'files' in config and len(config['files']) > max_files:
        content.append('...')
    
    return "\n\n".join(content)

def generate_directory_metadata(directory, template_path):
    logging.info(f"Generating metadata for directory: {directory}")
    
    # Read and format the template
    with open(template_path, 'r', encoding='utf-8') as template_file:
        template = template_file.read()
        
    # Read existing config
    config_path = os.path.join(directory, 'config.yml')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f) or {}
        
    # Get content summary
    content_summary = get_content_summary(directory, config)
        
    # Format the template with directory information
    input_content = template.format(
            directory_path=directory,
            directory_files=content_summary
    )
    print(f"Formatted template with content summary of length: {len(content_summary)}")
    print(input_content)
    
    # Define the JSON schema
    schema = {
        "type": "object",
        "properties": {
            "description": {"type": "string"},
            "tags": {
                "type": "array",
                "items": {"type": "string"}
            }
        },
        "required": ["description", "tags"],
        "additionalProperties": False
    }

    # Generate the structured content directly
    metadata = generate_structured_content(input_content, schema)
    return metadata

def update_directory_metadata(directory, template_path):
    logging.info(f"Processing directory: {directory}")
    config_path = os.path.join(directory, 'config.yml')
    if not os.path.exists(config_path):
        logging.warning(f"No config.yml found in {directory}")
        return

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f) or {}

    # Skip if description already exists
    if config.get('description') != '':
        logging.info(f"Skipping {directory} as it already has description")
        return

    metadata = generate_directory_metadata(directory, template_path)
    print("metadata", metadata)
    if metadata:
        config.update(metadata)
        logging.info(f"Updated metadata for {directory}")
        
        # Save the updated config
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config, f, allow_unicode=True, sort_keys=False)
            logging.info(f"Saved config for {directory}")

def gen_dir_meta_main(root_directory="."):
    """Generate metadata for directories in the project"""
    logging.info("Starting directory metadata generation")
    template_path = os.path.join(root_directory, '.github/prompts/gen_dir_meta.md.template')
    
    processed_count = 0
    for root, dirs, files in os.walk(root_directory):
        if is_ignored(root, ignore_patterns):
            logging.info(f"Ignoring directory {root}")
            continue
        if 'config.yml' in files:
            update_directory_metadata(root, template_path)
            processed_count += 1
    
    logging.info(f"Finished processing {processed_count} directories")

def main():
    gen_dir_meta_main()

if __name__ == "__main__":
    main()
