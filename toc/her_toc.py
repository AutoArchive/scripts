#! /usr/bin/env python3
# Generate her-toc for the project
# the her-toc is used for the index page
# it includes all the categories and files in the subdirectories
# Each subdirectory has a README.md file, the file name is the category name
import os
from pathlib import Path
import subprocess

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

def is_ignored(path):
    """Check if a path is ignored by git using git check-ignore command."""
    try:
        result = subprocess.run(
            ['git', 'check-ignore', '-q', path],
            capture_output=True,
            text=True
        )
        # Return True if path is ignored (exit code 0)
        return result.returncode == 0
    except subprocess.SubprocessError:
        # If git command fails, fallback to basic check
        return False

def get_categories():
    """Get all top-level directories excluding git-ignored ones."""
    categories = []
    for item in os.listdir():
        # Skip if item is not a directory or starts with .
        if not os.path.isdir(item) or item.startswith('.'):
            continue
            
        # Skip if item is ignored by git
        if is_ignored(item):
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

def get_template_path(dir_path):
    """Get template path for a specific directory if it exists."""
    relative_path = os.path.relpath(dir_path, '.')
    template_path = os.path.join('.github/templates', relative_path, 'README.md.template')
    if os.path.exists(template_path):
        return template_path
    return None

def generate_file_toc(directory):
    """Generate TOC for files in a directory."""
    toc = []
    for item in sorted(os.listdir(directory)):
        full_path = os.path.join(directory, item)
        if os.path.isfile(full_path) and not item.startswith('.') and item != 'README.md':
            name = os.path.splitext(item)[0]
            toc.append(f"- [{name}]({item})")
    return "\n".join(toc)

def generate_directory_toc(directory):
    """Generate TOC for subdirectories."""
    toc = []
    for item in sorted(os.listdir(directory)):
        full_path = os.path.join(directory, item)
        if os.path.isdir(full_path) and not item.startswith('.'):
            file_count = count_files_in_dir(full_path)
            toc.append(f"- [{item}]({item}) ({file_count} 篇内容)")
    return "\n".join(toc)

def get_file_type(filename):
    """Determine the type of file based on extension."""
    ext = os.path.splitext(filename)[1].lower()
    if ext in {'.md', '.txt', '.doc', '.docx', '.pdf'}:
        return 'document'
    elif ext in {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}:
        return 'image'
    elif ext in {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm'}:
        return 'video'
    elif ext in {'.mp3', '.wav', '.ogg', '.m4a'}:
        return 'audio'
    else:
        return 'other'

def should_include_file(filepath, filename):
    """Check if a file should be included in TOC."""
    # Skip common files that shouldn't be in TOC
    if filename in {'README.md', 'LICENSE', 'LICENSE.md', '.gitignore'}:
        return False
        
    # Skip hidden files
    if filename.startswith('.'):
        return False
        
    # Skip git ignored files
    if is_ignored(filepath):
        return False
        
    return True

def natural_sort_key(s):
    """Natural sort key function for sorting strings with numbers."""
    import re
    def convert(text):
        return int(text) if text.isdigit() else text.lower()
    return [convert(c) for c in re.split('([0-9]+)', s)]

def generate_categorized_file_toc(directory):
    """Generate TOC for files in a directory, categorized by type."""
    files = {
        'document': [],
        'image': [],
        'video': [],
        'audio': [],
        'other': []
    }
    
    # First collect all files
    items = []
    for item in os.listdir(directory):
        full_path = os.path.join(directory, item)
        if os.path.isfile(full_path) and should_include_file(full_path, item):
            items.append(item)
    
    # Sort items using natural sort
    items.sort(key=natural_sort_key)
    
    # Process sorted items
    for item in items:
        name = os.path.splitext(item)[0]
        file_type = get_file_type(item)
        if file_type == 'image':
            # For images, include the image in markdown
            files[file_type].append(f"[{name}]({item})\n\n![{name}]({item})\n\n")
        else:
            files[file_type].append(f"- [{name}]({item})")
    
    toc = []
    type_names = {
        'document': '📄 文档',
        'image': '🖼️ 图片',
        'video': '🎬 视频',
        'audio': '🎵 音频',
        'other': '📎 其他'
    }
    
    for file_type, items in files.items():
        if items:  # Only add sections that have files
            toc.append(f"\n### {type_names[file_type]}\n")
            toc.extend(items)
    
    return "\n".join(toc)

def process_directory(directory):
    """Process a directory recursively to generate README.md files."""
    # Process subdirectories first
    subdirs_toc = []
    for item in sorted(os.listdir(directory)):
        full_path = os.path.join(directory, item)
        if os.path.isdir(full_path) and not item.startswith('.'):
            # Skip if directory is ignored by git
            if is_ignored(full_path):
                continue
            process_directory(full_path)
            file_count = count_files_in_dir(full_path)
            subdirs_toc.append(f"- [{item}]({item}) ({file_count} 篇内容)")
    
    # Generate README.md for current directory
    template_path = get_template_path(directory)
    readme_path = os.path.join(directory, 'README.md')
    
    # Generate TOC content
    toc_content = []
    if subdirs_toc:
        toc_content.append("### 📁 子目录\n")
        toc_content.append("\n".join(subdirs_toc))
    
    # Add categorized file TOC
    files_toc = generate_categorized_file_toc(directory)
    if files_toc:
        if toc_content:  # If we already have subdirs, add an extra newline
            toc_content.append("\n")
        toc_content.append(files_toc)
    
    toc = "\n".join(toc_content)
    
    if template_path:
        # Use template if exists
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        updated_content = content.replace('{{TABLE_OF_CONTENTS}}', toc)
    else:
        # Generate simple README with directory name and TOC
        dir_name = os.path.basename(directory)
        updated_content = f"# {dir_name}\n\n{toc}"
    
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)

def update_project_readme():
    """Update README files throughout the project."""
    excluded = read_gitignore()
    
    # Start from current directory
    process_directory('.')
    
    print("Table of contents generated successfully!")

if __name__ == "__main__":
    update_project_readme()
