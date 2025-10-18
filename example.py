#!/usr/bin/env python3
"""
Example usage of the netconf_parser library.
"""

from pprint import pprint
from netconf_parser import Conf, search_line_start_with, compare_confs


def example_basic_parsing():
    """Demonstrate basic configuration parsing."""
    print("=" * 60)
    print("Example 1: Basic Configuration Parsing")
    print("=" * 60)
    
    config_text = """hostname router1
interface GigabitEthernet0/1
 description WAN Link
 ip address 192.168.1.1 255.255.255.0
 no shutdown
interface GigabitEthernet0/2
 description LAN Link
 ip address 10.0.0.1 255.255.255.0
 no shutdown
router bgp 65000
 neighbor 192.168.1.2
  remote-as 65001
  description Peer Router
 network 10.0.0.0"""
    
    conf = Conf.from_string(config_text)
    
    print(f"\nTotal lines: {len(conf.lines)}")
    print(f"Root-level lines: {len(conf.root_lines)}")
    
    print("\nRoot lines:")
    for line in conf.root_lines:
        print(f"  - {line} (level={line.level}, children={line.direct_children_count})")
    
    # Show details of the first interface
    interface1 = conf.root_lines[1]
    print(f"\nDetails of '{interface1}':")
    print(f"  Has children: {interface1.has_children}")
    print(f"  Direct children: {interface1.direct_children_count}")
    print(f"  All children: {interface1.all_children_count}")
    print(f"  Children:")
    for child in interface1.children:
        print(f"    - {child}")


def example_search():
    """Demonstrate search functionality."""
    print("\n" + "=" * 60)
    print("Example 2: Searching Configuration")
    print("=" * 60)
    
    config_text = """hostname router1
interface GigabitEthernet0/1
 description WAN Link
 ip address 192.168.1.1 255.255.255.0
 no shutdown
interface GigabitEthernet0/2
 description LAN Link
 ip address 10.0.0.1 255.255.255.0
 shutdown"""
    
    conf = Conf.from_string(config_text)
    
    # Search for all interfaces
    print("\n1. All interfaces:")
    interfaces = search_line_start_with(conf, "interface", level=0)
    for line in interfaces:
        print(f"  - {line}")
    
    # Search for IP addresses
    print("\n2. All IP addresses:")
    ip_addresses = search_line_start_with(conf, "ip address", level=1)
    for line in ip_addresses:
        print(f"  - {line}")
    
    # Search for descriptions under interfaces
    print("\n3. Descriptions under interfaces:")
    descriptions = search_line_start_with(
        conf, "description", level=1, parent_start_with="interface"
    )
    for line in descriptions:
        print(f"  - {line} (parent: {line.parent})")


def example_comparison():
    """Demonstrate configuration comparison."""
    print("\n" + "=" * 60)
    print("Example 3: Comparing Configurations")
    print("=" * 60)
    
    old_config = """hostname old-router
reference line
interface GigabitEthernet0/1
 description Old WAN
 ip address 192.168.1.1 255.255.255.0
 no shutdown
interface GigabitEthernet0/2
 ip address 10.0.0.1 255.255.255.0
router bgp 65000
 removed line 222
 neighbor 192.168.1.2
  remote-as 65001
  description Peer Router
  removed line 22---
 network 10.0.0.1"""
    
    new_config = """hostname new-router
test line
interface GigabitEthernet0/1
 description New WAN
 ip address 192.168.1.2 255.255.255.0
 no shutdown
interface GigabitEthernet0/3
 ip address 172.16.0.1 255.255.255.0
router bgp 65000
 added line 22
 neighbor 192.168.1.2
  remote-as 65002
  description Peer Router2
 network 10.0.0.0"""
    
    old_conf = Conf.from_string(old_config)
    new_conf = Conf.from_string(new_config)
    
    deleted, added, modified_root, modified_children = compare_confs(old_conf, new_conf)
    
    print("\nDeleted lines:")
    for line in deleted:
        print(f"  - {line}")
    
    print("\nAdded lines:")
    for line in added:
        print(f"  + {line}")
    
    print("\nModified root lines:")
    for pair in modified_root:
        print(f"  Reference: {pair['reference']}")
        print(f"  Compared:  {pair['compared']}")
        print()
    
    print("\n--------------------------------------")
    pprint(modified_children)
    print("\n--------------------------------------")
    print("\nModified children:")
    for i, diff in enumerate(modified_children, 1):
        print(f"  [{i}] Parent: {diff['parent']}")
        if diff['deleted_children']:
            print(f"      Deleted children:")
            for child in diff['deleted_children']:
                print(f"        - {child}")
        if diff['added_children']:
            print(f"      Added children:")
            for child in diff['added_children']:
                print(f"        + {child}")
        if diff['modified_children']:
            print(f"      Modified children:")
            for item in diff['modified_children']:
                print(f"        Reference: {item['reference']}")
                print(f"        Compared:  {item['compared']}")
        print()


def example_analysis():
    """Demonstrate configuration analysis."""
    print("\n" + "=" * 60)
    print("Example 4: Configuration Analysis")
    print("=" * 60)
    
    config_text = """interface GigabitEthernet0/1
 description Configured Interface
 ip address 192.168.1.1 255.255.255.0
 no shutdown
interface GigabitEthernet0/2
 ip address 10.0.0.1 255.255.255.0
 shutdown
interface GigabitEthernet0/3
 ip address 172.16.0.1 255.255.255.0"""
    
    conf = Conf.from_string(config_text)
    
    print("\nInterface Analysis:")
    for line in conf.root_lines:
        if line.content[0] == "interface":
            interface_name = line.content[1]
            
            # Check for description
            has_description = any(
                child.content[0] == "description" for child in line.children
            )
            
            # Check shutdown status
            is_shutdown = any(
                " ".join(child.content) == "shutdown" for child in line.children
            )
            is_no_shutdown = any(
                " ".join(child.content) == "no shutdown" for child in line.children
            )
            
            status = "UP" if is_no_shutdown else ("DOWN" if is_shutdown else "UNKNOWN")
            desc_status = "YES" if has_description else "NO"
            
            print(f"  {interface_name:25} Status: {status:7} Description: {desc_status}")


if __name__ == "__main__":
    example_basic_parsing()
    example_search()
    example_comparison()
    example_analysis()
    
    print("\n" + "=" * 60)
    print("Examples completed successfully!")
    print("=" * 60)

