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
        
    def generate_categorized_toc(self, categories):
        """Generate TOC from categorized content"""
        toc = []
        type_names = {
            'document': '📄 文档', 'image': '🖼️ 图片',
            'video': '🎬 视频', 'audio': '🎵 音频',
            'webpage': '🌐 网页', 'other': '📎 其他'
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
            
        toc_content = self._generate_toc_content(config, directory, ignore_regexes, include_wordcloud)
        
        # Generate and write README
        self._write_readme(directory, config, toc_content)
        
        # Process subdirectories
        for subdir in config.get('subdirs', []):
            subdir_path = os.path.join(directory, subdir)
            self.process_directory(subdir_path, ignore_regexes, include_wordcloud)

    def _generate_toc_content(self, config, directory, ignore_regexes, include_wordcloud):
        """Generate the TOC content for a directory"""
        toc_content = []
        
        # Add header section with metadata
        if 'description' in config:
            toc_content.append(f"{config['description']}\n")
        
        # Add metadata using markdown admonition
        toc_content.append('!!! info "📊 统计信息"\n')
        total_count = count_files_recursive(directory, ignore_regexes)
        toc_content.append(f'    总计内容：{total_count} 篇\n')
        
        if 'tags' in config and config['tags']:
            toc_content.append('    标签：' + " ".join([f"`{tag}`" for tag in config['tags']]) + "\n")
        toc_content.append('\n')

        # Process directories
        if config.get('subdirs'):
            toc_content.append("## 📁 子目录\n")
            dir_entries = self.dir_processor.process(config['subdirs'], directory, ignore_regexes)
            dir_table = self._generate_table(
                headers=[('目录名', '30%'), ('文件数量', '20%'), ('简介', '50%')],
                entries=dir_entries,
                sort_columns=[0, 1]
            )
            toc_content.append(dir_table)

        # Process independence entries
        if directory == '.':
            independence_entries = self.independence_processor.process()
            if independence_entries:
                toc_content.append("## 📚 独立档案库与网站\n")
                independence_table = self._generate_table(
                    headers=[('名称', '70%'), ('内容数量', '30%')],
                    entries=independence_entries,
                    sort_columns=[0, 1]
                )
                toc_content.append(independence_table)

        # Process files by category
        if config.get('files'):
            categories = self.files_processor.process(config['files'], directory)
            files_toc = self.generate_categorized_toc(categories)
            if files_toc:
                toc_content.append("## 📑 文件列表\n")
                toc_content.append(files_toc)
        
        # Add wordcloud using markdown
        if include_wordcloud:
            wordcloud_path = os.path.join(directory, 'abstracts_wordcloud.png')
            if os.path.exists(wordcloud_path):
                toc_content.append('\n## 📊 词云图 { data-search-exclude }\n')
                toc_content.append('![词云图](abstracts_wordcloud.png)\n')
        
        # Add sorting JavaScript with custom sort functions
        toc_content.append('''
<script>
const sortFunctions = {
    year: (a, b, direction) => {
        a = a === '未知' ? '0000' : a;
        b = b === '未知' ? '0000' : b;
        return direction === 'desc' ? b.localeCompare(a) : a.localeCompare(b);
    },
    count: (a, b, direction) => {
        const aNum = parseInt(a.match(/\\d+/)?.[0] || '0');
        const bNum = parseInt(b.match(/\\d+/)?.[0] || '0');
        return direction === 'desc' ? bNum - aNum : aNum - bNum;
    },
    text: (a, b, direction) => {
        return direction === 'desc' 
            ? b.localeCompare(a, 'zh-CN') 
            : a.localeCompare(b, 'zh-CN');
    }
};

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('th[data-sortable="true"]').forEach(th => {
        th.style.cursor = 'pointer';
        th.addEventListener('click', () => sortTable(th));
        
        if (th.getAttribute('data-sort-direction')) {
            sortTable(th, true);
        }
    });
});

function sortTable(th, isInitial = false) {
    const table = th.closest('table');
    const tbody = table.querySelector('tbody');
    const colIndex = Array.from(th.parentNode.children).indexOf(th);
    
    // Store original rows with their sort values
    const rowsWithValues = Array.from(tbody.querySelectorAll('tr')).map(row => ({
        element: row,
        value: row.children[colIndex].textContent.trim(),
        html: row.innerHTML
    }));
    
    // Toggle or set initial sort direction
    const currentDirection = th.getAttribute('data-sort-direction');
    const direction = isInitial ? currentDirection : (currentDirection === 'desc' ? 'asc' : 'desc');
    
    // Update sort indicators
    th.closest('tr').querySelectorAll('th').forEach(header => {
        if (header !== th) {
            header.textContent = header.textContent.replace(/ [▼▲]$/, '');
            header.removeAttribute('data-sort-direction');
        }
    });
    
    th.textContent = th.textContent.replace(/ [▼▲]$/, '') + (direction === 'desc' ? ' ▼' : ' ▲');
    th.setAttribute('data-sort-direction', direction);
    
    // Get sort function based on column type
    const sortType = th.getAttribute('data-sort-type') || 'text';
    const sortFn = sortFunctions[sortType] || sortFunctions.text;
    
    // Sort rows
    rowsWithValues.sort((a, b) => sortFn(a.value, b.value, direction));
    
    // Clear and rebuild tbody
    tbody.innerHTML = '';
    rowsWithValues.forEach(row => {
        const tr = document.createElement('tr');
        tr.innerHTML = row.html;
        tbody.appendChild(tr);
    });
}
</script>
''')
        
        # Add auto-generated note using markdown blockquote
        toc_content.append('\n!!! note "自动生成说明"\n')
        toc_content.append('    目录及摘要为自动生成，仅供索引和参考，请修改 .github/ 目录下的对应脚本、模板或对应文件以更正。\n')
        
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
        exclude_marker = """---
search:
  exclude: true
---


"""
        template_path = get_template_path(directory)
        if template_path:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            updated_content = content.replace('{{TABLE_OF_CONTENTS}}', toc_content)
        else:
            dir_name = config.get('name', os.path.basename(directory))
            updated_content = exclude_marker + f"# {dir_name}\n\n{toc_content}"
        
        readme_path = os.path.join(directory, 'README.md')
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)

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
