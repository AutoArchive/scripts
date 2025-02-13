#!/usr/bin/env python3
import json
from pathlib import Path
import os
import yaml
from utils import count_files_recursive, natural_sort_key

class ContentProcessor:
    """Base class for processing different types of content"""
    def __init__(self, entry_generator, entry_formatter):
        self.entry_generator = entry_generator
        self.entry_formatter = entry_formatter
    
    def process(self, items, directory='.', ignore_regexes=None):
        raise NotImplementedError

class FilesProcessor(ContentProcessor):
    """Processes files and categorizes them by type"""
    def __init__(self, entry_generator, entry_formatter):
        super().__init__(entry_generator, entry_formatter)
        self.all_entries = []
        self._processed_paths = set()
        
    def process(self, files, directory='.'):
        # Clear entries for each new directory
        self.all_entries = []
        
        categories = {
            'document': {'0000': []}, 'image': {'0000': []}, 
            'video': {'0000': []}, 'audio': {'0000': []},
            'webpage': {'0000': []}, 'other': {'0000': []}
        }
        
        # Sort and categorize only by type
        for file_info in sorted(files, key=lambda x: natural_sort_key(x['name'])):
            file_type = file_info['type']
            entry_data = self.entry_generator.generate(file_info, directory)
            formatted_entry = self.entry_formatter(entry_data)
            archived_date = file_info.get('archived_date', '0000-12-31')
            
            # Store all content entries with dates
            if entry_data and entry_data['type'] == 'content':
                # Calculate absolute paths for deduplication
                root_dir = os.path.abspath('.')
                current_dir = os.path.abspath(directory)
                rel_dir = os.path.relpath(current_dir, root_dir)
                
                # Create a unique path identifier
                full_path = os.path.normpath(os.path.join(rel_dir, entry_data.get('link', '')))
                
                # Only add if we haven't processed this path before
                if full_path not in self._processed_paths:
                    self._processed_paths.add(full_path)
                    
                    # Update the link to be relative to root
                    entry_data['link'] = full_path.replace(os.sep, '/')
                    
                    # Store entry with its directory info
                    self.all_entries.append({
                        'entry_data': entry_data,
                        'formatted_entry': formatted_entry,
                        'archived_date': archived_date,
                        'current_dir': rel_dir,
                        'file_info': file_info
                    })
            
            categories[file_type]['0000'].append((formatted_entry, archived_date))
            
        return categories

    def clear(self):
        """Clear all stored entries and processed paths"""
        self.all_entries = []
        self._processed_paths = set()

class DirectoryProcessor(ContentProcessor):
    """Processes directories and their metadata"""
    def __init__(self, entry_generator, entry_formatter):
        super().__init__(entry_generator, entry_formatter)
        
    def process(self, subdirs, directory='.', ignore_regexes=None):
        entries = []
        for subdir in sorted(subdirs):
            subdir_info = {
                'name': subdir,
                'count': count_files_recursive(os.path.join(directory, subdir), ignore_regexes)
            }
            
            # Add description if config.yml exists
            subdir_config_path = os.path.join(directory, subdir, 'config.yml')
            if os.path.exists(subdir_config_path):
                try:
                    with open(subdir_config_path, 'r', encoding='utf-8') as f:
                        subdir_config = yaml.safe_load(f)
                        if description := subdir_config.get('description'):
                            subdir_info['description'] = description
                except Exception as e:
                    print(f"Warning: Failed to read config for {subdir}: {e}")
            
            entry_data = self.entry_generator.generate(subdir_info, directory)
            formatted_entry = self.entry_formatter(entry_data)
            entries.append(formatted_entry)
        return entries

class IndependenceProcessor(ContentProcessor):
    """Processes independence repository entries"""
    def __init__(self, entry_generator, entry_formatter):
        super().__init__(entry_generator, entry_formatter)
        
    def process(self, json_path='independence_repo.json', directory='.'):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                independence_data = json.loads(f.read())
                
            entries = []
            for entry in independence_data:
                if result := self.entry_generator.generate(entry, directory):
                    formatted_entry = self.entry_formatter(result)
                    entries.append(formatted_entry)
            return entries
            
        except FileNotFoundError:
            print(f"Warning: independence_repo.json not found")
            return []
        except json.JSONDecodeError:
            print(f"Warning: Failed to parse independence_repo.json")
            return [] 