import os
import yaml

def load_yaml(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"Error parsing {file_path}: {e}")
            return None

def save_yaml(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)

def find_link_in_files(visit_links_data, target_file):
    """Search for MD5 hash in visit_links.yml content and return the link if found"""
    for key, value in visit_links_data.items():
        # print(key)
        # print(target_file['filename'].replace('.html', '.md'))
        if target_file['filename'] == key.replace('.html', '.md'):
            return value.get('link')
    print(f"No link found for {target_file['filename']}")
    return None

def update_files(root_dir):

    # Walk through directories
    for root, dirs, files in os.walk(root_dir):

        if 'config.yml' in files:
            try:
                visit_links_path = os.path.join(root, 'page.yml')
                visit_links_data = load_yaml(visit_links_path)
                if not visit_links_data:
                    print("Failed to load page.yml")
                    continue
            except Exception as e:
                print(f"Error loading page.yml: {e}")
                continue

            config_path = os.path.join(root, 'config.yml')
            config_data = load_yaml(config_path)
            
            if not config_data or 'files' not in config_data:
                continue

            for file in config_data['files']:
                # Check if file has MD5 and page field
                if file.get('page'):
                    link = find_link_in_files(visit_links_data, file)
                    if link:
                        # Read and update the page file
                        page_path = os.path.join(root, file['page'])
                        if os.path.exists(page_path):
                            with open(page_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            if "[Unknown link(update needed)]" in content:
                                print(f"Updating link for {file['name']} in {page_path}")
                                updated_content = content.replace("[Unknown link(update needed)]", link)
                                with open(page_path, 'w', encoding='utf-8') as f:
                                    f.write(updated_content)
                                print(f"Updated link for {file['name']} in {page_path}")

if __name__ == "__main__":
    # Adjust these paths according to your project structure
    root_directory = "."  # Start from current directory
    
    update_files(root_directory)
