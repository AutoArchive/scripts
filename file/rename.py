import os

def rename_files_in_directory(directory: str):
    """Recursively rename files in the directory to remove spaces."""
    for root, _, files in os.walk(directory):
        for filename in files:
            if ' ' in filename:
                new_filename = filename.replace(' ', '_')
                old_file_path = os.path.join(root, filename)
                new_file_path = os.path.join(root, new_filename)
                
                # Rename the file
                os.rename(old_file_path, new_file_path)
                print(f"Renamed: {old_file_path} -> {new_file_path}")

def main():
    directory = '.'  # Change this to the directory you want to process
    rename_files_in_directory(directory)

if __name__ == "__main__":
    main()
