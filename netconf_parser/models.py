"""
Core data models for network configuration parsing.
"""

from typing import Optional


class ConfLine:
    """
    Represents a single line in a network configuration with its hierarchical properties.
    
    Attributes:
        content: List of keywords in the line (whitespace ignored)
        line_num: Line number in the original configuration
        has_children: True if this line has child lines
        has_parent: True if this line has a parent line
        level: Depth level (0 for root, 1 for first level children, etc.)
        parent: Reference to parent ConfLine, None if root level
        children: List of direct child ConfLine objects
        siblings: List of sibling ConfLine objects (same parent and level)
        lone_line: True if line has no parent and no children
        direct_children_count: Number of direct children
        all_children_count: Total number of descendants (children + grandchildren + ...)
        direct_children: List of content (as lists) of direct children
        all_children: List of content (as lists) of all descendants
    """
    
    def __init__(self, content: list[str], line_num: int, level: int):
        """
        Initialize a ConfLine.
        
        Args:
            content: List of keywords from the line
            line_num: Line number in the configuration
            level: Indentation level (0-based)
        """
        self.content: list[str] = content
        self.line_num: int = line_num
        self.level: int = level
        self.parent: Optional[ConfLine] = None
        self.children: list[ConfLine] = []
        
    @property
    def has_children(self) -> bool:
        """Check if this line has any children."""
        return len(self.children) > 0
    
    @property
    def has_parent(self) -> bool:
        """Check if this line has a parent."""
        return self.parent is not None
    
    @property
    def siblings(self) -> list["ConfLine"]:
        """Get list of sibling lines (same parent and level)."""
        if not self.has_parent:
            return []
        return [child for child in self.parent.children if child is not self]
    
    @property
    def lone_line(self) -> bool:
        """Check if line has no parent and no children."""
        return not self.has_parent and not self.has_children
    
    @property
    def direct_children_count(self) -> int:
        """Get count of direct children."""
        return len(self.children)
    
    @property
    def all_children_count(self) -> int:
        """Get count of all descendants (children + grandchildren + ...)."""
        count = len(self.children)
        for child in self.children:
            count += child.all_children_count
        return count
    
    @property
    def direct_children(self) -> list[list[str]]:
        """Get list of direct children's content."""
        return [child.content for child in self.children]
    
    @property
    def all_children(self) -> list[list[str]]:
        """Get list of all descendants' content."""
        result = []
        for child in self.children:
            result.append(child.content)
            result.extend(child.all_children)
        return result
    
    def __repr__(self) -> str:
        """String representation of the ConfLine."""
        return f"ConfLine(line_num={self.line_num}, level={self.level}, content={self.content})"
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        return " ".join(self.content)


class Conf:
    """
    Represents a complete network configuration with all its lines.
    
    Attributes:
        lines: List of all ConfLine objects in the configuration
        root_lines: List of root-level ConfLine objects (level 0)
    """
    
    def __init__(self):
        """Initialize an empty Conf object."""
        self.lines: list[ConfLine] = []
    
    @classmethod
    def from_string(cls, config_text: str) -> "Conf":
        """
        Create a Conf object from a multiline string.
        
        Args:
            config_text: Multiline configuration string
            
        Returns:
            Parsed Conf object
        """
        from .parser import parse_config
        conf = cls()
        conf.lines = parse_config(config_text)
        return conf
    
    @classmethod
    def from_file(cls, file_path: str) -> "Conf":
        """
        Create a Conf object from a configuration file.
        
        Args:
            file_path: Path to the configuration file
            
        Returns:
            Parsed Conf object
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            config_text = f.read()
        return cls.from_string(config_text)
    
    @property
    def root_lines(self) -> list[ConfLine]:
        """Get all root-level lines (level 0)."""
        return [line for line in self.lines if line.level == 0]
    
    def __repr__(self) -> str:
        """String representation of the Conf."""
        return f"Conf(lines={len(self.lines)})"
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"Configuration with {len(self.lines)} lines"

