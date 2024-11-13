import os
import yaml
import sys
from pathlib import Path

def check_file_size(file_path, size_limit_mb=20):
    """
    Check if file exists and is larger than size_limit_mb
    """
    try:
        if os.path.exists(file_path):
            size_mb = os.path.getsize(file_path) / (1024 * 1024)  # Convert to MB
            return size_mb > size_limit_mb, size_mb
        return False, 0
    except Exception as e:
        print(f"Error checking size for {file_path}: {e}")
        return False, 0

def process_config_file(config_path):
    """
    Process a config file and check sizes of referenced files
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            
        large_files = []
        if isinstance(config, dict) and 'files' in config:
            config_dir = Path(config_path).parent
            for file_info in config['files']:
                if 'filename' in file_info:
                    file_path = str(config_dir / file_info['filename'])
                    is_large, size_mb = check_file_size(file_path)
                    if is_large:
                        large_files.append({
                            'name': file_info['filename'],
                            'path': file_path,
                            'size_mb': round(size_mb, 2),
                            'page': str(config_dir / file_info.get('page', ''))  # Add page path
                        })
        return large_files
    except Exception as e:
        print(f"Error reading {config_path}: {e}")
        return []

def parse_gitmodules(repo_root):
    """
    Parse the .gitmodules file and return a mapping of submodule paths to their URLs
    """
    gitmodules_path = os.path.join(repo_root, '.gitmodules')
    submodules = {}
    if os.path.exists(gitmodules_path):
        with open(gitmodules_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        current_path = None
        current_url = None
        for line in lines:
            line = line.strip()
            if line.startswith('[submodule'):
                current_path = None
                current_url = None
            elif line.startswith('path ='):
                current_path = line.split('=', 1)[1].strip()
            elif line.startswith('url ='):
                current_url = line.split('=', 1)[1].strip()
            if current_path and current_url:
                submodules[current_path] = current_url
    return submodules

def update_page_content(page_path, filename, submodules):
    """
    Update the page content to replace download link with GitHub raw link,
    handling git submodules if necessary
    """
    try:
        if os.path.exists(page_path):
            with open(page_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Get relative path from repo root
            repo_root = os.path.abspath('./')
            file_abs_path = os.path.abspath(os.path.join(os.path.dirname(page_path), filename))
            rel_path = os.path.relpath(file_abs_path, repo_root).replace('\\', '/')
            
            # Determine if the file is in a submodule
            github_raw_url = ""
            in_submodule = False
            for submodule_path, submodule_repo in submodules.items():
                submodule_path = submodule_path.replace('\\', '/').rstrip('/')
                if rel_path.startswith(submodule_path):
                    # File is in this submodule
                    in_submodule = True
                    sub_rel_path = rel_path[len(submodule_path):].lstrip('/')
                    # Adjust submodule_repo URL to get raw URL
                    if submodule_repo.endswith('.git'):
                        submodule_repo = submodule_repo[:-4]
                    github_raw_url = f"{submodule_repo}/raw/HEAD/{sub_rel_path}"
                    break
            if not in_submodule:
                # Use main repo URL
                github_raw_url = f"https://raw.githubusercontent.com/transTerminus/trans-digital-cn/refs/heads/main/{rel_path}"
            
            # Replace content between markers
            start_marker = "<!-- tcd_download_link -->"
            end_marker = "<!-- tcd_download_link_end -->"
            
            start_idx = content.find(start_marker)
            end_idx = content.find(end_marker)
            
            if start_idx != -1 and end_idx != -1:
                new_content = (
                    content[:start_idx + len(start_marker)] +
                    "\n" + f"Download: [{filename}]({github_raw_url})" + "\n" +
                    content[end_idx:]
                )
                
                with open(page_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Updated {page_path} with GitHub raw link")
                
    except Exception as e:
        print(f"Error updating page content for {page_path}: {e}")

def find_large_files(root_dir):
    """
    Find all config.yml files and check for large files
    """
    large_files = []
    
    for root, dirs, files in os.walk(root_dir):
        # Skip docs directory
        if 'docs' in dirs:
            dirs.remove('docs')
            
        if 'config.yml' in files:
            config_path = os.path.join(root, 'config.yml')
            print(f"Checking {config_path}")
            found_files = process_config_file(config_path)
            large_files.extend(found_files)
    
    return large_files

def main():
    try:
        root_dir = "./"
        repo_root = os.path.abspath(root_dir)
        submodules = parse_gitmodules(repo_root)
        large_files = find_large_files(root_dir)
        
        if large_files:
            print("\nFound files larger than 20MB:")
            for file_info in sorted(large_files, key=lambda x: x['size_mb'], reverse=True):
                print(f"\nFile: {file_info['name']}")
                print(f"Path: {file_info['path']}")
                print(f"Size: {file_info['size_mb']} MB")
                
                # Remove large file
                if os.path.exists(file_info['path']):
                    os.remove(file_info['path'])
                    print(f"Removed large file: {file_info['path']}")
                
                # Update page content if page path exists
                if file_info.get('page'):
                    update_page_content(file_info['page'], file_info['name'], submodules)
                        
            print(f"\nTotal large files found and processed: {len(large_files)}")
            sys.exit(0)
        else:
            print("\nNo files larger than 20MB found.")
            sys.exit(0)
                
    except Exception as e:
        print(f"Error in main execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()