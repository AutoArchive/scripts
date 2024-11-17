import os
import shutil
import argparse

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
                    if os.path.exists(source_page_path):
                        shutil.copy2(source_page_path, dest_path)
                        os.remove(source_page_path)
                    
                    # Remove the original txt file
                    os.remove(source_path)
                    print(f"Copied: {source_path} -> {dest_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Copy small files to a new directory')
    parser.add_argument('--source', default='workspace', help='Source directory path')
    parser.add_argument('--dest', default='workspace_short', help='Destination directory path')
    parser.add_argument('--size', type=float, default=1, help='Size limit in MB')
    
    args = parser.parse_args()
    
    copy_small_files(args.source, args.dest, args.size)
