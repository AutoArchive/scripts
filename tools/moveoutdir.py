import os
import shutil

def cleanup_single_file_dirs(root_path):
    # Walk through all subdirectories
    for dirpath, dirnames, filenames in os.walk(root_path, topdown=False):
        # Skip the root directory
        if dirpath == root_path:
            continue
            
        # Check if directory contains exactly one file and no subdirectories
        if len(filenames) == 1 and len(dirnames) == 0:
            file_path = os.path.join(dirpath, filenames[0])
            parent_dir = os.path.dirname(dirpath)
            target_path = os.path.join(parent_dir, filenames[0])
            
            try:
                # Move the file to parent directory
                shutil.move(file_path, target_path)
                # Remove the empty directory
                os.rmdir(dirpath)
                print(f"Moved {filenames[0]} from {dirpath} to {parent_dir}")
                print(f"Removed directory: {dirpath}")
            except Exception as e:
                print(f"Error processing {dirpath}: {str(e)}")

if __name__ == "__main__":
    # Replace with your folder path
    folder_path = "trans-sexy-novel/tag-R-18"
    cleanup_single_file_dirs(folder_path)