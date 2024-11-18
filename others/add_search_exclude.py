import os
import yaml

def add_search_exclude(directory):
    """Process markdown files to add search exclude marker after first title."""
    config_path = os.path.join(directory, 'config.yml')
    if not os.path.exists(config_path):
        return
    
    # Read config
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Process each markdown file
    for file_info in config.get('files', []):
        filename = file_info['filename']
        if filename.endswith('.md'):
            file_path = os.path.join(directory, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Skip if file already has search exclude
            if 'data-search-exclude' in content:
                continue
                
            # Split content into lines
            lines = content.split('\n')
            new_lines = []
            title_found = False
            
            # Process lines to ensure first heading is single # and add search exclude
            first_heading = True
            for line in lines:
                if first_heading:
                    # If first heading starts with more than one #, convert to single #
                    if line.startswith('##'):
                        # Count leading #s and get the title text
                        heading_text = line.lstrip('#').strip()
                        new_lines.append(f'# {heading_text}')
                    else:
                        # add # to the first heading
                        new_lines.append(f'# {line}')
                elif line.startswith('##') and not line.startswith('###') and '## 摘要与附加信息' not in line:
                    # Check if data-search-exclude is already present
                    if '{ data-search-exclude }' not in line:
                        new_lines.append(f'{line} {{ data-search-exclude }}')
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
    
                # Add the search exclude marker after the first title
                if not title_found and first_heading:
                    new_lines.append('')  # Add blank line
                    new_lines.append('## 正文 { data-search-exclude }')
                    new_lines.append('')  # Add blank line
                    title_found = True
                
                first_heading = False

            # Write modified content back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))
    
    # Process subdirectories
    for subdir in config.get('subdirs', []):
        subdir_path = os.path.join(directory, subdir)
        add_search_exclude(subdir_path)

if __name__ == "__main__":
    add_search_exclude('.')
