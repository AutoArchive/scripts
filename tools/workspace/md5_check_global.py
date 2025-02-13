import os
import hashlib
import shutil
from pathlib import Path
import yaml
import urllib.request

def download_combined_index():
    """Download the combined index file from GitHub"""
    url = "https://github.com/transTerminus/data-analysis/raw/refs/heads/main/index/combined_index.yml"
    try:
        urllib.request.urlretrieve(url, "combined_index.yml")
        print("Successfully downloaded combined_index.yml")
        return True
    except Exception as e:
        print(f"Error downloading combined index: {e}")
        return False

def calculate_md5(file_path):
    """Calculate MD5 hash of a file"""
    md5_hash = hashlib.md5()
    with open(file_path, "rb") as f:
        # Read file in chunks to handle large files efficiently
        for chunk in iter(lambda: f.read(4096), b""):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()

def check_file_exists_by_md5(md5_hash, md5_data):
    """Check if file exists in md5 data"""
    for _, info in md5_data.items():
        if isinstance(info, dict) and info.get('md5') == md5_hash:
            return True
    return False

def should_skip_file(file_path, workspace_dir):
    """Check if file should be skipped based on various criteria"""
    try:
        relative_path = file_path.relative_to(workspace_dir)
    except ValueError:
        print(f"Error: {file_path} is not in workspace directory")
        return True

    # Skip system files
    if any(part.startswith('.') for part in relative_path.parts):
        print(f"Skipping {relative_path}: System file/directory")
        return True
        
    # Skip common binary/executable files
    binary_extensions = {'.exe', '.dll', '.so', '.dylib', '.bin'}
    if file_path.suffix.lower() in binary_extensions:
        print(f"Skipping {relative_path}: Binary file")
        return True
        
    return False

def process_md5_check():
    # Download and load combined index
    if not download_combined_index():
        print("Failed to download combined index. Exiting.")
        return

    try:
        with open('combined_index.yml', 'r', encoding='utf-8') as f:
            md5_data = yaml.safe_load(f) or {}
    except FileNotFoundError:
        print("Could not load combined_index.yml")
        return

    workspace_dir = Path("workspace").resolve()
    if not workspace_dir.exists():
        print("Workspace directory not found")
        return

    repeated_dir = Path("repeated").resolve()
    repeated_dir.mkdir(exist_ok=True)

    # Keep track of MD5 hashes we've seen in this workspace
    seen_md5_hashes = set()

    # Process each file in workspace recursively
    moved_files = []
    for root, dirs, files in os.walk(workspace_dir):
        for filename in files:
            file_path = Path(root) / filename
            print(f"Checking: {file_path}")

            if should_skip_file(file_path, workspace_dir):
                continue

            file_md5 = calculate_md5(file_path)
            
            # Check if MD5 exists in either the combined index or our seen hashes
            if check_file_exists_by_md5(file_md5, md5_data) or file_md5 in seen_md5_hashes:
                print(f"Moving {file_path} to repeated directory: MD5 already exists")
                shutil.move(file_path, repeated_dir / filename)
                moved_files.append(str(file_path))
                continue
            
            # Add this file's MD5 to our seen hashes
            seen_md5_hashes.add(file_md5)

    if moved_files:
        print("\nMoved files:")
        for file in moved_files:
            print(f"- {file}")
    else:
        print("\nNo duplicate files found")

if __name__ == "__main__":
    process_md5_check()
