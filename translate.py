import os
import json
import argparse
import subprocess

def read_json(file_path):
    """Read and parse JSON file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def write_json(file_path, data):
    """Write data to JSON file."""
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

def read_file(file_path):
    """Read content from a file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def write_file(file_path, content):
    """Write content to a file."""
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

def process_docs_directory(docs_dir, config_path):
    """Walk through docs directory and process files."""
    config = read_json(config_path)
    files_to_translate = config.get("files-to-translate", [])

    for root, _, files in os.walk(docs_dir):
        for file in files:
            if file.endswith('.md'):
                md_path = os.path.join(root, file)
                
                if file.endswith('.zh.md'):
                    en_path = os.path.join(root, file[:-6] + '.md')
                    source_lang, target_lang = "Chinese", "English"
                    source_path, target_path = md_path, en_path
                else:
                    zh_path = os.path.join(root, file[:-3] + '.zh.md')
                    source_lang, target_lang = "English", "Chinese"
                    source_path, target_path = md_path, zh_path

                if not os.path.exists(target_path):
                    # Copy content from source to target and add prompt
                    content = read_file(source_path)
                    prompt = f"Translate the following content from {source_lang} to {target_lang}:\n\n"
                    new_content = prompt + content
                    write_file(target_path, new_content)
                    print(f"Created file with prompt: {target_path}")

                    if target_path not in files_to_translate:
                        files_to_translate.append(target_path)

    config["files-to-translate"] = files_to_translate
    write_json(config_path, config)
    print(f"Updated config file: {config_path}")

def translate_files(config_path):
    """Process files in config.json and translate them using gen.py"""
    config = read_json(config_path)
    files_to_translate = config.get("files-to-translate", [])

    for file_path in files_to_translate:
        input_file = file_path
        output_file = file_path
        
        try:
            subprocess.run(["python3", ".github/manage/gen.py", input_file, output_file], check=True)
            print(f"Translated: {input_file} -> {output_file}")
            
            # Replace the original file with the translated one
            # os.replace(output_file, input_file)
            # print(f"Replaced original file with translated content: {input_file}")
            
            # Remove the file from the list
            files_to_translate.remove(file_path)
            # remove from the json
            config["files-to-translate"] = files_to_translate
            write_json(config_path, config)
        except subprocess.CalledProcessError as e:
            print(f"Error translating {input_file}: {e}")

    # Update the config file with the remaining files to translate
    config["files-to-translate"] = files_to_translate
    write_json(config_path, config)
    print(f"Updated config file: {config_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Process documents in the My-AI-experiment/docs directory, update config.json, and translate files."
    )
    parser.add_argument('docs_dir', help='Path to the docs directory')
    parser.add_argument('config_file', help='Path to the config.json file')

    args = parser.parse_args()

    try:
        process_docs_directory(args.docs_dir, args.config_file)
        print("Successfully processed documents and updated config.json.")
        
        translate_files(args.config_file)
        print("Finished translating files.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
