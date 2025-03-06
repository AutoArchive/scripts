import os
import json
import openai
import argparse
from openai import OpenAI
from dotenv import load_dotenv
import base64


def read_file(file_path):
    """Read the content of the input file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def write_file(file_path, content):
    """Write the content to the output file."""
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

def encode_image(image_path):
    """Encode image to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def generate_cleanup_content(content, schema, image_path=None):
    """Send the prompt and content to OpenAI's API and get the structured content."""
       
    load_dotenv()
    openai.api_key = os.getenv('OPENAI_API_KEY')
    model_name = os.getenv('OPENAI_MODEL_NAME')
    if not model_name:
        model_name = "gpt-4o-mini"
    print(f"Using model: {model_name}")
    temperature = os.getenv('OPENAI_TEMPERATURE')
    if not temperature:
        temperature = 0.7
    print(f"Using temperature: {temperature}")
    client = OpenAI()
    messages = [
        {"role": "system", "content": f"You are a helpful assistant that generates structured output based on the following JSON schema: {json.dumps(schema)}"}
    ]

    # Prepare user message with optional image
    if image_path:
        base64_image = encode_image(image_path)
        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": content
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                }
            ]
        })
    else:
        messages.append({"role": "user", "content": content})

    completion = client.chat.completions.create(
        model=model_name,
        messages=messages,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "response",
                "schema": schema,
                "strict": True
            }
        }
    )

    return json.loads(completion.choices[0].message.content)

def generate_structured_content(input_content, schema, image_path=None, output_file=None):
    """
    Generate structured content from input content and schema, with optional image.
    
    Args:
        input_content (str): The input content or path to input file
        schema (dict or str): Schema dictionary or path to schema file
        image_path (str, optional): Path to an image file
        output_file (str, optional): Path to save output. If None, only returns the result.
        
    Returns:
        dict: The structured content generated
    """
    # Handle input content as file path or direct content
    if os.path.isfile(input_content):
        input_content = read_file(input_content)

    # Handle schema as file path or direct schema
    if isinstance(schema, str) and os.path.isfile(schema):
        schema = json.loads(read_file(schema))

    # Generate structured content
    structured_content = generate_cleanup_content(input_content, schema, image_path)

    # Write to output file if specified
    if output_file:
        write_file(output_file, json.dumps(structured_content, indent=2))
            
    return structured_content

def main():
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(
        description="Generate a structured version of a text file using OpenAI's GPT-4."
    )
    parser.add_argument('input_file', help='Path to the input .txt file')
    parser.add_argument('output_file', help='Path to save the structured output file')
    parser.add_argument('schema_file', help='Path to the JSON schema file')
    parser.add_argument('--image', help='Optional path to an image file', default=None)

    args = parser.parse_args()

    result = generate_structured_content(args.input_file, args.schema_file, args.image, args.output_file)
    if result:
        print(f"Successfully processed '{args.input_file}' and saved structured output to '{args.output_file}'.")

if __name__ == "__main__":
    main()
