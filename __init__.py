"""
Scripts package for futa-novel project.

This package contains various scripts for building, processing and managing the futa-novel project.
It includes tools for file management, page generation, AI processing, and more.
"""

__version__ = '1.0.0'

# Import commonly used functions for easier access
from .toc.her_toc import her_toc_main
from .file.rename import rename_main

__all__ = ['her_toc_main', 'rename_main'] 