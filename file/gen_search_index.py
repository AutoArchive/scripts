import os
import re
import yaml
from ignore import load_ignore_patterns, is_ignored

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

def extract_metadata_from_markdown(content):
    metadata = {}
    
    # Extract abstract
    abstract_match = re.search(
        r'<!-- tcd_abstract -->\n(.*?)\n<!-- tcd_abstract_end -->',
        content, re.DOTALL)
    if abstract_match:
        metadata['description'] = abstract_match.group(1).strip()

    # Extract table metadata
    table_match = re.search(r'\| Attribute\s*\|\s*Value\s*\|([\s\S]*?)\n\n', content)
    if table_match:
        table_content = table_match.group(1)
        rows = re.findall(r'\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|', table_content)
        for key, value in rows:
            key = key.strip().lower()
            value = value.strip()
            if key in ['date', 'author', 'tags', 'original link', 'archived date']:
                if key == 'tags':
                    metadata['tags'] = [tag.strip() for tag in value.split(',')]
                elif key == 'original link':
                    metadata['link'] = extract_markdown_link(value)
                else:
                    metadata[key] = value

    return metadata

def extract_markdown_link(markdown_text):
    # Matches markdown links in format [text](url)
    pattern = r'\[(.*?)\]\((.*?)\)'
    match = re.search(pattern, markdown_text)
    if match:
        return match.group(2)  # group 2 contains the URL
    return None

def is_binary_file(file_path):
    """
    Check if a file is binary.
    """
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            if b'\0' in chunk:
                return True
            else:
                text_characters = bytearray({7,8,9,10,12,13,27}) + bytearray(range(0x20, 0x100))
                nontext = chunk.translate(None, text_characters)
                if len(nontext) / len(chunk) > 0.30:
                    return True
        return False
    except:
        return True  # Assume binary if unreadable

def update_files(root_dir, output_path):
    ignore_regexes = load_ignore_patterns()
    search_index = {}
    files_processed = 0

    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if not is_ignored(os.path.join(root, d), ignore_regexes)]
        
        if 'config.yml' in files and not is_ignored(os.path.join(root, 'config.yml'), ignore_regexes):
            config_path = os.path.join(root, 'config.yml')
            config_data = load_yaml(config_path)

            if not config_data or 'files' not in config_data:
                continue

            for file_entry in config_data['files']:
                page = file_entry.get('page')
                if not page:
                    continue
                page_path = os.path.join(root, page)
                rel_path = os.path.relpath(page_path, root_dir)

                if is_ignored(page_path, ignore_regexes):
                    continue

                if os.path.exists(page_path):
                    files_processed += 1
                    
                    # Get basic metadata from file_entry
                    metadata = {
                        'type': file_entry.get('type', 'document'),
                        'format': file_entry.get('format', 'Unknown'),
                        'size': file_entry.get('size', 0),
                        'md5': file_entry.get('md5', ''),
                        'link': '',
                        'description': os.path.join(root, file_entry.get('name')),
                        'archived date': '未知',
                        'link': '未知',
                        'author': '未知',
                        'date': '未知',
                        'tags': ['binary']
                    }

                    if is_binary_file(page_path):
                        search_index[rel_path] = metadata
                    else:
                        try:
                            with open(page_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                content_metadata = extract_metadata_from_markdown(content)
                                metadata.update(content_metadata)
                                search_index[rel_path] = metadata
                        except Exception as e:
                            print(f"Error processing {page_path}: {e}")
                else:
                    print(f"Page file not found: {page_path}")

    # Save search index
    save_yaml(output_path, search_index)
    print(f"Generated search index at {output_path}")
    print(f"Total files processed: {files_processed}")  # Print total

if __name__ == "__main__":
    root_directory = "."
    output_path = ".github/search_index.yml"
    update_files(root_directory, output_path)
