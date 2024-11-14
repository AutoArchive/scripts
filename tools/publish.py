import os
import json
import requests
from typing import Optional
import dotenv

dotenv.load_dotenv()

def read_json(file_path: str) -> dict:
    """Read and parse JSON file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def write_json(file_path: str, data: dict) -> None:
    """Write data to JSON file."""
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

def read_markdown_file(file_path: str) -> str:
    """Read markdown file content."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def extract_title_and_content(markdown_content: str) -> tuple[str, str]:
    """Extract title and content from markdown file."""
    lines = markdown_content.split('\n')
    title = ''
    content_start = 0
    
    # Find the first heading
    for i, line in enumerate(lines):
        if line.startswith('# '):
            title = line[2:].strip()
            content_start = i
            break
    
    # If no title found, use the whole content
    if not title:
        return '', markdown_content
    
    # Return title and content (excluding the title)
    return title, '\n'.join(lines[content_start+1:]).strip()

def publish_to_platform(platform: str, content: str, title: str, config: dict) -> bool:
    """Publish content to specified platform."""
    api_key = os.environ.get('PUBLISHER_API_KEY')
    if not api_key:
        raise ValueError(f"Missing PUBLISHER_API_KEY environment variable")

    base_url = "https://media-publisher.vercel.app/api/publish"
    
    # Get is_draft from environment or default to True
    is_draft = os.environ.get('PUBLISH_AS_DRAFT', 'true').lower() == 'true'
    
    payload = {
        "title": title,
        "content": content,
        "tags": config.get("keywords", ["ai", "programming"])[:3],  # Most platforms limit to 4 tags
        "is_draft": is_draft
    }
    
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key
    }
    
    # Debug: Print the payload and headers
    print("Payload:", json.dumps(payload, indent=2))
    print("Headers:", headers)
    
    try:
        response = requests.post(
            f"{base_url}/{platform}",
            json=payload,  # Ensure this is a JSON object
            headers=headers
        )
        
        # Debug: Print the response details
        print("Response Status Code:", response.status_code)
        print("Response Text:", response.text)
        
        if response.status_code != 200:
            print(f"API Response: {response.text}")
            return False
            
        return True
    except Exception as e:
        print(f"Request failed: {str(e)}")
        return False

def find_unpublished_article(docs_dir: str, config_path: str) -> Optional[str]:
    """Find first unpublished article and return its path."""
    config = read_json(config_path)
    # Initialize passages if it doesn't exist
    if "passages" not in config:
        config["passages"] = {}
        write_json(config_path, config)
    
    platforms = config.get("platforms", ["medium", "dev.to"])

    for root, _, files in os.walk(docs_dir):
        for file in files:
            if file.endswith('.md') and not file.endswith('.zh.md'):
                file_path = os.path.relpath(os.path.join(root, file), docs_dir)
                
                # Initialize passage entry if it doesn't exist
                if file_path not in config["passages"]:
                    config["passages"][file_path] = {"published": []}
                    write_json(config_path, config)
                
                # Check if article hasn't been published to all platforms
                published_platforms = config["passages"][file_path].get("published", [])
                if any(platform not in published_platforms for platform in platforms):
                    return os.path.join(docs_dir, file_path)
    
    return None

def main():
    docs_dir = "docs"
    config_path = ".github/config.json"
    
    # Read and initialize config if needed
    config = read_json(config_path)
    if "passages" not in config:
        print("No passages found in config.json, please run add_to_config.py first.")
        return
    
    # Find an unpublished article
    article_path = find_unpublished_article(docs_dir, config_path)
    if not article_path:
        print("No unpublished articles found.")
        return

    # Read config first
    config = read_json(config_path)
    
    # Read the article content and extract title
    raw_content = read_markdown_file(article_path)
    title, content = extract_title_and_content(raw_content)
    if not title:
        title = os.path.basename(article_path).replace('.md', '')
    
    file_path = os.path.relpath(article_path, docs_dir)
    
    # Try to publish to each platform
    for platform in config.get("platforms", ["medium", "dev.to"]):
        if platform not in config["passages"][file_path].get("published", []):
            try:
                if publish_to_platform(platform, content, title, config):
                    # Check if not publishing as draft
                    if not os.environ.get('PUBLISH_AS_DRAFT', 'true').lower() == 'true':
                        # Update config
                        if "published" not in config["passages"][file_path]:
                            config["passages"][file_path]["published"] = []
                        config["passages"][file_path]["published"].append(platform)
                        write_json(config_path, config)
                        print(f"Successfully published to {platform}: {file_path}")
                    else:
                        print(f"Published as draft to {platform}: {file_path}")
                    return  # Exit after publishing to one platform
                else:
                    print(f"Failed to publish to {platform}: {file_path}")
            except Exception as e:
                print(f"Error publishing to {platform}: {e}")

if __name__ == "__main__":
    main()
