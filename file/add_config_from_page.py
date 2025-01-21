import datetime
import os
import yaml
import re

def extract_embedded_link(markdown_path):
    """Extract link from HTML comment in markdown file."""
    if not os.path.exists(markdown_path):
        return None
        
    with open(markdown_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    pattern = r'<!--\s*tcd_original_link\s+(https?://[^\s]+)\s*-->'
    match = re.search(pattern, content)
    return match.group(1) if match else None

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

def update_files(root_dir):

    # Walk through directories
    for root, dirs, files in os.walk(root_dir):

        if 'config.yml' in files:
            visit_links_path = os.path.join(root, 'page.yml')
            config_path = os.path.join(root, 'config.yml')
            config_data = load_yaml(config_path)
            
            if not config_data or 'files' not in config_data:
                continue

            # Try to load page.yml first
            visit_links_data = None
            if os.path.exists(visit_links_path):
                visit_links_data = load_yaml(visit_links_path)

            for file in config_data['files']:
                if not file.get('page'):
                    print(f"No page field found for {file.get('name', 'unnamed file')}")
                    continue

                visited_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                link = None

                # Try to get link from page.yml first
                if visit_links_data:
                    related_record = visit_links_data.get(file['filename'].replace('.md', '.html'))
                    if related_record:
                        link = related_record.get('link')
                        if related_record.get('visited_date'):
                            visited_date = related_record['visited_date']

                # If no link found in page.yml, try embedded link
                if not link:
                    markdown_path = os.path.join(root, file['filename'])
                    link = extract_embedded_link(markdown_path)

                if link:
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
                        
                        if "[Unknown archived date(update needed)]" in content:
                            print(f"Updating archived date for {file['name']} in {page_path}")
                            updated_content = content.replace("[Unknown archived date(update needed)]", visited_date)
                            with open(page_path, 'w', encoding='utf-8') as f:
                                f.write(updated_content)
                            print(f"Updated archived date for {file['name']} in {page_path}")
                else:
                    print(f"No link found for {file['name']}")

if __name__ == "__main__":
    # Adjust these paths according to your project structure
    root_directory = "."  # Start from current directory
    
    update_files(root_directory)
