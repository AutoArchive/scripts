import os
import json
import argparse
import time
import random

def read_json(file_path):
    """Read and parse JSON file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def write_json(file_path, data):
    """Write data to JSON file."""
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

def mock_publish(file_path):
    """Mock function to simulate publishing a file."""
    print(f"Publishing file: {file_path}")
    time.sleep(random.uniform(0.5, 2.0))  # Simulate some processing time
    success = random.random() < 0.9  # 90% success rate
    if success:
        print(f"Successfully published: {file_path}")
    else:
        print(f"Failed to publish: {file_path}")
    return success

def check_and_publish(docs_dir, config_path):
    """Check all English .md files and publish if not in published_en."""
    config = read_json(config_path)
    published_en = set(config.get("published_en", []))
    new_published = []

    for root, _, files in os.walk(docs_dir):
        for file in files:
            if file.endswith('.md') and not file.endswith('.zh.md'):
                file_path = os.path.relpath(os.path.join(root, file), docs_dir)
                if file_path not in published_en:
                    print(f"Found unpublished file: {file_path}")
                    if mock_publish(file_path):
                        new_published.append(file_path)

    if new_published:
        config["published_en"] = list(published_en.union(new_published))
        write_json(config_path, config)
        print(f"Updated config file: {config_path}")
        print(f"Newly published files: {len(new_published)}")
    else:
        print("No new files to publish.")

    print(f"Total published English files: {len(config['published_en'])}")

def main():
    parser = argparse.ArgumentParser(
        description="Check and publish English .md files that are not in the published_en list."
    )
    parser.add_argument('docs_dir', help='Path to the docs directory')
    parser.add_argument('config_file', help='Path to the config.json file')

    args = parser.parse_args()

    try:
        check_and_publish(args.docs_dir, args.config_file)
        print("Successfully checked and published documents.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()