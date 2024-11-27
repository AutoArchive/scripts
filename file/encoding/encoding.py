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
            
            # Skip if already UTF-8
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    file.read()
                    print(f"Skipping {file_path} - already UTF-8")
                    continue
            except UnicodeDecodeError:
                pass

            # Detect and convert
            original_encoding = detect_encoding(file_path)
            try:
                # Read raw bytes
                with open(file_path, 'rb') as file:
                    content = file.read()
                
                # Decode with errors='ignore' to skip problematic characters
                text = content.decode(original_encoding, errors='ignore')
                
                # Write content in UTF-8
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(text)
                
                print(f"Converted {file_path} from {original_encoding} to UTF-8")
                
            except Exception as e:
                print(f"Error processing {file_path}: {str(e)}")

def main():
    directory = '.'  # Change this to the directory you want to process
    convert_to_utf8(directory)

if __name__ == "__main__":
    main()
