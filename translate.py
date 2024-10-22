import os
import json
import argparse

def read_json(file_path):
    """Read and parse JSON file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def write_json(file_path, data):
    """Write data to JSON file."""
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

def create_empty_file(file_path):
    """Create an empty file."""
    with open(file_path, 'w', encoding='utf-8') as file:
        pass

def process_docs_directory(docs_dir, config_path):
    """Walk through docs directory and process files."""
    config = read_json(config_path)
    files_to_translate = config.get("files-to-translate", [])

    for root, _, files in os.walk(docs_dir):
        for file in files:
            if file.endswith('.md') and not file.endswith('.zh.md'):
                md_path = os.path.join(root, file)
                zh_path = os.path.join(root, file[:-3] + '.zh.md')

                if md_path not in files_to_translate:
                    files_to_translate.append(md_path)

                if not os.path.exists(zh_path):
                    # Create empty .zh.md file if missing
                    create_empty_file(zh_path)
                    print(f"Created empty file: {zh_path}")

                    if zh_path not in files_to_translate:
                        files_to_translate.append(zh_path)

    config["files-to-translate"] = files_to_translate
    write_json(config_path, config)
    print(f"Updated config file: {config_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Process documents in the My-AI-experiment/docs directory and update config.json."
    )
    parser.add_argument('docs_dir', help='Path to the docs directory')
    parser.add_argument('config_file', help='Path to the config.json file')

    args = parser.parse_args()

    try:
        process_docs_directory(args.docs_dir, args.config_file)
        print("Successfully processed documents and updated config.json.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
