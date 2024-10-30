import yaml
from pathlib import Path

def extract_visited_links():
    """Extract visited links from links.yml and create visit_links.yml"""
    try:
        # Read links.yml
        with open('.github/links.yml', 'r', encoding='utf-8') as f:
            links_data = yaml.safe_load(f) or {}

        # Extract visited links
        visited_links = {}
        for link, info in links_data.items():
            if info.get('visited') == True and info.get('md5'):
                visited_links[info['md5']] = {
                    'snippet': info.get('snippet', ''),
                    'title': info.get('title', ''),
                    'link': info.get('link', ''),
                    'visited_date': info.get('visited_date', '')
                }

        # Write to visit_links.yml
        with open('.github/visit_links.yml', 'w', encoding='utf-8') as f:
            yaml.dump(visited_links, f, allow_unicode=True)

        print(f"Extracted {len(visited_links)} visited links")

    except Exception as e:
        print(f"Error processing files: {e}")

if __name__ == "__main__":
    extract_visited_links() 