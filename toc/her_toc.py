#!/usr/bin/env python3
import os
import yaml
import argparse
from utils import *
from entry_generators import *
from content_processors import *
import pandas as pd
import requests
from io import StringIO

class TOCGenerator:
    """Generates table of contents for directories and files"""
    def __init__(self):
        # Initialize generators
        self.file_generator = FileEntryGenerator()
        self.dir_generator = DirectoryEntryGenerator()
        self.independence_generator = IndependenceEntryGenerator()
        
        # Initialize processors with generators and formatter
        self.files_processor = FilesProcessor(self.file_generator, self._format_entry)
        self.dir_processor = DirectoryProcessor(self.dir_generator, self._format_entry)
        self.independence_processor = IndependenceProcessor(self.independence_generator, self._format_entry)
        
        # Add a list to store all entries
        self.all_entries = []
        
        # Add GA data processing
        self.ga_data = self._load_ga_data()
        
        # Initialize current directory
        self.current_directory = '.'

    def generate_categorized_toc(self, categories):
        """Generate TOC from categorized content"""
        toc = []
        type_names = {
            'webpage': '🌐 网页', 'other': '📎 其他',
            'document': '📄 文档', 'image': '🖼️ 图片',
            'video': '🎬 视频', 'audio': '🎵 音频'
        }
        
        for file_type, years in categories.items():
            all_entries = []
            for year_entries in years.values():
                all_entries.extend(entry for entry, _ in year_entries)
            
            if not all_entries:
                continue
            
            toc.append(f"\n### {type_names[file_type]}\n")
            content_table = self._generate_table(
                headers=[('标题', '40%'), ('年份', '15%'), ('摘要', '45%')],
                entries=all_entries,
                sort_columns=[0, 1],
                default_sort={'column': 1, 'direction': 'desc', 'type': 'year'}
            )
            toc.append(content_table)
        
        return "\n".join(toc)

    def process_directory(self, directory, ignore_regexes, include_wordcloud=False):
        """Process a directory to generate README.md based on config.yml"""
        if is_ignored(directory, ignore_regexes):
            print(f"Skipping ignored directory: {directory}")
            return

        # Update current directory
        self.current_directory = directory

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
            # Store entries with path relative to current directory
            for entry in self.files_processor.all_entries:
                entry['current_dir'] = directory
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
            dir_table = self._generate_table(
                headers=[('目录名', '30%'), ('文件数量', '20%'), ('简介', '50%')],
                entries=dir_entries,
                sort_columns=[0, 1]
            )
            toc_content.append(dir_table)

        # Add wordcloud using markdown
        if include_wordcloud:
            wordcloud_path = os.path.join(directory, 'abstracts_wordcloud.png')
            if os.path.exists(wordcloud_path):
                toc_content.append('\n## 📊 词云图 { data-search-exclude }\n')
                toc_content.append('![词云图](abstracts_wordcloud.png)\n')
        
        # Add sorting script
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
        
        def truncate_text(text, length=50):
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
                summary = truncate_text(entry['description'])
                description_html = f'''<details>
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
                summary = truncate_text(entry['description'])
                description_html = f'''<details>
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

    def _generate_table(self, headers, entries, sort_columns=None, default_sort=None):
        """Generate a sortable HTML table
        Args:
            headers: List of column headers [(name, width), ...]
            entries: List of formatted entry strings
            sort_columns: List of column indices that should be sortable (0-based)
            default_sort: Dict with {'column': idx, 'direction': 'desc', 'type': 'year|name|count'}
        """
        sort_columns = sort_columns or []
        table = ['<table>']
        
        # Generate header
        table.append('<thead><tr>')
        for idx, (header, width) in enumerate(headers):
            if idx in sort_columns:
                is_default = default_sort and default_sort['column'] == idx
                direction = default_sort['direction'] if is_default else 'asc'
                sort_type = default_sort['type'] if is_default else 'text'
                indicator = ' ▼' if direction == 'desc' else ' ▲' if direction == 'asc' else ''
                table.append(
                    f'<th style="width: {width}" data-sortable="true" '
                    f'data-sort-direction="{direction}" data-sort-type="{sort_type}">'
                    f'{header}{indicator}</th>'
                )
            else:
                table.append(f'<th style="width: {width}">{header}</th>')
        table.append('</tr></thead>')
        
        # Add entries
        table.append('<tbody>')
        table.extend(entries)
        table.append('</tbody>')
        table.append('</table>\n')
        
        return '\n'.join(table)

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
        """Get the most visited content entries"""
        if self.ga_data is None or not self.all_entries:
            print("Debug: No GA data or no entries")
            return []
            
        all_matches = []  # Store all matches first
        root_dir = os.path.abspath('.')
        
        for _, row in self.ga_data.iterrows():
            ga_path = row['clean_path']
            views = int(row['Views'])
            if ga_path == '':
                continue
            
            # Find matching content entry
            matching_entry = None
            for entry in self.all_entries:
                if 'entry_data' not in entry or 'current_dir' not in entry:
                    continue
                    
                # Get the link and normalize it
                entry_link = entry['entry_data'].get('link', '')
                if entry_link.endswith('.md'):
                    entry_link = entry_link[:-3]
                
                # Join path parts and normalize
                entry_path = entry_link
                
                # Try exact match
                if ga_path == entry_path:
                    print(f"    Found exact match! {entry_path}")
                    matching_entry = entry
                    break
            
            if matching_entry:
                # Calculate relative link from current directory
                rel_link = os.path.relpath(
                    os.path.join(matching_entry['current_dir'], matching_entry['entry_data']['link']),
                    self.current_directory
                ).replace(os.sep, '/')
                
                all_matches.append({
                    'name': matching_entry['entry_data']['name'],
                    'link': rel_link,
                    'views': views
                })
        
        # Sort all matches by views and get top entries
        sorted_matches = sorted(all_matches, key=lambda x: x['views'], reverse=True)
        top_entries = sorted_matches[:limit]
        
        print(f"\nDebug: Found {len(all_matches)} matches total")
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

def main():
    parser = argparse.ArgumentParser(description='Generate table of contents for the project')
    parser.add_argument('--wordcloud', action='store_true', help='Include wordcloud visualizations in the output')
    args = parser.parse_args()
    
    ignore_regexes = load_ignore_patterns()
    toc_generator = TOCGenerator()
    toc_generator.process_directory('.', ignore_regexes, args.wordcloud)
    print("Table of contents generated successfully!")

if __name__ == "__main__":
    main()
