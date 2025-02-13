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
        
        if file_type == 'image':
            return {
                'type': 'image',
                'name': name,
                'filename': filename
            }
        else:
            return self._generate_content_entry(name, page_link, file_info, directory)
    
    def _generate_content_entry(self, name, page_link, file_info, directory):
        year = 'Unknown'
        archived_date = '9999-12-31'
        description = ''
        
        if page := file_info.get('page'):
            page_path = os.path.join(directory, page)
            if os.path.exists(page_path):
                year, archived_date, description = extract_metadata_from_markdown(page_path)
                file_info['year'] = year or 'Unknown'
                file_info['archived_date'] = archived_date or '9999-12-31'
        
        return {
            'type': 'content',
            'name': name,
            'link': page_link,
            'year': year,
            'date': archived_date,
            'description': description
        }

class DirectoryEntryGenerator(EntryGenerator):
    """Generates entries for directories"""
    def generate(self, subdir_info, directory='.'):
        subdir = subdir_info['name']
        file_count = subdir_info['count']
        description = subdir_info.get('description', '')
        last_modified = subdir_info.get('last_modified', '0000-00-00')
        
        return {
            'type': 'directory',
            'name': subdir,
            'count': file_count,
            'description': description,
            'date': last_modified
        }

class IndependenceEntryGenerator(EntryGenerator):
    """Generates entries for independence repositories"""
    def generate(self, entry, directory='.'):
        name = entry.get('name', '')
        url = entry.get('url', '')
        size = entry.get('size', 0)
        
        if name and url and size:
            return {
                'type': 'independence',
                'name': name,
                'url': url,
                'size': size
            }
        return None 