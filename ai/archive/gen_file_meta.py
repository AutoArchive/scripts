import os
import yaml
import json
import subprocess
import tempfile
import logging
from docx import Document
import pdfplumber

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_text(file_path):
    """Extract text from a file based on its type."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext in ['.txt', '.md']:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()[:24000]
    elif ext == '.pdf':
        try:
            with pdfplumber.open(file_path) as pdf:
                text = ''
                for page in pdf.pages:
                    text += page.extract_text() or ''
            return text[:24000]  # Limit to 2400 characters
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return "Error extracting text from PDF."
    elif ext in ['.doc', '.docx']:
        try:
            doc = Document(file_path)
            text = '\n'.join([para.text for para in doc.paragraphs])
            return text[:24000]  # Limit to 2400 characters
        except Exception as e:
            print(f"Error extracting text from Word document: {e}")
            return "Error extracting text from Word document."
    # for image files, try to extract text from the image
    elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']:
        return "This is a image file, see the image file for more information."
    else:
        return "This is a binary file."

def generate_metadata(file_path, gen_struct_path, template_path, additional_meta):
    """Generate metadata using gen_struct.py."""
    content = extract_text(file_path)
    
    # Check if the file is an image
    ext = os.path.splitext(file_path)[1].lower()
    is_image = ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']
    
    # Read and format the template
    try:
        with open(template_path, 'r', encoding='utf-8') as template_file:
            template = template_file.read()
        
        # Debugging: Check the content of the template and the provided data
        # print(f"Template content: {template}")
        # print(f"File content: {content}")
        # print(f"File path: {file_path}")
        # print(f"Additional meta: {additional_meta}")

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

    # print(input_content)
    # Define the JSON schema
    schema = {
        "type": "object",
        "properties": {
            "description": {"type": "string"},
            "date": {"type": "string"},
            "tags": {
                "type": "array",
                "items": {"type": "string"}
            }
        },
        "required": ["description", "date", "tags"],
        "additionalProperties": False
    }

    # Create temporary files for input and schema
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt') as temp_input:
        temp_input.write(input_content)
        temp_input_path = temp_input.name

    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as temp_schema:
        json.dump(schema, temp_schema)
        schema_file = temp_schema.name

    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as temp_output:
        temp_output_path = temp_output.name

    try:
        cmd = [
            'python', gen_struct_path,
            temp_input_path, temp_output_path, schema_file
        ]
        
        # Add image path argument if it's an image file
        if is_image:
            cmd.extend(['--image', file_path])

        subprocess.run(cmd, check=True)

        with open(temp_output_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        return metadata
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running gen_struct.py: {e}")
        return None
    finally:
        os.unlink(temp_input_path)
        os.unlink(temp_output_path)
        os.unlink(schema_file)

def update_metadata(directory, gen_struct_path, template_path):
    """Walk through files and update metadata."""
    config_path = os.path.join(directory, 'config.yml')
    if not os.path.exists(config_path):
        logging.warning(f"No config.yml found in {directory}")
        return

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    if not config:
        logging.warning(f"Empty config.yml in {directory}")
        return

    for file_info in config.get('files', []):
        # Add check for page markdown file
        page_file = file_info.get('page')
        if page_file is None:
            continue
        page_path = os.path.join(directory, page_file)
        if not os.path.exists(page_path):
            print(f"error: no page file found for {file_info['filename']}")
            exit(1)

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
            continue

        # If the file was read with a non-UTF-8 encoding, save it back as UTF-8
        if used_encoding != 'utf-8':
            try:
                with open(page_path, 'w', encoding='utf-8') as f:
                    f.write(page_content)
                logging.info(f"Converted {page_path} from {used_encoding} to UTF-8")
            except Exception as e:
                logging.error(f"Failed to convert {page_path} to UTF-8: {e}")
                continue

        if '[Unknown description(update needed)]' not in page_content:
            logging.info(f"Skipping {file_info['filename']} as its page doesn't need updating")
            continue

        if file_info['filename'].endswith('.html') or file_info.get('type') == 'other':
            logging.info(f"Skipping {file_info['filename']} as it is an webpage or other")
            continue
        print(f"\n\nProcessing file_info: {file_info}\n\n")

        file_path = os.path.join(directory, file_info['filename'])

        additional_meta = {
            'type': file_info.get('type', ''),
            'format': file_info.get('format', '')
            # 'archived': file_info.get('archived', '')
        }
        metadata = generate_metadata(file_path, gen_struct_path, template_path, additional_meta)
        
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

            # Write the updated content back to the page file
            with open(page_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            logging.info(f"Updated page markdown for {file_info['filename']}")

def main():
    gen_struct_path = '.github/scripts/ai/gen_struct.py'
    template_path = '.github/prompts/gen_file_meta.md.template'
    root_directory = '.'  # Start from the current directory

    for root, dirs, files in os.walk(root_directory):
        update_metadata(root, gen_struct_path, template_path)

if __name__ == "__main__":
    main()
