import os
import re
import yaml
from typing import Optional

def rename_files_in_directory(directory: str):
    """Recursively rename files in the directory to remove spaces and special characters."""
    for root, _, files in os.walk(directory):
        # Skip .github directory
        if root.startswith('./.github') or root.startswith('.github'):
            continue
            
        for filename in files:
            # Generate new filename by replacing spaces and special characters with underscores
            new_filename = re.sub(r'[ \[\]\(\)#]', '_', filename)
            new_filename = new_filename.replace('soushu2023.com@', '')
            new_filename = new_filename.replace('搜书吧', '')
            if new_filename != filename:
                old_file_path = os.path.join(root, filename)
                new_file_path = os.path.join(root, new_filename)
                
                # Rename the file
                os.rename(old_file_path, new_file_path)
                print(f"Renamed: {old_file_path} -> {new_file_path}")

def update_download_links(directory: str):
    """Update download links in markdown files based on config.yml."""
    # Keep track of processed config files to avoid duplicates
    processed_configs = set()
    
    for root, _, files in os.walk(directory):
        if 'config.yml' in files:
            config_path = os.path.join(root, 'config.yml')
            
            # Skip if we've already processed this config
            if config_path in processed_configs:
                continue
                
            processed_configs.add(config_path)
            print(f"Processing config.yml at: {config_path}")
            
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    
                if not config or 'files' not in config:
                    print(f"No files section in config at {config_path}")
                    continue
                    
                print(f"Found {len(config['files'])} files in config")
                
                # Create a mapping of page files to their corresponding filenames
                page_to_filename = {}
                for file_entry in config['files']:
                    if 'page' in file_entry and 'filename' in file_entry:
                        page_path = os.path.join(root, file_entry['page'])
                        page_to_filename[page_path] = file_entry['filename']
                
                # Update links in all markdown files found in config
                for page_path, new_filename in page_to_filename.items():
                    if os.path.exists(page_path):
                        try:
                            with open(page_path, 'r', encoding='utf-8') as file:
                                content = file.read()

                            # Extract the old link pattern - support both Markdown and HTML links
                            match = re.search(
                                r'<!-- tcd_download_link -->\s*.*(?:\[(.*?)\]\((.*?)\)|<a href="(.*?)".*?>(.*?)</a>)\s*<!-- tcd_download_link_end -->',
                                content,
                                flags=re.DOTALL
                            )
                            
                            if match:
                                # Replace with download link and online reading link for txt files
                                download_link = f'下载: <a href="../{new_filename}" download>{new_filename}</a>'
                                online_read_link = ''
                                if new_filename.lower().endswith('.txt'):
                                    online_read_link = f'\n<a href="../{new_filename}" download onclick="this.href=\'https://app.webnovel.win/?add=\'+encodeURIComponent(this.getAttribute(\'href\'))">在线阅读 {new_filename}</a>'
                                
                                updated_content = re.sub(
                                    r'<!-- tcd_download_link -->.*?<!-- tcd_download_link_end -->',
                                    f'<!-- tcd_download_link -->\n{download_link}\n\n{online_read_link}\n<!-- tcd_download_link_end -->',
                                    content,
                                    flags=re.DOTALL
                                )

                                if content != updated_content:
                                    with open(page_path, 'w', encoding='utf-8') as file:
                                        file.write(updated_content)
                                    print(f"Updated links in: {page_path}")
                        except Exception as e:
                            print(f"Error processing file {page_path}: {e}")
                    else:
                        print(f"Warning: Page file not found: {page_path}")
                        
            except Exception as e:
                print(f"Error processing config at {config_path}: {e}")

def rename_main(base_path: Optional[str] = None) -> None:
    """
    Main function to rename files and update download links.
    
    Args:
        base_path (Optional[str]): Base directory path to process. Defaults to current directory.
    """
    directory = base_path if base_path is not None else '.'
    rename_files_in_directory(directory)
    update_download_links(directory)

if __name__ == "__main__":
    rename_main() 