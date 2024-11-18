import yaml
from datetime import datetime
from collections import defaultdict
import argparse

def load_search_index(filepath='search_index.yml'):
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def analyze_index(input_file='search_index.yml', output_file=None):
    index = load_search_index(input_file)
    
    # Track statistics
    year_counts = defaultdict(int)
    tag_counts = defaultdict(int)
    region_counts = defaultdict(int)
    
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
    
    # Create output dictionary
    analysis_results = {
        'year_summary': dict(sorted(year_counts.items())),
        'tag_summary': dict(sorted(tag_counts.items(), key=lambda x: (-x[1], x[0]))),
        'region_summary': dict(sorted(region_counts.items(), key=lambda x: (-x[1], x[0])))
    }

    # Either print to console or save to file
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(analysis_results, f, allow_unicode=True)
    else:
        print("\nYear Summary:")
        for year, count in analysis_results['year_summary'].items():
            print(f"{year}: {count} files")
        
        print("\nTag Summary:")
        for tag, count in analysis_results['tag_summary'].items():
            print(f"{tag}: {count} occurrences")
            
        print("\nRegion Summary:")
        for region, count in analysis_results['region_summary'].items():
            print(f"{region}: {count} files")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Analyze search index YAML file')
    parser.add_argument('-i', '--input', default='search_index.yml',
                        help='Input YAML file path (default: search_index.yml)')
    parser.add_argument('-o', '--output',
                        help='Output YAML file path (optional, prints to console if not specified)')

    args = parser.parse_args()
    analyze_index(args.input, args.output)
