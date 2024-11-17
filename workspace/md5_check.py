import os
import hashlib
import shutil
from pathlib import Path
import yaml

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
        if info.get('md5') == md5_hash:
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
    workspace_dir = Path("workspace").resolve()
    if not workspace_dir.exists():
        print("Workspace directory not found")
        return

    # Create repeated directory if it doesn't exist
    repeated_dir = Path("repeated").resolve()
    repeated_dir.mkdir(exist_ok=True)

    # Load existing MD5 data
    try:
        with open('.github/md5.yml', 'r', encoding='utf-8') as f:
            md5_data = yaml.safe_load(f) or {}
    except FileNotFoundError:
        md5_data = {}

    # Process each file in workspace recursively
    moved_files = []
    for root, dirs, files in os.walk(workspace_dir):
        for filename in files:
            file_path = Path(root) / filename
            print(f"Checking: {file_path}")

            # Check if file should be skipped
            if should_skip_file(file_path, workspace_dir):
                continue

            # Calculate MD5
            file_md5 = calculate_md5(file_path)
            
            # Move to repeated if MD5 already exists
            if check_file_exists_by_md5(file_md5, md5_data):
                print(f"Moving {file_path} to repeated directory: MD5 already exists")
                shutil.move(file_path, repeated_dir / filename)
                moved_files.append(str(file_path))
                continue

    if moved_files:
        print("\nMoved files:")
        for file in moved_files:
            print(f"- {file}")
    else:
        print("\nNo duplicate files found")

if __name__ == "__main__":
    process_md5_check()
