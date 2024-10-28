import os
import yaml
import json
import subprocess
import tempfile
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_directory_files(directory):
    logging.debug(f"Getting files from directory: {directory}")
    files = []
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isfile(item_path):
            files.append(item)
    return "\n".join(files)

def get_content_summary(config, max_files=20):
    logging.debug(f"Generating content summary from config with {len(config.get('files', []))} files")
    content = []
    
    # Get file names from config
    if 'files' in config:
        files = config['files'][:max_files] if len(config['files']) > max_files else config['files']
        for file in files:
            if isinstance(file, dict) and 'name' in file:
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
    
    return "\n".join(content)

def generate_directory_metadata(directory, gen_struct_path, template_path):
    logging.info(f"Generating metadata for directory: {directory}")
    
    # Read and format the template
    try:
        with open(template_path, 'r', encoding='utf-8') as template_file:
            template = template_file.read()
        
        # Read existing config
        config_path = os.path.join(directory, 'config.yml')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        
        # Get content summary
        content_summary = get_content_summary(config)
        
        # Format the template with directory information
        input_content = template.format(
            directory_path=directory,
            directory_files=content_summary
        )
        print(f"Formatted template with content summary of length: {len(content_summary)}")

    except Exception as e:
        logging.error(f"Error preparing template: {e}")
        return None

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

    # Create temporary files for input and schema
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt') as temp_input:
        temp_input.write(input_content)
        temp_input_path = temp_input.name

    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as temp_schema:
        json.dump(schema, temp_schema)
        schema_file = temp_schema.name

    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as temp_output:
        temp_output_path = temp_output.name

    try:
        cmd = [
            'python', gen_struct_path,
            temp_input_path, temp_output_path, schema_file
        ]

        subprocess.run(cmd, check=True)

        with open(temp_output_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        return metadata
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running gen_struct.py: {e}")
        return None
    finally:
        os.unlink(temp_input_path)
        os.unlink(temp_output_path)
        os.unlink(schema_file)

def update_directory_metadata(directory, gen_struct_path, template_path):
    logging.info(f"Processing directory: {directory}")
    config_path = os.path.join(directory, 'config.yml')
    if not os.path.exists(config_path):
        logging.warning(f"No config.yml found in {directory}")
        return

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f) or {}

    # Skip if description already exists
    if config.get('description'):
        logging.info(f"Skipping {directory} as it already has description")
        return

    metadata = generate_directory_metadata(directory, gen_struct_path, template_path)
    print("metadata", metadata)
    if metadata:
        config.update(metadata)
        logging.info(f"Updated metadata for {directory}")
        
        # Save the updated config
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config, f, allow_unicode=True, sort_keys=False)
            logging.info(f"Saved config for {directory}")

def main():
    logging.info("Starting directory metadata generation")
    gen_struct_path = '.github/scripts/ai/gen_struct.py'
    template_path = '.github/prompts/gen_dir_meta.md.template'
    root_directory = '.'  # Start from the current directory

    processed_count = 0
    for root, dirs, files in os.walk(root_directory):
        if 'config.yml' in files:
            update_directory_metadata(root, gen_struct_path, template_path)
            processed_count += 1
    
    logging.info(f"Finished processing {processed_count} directories")

if __name__ == "__main__":
    main()
