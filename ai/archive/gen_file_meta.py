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
        # Check if all metadata fields are non-empty
        if file_info.get('description') != '':
            logging.info(f"Skipping {file_info['filename']} as it already has description")
            continue  # Skip this file if all fields are non-empty
        if file_info.get('type') == 'webpage' or file_info.get('type') == 'other':
            logging.info(f"Skipping {file_info['filename']} as it is an webpage or other")
            continue
        print(f"\n\nProcessing file_info: {file_info}\n\n")

        file_path = os.path.join(directory, file_info['filename'])

        additional_meta = {
            'type': file_info.get('type', ''),
            'format': file_info.get('format', ''),
            'archived': file_info.get('archived', '')
        }
        metadata = generate_metadata(file_path, gen_struct_path, template_path, additional_meta)
        
        if metadata:
            file_info.update(metadata)
            logging.info(f"Updated metadata for {file_info['filename']}")
            print(f"\n\nUpdated metadata for {file_info['filename']}: {metadata}\n\n")

        # Save the config after processing each file
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config, f, allow_unicode=True, sort_keys=False)
            print(f"\n\nSaved config for {file_info['filename']} to {config_path}\n\n")
def main():
    gen_struct_path = '.github/scripts/ai/gen_struct.py'
    template_path = '.github/prompts/gen_file_meta.md.template'
    root_directory = '.'  # Start from the current directory

    for root, dirs, files in os.walk(root_directory):
        update_metadata(root, gen_struct_path, template_path)

if __name__ == "__main__":
    main()
