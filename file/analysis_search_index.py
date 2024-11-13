import yaml
from datetime import datetime
from collections import defaultdict

def load_search_index(filepath='.github/search_index.yml'):
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def normalize_date(date_str):
    if date_str is None or date_str == '未知' or not date_str:
        return '未知'
    
    # Try parsing different formats
    date_formats = [
        '%Y-%m-%d %H:%M:%S',  # Add timestamp format
        '%Y-%m-%d',
        '%Y-%m',
        '%Y'
    ]
    
    for fmt in date_formats:
        try:
            date_obj = datetime.strptime(str(date_str), fmt)
            if fmt == '%Y':
                return f"{date_obj.year}-01-01"
            elif fmt == '%Y-%m':
                return f"{date_str}-01"
            # Always return just the date portion in YYYY-MM-DD format
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    print(f"Warning: Invalid date format: {date_str}")
    return '未知'

def analyze_index():
    index = load_search_index()
    
    # Track statistics
    year_counts = defaultdict(int)
    tag_counts = defaultdict(int)
    
    # Process each entry
    for path, metadata in index.items():
        # Normalize date
        date = metadata.get('date')
        normalized_date = normalize_date(date)
        if normalized_date != date:
            print(f"Normalized date for {path}: {date} -> {normalized_date}")
            metadata['date'] = normalized_date
            
        # Normalize archived date
        archived_date = metadata.get('archived date')
        normalized_archived = normalize_date(archived_date)
        if normalized_archived != archived_date:
            print(f"Normalized archived date for {path}: {archived_date} -> {normalized_archived}")
            metadata['archived date'] = normalized_archived
            
        # Update year counts
        if normalized_date != '未知':
            year = normalized_date[:4]
            year_counts[year] += 1
            
        # Count tags
        tags = metadata.get('tags', [])
        if isinstance(tags, list):
            for tag in tags:
                tag_counts[tag] += 1
    
    # Print summaries
    print("\nYear Summary:")
    for year in sorted(year_counts.keys()):
        print(f"{year}: {year_counts[year]} files")
    
    print("\nTag Summary:")
    for tag, count in sorted(tag_counts.items(), key=lambda x: (-x[1], x[0])):
        print(f"{tag}: {count} occurrences")

if __name__ == "__main__":
    analyze_index()
