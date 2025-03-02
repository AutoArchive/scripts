#!/usr/bin/env python3
from abc import ABC, abstractmethod

class TOCFormatter(ABC):
    """Base class for different TOC formatting styles"""
    
    @abstractmethod
    def format_categorized_content(self, categories, type_names):
        """Format categorized content into a TOC"""
        pass
        
    @abstractmethod
    def format_directory_content(self, dir_entries):
        """Format directory entries into a TOC"""
        pass


class TableTOCFormatter(TOCFormatter):
    """Formats TOC content as HTML tables with sorting capabilities"""
    
    def __init__(self):
        self.type_names = {
            'webpage': '🌐 网页', 'other': '📎 其他',
            'document': '📄 文档', 'image': '🖼️ 图片',
            'video': '🎬 视频', 'audio': '🎵 音频'
        }
    
    def format_categorized_content(self, categories, type_names=None):
        """Format categorized file content into sortable tables"""
        if type_names:
            self.type_names = type_names
            
        toc = []
        
        for file_type, years in categories.items():
            all_entries = []
            for year_entries in years.values():
                all_entries.extend(entry for entry, _ in year_entries)
            
            if not all_entries:
                continue
            
            toc.append(f"\n### {self.type_names[file_type]}\n")
            content_table = self._generate_table(
                headers=[('标题', '40%'), ('年份', '15%'), ('摘要', '45%')],
                entries=all_entries,
                sort_columns=[0, 1],
                default_sort={'column': 1, 'direction': 'desc', 'type': 'year'}
            )
            toc.append(content_table)
        
        return "\n".join(toc)
    
    def format_directory_content(self, dir_entries):
        """Format directory entries into a sortable table"""
        if not dir_entries:
            return ""
            
        return self._generate_table(
            headers=[('目录名', '30%'), ('文件数量', '20%'), ('简介', '50%')],
            entries=dir_entries,
            sort_columns=[0, 1]
        )
    
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


class MarkdownListTOCFormatter(TOCFormatter):
    """Formats TOC content as simple markdown lists with file counts"""
    
    def __init__(self):
        self.type_names = {
            'webpage': '🌐 网页', 'other': '📎 其他',
            'document': '📄 文档', 'image': '🖼️ 图片',
            'video': '🎬 视频', 'audio': '🎵 音频'
        }
    
    def format_categorized_content(self, categories, type_names=None):
        """Format categorized file content into markdown lists"""
        if type_names:
            self.type_names = type_names
            
        toc = []
        
        for file_type, years in categories.items():
            # Collect all entries for this file type
            all_entries = []
            for year_entries in years.values():
                all_entries.extend(entry for entry, _ in year_entries)
            
            if not all_entries:
                continue
            
            # Add category header
            toc.append(f"\n### {self.type_names[file_type]} ({len(all_entries)} 篇)\n")
            
            # Extract links from HTML entries and convert to markdown list items
            for entry_html in all_entries:
                # Extract name and link using simple parsing - this assumes specific format from entry generator
                link_match = entry_html.split('<a href="')[1].split('"')[0]
                name_match = entry_html.split('class="md-button">')[1].split('</a>')[0]
                
                toc.append(f"- [{name_match}]({link_match})")
            
            toc.append("")  # Add empty line after each category
        
        return "\n".join(toc)
    
    def format_directory_content(self, dir_entries):
        """Format directory entries into a markdown list"""
        if not dir_entries:
            return ""
            
        toc = []
        
        # Extract directory info from HTML entries and convert to markdown list items
        for entry_html in dir_entries:
            # Extract directory name, count and link
            link_match = entry_html.split('<a href="')[1].split('"')[0] 
            name_match = entry_html.split('class="md-button">')[1].split('</a>')[0]
            count_match = entry_html.split('class="count-cell">')[1].split('</td>')[0].strip()
            
            toc.append(f"- [{name_match}]({link_match}) ({count_match})")
        
        toc.append("")  # Add empty line at the end
        return "\n".join(toc)