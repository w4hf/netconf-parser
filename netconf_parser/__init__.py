"""
Network Configuration Parser Library

A Python library for parsing and analyzing hierarchical network device configurations.
"""

from .models import ConfLine, Conf
from .search import search_line_start_with
from .compare import compare_confs

__version__ = "1.0.0"
__all__ = ["ConfLine", "Conf", "search_line_start_with", "compare_confs"]

