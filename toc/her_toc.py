#!/usr/bin/env python3
import os
import yaml
import argparse
from utils import *
from entry_generators import *
from content_processors import *
from toc_formatters import TableTOCFormatter, MarkdownListTOCFormatter
import pandas as pd
import requests
from io import StringIO

class TOCGenerator:
    """Generates table of contents for directories and files"""
    def __init__(self, formatter_type='table'):
        # Initialize generators
        self.file_generator = FileEntryGenerator()
        self.dir_generator = DirectoryEntryGenerator()
        self.independence_generator = IndependenceEntryGenerator()
        
        # Set formatter based on type
        self.formatter_type = formatter_type
        if formatter_type == 'table':
            self.formatter = TableTOCFormatter()
        elif formatter_type == 'markdown':
            self.formatter = MarkdownListTOCFormatter()
        else:
            print(f"Warning: Unknown formatter type '{formatter_type}', defaulting to table")
            self.formatter = TableTOCFormatter()
        
        # Initialize processors with generators and formatter
        self.files_processor = FilesProcessor(self.file_generator, self._format_entry)
        self.dir_processor = DirectoryProcessor(self.dir_generator, self._format_entry)
        self.independence_processor = IndependenceProcessor(self.independence_generator, self._format_entry)
        
        # Clear any existing entries
        self.files_processor.clear()
        
        # Add a list to store all entries
        self.all_entries = []
        
        # Add GA data processing
        self.ga_data = self._load_ga_data()
        
        # Initialize current directory
        self.current_directory = '.'

    def generate_categorized_toc(self, categories):
        """Generate TOC from categorized content"""
        type_names = {
            'webpage': '🌐 网页', 'other': '📎 其他',
            'document': '📄 文档', 'image': '🖼️ 图片',
            'video': '🎬 视频', 'audio': '🎵 音频'
        }
        
        return self.formatter.format_categorized_content(categories, type_names)

    def process_directory(self, directory, ignore_regexes, include_wordcloud=False):
        """Process a directory to generate README.md based on config.yml"""
        if is_ignored(directory, ignore_regexes):
            print(f"Skipping ignored directory: {directory}")
            return

        # Update current directory
        self.current_directory = directory

        # Clear all entries if this is the root directory
        if directory == '.':
            self.files_processor.clear()
            self.all_entries = []

        config_path = os.path.join(directory, 'config.yml')
        if not os.path.exists(config_path):
            print(f"Warning: No config.yml found in {directory}")
            return
        
        # Read config and generate content
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            
        # Process subdirectories first to collect all entries
        if config.get('subdirs'):
            for subdir in config.get('subdirs', []):
                subdir_path = os.path.join(directory, subdir)
                self.process_directory(subdir_path, ignore_regexes, include_wordcloud)
        
        # Process current directory
        if config.get('files'):
            self.files_processor.process(config['files'], directory)
            # Store entries
            self.all_entries.extend(self.files_processor.all_entries)
            
        # Generate TOC content
        toc_content = self._generate_toc_content(config, directory, ignore_regexes, include_wordcloud)
        
        # Get most visited entries
        most_visited = self.get_most_visited(10)
        most_visited_html = self._format_most_visited(most_visited)
        
        # Update template replacements
        template_replacements = {
            '{{MOST_VISITED}}': most_visited_html,
        }
        
        # Generate and write README
        self._write_readme(directory, config, toc_content, template_replacements)

    def _generate_toc_content(self, config, directory, ignore_regexes, include_wordcloud):
        """Generate the TOC content for a directory"""
        toc_content = []
        
        # Process files by category
        if config.get('files'):
            categories = self.files_processor.process(config['files'], directory)
            files_toc = self.generate_categorized_toc(categories)
            if files_toc:
                toc_content.append(files_toc)

        # Process directories
        if config.get('subdirs'):
            toc_content.append("\n## 📁 子目录\n")
            dir_entries = self.dir_processor.process(config['subdirs'], directory, ignore_regexes)
            dir_section = self.formatter.format_directory_content(dir_entries)
            toc_content.append(dir_section)

        # Add wordcloud using markdown
        if include_wordcloud:
            wordcloud_path = os.path.join(directory, 'abstracts_wordcloud.png')
            if os.path.exists(wordcloud_path):
                toc_content.append('\n## 📊 词云图 { data-search-exclude }\n')
                toc_content.append('![词云图](abstracts_wordcloud.png)\n')
        
        # Add sorting script only if using table formatter
        if self.formatter_type == 'table':
            script_path = os.path.join(os.path.dirname(__file__), 'toc_sort.js')
            try:
                with open(script_path, 'r', encoding='utf-8') as f:
                    script_content = f.read()
                    toc_content.append(f'\n<script>\n{script_content}\n</script>\n')
            except FileNotFoundError:
                print(f"Warning: Sorting script not found at {script_path}")
        
        return "\n".join(toc_content)

    def _generate_featured_entry(self, item):
        """Generate entry for featured content"""
        return f'''<tr data-name="{item['name']}" data-type="{item['type']}" data-date="{item.get('date', '')}">
            <td><a href="{item['link']}">{item['name']}</a></td>
            <td>{item['type']}</td>
            <td>{item.get('date', '未知')}</td>
        </tr>'''

    def _write_readme(self, directory, config, toc_content, template_replacements):
        """Write the README.md file"""
        # Store current directory for use in _generate_recent_updates
        self.current_directory = directory
        
        template_path = get_template_path(directory)
        if not template_path:
            template_path = os.path.join(os.path.dirname(get_template_path('.')), 'default_toc.md.template')
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            print(f"Warning: No template found at {template_path}")
            dir_name = config.get('name', os.path.basename(directory))
            updated_content = f"# {dir_name}\n\n{toc_content}"
            
            readme_path = os.path.join(directory, 'README.md')
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            return
            
        # Replace template placeholders
        dir_name = config.get('name', os.path.basename(directory))
        updated_content = content.replace('{{TITLE}}', dir_name)
        
        # Add info section if description exists
        info_section = ""
        if 'description' in config:
            info_section = "\n!!! info\n\n" + \
                         "    " + config['description'].replace("\n", "\n    ") + "\n"
        updated_content = updated_content.replace('{{INFO_SECTION}}', info_section)
        
        # Generate statistics section
        stats_section = "\n!!! note \"📊 统计信息\"\n\n"
        total_count = count_files_recursive(directory, [])  # Count all files in this dir and subdirs
        stats_section += f"    总计内容：{total_count} 篇\n"
        
        # Add tags if they exist
        if 'tags' in config and config['tags']:
            stats_section += '    标签：' + " ".join([f"`{tag}`" for tag in config['tags']]) + "\n"
            
        updated_content = updated_content.replace('{{TAGS_SECTION}}', stats_section)
        
        # Add recent updates if placeholder exists
        if '{{RECENT_UPDATES}}' in content:
            recent_updates = self._generate_recent_updates()
            updated_content = updated_content.replace('{{RECENT_UPDATES}}', recent_updates)
        
        # Add table of contents
        updated_content = updated_content.replace('{{TABLE_OF_CONTENTS}}', toc_content)
        
        # Add most visited section
        updated_content = updated_content.replace('{{MOST_VISITED}}', template_replacements['{{MOST_VISITED}}'])
        
        # Write the README file
        readme_path = os.path.join(directory, 'README.md')
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)

    def _generate_recent_updates(self):
        """Generate the recent updates section"""
        if not self.all_entries:
            return ""
            
        content = []
        
        # Sort all entries by date and get the 10 most recent
        latest_entries = sorted(
            [e for e in self.all_entries if 'entry_data' in e],  # Filter valid entries
            key=lambda x: x['archived_date'],
            reverse=True
        )[:10]
        
        # Use the directory where README is being written
        current_dir = os.path.relpath(self.current_directory, '.')
        
        for entry in latest_entries:
            entry_data = entry['entry_data']
            date = entry['archived_date'][:10]  # Get just the date part
            
            # Since links are now relative to root, calculate relative to current dir
            link = os.path.relpath(entry_data['link'], current_dir)
            link = link.replace(os.sep, '/')
            
            # Remove .md extension if present
            if link.endswith('.md'):
                link = link[:-3]
                
            content.append(f"    * {date} [{entry_data['name']}]({link})")
        
        content.append("\n")
        return "\n".join(content)

    def _format_entry(self, entry):
        """Format entry data into HTML/Markdown"""
        if entry is None:
            return ''
        
        def truncate_text(text, length=20):
            """Helper function to truncate text and add ellipsis if needed"""
            if not text:
                return ""
            return text[:length] + ('...' if len(text) > length else '')
        
        entry_type = entry['type']
        if entry_type == 'image':
            return f'''<tr class="image-row">
                <td colspan="3">
                    <div class="image-item">
                        <img src="{entry['filename']}" alt="{entry['name']}" />
                        <p>{entry['name']}</p>
                    </div>
                </td>
            </tr>'''
        elif entry_type == 'content':
            description_html = ''
            if entry['description']:
                summary = "展开" # + truncate_text(entry['description'])
                description_html = f'''<details markdown>
                    <summary>{summary}</summary>
                    <div class="description">
                        {entry['description']}
                        <br>年份：{entry['year'] if entry['year'] != 'Unknown' else '未知'}
                        <br>收录日期：{entry['date']}
                    </div>
                </details>'''
            else:
                description_html = '无摘要'
            
            return f'''<tr data-name="{entry['name']}" data-year="{entry['year']}" data-date="{entry['date']}">
                <td><a href="{entry['link']}" class="md-button">{entry['name']}</a></td>
                <td class="year-cell">{entry['year'] if entry['year'] != 'Unknown' else '未知'}</td>
                <td class="description-cell">{description_html}</td>
            </tr>'''
        elif entry_type == 'directory':
            description_html = ''
            if entry['description']:
                summary = "展开" # + truncate_text(entry['description'])
                description_html = f'''<details markdown>
                    <summary>{summary}</summary>
                    <div class="description">
                        {entry['description']}
                        <br>文件数量：{entry['count']} 篇
                    </div>
                </details>'''
            else:
                description_html = '无简介'
            
            return f'''<tr data-name="{entry['name']}" data-count="{entry['count']}" data-date="{entry['date']}">
                <td><a href="{entry['name']}" class="md-button">{entry['name']}</a></td>
                <td class="count-cell">{entry['count']} 篇</td>
                <td class="description-cell">{description_html}</td>
            </tr>'''
        elif entry_type == 'independence':
            return f'<tr><td><a href="{entry["url"]}">{entry["name"]}</a></td><td>{entry["size"]} 篇</td></tr>'
        
        return ''

    def _load_ga_data(self):
        """Load Google Analytics data from GitHub"""
        try:
            url = "https://raw.githubusercontent.com/project-polymorph/data-analysis/refs/heads/main/ga_visitor/google_analysis.csv"
            response = requests.get(url)
            response.raise_for_status()
            
            # Read CSV data
            content = response.text
            lines = content.split('\n')
            
            # Find the actual data start (after metadata)
            start_idx = 0
            for i, line in enumerate(lines):
                if line.startswith('Page path and screen class,Views,'):
                    start_idx = i
                    break
            
            # Create DataFrame from the actual data
            data = '\n'.join(lines[start_idx:])
            df = pd.read_csv(StringIO(data))
            
            # Clean up GA paths - remove leading/trailing slashes and _page suffix
            df['clean_path'] = df['Page path and screen class'].apply(lambda x: 
                x.strip('/') if isinstance(x, str) else '')
            
            # Sort by views and get top entries
            df = df.sort_values('Views', ascending=False)
            return df
        except Exception as e:
            print(f"Warning: Failed to load GA data: {e}")
            return None

    def get_most_visited(self, limit=10):
        """Get the most visited content entries from config.yml files"""
        if not self.all_entries:
            print("Debug: No entries found")
            return []
            
        all_matches = []
        current_dir_abs = os.path.abspath(self.current_directory)
        
        # Filter entries to only include those from current directory or its subdirectories
        current_entries = [
            entry for entry in self.all_entries 
            if 'current_dir' in entry and 
            os.path.abspath(os.path.join('.', entry['current_dir'])).startswith(current_dir_abs)
        ]
        
        print(f"\nTotal entries in repository: {len(self.all_entries)}")
        print(f"Processing {len(current_entries)} entries for current directory: {self.current_directory}")
        
        # Collect entries with visitor counts
        for entry in current_entries:
            if 'entry_data' not in entry:
                continue
            
            entry_data = entry['entry_data']
            file_info = entry.get('file_info', {})
            
            # Get visitor count if available
            visitors = file_info.get('visitors', 0)
            if visitors > 0:
                # Calculate relative link from current directory
                rel_link = os.path.relpath(
                    os.path.join(entry['current_dir'], entry_data['link']),
                    self.current_directory
                ).replace(os.sep, '/')
                
                all_matches.append({
                    'name': entry_data['name'],
                    'link': '/' + rel_link,
                    'views': visitors
                })
        
        # Sort by views and get top entries
        sorted_matches = sorted(all_matches, key=lambda x: x['views'], reverse=True)
        top_entries = sorted_matches[:limit]
        
        print(f"Found {len(all_matches)} entries with visitor data")
        print(f"Returning top {len(top_entries)} entries")
        return top_entries

    def _format_most_visited(self, entries):
        """Format most visited entries as a list"""
        if not entries:
            return ""
            
        content = []
        for entry in entries:
            name = entry['name']
            link = entry['link']
            views = entry['views']
            content.append(f"    * {views:,} 访问 [{name}]({link})")
        
        content.append("\n")
        return "\n".join(content)

def her_toc_main(format='table', wordcloud=False, start_dir='.'):
    """
    Generate table of contents for the project.
    
    Args:
        format (str): Format to use for TOC ('table' or 'markdown')
        wordcloud (bool): Whether to include wordcloud visualizations
        start_dir (str): Starting directory for TOC generation
        
    Returns:
        str: Success message
    """
    ignore_regexes = load_ignore_patterns()
    toc_generator = TOCGenerator(formatter_type=format)
    toc_generator.process_directory(start_dir, ignore_regexes, wordcloud)
    return f"Table of contents generated successfully using {format} format!"

def main():
    parser = argparse.ArgumentParser(description='Generate table of contents for the project')
    parser.add_argument('--wordcloud', action='store_true', help='Include wordcloud visualizations in the output')
    parser.add_argument('--format', choices=['table', 'markdown'], default='table', 
                      help='Format to use for the table of contents (default: table)')
    args = parser.parse_args()
    
    result = her_toc_main(format=args.format, wordcloud=args.wordcloud)
    print(result)

if __name__ == "__main__":
    main()
