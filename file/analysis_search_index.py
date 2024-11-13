import yaml
from datetime import datetime
from collections import defaultdict

def load_search_index(filepath='.github/search_index.yml'):
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def analyze_index():
    index = load_search_index()
    
    # Track statistics
    year_counts = defaultdict(int)
    tag_counts = defaultdict(int)
    region_counts = defaultdict(int)  # New counter for regions
    
    # Process each entry
    for path, metadata in index.items():
        # Normalize date
        date = metadata.get('date')

        # Update year counts
        if date != '未知':
            year = date[:4]
            year_counts[year] += 1
            
        # Count tags
        tags = metadata.get('tags', [])
        if isinstance(tags, list):
            for tag in tags:
                tag_counts[tag] += 1
                
        # Count regions
        region = metadata.get('region', '未知')
        region_counts[region] += 1
    
    # Print summaries
    print("\nYear Summary:")
    for year in sorted(year_counts.keys()):
        print(f"{year}: {year_counts[year]} files")
    
    print("\nTag Summary:")
    for tag, count in sorted(tag_counts.items(), key=lambda x: (-x[1], x[0])):
        print(f"{tag}: {count} occurrences")
        
    print("\nRegion Summary:")
    for region, count in sorted(region_counts.items(), key=lambda x: (-x[1], x[0])):
        print(f"{region}: {count} files")

if __name__ == "__main__":
    analyze_index()
