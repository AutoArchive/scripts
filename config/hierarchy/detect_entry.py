#! /usr/bin/env python3
import os
import yaml
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

class EntryDetector:
    def __init__(self):
        self.type_mapping = {
            'document': ['.md', '.txt', '.doc', '.docx', '.pdf'],
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'],
            'video': ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm'],
            'audio': ['.mp3', '.wav', '.ogg', '.m4a'],
            'other': []
        }
        self.changes = []  # Track changes
    
    def calculate_md5(self, filepath: str) -> str:
        """Calculate MD5 hash of a file."""
        md5_hash = hashlib.md5()
        with open(filepath, "rb") as f:
            # Read the file in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
    
    def is_ignored(self, path: str) -> bool:
        """Check if a path is ignored by git."""
        try:
            result = subprocess.run(
                ['git', 'check-ignore', '-q', path],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except subprocess.SubprocessError:
            return False
    
    def should_include_file(self, filepath: str, filename: str) -> bool:
        """Check if a file should be included in config."""
        if filename in {'README.md', 'LICENSE', 'LICENSE.md', '.gitignore', 'config.yml'}:
            return False
        if filename.startswith('.'):
            return False
        if self.is_ignored(filepath):
            return False
        return True
    
    def get_file_type(self, filename: str) -> str:
        """Determine file type based on extension."""
        ext = os.path.splitext(filename)[1].lower()
        for file_type, extensions in self.type_mapping.items():
            if ext in extensions:
                return file_type
        return 'other'
    
    def detect_directory(self, directory: str) -> Dict:
        """Detect and generate config for a directory."""
        config = {
            'name': '' if directory == '.' else os.path.basename(directory),
            'files': [],
            'subdirs': []
        }
        
        # Process files
        for item in sorted(os.listdir(directory)):
            full_path = os.path.join(directory, item)
            
            if os.path.isfile(full_path) and self.should_include_file(full_path, item):
                file_info = {
                    'name': os.path.splitext(item)[0],
                    'filename': item,
                    'type': self.get_file_type(item),
                    'md5': self.calculate_md5(full_path)
                }
                config['files'].append(file_info)
            
            elif os.path.isdir(full_path) and not item.startswith('.') and not self.is_ignored(full_path):
                config['subdirs'].append(item)
        
        return config
    
    def save_config(self, directory: str, config: Dict):
        """Save config to yaml file."""
        config_path = os.path.join(directory, 'config.yml')
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config, f, allow_unicode=True, sort_keys=False)
    
    def load_existing_config(self, directory: str) -> Dict:
        """Load existing config.yml if it exists."""
        config_path = os.path.join(directory, 'config.yml')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return None
    
    def merge_configs(self, old_config: Dict, new_config: Dict, directory: str) -> Dict:
        """Merge old and new configs, tracking changes."""
        if old_config is None:
            return new_config
            
        # Create file lookup from old config
        old_files = {f['filename']: f for f in old_config.get('files', [])}
        
        # Check for file changes
        merged_files = []
        for new_file in new_config['files']:
            filename = new_file['filename']
            full_path = os.path.join(directory, filename)
            
            if filename in old_files:
                old_file = old_files[filename]
                if old_file['md5'] != new_file['md5']:
                    # File content changed
                    self.changes.append(f"Modified: {full_path}")
                    merged_files.append(new_file)
                else:
                    # File unchanged, keep old metadata
                    merged_files.append(old_file)
            else:
                # New file
                self.changes.append(f"Added: {full_path}")
                merged_files.append(new_file)
        
        # Check for deleted files
        for old_filename in old_files:
            if old_filename not in {f['filename'] for f in new_config['files']}:
                self.changes.append(f"Deleted: {os.path.join(directory, old_filename)}")
        
        # Merge configs
        merged_config = old_config.copy()
        merged_config['files'] = merged_files
        merged_config['subdirs'] = new_config['subdirs']  # Update subdirs list
        
        return merged_config
    
    def process_directory_recursive(self, directory: str = '.'):
        """Process directory and its subdirectories recursively."""
        # Load existing config if any
        old_config = self.load_existing_config(directory)
        
        # Generate new config
        new_config = self.detect_directory(directory)
        
        # Merge configs and track changes
        final_config = self.merge_configs(old_config, new_config, directory)
        
        # Only save if there was no previous config or if there are changes
        if old_config is None or self.changes:
            self.save_config(directory, final_config)
        
        # Process subdirectories
        for subdir in final_config['subdirs']:
            subdir_path = os.path.join(directory, subdir)
            self.process_directory_recursive(subdir_path)

def main():
    detector = EntryDetector()
    detector.process_directory_recursive()
    
    # Print changes if any
    if detector.changes:
        print("\nDetected changes:")
        for change in detector.changes:
            print(change)
    else:
        print("\nNo changes detected.")

if __name__ == "__main__":
    main()
