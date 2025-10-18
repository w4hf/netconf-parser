# Network Configuration Parser

A Python library for parsing and analyzing hierarchical network device configurations with space-based indentation.

## Features

- Parse network configurations from files or strings
- Build hierarchical parent-child relationships based on indentation
- Rich metadata for each configuration line (level, children, siblings, etc.)
- Search configurations with flexible filters
- Compare configurations to identify differences
- Support for any device with space-based indentation (Cisco, Arista, etc.)

## Installation

### From PyPI (Recommended)

```bash
pip install netconf-parser
```

### From Source

```bash
git clone https://github.com/w4hf/netconf-parser.git
cd netconf-parser
pip install -e .
```

### For Development

```bash
git clone https://github.com/w4hf/netconf-parser.git
cd netconf-parser
pip install -e ".[dev]"
```

## Quick Start

### Basic Usage

```python
from netconf_parser import Conf

# Load from a string
config_text = """hostname router1
interface GigabitEthernet0/1
 ip address 192.168.1.1 255.255.255.0
 no shutdown
 description WAN Link
"""

conf = Conf.from_string(config_text)

# Or load from a file
conf = Conf.from_file("config.txt")

# Access all lines
print(f"Total lines: {len(conf.lines)}")

# Access root-level lines
for line in conf.root_lines:
    print(f"Root line: {line}")
```

### Working with ConfLine Objects

Each line in the configuration is represented by a `ConfLine` object with rich metadata:

```python
# Get a line
line = conf.lines[1]  # interface line

# Access properties
print(f"Content: {line.content}")  # ['interface', 'GigabitEthernet0/1']
print(f"Line number: {line.line_num}")
print(f"Level: {line.level}")
print(f"Has children: {line.has_children}")
print(f"Has parent: {line.has_parent}")
print(f"Is lone line: {line.lone_line}")

# Access relationships
print(f"Direct children: {line.direct_children_count}")
print(f"All descendants: {line.all_children_count}")

# Iterate through children
for child in line.children:
    print(f"  Child: {child}")

# Check siblings
for sibling in line.siblings:
    print(f"  Sibling: {sibling}")
```

### Searching Configurations

Use `search_line_start_with()` to find specific lines:

```python
from netconf_parser import search_line_start_with

# Find all interface lines at level 0
interfaces = search_line_start_with(conf, "interface", level=0)

# Find IP address lines under interfaces
ip_addresses = search_line_start_with(
    conf, 
    "ip address", 
    level=1, 
    parent_start_with="interface"
)

# Find descriptions under a specific interface
descriptions = search_line_start_with(
    conf,
    "description",
    level=1,
    parent_start_with="interface GigabitEthernet0/1"
)
```

### Comparing Configurations

Compare two configurations to identify differences:

```python
from netconf_parser import compare_confs

# Load two configurations
ref_conf = Conf.from_file("baseline.txt")
new_conf = Conf.from_file("current.txt")

# Compare them
deleted, added, modified_root, modified_children = compare_confs(
    ref_conf, 
    new_conf,
    ignore_regex=r"^!"  # Ignore comment lines
)

# Check deleted lines
print("Deleted lines:")
for line in deleted:
    print(f"  - {line}")

# Check added lines
print("Added lines:")
for line in added:
    print(f"  + {line}")

# Check modified root lines
print("Modified root lines:")
for line in modified_root:
    print(f"  ~ {line}")

# Check modified children
print("Modified children:")
for group in modified_children:
    print(f"  Group with parent: {group[0].parent}")
    for line in group:
        print(f"    ~ {line}")
```

## API Reference

### Classes

#### `Conf`

Represents a complete network configuration.

**Class Methods:**
- `from_string(config_text: str) -> Conf`: Create from a multiline string
- `from_file(file_path: str) -> Conf`: Create from a file

**Properties:**
- `lines`: List of all ConfLine objects
- `root_lines`: List of root-level ConfLine objects (level 0)

#### `ConfLine`

Represents a single configuration line with hierarchical properties.

