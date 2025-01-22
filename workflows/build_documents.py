#!/usr/bin/env python3

import os
import sys
import shutil
import yaml
import argparse
import importlib
import logging
from pathlib import Path
from typing import List, Tuple, Dict

def load_config(config_path):
    """Load configuration from digital.yml"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def clean_directories():
    """Clean docs and workspace/download directories"""
    dirs_to_clean = ['docs', 'workspace/download']
    for dir_path in dirs_to_clean:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
            os.makedirs(dir_path)
            logging.info(f"Cleaned directory: {dir_path}")

def run_script(script_path: str, description: str):
    """Run a Python script and log its execution"""
    logging.info(f"Running {description}...")
    result = os.system(f"{script_path}")
    if result != 0:
        logging.error(f"Script {description} failed with exit code {result}")
        sys.exit(1)
    logging.info(f"{description} completed successfully!")

def get_document_scripts(generate_wordcloud: bool) -> List[Tuple[str, str]]:
    """Get the list of scripts for document building"""
    scripts = [
        ('python .github/scripts/file/rename.py', 'File renaming'),
        ('python .github/scripts/config/hierarchy/detect_entry.py', 'Entry detection'),
        ('python .github/scripts/others/catalog.py', 'Global catalog generation'),
        ('python .github/scripts/others/get_md5_list.py', 'MD5 list generation'),
        ('python .github/scripts/page/gen_page.py', 'Page generation'),
        ('python .github/scripts/ai/archive/gen_file_meta.py', 'File meta generation'),
        ('python .github/scripts/file/add_config.py', 'Metadata addition'),
        ('python .github/scripts/toc/independence_info.py', 'Independence info generation'),
        ('python .github/scripts/page/embed_text.py', 'Text embedding'),
        ('python .github/scripts/ai/archive/gen_dir_meta.py', 'Directory meta generation'),
    ]
    
    if generate_wordcloud:
        scripts.append(('python .github/scripts/page/gen_wordcloud.py', 'Wordcloud generation'))
        scripts.append(('python .github/scripts/toc/her_toc.py --wordcloud', 'Table of contents generation'))
    else:
        scripts.append(('python .github/scripts/toc/her_toc.py', 'Table of contents generation'))
    return scripts

def get_webpage_scripts(generate_wordcloud: bool) -> List[Tuple[str, str]]:
    """Get the list of scripts for webpage building"""
    scripts = [
        ('python .github/scripts/file/rename.py', 'File renaming'),
        ('python .github/scripts/config/hierarchy/detect_entry.py', 'Entry detection'),
        ('python .github/scripts/others/catalog.py', 'Global catalog generation'),
        ('python .github/scripts/others/get_md5_list.py', 'MD5 list generation'),
        ('python .github/scripts/page/gen_page.py', 'Page generation'),
        ('python .github/scripts/others/add_search_exclude.py', 'Search exclude addition'),
        ('python .github/scripts/ai/archive/gen_file_meta.py', 'File meta generation'),
        ('python .github/scripts/file/add_config_from_page.py', 'Metadata addition'),
        ('python .github/scripts/ai/archive/gen_dir_meta.py', 'Directory meta generation'),
    ]
    
    if generate_wordcloud:
        scripts.append(('python .github/scripts/page/gen_wordcloud.py', 'Wordcloud generation'))
        scripts.append(('python .github/scripts/toc/her_toc.py --wordcloud', 'Table of contents generation'))
    else:
        scripts.append(('python .github/scripts/toc/her_toc.py', 'Table of contents generation'))
    
    scripts.extend([
        ('python .github/scripts/file/add_config_from_page.py', 'Second metadata addition'),
    ])
    return scripts

def get_final_scripts() -> List[Tuple[str, str]]:
    """Get the list of final scripts that run for both types"""
    return [
        ('python .github/scripts/file/gen_search_index.py', 'Search index generation'),
        ('python .github/scripts/file/analysis_search_index.py', 'Search index analysis'),
    ]

def main():
    parser = argparse.ArgumentParser(description='Build documents with configuration')
    parser.add_argument('--config', default='digital.yml', help='Path to configuration file')
    parser.add_argument('--type', choices=['document', 'webpage'], default='document',
                      help='Type of build to perform')
    args = parser.parse_args()

    setup_logging()
    config = load_config(args.config)
    build_config = config.get('build_config', {})

    # Set environment variables from config
    os.environ['OPENAI_TEMPERATURE'] = str(build_config.get('openai_temperature', 0.7))

    # Get wordcloud configuration
    generate_wordcloud = build_config.get('generate_wordcloud', False)

    # Clean directories
    clean_directories()

    # Get the appropriate script list based on build type
    scripts = get_document_scripts(generate_wordcloud) if args.type == 'document' else get_webpage_scripts(generate_wordcloud)

    # Execute main scripts
    for script_path, description in scripts:
        run_script(script_path, description)

    # Execute final scripts
    for script_path, description in get_final_scripts():
        run_script(script_path, description)

if __name__ == '__main__':
    main() 