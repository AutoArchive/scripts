import os
import re

def rename_files_in_directory(directory: str):
    """Recursively rename files in the directory to remove spaces and special characters."""
    for root, _, files in os.walk(directory):
        for filename in files:
            # Generate new filename by replacing spaces and special characters with underscores
            new_filename = re.sub(r'[ \[\]\(\)#]', '_', filename)
            if new_filename != filename:
                old_file_path = os.path.join(root, filename)
                new_file_path = os.path.join(root, new_filename)
                
                # Rename the file
                os.rename(old_file_path, new_file_path)
                print(f"Renamed: {old_file_path} -> {new_file_path}")

def update_download_links(directory: str):
    """Update download links in markdown files dynamically."""
    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.endswith("_page.md"):
                file_path = os.path.join(root, filename)
                
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                # Extract the old link pattern
                match = re.search(
                    r'<!-- tcd_download_link -->\s*.*\[(.*?)\]\((.*?)\)\s*<!-- tcd_download_link_end -->',
                    content
                )
                
                if match:
                    old_filename = match.group(1)
                    old_link = match.group(2)

                    # Generate the new filename and link
                    new_filename = re.sub(r'[ \[\]\(\)#]', '_', old_filename)
                    new_link = re.sub(r'[ \[\]\(\)#]', '_', old_link)

                    # Replace the old link block with the new link block
                    updated_content = re.sub(
                        r'<!-- tcd_download_link -->.*?<!-- tcd_download_link_end -->',
                        f"<!-- tcd_download_link -->\n下载: [{new_filename}]({new_link})\n<!-- tcd_download_link_end -->",
                        content,
                        flags=re.DOTALL
                    )

                    if content != updated_content:
                        with open(file_path, 'w', encoding='utf-8') as file:
                            file.write(updated_content)
                        print(f"Updated links in: {file_path}")

def main():
    directory = '.'  # Change this to the directory you want to process
    rename_files_in_directory(directory)
    update_download_links(directory)

if __name__ == "__main__":
    main()
