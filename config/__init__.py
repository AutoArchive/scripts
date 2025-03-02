"""
Configuration module for managing project settings and metadata.

This module contains scripts for handling configuration files, catalogs, and project hierarchy.
"""

from .catalog import catalog_main
from .get_md5_list import md5_list_main
from .visitor import visitor_main
from .hierarchy.detect_entry import detect_entry_main

__all__ = ['catalog_main', 'md5_list_main', 'visitor_main', 'detect_entry_main'] 