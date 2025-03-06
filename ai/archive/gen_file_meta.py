import os
import yaml
import json
import logging
import pdfplumber
import sys
from .ignore import load_ignore_patterns, is_ignored
import docx2txt
import concurrent.futures
from typing import List, Dict, Any
from bs4 import BeautifulSoup
import epub2txt

from ..gen_struct import generate_structured_content

ignore_patterns = load_ignore_patterns()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_text(file_path):
    """Extract text from a file based on its type."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext in ['.txt', '.md']:
        # Try different encodings, add utf-16le
        encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'utf-16le']
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as file:
                    content = file.read()
                    # If successful, convert to UTF-8 if needed
                    if encoding != 'utf-8':
                        content = content.encode('utf-8').decode('utf-8')
                    return content[:5000]
            except UnicodeDecodeError:
                continue
        # If all encodings fail
        logging.error(f"Failed to read {file_path} with any supported encoding")
        return "Error: Unable to decode file content."
    elif ext == '.pdf':
        try:
            with pdfplumber.open(file_path) as pdf:
                text = ''
                for page in pdf.pages:
                    text += page.extract_text() or ''
            return text[:5000]  # Limit to 5000 characters
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return "Error extracting text from PDF."
    elif ext == '.doc':
        try:
            # Requires antiword to be installed on the system
            result = subprocess.run(['antiword', file_path], capture_output=True, text=True)
            return result.stdout[:5000]
        except Exception as e:
            logging.error(f"Error extracting DOC with antiword: {str(e)}")
            return f"Error: Could not read DOC file: {str(e)}"
    elif ext == '.docx':
        try:
            text = docx2txt.process(file_path)
            return text[:4000]
        except Exception as e:
            logging.error(f"Error extracting text from Word document {file_path}: {str(e)}")
            return f"Error extracting text from Word document: {str(e)}"
    elif ext == '.epub':
        try:
            text = epub2txt.epub2txt(file_path)
            return text[:10000]
        except Exception as e:
            logging.error(f"Error extracting text from EPUB {file_path}: {str(e)}")
            return f"Error extracting text from EPUB: {str(e)}"
    # for image files, try to extract text from the image
    elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']:
        return "This is an image file, see the image file for more information."
    else:
        return "This is a binary file."

def generate_metadata(file_path, template_path, additional_meta):
    """Generate metadata using gen_struct.py."""
    content = extract_text(file_path)
    
    # Check if the file is an image
    ext = os.path.splitext(file_path)[1].lower()
    is_image = ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']
    
    # Read and format the template
    try:
        with open(template_path, 'r', encoding='utf-8') as template_file:
            template = template_file.read()
        
        # Ensure all placeholders are filled
        input_content = template.format(
            file_content=content,
            file_path=file_path,
            **additional_meta
        )
        
        # Debugging: Check the generated input content
        print(f"Generated input content: {input_content}")

    except KeyError as e:
        print(f"Missing placeholder in template: {e}")
        return None

    # Define the JSON schema
    schema = {
        "type": "object",
        "properties": {
            "description": {"type": "string"},
            "date": {"type": "string"},
            "author": {"type": "string"},
            "region": {"type": "string"},
            "tags": {
                "type": "array",
                "items": {"type": "string"}
            }
        },
        "required": ["description", "date", "author", "region", "tags"],
        "additionalProperties": False
    }

    # Direct call to generate structured content
    image_path = file_path if is_image else None
    metadata = generate_structured_content(input_content, schema, image_path)
    return metadata

def process_single_file(args: tuple) -> None:
    """Process a single file with its metadata."""
    directory, file_info, template_path = args
    
    page_file = file_info.get('page')
    if page_file is None:
        return
        
    page_path = os.path.join(directory, page_file)
    if not os.path.exists(page_path):
        print(f"error: no page file found for {file_info['filename']}")
        return

    # Try different encodings
    encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030']
    page_content = None
    used_encoding = None
    
    for encoding in encodings:
        try:
            with open(page_path, 'r', encoding=encoding) as f:
                page_content = f.read()
            used_encoding = encoding
            break  # If successful, break the loop
        except UnicodeDecodeError:
            continue
                
    if page_content is None:
        logging.error(f"Failed to read {page_path} with any supported encoding")
        return

    # If the file was read with a non-UTF-8 encoding, save it back as UTF-8
    if used_encoding != 'utf-8':
        try:
            with open(page_path, 'w', encoding='utf-8') as f:
                f.write(page_content)
            logging.info(f"Converted {page_path} from {used_encoding} to UTF-8")
        except Exception as e:
            logging.error(f"Failed to convert {page_path} to UTF-8: {e}")
            return

    if '[Unknown description(update needed)]' not in page_content:
        logging.info(f"Skipping {file_info['filename']} as its page doesn't need updating")
        return

    if file_info['filename'].endswith('.html') or file_info.get('type') == 'other':
        logging.info(f"Skipping {file_info['filename']} as it is an webpage or other")
        return
    print(f"\n\nProcessing file_info: {file_info}\n\n")

    file_path = os.path.join(directory, file_info['filename'])

    additional_meta = {
        'type': file_info.get('type', ''),
        'format': file_info.get('format', '')
    }
    
    metadata = generate_metadata(file_path, template_path, additional_meta)

    if metadata:
        # Update the page markdown content
        new_content = page_content.replace(
            '[Unknown description(update needed)]',
            metadata['description']
        )
        new_content = new_content.replace(
            '[Unknown tags(update needed)]',
            ', '.join(metadata['tags'])
        )
        new_content = new_content.replace(
            '[Unknown date(update needed)]',
            metadata['date']
        )
        new_content = new_content.replace(
            '[Unknown author(update needed)]',
            metadata['author']
        )
        new_content = new_content.replace(
            '[Unknown region(update needed)]',
            metadata['region']
        )

        # Write the updated content back to the page file
        with open(page_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        logging.info(f"Updated page markdown for {file_info['filename']}")

def update_metadata(directory: str, template_path: str) -> None:
    """Walk through files and update metadata in parallel batches."""
    config_path = os.path.join(directory, 'config.yml')
    if not os.path.exists(config_path):
        logging.warning(f"No config.yml found in {directory}")
        return

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    if not config:
        logging.warning(f"Empty config.yml in {directory}")
        return

    # Filter files that need processing
    files_to_process = []
    for file_info in config.get('files', []):
        if (file_info.get('page') and 
            not file_info['filename'].endswith('.html') and 
            file_info.get('type') != 'other'):
            files_to_process.append(file_info)

    # Process files in batches of 8
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # Create arguments for each file
        args_list = [(directory, file_info, template_path) 
                    for file_info in files_to_process]
        
        # Execute in parallel
        list(executor.map(process_single_file, args_list))

def gen_file_meta_main(base_dir: str = '.', template_path: str = '.github/prompts/gen_file_meta.md.template') -> Dict[str, Any]:
    """
    Main function to generate file metadata.
    
    Args:
        base_dir (str): Base directory to process from
        
    Returns:
        Dict[str, Any]: Generated metadata
    """
    for root, dirs, files in os.walk(base_dir):
        if is_ignored(root, ignore_patterns):
            logging.info(f"Ignoring directory {root}")
            continue
        update_metadata(root, template_path)
        
    # Return config data from root directory
    return {}


if __name__ == "__main__":
    gen_file_meta_main()
