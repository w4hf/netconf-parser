"""
Search functionality for configuration lines.
"""

from .models import Conf, ConfLine


def search_line_start_with(
    conf: Conf,
    search_string: str,
    level: int,
    parent_start_with: str | None = None
) -> list[ConfLine]:
    """
    Search for configuration lines matching specific criteria.
    
    Args:
        conf: The Conf object to search in
        search_string: String that the line content must start with
        level: The level that matching lines must have
        parent_start_with: Optional string that the parent line must start with
        
    Returns:
        List of ConfLine objects matching all criteria
    """
    results = []
    
    for line in conf.lines:
        # Check if line matches the level
        if line.level != level:
            continue
        
        # Check if line content starts with search_string
        line_text = " ".join(line.content)
        if not line_text.startswith(search_string):
            continue
        
        # If parent filter is specified, check parent
        if parent_start_with is not None:
            if not line.has_parent:
                continue
            parent_text = " ".join(line.parent.content)
            if not parent_text.startswith(parent_start_with):
                continue
        
        results.append(line)
    
    return results

