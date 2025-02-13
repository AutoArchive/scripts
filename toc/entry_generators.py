#!/usr/bin/env python3
import os
from utils import extract_metadata_from_markdown, natural_sort_key

class EntryGenerator:
    """Base class for generating entries"""
    def generate(self, item, directory='.'):
        raise NotImplementedError

class FileEntryGenerator(EntryGenerator):
    """Generates entries for files with metadata"""
    def generate(self, file_info, directory='.'):
        name = file_info.get('name', 'Unknown') or 'Unknown'
        filename = file_info.get('filename', 'Unknown') or 'Unknown'
        file_type = file_info.get('type', 'Unknown') or 'Unknown'
        
        page_link = file_info.get('page', filename) if file_type != 'image' else filename
        entry = ""
        
        if file_type == 'image':
            entry = f"\n![{name}]({filename})\n"
        else:
            entry = f"\n\n[{name}]({page_link})"
            
            if page := file_info.get('page'):
                page_path = os.path.join(directory, page)
                if os.path.exists(page_path):
                    year, archived_date, description = extract_metadata_from_markdown(page_path)
                    if description:
                        entry += f"<details><summary>查看摘要</summary>\n\n{description}\n</details>\n\n"
                    file_info['year'] = year or 'Unknown'
                    file_info['archived_date'] = archived_date or '9999-12-31'
                    
        return entry

class DirectoryEntryGenerator(EntryGenerator):
    """Generates entries for directories"""
    def generate(self, subdir_info, directory='.'):
        subdir, file_count = subdir_info['name'], subdir_info['count']
        subdir_path = os.path.join(directory, subdir)
        entry = f"- [{subdir}]({subdir}) ({file_count} 篇内容)"
        
        # Add details/summary if subdir has config.yml with description
        if description := subdir_info.get('description'):
            entry += f"\n  <details><summary>内容简介</summary>\n\n  {description}\n  </details>"
        
        return entry

class IndependenceEntryGenerator(EntryGenerator):
    """Generates entries for independence repositories"""
    def generate(self, entry, directory='.'):
        name = entry.get('name', '')
        url = entry.get('url', '')
        size = entry.get('size', 0)
        
        if name and url and size:
            return f"- [{name}: {url}]({url}) ({size} 篇内容)"
        return None 