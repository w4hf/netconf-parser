"""
Configuration parsing logic.
"""

from .models import ConfLine


def get_indentation_level(line: str) -> int:
    """
    Calculate the indentation level of a line.
    
    Args:
        line: The line to check
        
    Returns:
        Number of leading spaces (tabs count as 4 spaces)
    """
    count = 0
    for char in line:
        if char == ' ':
            count += 1
        elif char == '\t':
            count += 4
        else:
            break
    return count


def parse_config(config_text: str) -> list[ConfLine]:
    """
    Parse a configuration text into a list of ConfLine objects.
    
    This function:
    1. Splits the configuration into lines
    2. Determines indentation levels
    3. Builds parent-child relationships
    4. Populates all ConfLine properties
    
    Args:
        config_text: The configuration text to parse
        
    Returns:
        List of ConfLine objects with all relationships established
    """
    lines_data = []
    
    # First pass: extract lines and calculate indentation
    for line_num, line in enumerate(config_text.splitlines(), start=1):
        # Skip empty lines
        if not line.strip():
            continue
            
        indent = get_indentation_level(line)
        content = line.strip().split()
        
        # Skip lines with no content
        if not content:
            continue
            
        lines_data.append({
            'line_num': line_num,
            'indent': indent,
            'content': content
        })
    
    if not lines_data:
        return []
    
    # Determine indentation unit (smallest non-zero indent difference)
    indent_values = sorted(set(data['indent'] for data in lines_data))
    if len(indent_values) > 1:
        indent_unit = min(indent_values[i+1] - indent_values[i] 
                         for i in range(len(indent_values)-1) 
                         if indent_values[i+1] - indent_values[i] > 0)
    else:
        indent_unit = 1
    
    # Second pass: create ConfLine objects with levels
    conf_lines = []
    for data in lines_data:
        level = data['indent'] // indent_unit if indent_unit > 0 else 0
        conf_line = ConfLine(
            content=data['content'],
            line_num=data['line_num'],
            level=level
        )
        conf_lines.append(conf_line)
    
    # Third pass: establish parent-child relationships
    for i, current_line in enumerate(conf_lines):
        # Find parent (last line with level = current_level - 1)
        if current_line.level > 0:
            for j in range(i - 1, -1, -1):
                if conf_lines[j].level == current_line.level - 1:
                    current_line.parent = conf_lines[j]
                    conf_lines[j].children.append(current_line)
                    break
    
    return conf_lines

