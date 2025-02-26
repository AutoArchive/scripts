import os
import argparse
from pathlib import Path
import yaml
import urllib.request
import shutil
from Levenshtein import distance

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

def normalize_filename(name):
    """Normalize filename by removing common suffixes and cleaning up"""
    stem = Path(name).stem
    # Remove common suffixes
    common_suffixes = ['_page', '_copy', '_新', '_旧', '副本', '.txt', '.TXT', 'TXT', '_1_', '_2_', '_3_','_Unicode', '（完结）']
    for suffix in common_suffixes:
        if stem.endswith(suffix):
            stem = stem[:-len(suffix)]
    return stem

def is_similar_name(name1, name2, threshold, prefix_only=False, min_prefix_length=6):
    """
    Check if two filenames are similar based on prefix and/or Levenshtein distance
    Args:
        name1: First filename
        name2: Second filename
        threshold: Maximum Levenshtein distance to consider names similar
        prefix_only: If True, only consider prefix matches, not Levenshtein distance
        min_prefix_length: Minimum length required for prefix matching
    """
    # Normalize filenames
    name1_stem = normalize_filename(name1)
    name2_stem = normalize_filename(name2)
    
    # Check for exact match after normalization
    if name1_stem == name2_stem:
        return True
    
    # Check if one is prefix of another
    if (len(name1_stem) >= min_prefix_length and len(name2_stem) >= min_prefix_length and
        (name1_stem.startswith(name2_stem) or name2_stem.startswith(name1_stem))):
        if prefix_only:
            return True
        # If not prefix_only, still need to check distance for prefix matches
        dist = distance(name1_stem, name2_stem)
        return dist <= threshold
    
    # If prefix_only and no prefix match, return False
    if prefix_only:
        return False
        
    # Calculate Levenshtein distance for non-prefix matches
    dist = distance(name1_stem, name2_stem)
    return dist <= threshold

def get_file_size(file_path):
    """Get file size in a human-readable format"""
    size_bytes = os.path.getsize(file_path)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"

def find_existing_file(workspace_dir, filename):
    """Find existing file in workspace directory, return None if not found"""
    try:
        return next(str(p) for p in Path(workspace_dir).rglob(filename)
                   if not should_skip_file(p, workspace_dir))
    except StopIteration:
        return None

def process_name_check(move_files=False, similarity_threshold=None, prefix_only=False):
    """
    Check for files with duplicate or similar names
    Args:
        move_files: If True, move duplicate files to repeatname directory
        similarity_threshold: If set, check for similar names within this Levenshtein distance
        prefix_only: If True, only consider prefix matches for similarity
    """
    # Download and load combined index
    if not download_combined_index():
        print("Failed to download combined index. Exiting.")
        return

    try:
        with open('combined_index.yml', 'r', encoding='utf-8') as f:
            index_data = yaml.safe_load(f) or {}
    except FileNotFoundError:
        print("Could not load combined_index.yml")
        return

    workspace_dir = Path("workspace").resolve()
    if not workspace_dir.exists():
        print("Workspace directory not found")
        return

    # Create repeatname directory if moving files
    if move_files:
        repeatname_dir = Path("repeatname").resolve()
        repeatname_dir.mkdir(exist_ok=True)

    # Get all filenames from combined index with their normalized versions
    index_filenames = {normalize_filename(Path(key).name): key for key in index_data.keys()}
    
    # Keep track of duplicate and similar files
    duplicate_files = []
    similar_files = []
    seen_names = {}  # Change to dict to store original name with normalized version

    # Process each file in workspace recursively
    for root, dirs, files in os.walk(workspace_dir):
        for filename in files:
            file_path = Path(root) / filename
            print(f"Checking: {file_path}")

            if should_skip_file(file_path, workspace_dir):
                continue

            normalized_name = normalize_filename(filename)

            # Check for exact duplicates
            if normalized_name in index_filenames or normalized_name in seen_names:
                size = get_file_size(file_path)
                if normalized_name in index_filenames:
                    index_path = index_filenames[normalized_name]
                    duplicate_files.append((file_path, "exact duplicate (normalized)", size, index_path))
                else:
                    existing_file = find_existing_file(workspace_dir, seen_names[normalized_name])
                    if existing_file and existing_file != str(file_path):
                        duplicate_files.append((file_path, "exact duplicate (normalized)", size, existing_file))
                if move_files:
                    print(f"Moving {file_path} to repeatname directory: Normalized filename already exists")
                    shutil.move(file_path, repeatname_dir / filename)
                else:
                    print(f"Warning: {file_path} has a duplicate normalized filename")
            
            # Check for similar names if threshold is set
            elif similarity_threshold is not None:
                size = get_file_size(file_path)
                # Check against index filenames
                for index_norm_name, index_path in index_filenames.items():
                    if is_similar_name(filename, Path(index_path).name, similarity_threshold, prefix_only):
                        match_type = "prefix match with" if prefix_only else "similar to"
                        similar_files.append((file_path, f"{match_type} {Path(index_path).name}", size, index_path))
                        if move_files:
                            print(f"Moving {file_path} to repeatname directory: {match_type} {Path(index_path).name}")
                            shutil.move(file_path, repeatname_dir / filename)
                        else:
                            print(f"Warning: {file_path} is {match_type} {Path(index_path).name}")
                        break
                
                # Check against seen names
                for seen_norm_name, seen_orig_name in seen_names.items():
                    if is_similar_name(filename, seen_orig_name, similarity_threshold, prefix_only):
                        match_type = "prefix match with" if prefix_only else "similar to"
                        existing_file = find_existing_file(workspace_dir, seen_orig_name)
                        if existing_file and existing_file != str(file_path):
                            similar_files.append((file_path, f"{match_type} {seen_orig_name}", size, existing_file))
                            if move_files:
                                print(f"Moving {file_path} to repeatname directory: {match_type} {seen_orig_name}")
                                shutil.move(file_path, repeatname_dir / filename)
                            else:
                                print(f"Warning: {file_path} is {match_type} {seen_orig_name}")
                            break
            
            seen_names[normalized_name] = filename

    # Print summary
    print("\nSummary:")
    print(f"Total files checked: {len(seen_names)}")
    print(f"Exact duplicates found: {len(duplicate_files)}")
    if similarity_threshold is not None:
        print(f"Similar names found: {len(similar_files)}")
    
    if duplicate_files:
        print("\nExact duplicate files:")
        for file_path, reason, size, original in duplicate_files:
            original_size = get_file_size(original) if os.path.exists(original) else "N/A"
            print(f"- {file_path} ({reason})")
            print(f"  Size: {size} | Original: {original} ({original_size})")
            
    if similar_files:
        print("\nSimilar named files:")
        for file_path, reason, size, original in similar_files:
            original_size = get_file_size(original) if os.path.exists(original) else "N/A"
            print(f"- {file_path} ({reason})")
            print(f"  Size: {size} | Original: {original} ({original_size})")

def main():
    parser = argparse.ArgumentParser(description='Check for duplicate filenames against combined index')
    parser.add_argument('--move', action='store_true', 
                      help='Move duplicate files to repeatname directory (default: just warn)')
    parser.add_argument('--similarity-threshold', type=int, 
                      help='Check for similar names within this Levenshtein distance')
    parser.add_argument('--prefix-only', action='store_true',
                      help='Only consider prefix matches when checking for similar names')
    
    args = parser.parse_args()
    process_name_check(move_files=args.move, 
                      similarity_threshold=args.similarity_threshold,
                      prefix_only=args.prefix_only)

if __name__ == "__main__":
    main() 