import os
import yaml

def load_yaml(file_path):
    """
    Load YAML data from a file.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"Error parsing {file_path}: {e}")
            return None

def add_notice_to_txt_files_from_yaml(root_dir, notice_template_path):
    """
    Walk the directory tree, load YAML configurations, and use the data to add notices to .txt files.
    """
    # Load the notice template
    try:
        with open(notice_template_path, 'r', encoding='utf-8') as f:
            notice_content = f.read()
    except Exception as e:
        print(f"Error reading notice template: {e}")
        return

    files_modified = 0

    for root, dirs, files in os.walk(root_dir):
        if 'config.yml' in files:
            config_path = os.path.join(root, 'config.yml')
            config_data = load_yaml(config_path)
            
            if not config_data or 'files' not in config_data:
                continue

            for file_entry in config_data['files']:
                txt_file = file_entry.get('filename')
                if txt_file and txt_file.endswith('.txt'):
                    txt_file_path = os.path.join(root, txt_file)
                    
                    if os.path.exists(txt_file_path):
                        try:
                            # Check if the notice is already present
                            with open(txt_file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            if notice_content.strip() in content:
                                continue  # Skip if notice already exists
                            
                            # Append the notice to the file
                            with open(txt_file_path, 'a', encoding='utf-8') as f:
                                f.write("\n\n" + notice_content.strip())
                            files_modified += 1
                            print(f"Notice added to: {txt_file_path}")
                        except Exception as e:
                            print(f"Error modifying {txt_file_path}: {e}")
                    else:
                        print(f"File not found: {txt_file_path}")

    print(f"Total .txt files modified: {files_modified}")

if __name__ == "__main__":
    root_directory = "."
    notice_template_path = ".github/templates/notice.md.template"
    add_notice_to_txt_files_from_yaml(root_directory, notice_template_path)
