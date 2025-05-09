#! /usr/bin/env python3
import os
import yaml
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import datetime
import re  # Add this import at the top

class EntryDetector:
    def __init__(self):
        self.type_mapping = {
            'webpage': ['.html', '.md', '.htm'],
            'document': ['.txt', '.doc', '.docx', '.pdf', '.epub'],
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'],
            'video': ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm'],
            'audio': ['.mp3', '.wav', '.ogg', '.m4a'],
            'other': []
        }
        self.format_mapping = {
            # Documents
            '.pdf': 'PDF Document',
            '.doc': 'Microsoft Word Document',
            '.docx': 'Microsoft Word Document (OpenXML)',
            '.txt': 'Plain Text',
            '.md': 'Markdown',
            '.epub': 'EPUB Document',
            # Images
            '.jpg': 'JPEG Image',
            '.jpeg': 'JPEG Image',
            '.png': 'PNG Image',
            '.gif': 'GIF Image',
            '.webp': 'WebP Image',
            # Video
            '.mp4': 'MPEG-4 Video',
            '.avi': 'AVI Video',
            '.mov': 'QuickTime Video',
            '.webm': 'WebM Video',
            # Audio
            '.mp3': 'MP3 Audio',
            '.wav': 'WAV Audio',
            '.ogg': 'OGG Audio',
            '.m4a': 'M4A Audio',
        }
        self.changes = []  # Track changes

        # Load ignore list from digital.yml and compile regex patterns
        with open('digital.yml', 'r', encoding='utf-8') as f:
            digital_config = yaml.safe_load(f)
        ignore_patterns = digital_config.get('ignore', [])
        self.ignore_regexes = [re.compile(pattern) for pattern in ignore_patterns]
    
    def calculate_md5(self, filepath: str) -> str:
        """Calculate MD5 hash of a file."""
        md5_hash = hashlib.md5()
        with open(filepath, "rb") as f:
            # Read the file in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
    
    def is_ignored(self, path: str) -> bool:
        """Check if a path matches any ignore pattern or is git-ignored."""
        normalized_path = os.path.normpath(path)

        # Check if any ignore regex matches the path
        for regex in self.ignore_regexes:
            if regex.search(normalized_path):
                print(f"Ignore: {path} (matched pattern: {regex.pattern})")
                return True

        # Check if path is git-ignored
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
        if filename in {'README.md', 'LICENSE', 'LICENSE.md', '.gitignore', 'config.yml', 'CONTRIBUTING.md', 'CODE_OF_CONDUCT.md'}:
            return False
        if filename.startswith('.'):
            return False
        if filename.endswith('_page.md'):  # Ignore files ending with _page.md
            return False
        if filename.endswith('.conf'):  # Ignore files ending with .conf
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
    
    def get_file_format(self, filepath: str) -> str:
        """Get detailed format information using file extension."""
        ext = os.path.splitext(filepath)[1].lower()
        return self.format_mapping.get(ext, 'Unknown Format')
    
    def format_timestamp(self, timestamp: float) -> str:
        """Convert a Unix timestamp to a human-readable date string."""
        return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    
    def detect_directory(self, directory: str) -> Dict:
        """Detect and generate config for a directory."""
        config = {
            # Directory-level metadata
            'name': '' if directory == '.' else os.path.basename(directory),
            'description': '',  # Collection description
            'curator': '',  # Person/org managing this collection
            'source': '',  # Source organization/archive
            'tags': [],  # Collection categories/themes
            'license': '',  # Overall collection license

            # Structure
            'files': [],
            'subdirs': []
        }
        
        # Process files
        for item in sorted(os.listdir(directory)):
            full_path = os.path.join(directory, item)
            
            if os.path.isfile(full_path) and self.should_include_file(full_path, item):
                file_info = {
                    # File identification
                    'name': os.path.splitext(item)[0],
                    'filename': item,

                    'type': self.get_file_type(item),
                    'format': self.get_file_format(full_path),
                    'size': os.path.getsize(full_path),
                    'md5': self.calculate_md5(full_path),
                }
                config['files'].append(file_info)
            
            elif os.path.isdir(full_path) and not item.startswith('.') and not self.is_ignored(full_path) and 'workspace' not in item:
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
        """Merge old and new configs, ensuring new fields are added."""
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
                # Preserve existing metadata but add new fields
                merged_file = new_file.copy()
                for key in old_file:
                    if key in old_file and old_file[key]:  # Only preserve non-empty values
                        merged_file[key] = old_file[key]
                merged_files.append(merged_file)
            else:
                # New file
                self.changes.append(f"Added: {full_path}")
                merged_files.append(new_file)
        
        # Check for deleted files
        for old_filename in old_files:
            if old_filename not in {f['filename'] for f in new_config['files']}:
                self.changes.append(f"Deleted: {os.path.join(directory, old_filename)}")
                # The file is not added to merged_files, effectively removing it from the config
        
        # Merge directory-level configs
        merged_config = new_config.copy()  # Start with new config to get any new fields
        for key in old_config:
            if key not in ['files', 'subdirs'] and old_config[key]:  # Preserve non-empty values
                merged_config[key] = old_config[key]
        
        merged_config['files'] = merged_files
        
        return merged_config
    
    def process_directory_recursive(self, directory: str = '.'):
        """Process directory and its subdirectories recursively."""
        if self.is_ignored(directory):
            print(f"Ignore: {directory}")
            return
        # Load existing config if any
        old_config = self.load_existing_config(directory)
        
        # Generate new config
        new_config = self.detect_directory(directory)
        
        # Merge configs and track changes
        final_config = self.merge_configs(old_config, new_config, directory)
        
        # Only save if there was no previous config or if there are changes
        self.save_config(directory, final_config)
        
        # Process subdirectories
        for subdir in final_config['subdirs']:
            subdir_path = os.path.join(directory, subdir)
            self.process_directory_recursive(subdir_path)

def detect_entry_main(base_dir: str = '.', digital_yml_path: Optional[str] = None) -> List[str]:
    """
    Main function to detect and process entries in the directory structure.
    
    Args:
        base_dir (str): Base directory to start processing from
        digital_yml_path (Optional[str]): Path to digital.yml file. If None, uses 'digital.yml' in base_dir
        
    Returns:
        List[str]: List of changes made during processing
    """
    if digital_yml_path is None:
        digital_yml_path = os.path.join(base_dir, 'digital.yml')
        
    detector = EntryDetector()
    os.chdir(base_dir)  # Change to base directory
    detector.process_directory_recursive()
    
    # Return changes if any
    if detector.changes:
        print("\nDetected changes:")
        for change in detector.changes:
            print(change)
    else:
        print("\nNo changes detected.")
        
    return detector.changes

if __name__ == "__main__":
    main()
