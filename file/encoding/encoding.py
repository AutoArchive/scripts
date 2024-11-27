import os
import chardet

def detect_encoding(file_path: str) -> str:
    """Detect the encoding of a file using chardet."""
    with open(file_path, 'rb') as file:
        raw_data = file.read()
        result = chardet.detect(raw_data)
        return result['encoding'] or 'utf-8'

def convert_to_utf8(directory: str):
    """Recursively process txt files in the directory to convert them to UTF-8."""
    fallback_encodings = ['utf-8', 'gb2312', 'gbk', 'gb18030', 'big5', 'cp936']
    
    for root, _, files in os.walk(directory):
        for filename in files:
            if not filename.lower().endswith('.txt'):
                continue

            file_path = os.path.join(root, filename)
            
            # Read raw content once
            with open(file_path, 'rb') as file:
                content = file.read()

            # Try fallback encodings first
            converted = False
            for encoding in fallback_encodings:
                try:
                    text = content.decode(encoding)
                    with open(file_path, 'w', encoding='utf-8') as file:
                        file.write(text)
                    print(f"Converted {file_path} using {encoding} to UTF-8")
                    converted = True
                    break
                except UnicodeDecodeError:
                    continue

            # If all fallbacks fail, try with detected encoding
            if not converted:
                try:
                    detected_encoding = detect_encoding(file_path)
                    text = content.decode(detected_encoding, errors='ignore')
                    with open(file_path, 'w', encoding='utf-8') as file:
                        file.write(text)
                    print(f"Converted {file_path} using detected encoding {detected_encoding} to UTF-8")
                except Exception as e:
                    print(f"Error processing {file_path}: {str(e)}")

def main():
    directory = '.'  # Change this to the directory you want to process
    convert_to_utf8(directory)

if __name__ == "__main__":
    main()
