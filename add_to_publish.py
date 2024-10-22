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

def process_docs_directory(docs_dir, config_path):
    """Walk through docs directory and add .md files to published_zh and published_en lists."""
    config = read_json(config_path)
    published_zh = config.get("published_zh", [])
    published_en = config.get("published_en", [])

    for root, _, files in os.walk(docs_dir):
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.relpath(os.path.join(root, file), docs_dir)
                if file.endswith('.zh.md'):
                    if file_path not in published_zh:
                        published_zh.append(file_path)
                        print(f"Added to published_zh: {file_path}")
                else:
                    if file_path not in published_en:
                        published_en.append(file_path)
                        print(f"Added to published_en: {file_path}")

    config["published_zh"] = published_zh
    config["published_en"] = published_en
    write_json(config_path, config)
    print(f"Updated config file: {config_path}")
    print(f"Total published Chinese files: {len(published_zh)}")
    print(f"Total published English files: {len(published_en)}")

def main():
    parser = argparse.ArgumentParser(
        description="Process documents in the docs directory and update the published_zh and published_en lists in config.json."
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