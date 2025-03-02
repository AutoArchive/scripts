"""
Page generation module.

This module contains scripts for generating pages, embedding text,
and creating word clouds.
"""

from .gen_page import gen_page_main
from .embed_text import embed_text_main
from .gen_wordcloud import gen_wordcloud_main
from .add_search_exclude import add_search_exclude_main

__all__ = ['gen_page_main', 'embed_text_main', 'gen_wordcloud_main', 'add_search_exclude_main'] 