import os
import shutil

def copy_small_files(source_dir, dest_dir, size_limit_mb=1):
    # Convert MB to bytes
    size_limit = size_limit_mb * 1024 * 1024
    
    # Create destination directory if it doesn't exist
    os.makedirs(dest_dir, exist_ok=True)
    
    # Walk through the source directory
    for root, _, files in os.walk(source_dir):
        for file in files:
            # Check if file is .txt or _page.md
            if file.endswith('.txt'):
                source_path = os.path.join(root, file)
                
                # Check file size
                file_size = os.path.getsize(source_path)
                if file_size < size_limit:
                    # Maintain the same directory structure in destination
                    rel_path = os.path.relpath(root, source_dir)
                    dest_path = os.path.join(dest_dir, rel_path)
                    
                    # Create subdirectories if needed
                    os.makedirs(dest_path, exist_ok=True)
                    
                    # Copy the file
                    shutil.copy2(source_path, dest_path)
                    # copy the page file
                    page_file = file.replace('.txt', '_page.md')
                    source_page_path = os.path.join(root, page_file)
                    shutil.copy2(source_page_path, dest_path)

                    # remove the original file
                    os.remove(source_path)
                    os.remove(source_page_path)

                    print(f"Copied: {source_path} -> {dest_path}")

if __name__ == "__main__":
    # Example usage
    source_directory = "txt下载"  # Source directory path
    destination_directory = "未分类中短篇"  # Destination directory path
    
    copy_small_files(source_directory, destination_directory)
