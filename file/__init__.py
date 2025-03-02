"""
File management module.

This module contains scripts for file operations like renaming, cleaning markdown files,
and managing search indices.
"""

from .rename import rename_main
from .add_config import add_config_main
from .add_config_from_page import add_config_from_page_main
from .gen_search_index import gen_search_index_main

__all__ = [
    'rename_main',
    'add_config_main',
    'add_config_from_page_main',
    'gen_search_index_main',
] 