import os
import chardet

def detect_encoding(file_path: str) -> str:
    """Detect the encoding of a file using chardet."""
    with open(file_path, 'rb') as file:
        raw_data = file.read()
        result = chardet.detect(raw_data)
        return result['encoding']

def convert_to_utf8(directory: str):
    """Recursively process txt files in the directory to convert them to UTF-8."""
    for root, _, files in os.walk(directory):
        for filename in files:
            if not filename.lower().endswith('.txt'):
                continue

            file_path = os.path.join(root, filename)
                        # First check if already UTF-8
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    file.read()
                    print(f"Skipping {file_path} - already UTF-8")
                    continue
            except UnicodeDecodeError:
                pass  # Not UTF-8, proceed with conversion
            
            # Detect original encoding
            original_encoding = detect_encoding(file_path)
            if original_encoding is None:
                print(f"Warning: Could not detect encoding for {file_path}")
                continue
                
            try:
                # Read content with detected encoding
                with open(file_path, 'r', encoding=original_encoding) as file:
                    content = file.read()
                
                # Write content in UTF-8
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(content)
                
                print(f"Converted {file_path} from {original_encoding} to UTF-8")
                
                # Rename if contains spaces
                if ' ' in filename:
                    new_filename = filename.replace(' ', '_')
                    new_file_path = os.path.join(root, new_filename)
                    os.rename(file_path, new_file_path)
                    print(f"Renamed: {file_path} -> {new_file_path}")
                    
            except Exception as e:
                print(f"Error processing {file_path}: {str(e)}")

def main():
    directory = '.'  # Change this to the directory you want to process
    convert_to_utf8(directory)

if __name__ == "__main__":
    main()
