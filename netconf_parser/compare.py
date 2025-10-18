"""
Configuration comparison functionality.
"""

import re
from .models import Conf, ConfLine


def _line_matches_regex(line: ConfLine, regex_pattern: str) -> bool:
    """
    Check if a line matches the ignore regex pattern.
    
    Args:
        line: The ConfLine to check
        regex_pattern: The regex pattern to match against
        
    Returns:
        True if the line matches the pattern (should be ignored)
    """
    if not regex_pattern:
        return False
    
    line_text = " ".join(line.content)
    try:
        return bool(re.search(regex_pattern, line_text))
    except re.error:
        return False


def _get_line_signature(line: ConfLine) -> str:
    """
    Get a signature for a line based on its full path (parent chain + content).
    
    Args:
        line: The ConfLine to get signature for
        
    Returns:
        String signature including parent path and content
    """
    path_parts = []
    current = line.parent
    while current is not None:
        path_parts.insert(0, " ".join(current.content))
        current = current.parent
    
    path_parts.append(" ".join(line.content))
    return " > ".join(path_parts)


def _get_line_start(line: ConfLine) -> str:
    """
    Get the starting keyword(s) of a line.
    
    Args:
        line: The ConfLine to get start from
        
    Returns:
        The first word of the line content
    """
    return line.content[0] if line.content else ""


def _lines_match_start(line1: ConfLine, line2: ConfLine) -> bool:
    """
    Check if two lines start with the same keyword.
    
    Args:
        line1: First ConfLine
        line2: Second ConfLine
        
    Returns:
        True if both lines start with the same keyword
    """
    return _get_line_start(line1) == _get_line_start(line2)


def _lines_exact_match(line1: ConfLine, line2: ConfLine) -> bool:
    """
    Check if two lines have exactly the same content.
    
    Args:
        line1: First ConfLine
        line2: Second ConfLine
        
    Returns:
        True if both lines have identical content
    """
    return line1.content == line2.content


def _parent_signature(line: ConfLine) -> str:
    """
    Get the full parent path signature for a line.
    
    Args:
        line: The ConfLine to get parent signature for
        
    Returns:
        String representing the full parent path
    """
    if not line.has_parent:
        return ""
    
    path_parts = []
    current = line.parent
    while current is not None:
        path_parts.insert(0, " ".join(current.content))
        current = current.parent
    
    return " > ".join(path_parts)




def _compare_children_of_parent(
    ref_parent: ConfLine, 
    cmp_parent: ConfLine,
    all_diffs: list
) -> None:
    """
    Compare children of two matching parent lines and collect all differences.
    
    This function compares direct children and recursively compares their descendants,
    adding each level's differences as separate entries in all_diffs list.
    
    Args:
        ref_parent: Parent line from reference config
        cmp_parent: Corresponding parent line from compared config
        all_diffs: List to accumulate all parent-level differences
    """
    result = {
        "parent": ref_parent,  # Use reference parent as the common parent
        "added_children": [],
        "deleted_children": [],
        "modified_children": []
    }
    
    matched_ref_children = set()
    matched_cmp_children = set()
    
    # Match children by starting keywords (same level only)
    for ref_child in ref_parent.children:
        best_match = None
        for cmp_child in cmp_parent.children:
            if cmp_child in matched_cmp_children:
                continue
            if ref_child.level == cmp_child.level and _lines_match_start(ref_child, cmp_child):
                best_match = cmp_child
                break
        
        if best_match:
            matched_ref_children.add(ref_child)
            matched_cmp_children.add(best_match)
            
            if not _lines_exact_match(ref_child, best_match):
                # Children are modified
                result["modified_children"].append({
                    "reference": ref_child,
                    "compared": best_match
                })
                # DON'T recursively compare grandchildren if parent is modified
                # Only compare children when parents are EXACTLY the same
            else:
                # Parents are exactly the same - recursively compare their children
                if ref_child.has_children or best_match.has_children:
                    _compare_children_of_parent(ref_child, best_match, all_diffs)
    
    # Find deleted children (direct children only, same level)
    for ref_child in ref_parent.children:
        if ref_child not in matched_ref_children:
            result["deleted_children"].append(ref_child)
    
    # Find added children (direct children only, same level)
    for cmp_child in cmp_parent.children:
        if cmp_child not in matched_cmp_children:
            result["added_children"].append(cmp_child)
    
    # Only add to all_diffs if there are differences
    if (result["added_children"] or 
        result["deleted_children"] or 
        result["modified_children"]):
        all_diffs.append(result)


def compare_confs(
    reference_conf: Conf,
    compared_conf: Conf,
    ignore_regex: str = ""
) -> tuple[list[ConfLine], list[ConfLine], list[dict[str, ConfLine]], list[dict]]:
    """
    Compare two configurations and identify differences.
    
    Args:
        reference_conf: The reference (baseline) configuration
        compared_conf: The configuration to compare against the reference
        ignore_regex: Regular expression pattern for lines to ignore in comparison
        
    Returns:
        A tuple containing:
        - deleted_root_lines: Root lines in reference but not in compared (includes children)
        - added_root_lines: Root lines in compared but not in reference (includes children)
        - modified_root_lines: List of dicts with 'reference' and 'compared' keys
        - modified_children: List of dicts, each with keys:
            - 'parent': the common parent ConfLine
            - 'added_children': list of children added under this parent
            - 'deleted_children': list of children deleted under this parent
            - 'modified_children': list of dicts with 'reference' and 'compared' keys
    """
    # Filter out lines matching the ignore regex
    ref_lines = [line for line in reference_conf.lines 
                 if not _line_matches_regex(line, ignore_regex)]
    cmp_lines = [line for line in compared_conf.lines 
                 if not _line_matches_regex(line, ignore_regex)]
    
    deleted_root_lines = []
    added_root_lines = []
    modified_root_lines = []
    modified_children_list = []
    
    matched_ref_roots = set()
    matched_cmp_roots = set()
    
    ref_root_lines = [line for line in ref_lines if line.level == 0]
    cmp_root_lines = [line for line in cmp_lines if line.level == 0]
    
    # Step 1: Match root lines by maximum resemblance (starting keywords)
    for ref_root in ref_root_lines:
        best_match = None
        for cmp_root in cmp_root_lines:
            if cmp_root in matched_cmp_roots:
                continue
            if _lines_match_start(ref_root, cmp_root):
                best_match = cmp_root
                break
        
        if best_match:
            matched_ref_roots.add(ref_root)
            matched_cmp_roots.add(best_match)
            
            if not _lines_exact_match(ref_root, best_match):
                # Root lines are modified
                modified_root_lines.append({
                    "reference": ref_root,
                    "compared": best_match
                })
            
            # Compare children of these matching parents
            # This will recursively add all descendant comparisons to modified_children_list
            _compare_children_of_parent(ref_root, best_match, modified_children_list)
    
    # Step 2: Find deleted root lines (not matched)
    for ref_root in ref_root_lines:
        if ref_root not in matched_ref_roots:
            deleted_root_lines.append(ref_root)
    
    # Step 3: Find added root lines (not matched)
    for cmp_root in cmp_root_lines:
        if cmp_root not in matched_cmp_roots:
            added_root_lines.append(cmp_root)
    
    return deleted_root_lines, added_root_lines, modified_root_lines, modified_children_list

