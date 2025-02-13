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
        # Initialize generators and processors
        self.file_generator = FileEntryGenerator()
        self.dir_generator = DirectoryEntryGenerator()
        self.independence_generator = IndependenceEntryGenerator()
        
        self.files_processor = FilesProcessor(self.file_generator)
        self.dir_processor = DirectoryProcessor(self.dir_generator)
        self.independence_processor = IndependenceProcessor(self.independence_generator)
        
    def generate_categorized_toc(self, categories):
        """Generate TOC from categorized content"""
        toc = []
        type_names = {
            'document': '📄 文档', 'image': '🖼️ 图片',
            'video': '🎬 视频', 'audio': '🎵 音频',
            'webpage': '🌐 网页', 'other': '📎 其他'
        }
        
        def sort_key(entry_tuple):
            entry, date = entry_tuple
            return date if date else '9999-12-31'
        
        for file_type, years in categories.items():
            if years:
                toc.append(f"\n### {type_names[file_type]}\n")
                for year in sorted(years.keys(), reverse=True):
                    if years[year]:
                        display_year = '时间未知，按收录顺序排列' if year == '0000' else year
                        toc.append(f"\n#### {display_year}\n")
                        sorted_entries = sorted(years[year], key=sort_key)
                        toc.extend(entry for entry, _ in sorted_entries)
        
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
        
        # Add basic information
        if 'description' in config:
            toc_content.append(f"{config['description']}\n")
        if 'tags' in config and config['tags']:
            toc_content.append("\n标签: " + ", ".join([f"`{tag}`" for tag in config['tags']]) + "\n")
            
        total_count = count_files_recursive(directory, ignore_regexes)
        toc_content.append(f"\n总计 {total_count} 篇内容\n\n")

        # Process directories
        if config.get('subdirs'):
            toc_content.append("### 📁 子目录\n")
            dir_entries = self.dir_processor.process(config['subdirs'], directory, ignore_regexes)
            toc_content.extend(dir_entries)
            toc_content.append("")

        # Process independence entries
        if directory == '.':
            independence_entries = self.independence_processor.process()
            if independence_entries:
                toc_content.append("### 📚 独立档案库与网站\n")
                toc_content.extend(independence_entries)
                toc_content.append("")

        # Process files
        if config.get('files'):
            categories = self.files_processor.process(config['files'], directory)
            files_toc = self.generate_categorized_toc(categories)
            if files_toc:
                toc_content.append(files_toc)
        
        # Add wordcloud if enabled
        if include_wordcloud:
            wordcloud_path = os.path.join(directory, 'abstracts_wordcloud.png')
            if os.path.exists(wordcloud_path):
                toc_content.append('\n\n### 词云图 { data-search-exclude }\n' + 
                                 f'\n![{directory}摘要词云图](abstracts_wordcloud.png)\n')
        
        # Add auto-generated note
        toc_content.append("\n> 目录及摘要为自动生成，仅供索引和参考，请修改 .github/ 目录下的对应脚本、模板或对应文件以更正。\n")
        
        return "\n".join(toc_content)

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
