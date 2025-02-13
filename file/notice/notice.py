import os
import json

def read_template(template_path):
    """Read the template file and get the English and Chinese notices."""
    with open(template_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        return lines[0].strip(), lines[1].strip()

def read_json(file_path):
    """Read and parse JSON file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def write_json(file_path, data):
    """Write data to JSON file."""
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

def add_action_notice(docs_dir, config_path, template_path):
    """Add action notice to markdown files and update config."""
    en_notice, zh_notice = read_template(template_path)
    config = read_json(config_path)
    passages = config.get("passages", {})
    modified_count = 0

    for root, _, files in os.walk(docs_dir):
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.relpath(os.path.join(root, file), docs_dir)
                full_path = os.path.join(root, file)
                
                # Initialize or get the file entry in config
                if file_path not in passages:
                    passages[file_path] = {}
                
                # Skip if already processed
                if passages[file_path].get("endactionnotice"):
                    continue

                # Read the file content
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Add appropriate notice
                if file.endswith('.zh.md'):
                    new_content = content + '\n\n' + zh_notice + '\n'
                else:
                    new_content = content + '\n\n' + en_notice + '\n'

                # Write the modified content
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)

                # Update config
                passages[file_path]["endactionnotice"] = True
                modified_count += 1

    config["passages"] = passages
    write_json(config_path, config)
    print(f"Modified {modified_count} files and updated config.json")

def main():
    docs_dir = "docs"  # Adjust path as needed
    config_path = ".github/config.json"
    template_path = ".github/action.md.template"
    
    try:
        add_action_notice(docs_dir, config_path, template_path)
        print("Successfully added action notices to documents.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
