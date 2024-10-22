import os
import json
import subprocess
import tempfile

def read_json(file_path):
    """Read and parse JSON file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def write_json(file_path, data):
    """Write data to JSON file."""
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

def read_file(file_path):
    """Read the content of a file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def generate_keywords(content, schema_file, gen_struct_path):
    """Generate keywords using gen_struct.py."""
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt') as temp_input:
        temp_input.write("extract the 5 most important keywords that can be used as topic to publish a blog. No space in the keyword, it shoud be one word. It should be common topics on medium, dev.to, zhihu, etc. \n\n")
        temp_input.write(content)
        temp_input_path = temp_input.name

    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as temp_output:
        temp_output_path = temp_output.name

    try:
        subprocess.run([
            'python', gen_struct_path,
            temp_input_path, temp_output_path, schema_file
        ], check=True)

        keywords = read_json(temp_output_path)
        return keywords.get('keywords', [])
    finally:
        os.unlink(temp_input_path)
        os.unlink(temp_output_path)

def main():
    config_path = '.github/config.json'
    docs_dir = 'docs'
    gen_struct_path = '.github/manage/gen_struct.py'

    config = read_json(config_path)
    passages = config.get('passages', {})

    # Create a temporary schema file
    schema = {
        "type": "object",
        "properties": {
            "keywords": {
                "type": "array",
                "items": {"type": "string"},
            }
        },
        "required": ["keywords"],
        "additionalProperties": False
    }

    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as temp_schema:
        json.dump(schema, temp_schema)
        schema_file = temp_schema.name

    try:
        for file_path, passage_info in passages.items():
            if 'keywords' not in passage_info:
                full_path = os.path.join(docs_dir, file_path)
                if os.path.exists(full_path):
                    content = read_file(full_path)
                    keywords = generate_keywords(content, schema_file, gen_struct_path)
                    passage_info['keywords'] = keywords
                    print(f"Generated keywords for {file_path}: {keywords}")
                else:
                    print(f"File not found: {full_path}")
                write_json(config_path, config)
        write_json(config_path, config)
        print("Successfully updated config with keywords.")
    finally:
        os.unlink(schema_file)

if __name__ == "__main__":
    main()