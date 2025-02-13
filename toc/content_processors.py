#!/usr/bin/env python3
import json
from pathlib import Path
import os
import yaml
from utils import count_files_recursive, natural_sort_key

class ContentProcessor:
    """Base class for processing different types of content"""
    def process(self, items, directory='.', ignore_regexes=None):
        raise NotImplementedError

class FilesProcessor(ContentProcessor):
    """Processes files and categorizes them by type and year"""
    def __init__(self, entry_generator):
        self.entry_generator = entry_generator
        
    def process(self, files, directory='.'):
        categories = {
            'document': {}, 'image': {}, 'video': {},
            'audio': {}, 'webpage': {}, 'other': {}
        }
        
        # Sort and categorize
        for file_info in sorted(files, key=lambda x: natural_sort_key(x['name'])):
            file_type = file_info['type']
            entry = self.entry_generator.generate(file_info, directory)
            year = file_info.get('year', '0000') if file_info.get('year') != 'Unknown' else '0000'
            
            if year not in categories[file_type]:
                categories[file_type][year] = []
                
            archived_date = file_info.get('archived_date', '9999-12-31')
            categories[file_type][year].append((entry, archived_date))
            
        return categories

class DirectoryProcessor(ContentProcessor):
    """Processes directories and their metadata"""
    def __init__(self, entry_generator):
        self.entry_generator = entry_generator
        
    def process(self, subdirs, directory='.', ignore_regexes=None):
        entries = []
        for subdir in sorted(subdirs):
            # Create subdir_info dictionary with required information
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
            
            entry = self.entry_generator.generate(subdir_info, directory)
            entries.append(entry)
        return entries

class IndependenceProcessor(ContentProcessor):
    """Processes independence repository entries"""
    def __init__(self, entry_generator):
        self.entry_generator = entry_generator
        
    def process(self, json_path='independence_repo.json', directory='.'):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                independence_data = json.loads(f.read())
                
            entries = []
            for entry in independence_data:
                if result := self.entry_generator.generate(entry, directory):
                    entries.append(result)
            return entries
            
        except FileNotFoundError:
            print(f"Warning: independence_repo.json not found")
            return []
        except json.JSONDecodeError:
            print(f"Warning: Failed to parse independence_repo.json")
            return [] 