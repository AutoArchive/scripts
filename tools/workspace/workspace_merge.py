import os
import hashlib
import shutil
from pathlib import Path
import yaml
import json
import sys

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from github.scripts.ai.gen_struct import generate_structured_content

from docx import Document
import pdfplumber

# Set up logging
def extract_text(file_path):
    """Extract text from a file based on its type."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext in ['.txt', '.md']:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    elif ext == '.pdf':
        try:
            with pdfplumber.open(file_path) as pdf:
                text = ''
                for page in pdf.pages:
                    text += page.extract_text() or ''
            return text[:2400]  # Limit to 2400 characters
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return "Error extracting text from PDF."
    elif ext in ['.doc', '.docx']:
        try:
            doc = Document(file_path)
            text = '\n'.join([para.text for para in doc.paragraphs])
            return text[:2400]  # Limit to 2400 characters
        except Exception as e:
            print(f"Error extracting text from Word document: {e}")
            return "Error extracting text from Word document."
    # for image files, try to extract text from the image
    elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']:
        return "This is a image file, see the image file for more information."
    else:
        return "This is a binary file."

def calculate_md5(file_path):
    """Calculate MD5 hash of a file"""
    md5_hash = hashlib.md5()
    with open(file_path, "rb") as f:
        # Read file in chunks to handle large files efficiently
        for chunk in iter(lambda: f.read(4096), b""):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()

def check_file_exists_by_md5(md5_hash):
    """Check if file exists in md5.yml"""
    try:
        with open('.github/md5.yml', 'r', encoding='utf-8') as f:
            md5_data = yaml.safe_load(f) or {}
            
        for _, info in md5_data.items():
            if info.get('md5') == md5_hash:
                return True
        return False
    except FileNotFoundError:
        return False

def get_ai_classification(file_path):
    """Ask AI to classify the file and suggest the best directory"""
    content = extract_text(str(file_path))
    
    # Get directory structure from catalog.yml
    try:
        with open('.github/catalog.yml', 'r', encoding='utf-8') as f:
            catalog = yaml.safe_load(f)
            current_dir_structure = yaml.dump(catalog, allow_unicode=True)
    except FileNotFoundError:
        print("Catalog file not found")
        return None

    # Read the template
    try:
        with open('.github/prompts/workspace.md.template', 'r', encoding='utf-8') as f:
            template = f.read()
    except FileNotFoundError:
        print("Template file not found")
        return None

    # Define the JSON schema for classification
    schema = {
        "type": "object",
        "properties": {
            "suggested_path": {
                "type": "string",
                "description": "The suggested path where this file should be stored, or '未知' if no suitable path exists"
            }
        },
        "required": ["suggested_path"],
        "additionalProperties": False
    }

    # Fill in the template
    prompt = template.format(
        file_name=file_path.name,
        file_content=content[:1000],
        current_dir_structure=current_dir_structure
    )
    print("prompt: ", prompt)
    
    # Add image path if it's an image
    image_path = None
    if file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']:
        image_path = str(file_path)
    
    # Direct call to generate structured content
    try:
        result = generate_structured_content(prompt, schema, image_path)
        return result
    except Exception as e:
        print(f"Error during AI classification: {e}")
        return None

def should_skip_file(file_path, workspace_dir):
    """Check if file should be skipped based on various criteria
    Args:
        file_path: absolute Path object of the file
        workspace_dir: absolute Path object of workspace directory
    """
    # Get relative path from workspace directory
    try:
        relative_path = file_path.relative_to(workspace_dir)
    except ValueError:
        print(f"Error: {file_path} is not in workspace directory")
        return True

    # Skip files larger than 10MB
    # if file_path.stat().st_size > 10 * 1024 * 1024:
    #     print(f"Skipping {relative_path}: File too large")
    #     return True
        
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

def process_workspace():
    workspace_dir = Path("workspace").resolve()  # Get absolute path
    if not workspace_dir.exists():
        print("Workspace directory not found")
        return

    # Create repeated directory if it doesn't exist
    repeated_dir = Path("repeated").resolve()
    repeated_dir.mkdir(exist_ok=True)

    # Process each file in workspace recursively
    for root, dirs, files in os.walk(workspace_dir):
        for filename in files:
            file_path = Path(root) / filename
            print(f"Processing: {file_path}")

            # Check if file should be skipped
            if should_skip_file(file_path, workspace_dir):
                continue

            # Check MD5
            file_md5 = calculate_md5(file_path)
            if check_file_exists_by_md5(file_md5):
                print(f"Moving {file_path} to repeated directory: MD5 already exists")
                shutil.copy2(file_path, repeated_dir / filename)
                continue
            
            # AI classification with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                classification = get_ai_classification(file_path)
                print("classification: ", classification)
                
                if classification:
                    suggested_path = classification['suggested_path']
                    target_path = Path(suggested_path)
                    
                    # Check if suggested directory exists
                    if not target_path.exists():
                        print(f"Suggested path {target_path} does not exist, retrying...")
                        if attempt == max_retries - 1:
                            print(f"Failed to get valid path after {max_retries} attempts")
                        continue
                    
                    # Copy the file to the suggested location
                    shutil.copy2(file_path, target_path / file_path.name)
                    print(f"Moved {file_path.name} to {target_path}")
                    break

    # Rename workspace to old_workspace after processing
    if workspace_dir.exists():
        old_workspace = Path("old_workspace")
        if old_workspace.exists():
            shutil.rmtree(old_workspace)
        workspace_dir.rename(old_workspace)
        print("Renamed workspace to old_workspace")

if __name__ == "__main__":
    process_workspace()
