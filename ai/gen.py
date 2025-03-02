import os
import openai
import argparse
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')
model_name = os.getenv('OPENAI_MODEL_NAME')
if not model_name:
    model_name = "gpt-4o"
temperature = os.getenv('OPENAI_TEMPERATURE')
if not temperature:
    temperature = 0.7
client = OpenAI()

def read_file(file_path):
    """Read the content of the input file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def write_file(file_path, content):
    """Write the content to the output file."""
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

def generate_cleanup_content(content):
    """Send the prompt and content to OpenAI's API and get the cleaned content."""

    completion = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "user", "content": content}
                ]
            )

    return str(completion.choices[0].message.content)

def generate_content_from_file(input_file, output_file=None):
    """
    Generate cleaned content from a file and optionally save to an output file.
    
    Args:
        input_file (str): Path to the input file
        output_file (str, optional): Path to save the output file. If None, only returns the content.
        
    Returns:
        str: The generated/cleaned content
    """
    try:
        # Read input file
        input_content = read_file(input_file)

        # Generate cleaned content
        cleaned_content = generate_cleanup_content(input_content)

        # Write to output file if specified
        if output_file:
            write_file(output_file, cleaned_content)
            
        return cleaned_content

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def main():
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(
        description="Generate a cleaned-up version of a text file using OpenAI's GPT-4."
    )
    parser.add_argument('input_file', help='Path to the input .txt file')
    parser.add_argument('output_file', help='Path to save the cleaned output file')

    args = parser.parse_args()

    result = generate_content_from_file(args.input_file, args.output_file)
    if result:
        print(f"Successfully processed '{args.input_file}' and saved to '{args.output_file}'.")

if __name__ == "__main__":
    main()
