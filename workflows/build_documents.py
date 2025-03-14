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

# Add parent directory to Python path for relative imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from scripts.toc.her_toc import her_toc_main
from scripts.file.rename import rename_main
from scripts.config.hierarchy.detect_entry import detect_entry_main
from scripts.config.catalog import catalog_main
from scripts.config.get_md5_list import md5_list_main
from scripts.config.visitor import visitor_main
from scripts.page.gen_page import gen_page_main
from scripts.ai.archive.gen_file_meta import gen_file_meta_main
from scripts.file.add_config import add_config_main
from scripts.toc.independence_info import independence_info_main
from scripts.page.embed_text import embed_text_main
from scripts.ai.archive.gen_dir_meta import gen_dir_meta_main
from scripts.page.gen_wordcloud import gen_wordcloud_main
from scripts.page.add_search_exclude import add_search_exclude_main
from scripts.file.add_config_from_page import add_config_from_page_main
from scripts.file.gen_search_index import gen_search_index_main

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

def get_document_scripts(generate_wordcloud: bool) -> List[Tuple[callable, str]]:
    """Get the list of scripts for document building"""
    # Start with common initial scripts
    scripts = [
        (rename_main, 'File renaming'),
        (detect_entry_main, 'Entry detection'),
        (catalog_main, 'Catalog generation'),
        (md5_list_main, 'MD5 list generation'),
        (visitor_main, 'Visitor count update'),
        (gen_page_main, 'Page generation'),
        (gen_file_meta_main, 'File meta generation'),
        (add_config_main, 'Metadata addition'),
        (independence_info_main, 'Independence info generation'),
        (embed_text_main, 'Text embedding'),
        (gen_dir_meta_main, 'Directory meta generation'),
    ]
    
    if generate_wordcloud:
        scripts.append((gen_wordcloud_main, 'Wordcloud generation'))
    
    # Add final scripts
    scripts.extend([
        (gen_search_index_main, 'Search index generation'),
    ])
    
    return scripts

def get_webpage_scripts(generate_wordcloud: bool) -> List[Tuple[callable, str]]:
    """Get the list of scripts for webpage building"""
    # Start with common initial scripts
    scripts = [
        (rename_main, 'File renaming'),
        (detect_entry_main, 'Entry detection'),
        (catalog_main, 'Catalog generation'),
        (md5_list_main, 'MD5 list generation'),
        (visitor_main, 'Visitor count update'),
        (gen_page_main, 'Page generation'),
        (add_search_exclude_main, 'Search exclude addition'),
        (gen_file_meta_main, 'File meta generation'),
        (add_config_from_page_main, 'Metadata addition'),
        (gen_dir_meta_main, 'Directory meta generation'),
    ]

    if generate_wordcloud:
        scripts.append((gen_wordcloud_main, 'Wordcloud generation'))
    
    scripts.extend([
        (add_config_from_page_main, 'Second metadata addition'),
        (gen_search_index_main, 'Search index generation'),
    ])
    
    return scripts

def get_all_available_scripts() -> Dict[str, callable]:
    """Get a dictionary of all available scripts with their normalized names as keys"""
    all_scripts = {
        'file_renaming': rename_main,
        'entry_detection': detect_entry_main,
        'catalog_generation': catalog_main,
        'md5_list_generation': md5_list_main,
        'visitor_count_update': visitor_main,
        'page_generation': gen_page_main,
        'file_meta_generation': gen_file_meta_main,
        'metadata_addition': add_config_main,
        'config_from_page': add_config_from_page_main,
        'independence_info_generation': independence_info_main,
        'text_embedding': embed_text_main,
        'directory_meta_generation': gen_dir_meta_main,
        'wordcloud_generation': gen_wordcloud_main,
        'search_exclude_addition': add_search_exclude_main,
        'search_index_generation': gen_search_index_main,
        'table_of_contents': her_toc_main
    }
    return all_scripts

def get_script_choices() -> List[str]:
    """Get a list of all available script choices for the argument parser"""
    return list(get_all_available_scripts().keys())

def main():
    # Get all available script choices for the help text
    script_choices = get_script_choices()
    
    parser = argparse.ArgumentParser(description='Build documents with configuration')
    parser.add_argument('--config', default='digital.yml', help='Path to configuration file')
    parser.add_argument('--type', choices=['document', 'webpage'], default='document',
                      help='Type of build to perform')
    parser.add_argument('--script', choices=script_choices, 
                      help='Run only a specific script instead of the full workflow')
    parser.add_argument('--no-clean', action='store_true', 
                      help='Do not clean directories before running (useful with --script)')
    args = parser.parse_args()

    setup_logging()
    config = load_config(args.config)
    build_config = config.get('build_config', {})

    # Set environment variables from config
    os.environ['OPENAI_TEMPERATURE'] = str(build_config.get('openai_temperature', 0.7))

    # Get wordcloud configuration
    generate_wordcloud = build_config.get('generate_wordcloud', False)

    # Clean directories if not using --no-clean
    if not args.no_clean:
        clean_directories()

    # If a specific script is requested, run only that script
    if args.script:
        all_scripts = get_all_available_scripts()
        script_func = all_scripts.get(args.script)
        
        if not script_func:
            logging.error(f"Script '{args.script}' not found")
            sys.exit(1)
            
        logging.info(f"Running single script: {args.script}...")
        try:
            # Special handling for table_of_contents which has different parameters
            if args.script == 'table_of_contents':
                script_func(format='table', wordcloud=generate_wordcloud, start_dir='.')
            else:
                script_func('.')
            logging.info(f"Script '{args.script}' completed successfully!")
        except Exception as e:
            logging.error(f"Script '{args.script}' failed: {e}")
            sys.exit(1)
        return

    # Get the appropriate script list based on build type
    scripts = get_document_scripts(generate_wordcloud) if args.type == 'document' else get_webpage_scripts(generate_wordcloud)

    # Execute scripts
    for script_func, description in scripts:
        logging.info(f"Running {description}...")
        try:
            script_func('.')
            logging.info(f"{description} completed!")
        except Exception as e:
            logging.error(f"Script {description} failed: {e}")
            sys.exit(1)

    # Generate table of contents using her_toc module
    logging.info("Generating table of contents...")
    her_toc_main(format='table', wordcloud=generate_wordcloud, start_dir='.')
    logging.info("Table of contents generation completed!")

if __name__ == '__main__':
    main() 