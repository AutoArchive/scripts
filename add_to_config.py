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

def check_and_publish(docs_dir, config_path):
    """Check all English .md files and update publishing information."""
    config = read_json(config_path)
    passages = config.get("passages", {})
    platforms = ["medium", "dev.to"]

    for root, _, files in os.walk(docs_dir):
        for file in files:
            if file.endswith('.md') and not file.endswith('.zh.md'):
                file_path = os.path.relpath(os.path.join(root, file), docs_dir)
                if file_path not in passages:
                    passages[file_path] = {"published": []}
                elif not isinstance(passages[file_path].get("published"), list):
                    passages[file_path]["published"] = []
                
                # Ensure all platforms are included
                # for platform in platforms:
                #     if platform not in passages[file_path]["published"]:
                #         passages[file_path]["published"].append(platform)

    config["passages"] = passages
    write_json(config_path, config)

    total_published = sum(1 for passage in passages.values() if passage.get("published"))
    print(f"Total files with publishing information: {total_published}")

def main():
    parser = argparse.ArgumentParser(
        description="Update publishing information for English .md files."
    )
    parser.add_argument('docs_dir', help='Path to the docs directory')
    parser.add_argument('config_file', help='Path to the config.json file')

    args = parser.parse_args()

    try:
        check_and_publish(args.docs_dir, args.config_file)
        print("Successfully updated publishing information for documents.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
