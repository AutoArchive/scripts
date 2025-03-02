from datetime import datetime
import os
import yaml
from .ignore import load_ignore_patterns, is_ignored

def load_yaml(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return None

def save_yaml(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)

def find_md5_in_visit_links(visit_links_data, target_md5):
    """Search for MD5 hash in visit_links.yml content and return the link if found"""
    for key, value in visit_links_data.items():
        if key.startswith(target_md5):
            return value.get('link')
    return None

def update_files(root_dir, visit_links_path):
    # Load ignore patterns
    ignore_regexes = load_ignore_patterns()
    
    # Load visit_links.yml
    visit_links_data = load_yaml(visit_links_path)
    if not visit_links_data:
        print("Failed to load visit_links.yml - will still update unknown archived dates with today's date")
    
    # Walk through directories
    for root, dirs, files in os.walk(root_dir):
        # Skip ignored directories
        dirs[:] = [d for d in dirs if not is_ignored(os.path.join(root, d), ignore_regexes)]
        
        if 'config.yml' in files and not is_ignored(os.path.join(root, 'config.yml'), ignore_regexes):
            config_path = os.path.join(root, 'config.yml')
            config_data = load_yaml(config_path)
            
            if not config_data or 'files' not in config_data:
                continue

            for file in config_data['files']:
                # Check if file path is ignored
                page_path = os.path.join(root, file.get('page', ''))
                if is_ignored(page_path, ignore_regexes):
                    continue
                    
                # Check if file has MD5 and page field
                if file.get('md5') and file.get('page'):
                    # Read the page file content first
                    if os.path.exists(page_path):
                        try:    
                            with open(page_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                        except Exception as e:
                            print(f"Error reading {page_path}: {e}")
                            continue
                            
                        # Initialize content and track if we need to update
                        content_modified = False
                        
                        if visit_links_data:  # Only try to update from visit_links if data exists
                            data = visit_links_data.get(file['md5'])
                            if data:
                                visited_date = data.get('visited_date')
                                link = data.get('link')
                                
                                if link and "[Unknown link(update needed)]" in content:
                                    content = content.replace("[Unknown link(update needed)]", link)
                                    content_modified = True
                                    print(f"Updated link for {file['name']} in {page_path}")

                                if visited_date and "[Unknown archived date(update needed)]" in content:
                                    content = content.replace("[Unknown archived date(update needed)]", visited_date)
                                    content_modified = True
                                    print(f"Updated archived date for {file['name']} in {page_path}")
                        
                        # If no visited_date was found in visit_links, use current date
                        if "[Unknown archived date(update needed)]" in content:
                            content = content.replace("[Unknown archived date(update needed)]", datetime.now().strftime("%Y-%m-%d"))
                            content_modified = True
                            print(f"Updated archived date for {file['name']} in {page_path}")
                            
                        if "[[Unknown link(update needed)]]([Unknown link(update needed)])" in content:
                            content = content.replace("[[Unknown link(update needed)]]([Unknown link(update needed)])", "[Unknown link(update needed)]")
                            content_modified = True
                            print(f"Updated link format for {file['name']} in {page_path}")
                        
                        # Write the file only once if any modifications were made
                        if content_modified:
                            with open(page_path, 'w', encoding='utf-8') as f:
                                f.write(content)
                                    
def add_config_main(root_directory=".", visit_links_path=None):
    """Add config data to files from visit_links.yml"""
    if visit_links_path is None:
        visit_links_path = os.path.join(".github", "visit_links.yml")
    update_files(root_directory, visit_links_path)

if __name__ == "__main__":
    # Adjust these paths according to your project structure
    root_directory = "."  # Start from current directory
    visit_links_path = ".github/visit_links.yml"
    
    update_files(root_directory, visit_links_path)
