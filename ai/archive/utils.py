import re

def extract_metadata_from_markdown(file_path):
        """Extract year, archived_date and description from markdown file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            print("cannot open page, skip image " + file_path)
            retunr None, None, None
        # Extract description from abstract
        desc_match = re.search(
            r'<!-- tcd_abstract -->\n(.*?)\n<!-- tcd_abstract_end -->',
            content, re.DOTALL)
        description = desc_match.group(1).strip() if desc_match else None
        if description == None:
            print("fail to get desc")
        # Extract year from date in metadata table
        date_match = re.search(r'\|\s*Date\s*\|\s*(\d{4})[^|]*\|', content)
        year = date_match.group(1) if date_match else None

        # Extract archived date from metadata table
        archived_match = re.search(r'\|\s*Archived Date\s*\|\s*([^|]+)\|', content)
        archived_date = archived_match.group(1).strip() if archived_match else '9999-12-31'

        return year, archived_date, description
