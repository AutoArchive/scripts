import os
import docx2txt
import glob
from pathlib import Path

def convert_doc_to_txt(root_dir):
    # Find all .doc and .docx files recursively
    doc_files = []
    for ext in ('*.doc', '*.docx'):
        doc_files.extend(glob.glob(os.path.join(root_dir, '**', ext), recursive=True))
    
    # Process each file
    for doc_path in doc_files:
        try:
            # Convert path to Path object
            doc_file = Path(doc_path)
            # Create output path with .txt extension
            txt_path = doc_file.with_suffix('.txt')
            
            print(f"Converting: {doc_path}")
            
            # Extract text from doc file
            text = docx2txt.process(doc_path)
            
            # Write text to new file
            with open(txt_path, 'w', encoding='utf-8') as txt_file:
                txt_file.write(text)
            
            # Remove original doc file
            os.remove(doc_path)
            print(f"Converted and removed: {doc_path}")
            
        except Exception as e:
            print(f"Error processing {doc_path}: {str(e)}")

if __name__ == "__main__":
    # Get the current working directory
    current_dir = os.getcwd()
    print(f"Starting conversion in: {current_dir}")
    
    # Run the conversion
    convert_doc_to_txt(current_dir)
    print("Conversion complete!")
