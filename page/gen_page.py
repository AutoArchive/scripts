import os
import yaml

def generate_metadata_page(file_info, directory):
    """Generate a markdown page for a file based on its metadata."""
    name = file_info['name']
    filename = file_info['filename']
    file_type = file_info['type']
    
    # Only generate pages for document, audio, and video files
    if file_type not in ['document', 'audio', 'video']:
        print(f"Skipping {filename} because it's not a document, audio, or video file")
        file_info['page'] = filename        
        return
    
    # Check if the file is a markdown file
    if filename.endswith('.md'):
        # Directly use the markdown file's path
        file_info['page'] = filename
        return
    
    # Read the template file
    template_path = os.path.join('.github', 'templates', 'page.md.template')
    with open(template_path, 'r', encoding='utf-8') as template_file:
        template_content = template_file.read()
    
    # Replace placeholders in the template with actual file information
    content = template_content.format(
        name=name or 'Unknown',
        filename=filename or 'Unknown',
        type=file_info.get('type', 'Unknown') or 'Unknown',
        format=file_info.get('format', 'Unknown') or 'Unknown',
        size=file_info.get('size', 'Unknown') or 'Unknown',
        md5=file_info.get('md5', 'Unknown') or 'Unknown',
        archived=file_info.get('archived', 'Unknown') or 'Unknown',
        description=file_info.get('description', 'No description available') or 'Unknown',
        tags=', '.join(file_info.get('tags', [])) or 'Unknown',
        date=file_info.get('date', 'Unknown') or 'Unknown',
        link=file_info.get('link', 'No link available') or 'Unknown',
        creator=file_info.get('creator', 'Unknown') or 'Unknown'
    )
    
    # Write the content to a markdown file
    page_filename = f"{name}_page.md"
    page_path = os.path.join(directory, page_filename)
    with open(page_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Update the file_info with the page filename
    file_info['page'] = page_filename

def process_directory(directory):
    """Process a directory to generate metadata pages for non-image files."""
    config_path = os.path.join(directory, 'config.yml')
    if not os.path.exists(config_path):
        print(f"Warning: No config.yml found in {directory}")
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

if __name__ == "__main__":
    process_directory('.')
