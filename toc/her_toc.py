#! /usr/bin/env python3
# Generate her-toc for the project
# the her-toc is used for the index page
# it includes all the categories and files in the subdirectories
# Each subdirectory has a README.md file, the file name is the category name
import os
from pathlib import Path

def count_files_in_dir(directory):
    """Count markdown files in a directory recursively."""
    if not os.path.exists(directory):
        return 0
        
    count = 0
    for root, _, files in os.walk(directory):
        # Count markdown files in current directory
        # count += sum(1 for f in files if f.endswith('.md'))
        print(files)
        count += sum(1 for f in files)
        # Check for directory.md file
        # dir_md = root + '.md'
        # if os.path.exists(dir_md):
        #     count += 1
            
    return count

def read_gitignore():
    """Read .gitignore file and return a set of patterns."""
    gitignore_patterns = {'.git', '.github', '__pycache__', 'node_modules'}
    
    if os.path.exists('.gitignore'):
        with open('.gitignore', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith('#'):
                    # Remove leading and trailing slashes
                    clean_pattern = line.strip('/')
                    gitignore_patterns.add(clean_pattern)
    
    return gitignore_patterns

def get_categories():
    """Get all top-level directories excluding .gitignore patterns."""
    excluded = read_gitignore()
    
    # Get all items in current directory
    categories = []
    for item in os.listdir():
        # Skip if item is in excluded list, starts with ., or is in .gitignore
        if (item.startswith('.') or 
            item in excluded or 
            os.path.splitext(item)[0] in excluded):
            continue
        # Skip if item is not a directory
        if not os.path.isdir(item):
            continue
        categories.append(item)
    
    return sorted(categories)

def generate_top_toc():
    """Generate table of contents with file counts."""
    categories = get_categories()
    
    toc = []
    for category in categories:
        print(category)
        # Count files directly in the category directory, not in docs/
        file_count = count_files_in_dir(category)
        toc.append(f"- [{category}]({category}) ({file_count} 篇内容)")
    
    return "\n".join(toc)

def update_project_readme():
    """Update README.md with the generated TOC."""
    template_path = '.github/README.md.template'
    output_path = 'README.md'
    
    if not os.path.exists(template_path):
        print(f"Template file not found: {template_path}")
        return
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Generate TOC and replace placeholder
    toc = generate_top_toc()
    updated_content = content.replace('{{TABLE_OF_CONTENTS}}', toc)
    
    # Write the updated content to README.md
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print("Table of contents generated successfully!")

if __name__ == "__main__":
    update_project_readme()
