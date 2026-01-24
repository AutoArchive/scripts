import os
import hashlib
import shutil
from pathlib import Path
import yaml
import urllib.request
import tempfile

def download_search_indices():
    """Download search_index.yml files from multiple sites"""
    # Create temp directory for downloads
    temp_dir = tempfile.mkdtemp(prefix="search_indices_")
    print(f"Using temporary directory: {temp_dir}")

    sources = [
        {
            "name": "变身文学与小说存档库一（剧情向）",
            "url": "https://xnovel.transchinese.org/search_index.yml",
            "file": "search_index_1.yml"
        },
        {
            "name": "变身文学与小说存档库二（变百或变嫁）",
            "url": "https://novel.transchinese.org/search_index.yml",
            "file": "search_index_2.yml"
        },
        {
            "name": "变身文学与小说存档库三",
            "url": "https://unovel.transchinese.org/search_index.yml",
            "file": "search_index_3.yml"
        }
    ]

    downloaded_files = []

    for source in sources:
        try:
            print(f"Downloading from {source['name']} ({source['url']})...")
            file_path = os.path.join(temp_dir, source['file'])
            urllib.request.urlretrieve(source['url'], file_path)
            print(f"Successfully downloaded {source['file']}")
            downloaded_files.append(file_path)
        except Exception as e:
            print(f"Error downloading from {source['name']}: {e}")

    return downloaded_files, temp_dir

def merge_indices(index_files):
    """Merge multiple search_index.yml files into a combined index"""
    combined_data = {}

    for index_file in index_files:
        try:
            print(f"Loading {index_file}...")
            with open(index_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}

            # Merge the data
            for key, value in data.items():
                if key not in combined_data:
                    combined_data[key] = value
                else:
                    # If key exists, keep the first occurrence
                    print(f"Duplicate key found: {key} (keeping first occurrence)")

            print(f"Loaded {len(data)} entries from {index_file}")
        except Exception as e:
            print(f"Error loading {index_file}: {e}")

    print(f"Combined {len(combined_data)} total entries from all indices")
    return combined_data

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
    # Download search indices from multiple sources
    print("Downloading search indices...")
    downloaded_files, temp_dir = download_search_indices()

    if not downloaded_files:
        print("Failed to download any search indices. Exiting.")
        return

    try:
        # Merge the downloaded indices
        print("\nMerging indices...")
        md5_data = merge_indices(downloaded_files)

        if not md5_data:
            print("Failed to merge indices. Exiting.")
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
    finally:
        # Clean up temporary directory
        try:
            shutil.rmtree(temp_dir)
            print(f"\nCleaned up temporary directory: {temp_dir}")
        except Exception as e:
            print(f"Warning: Could not clean up temp directory {temp_dir}: {e}")

if __name__ == "__main__":
    process_md5_check()
