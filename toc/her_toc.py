#!/usr/bin/env python3
import os
import yaml
import argparse
from utils import *
from entry_generators import *
from content_processors import *

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
        
        # Generate and write README
        self._write_readme(directory, config, toc_content)

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

    def _write_readme(self, directory, config, toc_content):
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
            self.all_entries,
            key=lambda x: x['archived_date'],
            reverse=True
        )[:10]
        
        # Use the directory where README is being written
        current_dir = self.current_directory  # We'll set this in _write_readme
        for entry in latest_entries:
            entry_data = entry['entry_data']
            date = entry['archived_date'][:10]  # Get just the date part
            # Make link relative to current directory
            link = os.path.relpath(
                os.path.join(entry['current_dir'], entry_data['link']),
                current_dir
            )
            content.append(f"- {date} [{entry_data['name']}]({link})")
        
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
