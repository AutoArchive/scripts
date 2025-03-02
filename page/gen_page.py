import os
import yaml
from typing import Optional, Dict

def generate_metadata_page(file_info, directory):
    """Generate a markdown page for a file based on its metadata."""
    name = file_info['name']
    filename = file_info['filename']
    file_type = file_info['type']
    
    # Only generate pages for document, audio, and video files
    if file_type not in ['document', 'audio', 'video', 'webpage'] and not filename.endswith('.md'):
        print(f"Skipping {filename} because it's not a document, audio, or video file")
        file_info['page'] = filename
        return
    
    # Check if the file is a markdown file
    if filename.endswith('.md'):
        # check if the file already has a additional page
        # read the file
        if not file_info.get('page') or file_info['page'] != filename:
            file_info['page'] = filename
        with open(os.path.join(directory, filename), 'r', encoding='utf-8') as f:
            content = f.read()
        if '[Processed Page Metadata]' in content:
            print(f"Skipping {filename} because it already has a additional page")
            return
        template_path = os.path.join('.github', 'templates', 'additional.md.template')
    else:
        # Read the template file
        template_path = os.path.join('.github', 'templates', 'page.md.template')
    
    with open(template_path, 'r', encoding='utf-8') as template_file:
        template_content = template_file.read()
    
    page_filename = f"{name}_page.md"
    # if page exists, skip
    page_path = os.path.join(directory, page_filename)
    if os.path.exists(page_path):
        print(f"Skipping {filename} because {page_path} already exists")
        # check if the file_info['page'] is the same as page_filename
        if file_info.get('page') != page_filename:
            print(f"Updating {filename} because {page_path} already exists")
            file_info['page'] = page_filename
        return

    # Replace placeholders in the template with actual file information
    content = template_content.format(
        name=name or 'Unknown',
        filename=filename or 'Unknown',
        type=file_info.get('type', 'Unknown') or 'Unknown',
        format=file_info.get('format', 'Unknown') or 'Unknown',
        size=file_info.get('size', 'Unknown') or 'Unknown',
        md5=file_info.get('md5', 'Unknown') or 'Unknown',
        archived='[Unknown archived date(update needed)]',
        description='[Unknown description(update needed)]',
        tags='[Unknown tags(update needed)]',
        date='[Unknown date(update needed)]',
        region='[Unknown region(update needed)]',
        link='[Unknown link(update needed)]',
        author='[Unknown author(update needed)]'
    )

    if filename.endswith('.md'):
        # add the content to the end of the file
        with open(os.path.join(directory, filename), 'a', encoding='utf-8') as f:
            f.write(content)
        # Ensure markdown files do not have a separate page
        file_info['page'] = filename
    else:
        # write the content to the new file
        with open(page_path, 'w', encoding='utf-8') as f:
            f.write(content)
        # Update the file_info with the page filename
        file_info['page'] = page_filename

def process_directory(directory):
    """Process a directory to generate metadata pages for non-image files."""
    config_path = os.path.join(directory, 'config.yml')
    if not os.path.exists(config_path):
        # print(f"Warning: No config.yml found in {directory}")
        return
    
    # Read config
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Generate metadata pages for each file
    for file_info in config.get('files', []):
        generate_metadata_page(file_info, directory)
    
    # Save updated config back to config.yml
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(config, f, allow_unicode=True, sort_keys=False)
    
    # Process subdirectories
    for subdir in config.get('subdirs', []):
        subdir_path = os.path.join(directory, subdir)
        process_directory(subdir_path)

def gen_page_main(base_dir: str = '.', template_dir: Optional[str] = None) -> Dict:
    """
    Main function to generate metadata pages for files.
    
    Args:
        base_dir (str): Base directory to process from
        template_dir (Optional[str]): Directory containing templates. If None, uses '.github/templates'
        
    Returns:
        Dict: Configuration data
    """
    try:
        os.chdir(base_dir)  # Change to base directory
        process_directory('.')
        
        # Return config data from root directory
        config_path = os.path.join('.', 'config.yml')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}
    except Exception as e:
        print(f"Error generating pages: {e}")
        return {}

if __name__ == "__main__":
    gen_page_main()