**Properties:**
- `content`: List of keywords (whitespace removed)
- `line_num`: Line number in the configuration
- `level`: Indentation depth (0 = root)
- `has_children`: Boolean indicating if line has children
- `has_parent`: Boolean indicating if line has a parent
- `parent`: Reference to parent ConfLine (or None)
- `children`: List of direct child ConfLine objects
- `siblings`: List of sibling ConfLine objects
- `lone_line`: True if line has no parent or children
- `direct_children_count`: Number of direct children
- `all_children_count`: Total number of descendants
- `direct_children`: List of direct children's content
- `all_children`: List of all descendants' content

### Functions

#### `search_line_start_with()`

Search for configuration lines matching specific criteria.

```python
search_line_start_with(
    conf: Conf,
    search_string: str,
    level: int,
    parent_start_with: str | None = None
) -> list[ConfLine]
```

**Parameters:**
- `conf`: The Conf object to search
- `search_string`: String that lines must start with
- `level`: The indentation level to match
- `parent_start_with`: Optional filter for parent line content

**Returns:** List of matching ConfLine objects

#### `compare_confs()`

Compare two configurations and identify differences.

```python
compare_confs(
    reference_conf: Conf,
    compared_conf: Conf,
    ignore_regex: str = ""
) -> tuple[list[ConfLine], list[ConfLine], list[ConfLine], list[list[ConfLine]]]
```

**Parameters:**
- `reference_conf`: The baseline configuration
- `compared_conf`: The configuration to compare
- `ignore_regex`: Regular expression for lines to ignore

**Returns:** A tuple containing:
1. `deleted_lines`: Lines in reference but not in compared
2. `added_lines`: Lines in compared but not in reference
3. `modified_root_lines`: Root lines with same start but different content
4. `modified_children`: Groups of child lines with modifications

## Running Tests

```bash
pytest tests/
```

To run with verbose output:

```bash
pytest -v tests/
```

To run a specific test file:

```bash
pytest tests/test_parser.py
```

## Requirements

- Python 3.12+
- pytest 8.0+ (for testing)

## License

This project is provided as-is for parsing network device configurations.

## Examples

### Example 1: Analyzing Interface Configuration

```python
from netconf_parser import Conf, search_line_start_with

config = """
interface GigabitEthernet0/1
 description WAN Link
 ip address 192.168.1.1 255.255.255.0
 no shutdown
interface GigabitEthernet0/2
 description LAN Link
 ip address 10.0.0.1 255.255.255.0
 shutdown
"""

conf = Conf.from_string(config)

# Find all interfaces with "shutdown" configured
for interface in conf.root_lines:
    if interface.content[0] == "interface":
        has_no_shutdown = any(
            " ".join(child.content) == "no shutdown" 
            for child in interface.children
        )
        has_shutdown = any(
            " ".join(child.content) == "shutdown" 
            for child in interface.children
        )
        
        if has_shutdown and not has_no_shutdown:
            print(f"Interface {interface.content[1]} is shutdown")
```

### Example 2: Configuration Audit

```python
from netconf_parser import Conf

config = """
interface GigabitEthernet0/1
 ip address 192.168.1.1 255.255.255.0
interface GigabitEthernet0/2
 ip address 10.0.0.1 255.255.255.0
 description Configured
interface GigabitEthernet0/3
 ip address 172.16.0.1 255.255.255.0
"""

conf = Conf.from_string(config)

# Find interfaces without descriptions
print("Interfaces without descriptions:")
for line in conf.root_lines:
    if line.content[0] == "interface":
        has_description = any(
            child.content[0] == "description" 
            for child in line.children
        )
        if not has_description:
            print(f"  - {line.content[1]}")
```

### Example 3: Configuration Diff Report

```python
from netconf_parser import Conf, compare_confs

old_config = """hostname old-router
interface GigabitEthernet0/1
 ip address 192.168.1.1 255.255.255.0"""

new_config = """hostname new-router
interface GigabitEthernet0/1
 ip address 192.168.1.2 255.255.255.0"""

old_conf = Conf.from_string(old_config)
new_conf = Conf.from_string(new_config)

deleted, added, modified_root, modified_children = compare_confs(old_conf, new_conf)

print("Configuration Changes Report")
print("=" * 50)
print(f"Deleted lines: {len(deleted)}")
print(f"Added lines: {len(added)}")
print(f"Modified root lines: {len(modified_root)}")
print(f"Modified child groups: {len(modified_children)}")
```

