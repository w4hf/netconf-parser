"""
Tests for the parser module.
"""

import pytest
from netconf_parser.parser import get_indentation_level, parse_config
from netconf_parser.models import Conf


class TestIndentationDetection:
    """Tests for indentation detection."""
    
    def test_no_indentation(self):
        """Test line with no indentation."""
        assert get_indentation_level("hostname router1") == 0
    
    def test_space_indentation(self):
        """Test line with space indentation."""
        assert get_indentation_level(" ip address 192.168.1.1") == 1
        assert get_indentation_level("  description Test") == 2
        assert get_indentation_level("    shutdown") == 4
    
    def test_tab_indentation(self):
        """Test line with tab indentation."""
        assert get_indentation_level("\tip address 192.168.1.1") == 4
        assert get_indentation_level("\t\tdescription Test") == 8


class TestConfigParsing:
    """Tests for configuration parsing."""
    
    def test_parse_empty_config(self):
        """Test parsing empty configuration."""
        lines = parse_config("")
        assert lines == []
    
    def test_parse_single_line(self):
        """Test parsing single line."""
        config = "hostname router1"
        lines = parse_config(config)
        
        assert len(lines) == 1
        assert lines[0].content == ["hostname", "router1"]
        assert lines[0].line_num == 1
        assert lines[0].level == 0
        assert lines[0].lone_line is True
    
    def test_parse_simple_hierarchy(self):
        """Test parsing simple parent-child hierarchy."""
        config = """interface GigabitEthernet0/1
 ip address 192.168.1.1 255.255.255.0
 no shutdown"""
        
        lines = parse_config(config)
        
        assert len(lines) == 3
        
        # Check parent
        parent = lines[0]
        assert parent.content == ["interface", "GigabitEthernet0/1"]
        assert parent.level == 0
        assert parent.has_children is True
        assert parent.direct_children_count == 2
        
        # Check children
        child1 = lines[1]
        assert child1.content == ["ip", "address", "192.168.1.1", "255.255.255.0"]
        assert child1.level == 1
        assert child1.has_parent is True
        assert child1.parent is parent
        
        child2 = lines[2]
        assert child2.content == ["no", "shutdown"]
        assert child2.level == 1
        assert child2.has_parent is True
        assert child2.parent is parent
    
    def test_parse_multiple_levels(self):
        """Test parsing multiple indentation levels."""
        config = """router bgp 65000
 neighbor 192.168.1.1
  remote-as 65001
  description Peer Router
 network 10.0.0.0"""
        
        lines = parse_config(config)
        
        assert len(lines) == 5
        
        # Check levels
        assert lines[0].level == 0  # router bgp
        assert lines[1].level == 1  # neighbor
        assert lines[2].level == 2  # remote-as
        assert lines[3].level == 2  # description
        assert lines[4].level == 1  # network
        
        # Check parent relationships
        assert lines[1].parent is lines[0]
        assert lines[2].parent is lines[1]
        assert lines[3].parent is lines[1]
        assert lines[4].parent is lines[0]
        
        # Check children
        assert lines[0].direct_children_count == 2
        assert lines[0].all_children_count == 4
        assert lines[1].direct_children_count == 2
        assert lines[1].all_children_count == 2
    
    def test_parse_siblings(self):
        """Test sibling relationships."""
        config = """interface GigabitEthernet0/1
 ip address 192.168.1.1 255.255.255.0
 no shutdown
 description Link1"""
        
        lines = parse_config(config)
        
        child1 = lines[1]
        child2 = lines[2]
        child3 = lines[3]
        
        assert len(child1.siblings) == 2
        assert child2 in child1.siblings
        assert child3 in child1.siblings
    
    def test_parse_skip_empty_lines(self):
        """Test that empty lines are skipped."""
        config = """hostname router1

interface GigabitEthernet0/1

 ip address 192.168.1.1 255.255.255.0"""
        
        lines = parse_config(config)
        
        assert len(lines) == 3
        assert lines[0].content == ["hostname", "router1"]
        assert lines[1].content == ["interface", "GigabitEthernet0/1"]
        assert lines[2].content == ["ip", "address", "192.168.1.1", "255.255.255.0"]
    
    def test_parse_complex_config(self):
        """Test parsing a more complex configuration."""
        config = """hostname router1
!
interface GigabitEthernet0/1
 description WAN Link
 ip address 192.168.1.1 255.255.255.0
 no shutdown
!
interface GigabitEthernet0/2
 description LAN Link
 ip address 10.0.0.1 255.255.255.0
 no shutdown
!
router bgp 65000
 neighbor 192.168.1.2 remote-as 65001
 network 10.0.0.0 mask 255.255.255.0"""
        
        lines = parse_config(config)
        
        # Check that we have the right number of lines (including ! lines)
        assert len(lines) == 15
        
        # Check root lines
        root_lines = [l for l in lines if l.level == 0]
        assert len(root_lines) == 7  # hostname, !, interface x2, !, router, !
        
        # Verify parent-child relationships
        interface1 = lines[2]  # First interface
        assert interface1.content[0] == "interface"
        assert interface1.direct_children_count == 3
    
    def test_parse_inconsistent_indentation(self):
        """Test parsing with varying indentation amounts."""
        config = """router bgp 65000
 neighbor 192.168.1.1
   remote-as 65001
 network 10.0.0.0
   mask 255.255.255.0"""
        
        lines = parse_config(config)
        
        # With indent of 0, 1, 3 spaces - indent unit is 1
        # So levels are: 0/1=0, 1/1=1, 3/1=3, 1/1=1, 3/1=3
        assert lines[0].level == 0
        assert lines[1].level == 1
        assert lines[2].level == 3
        assert lines[3].level == 1
        assert lines[4].level == 3


class TestConfIntegration:
    """Integration tests with Conf class."""
    
    def test_conf_from_string_integration(self):
        """Test full integration with Conf.from_string."""
        config = """hostname router1
interface GigabitEthernet0/1
 ip address 192.168.1.1 255.255.255.0
 no shutdown"""
        
        conf = Conf.from_string(config)
        
        assert len(conf.lines) == 4
        assert len(conf.root_lines) == 2
        
        # Check relationships are properly established
        interface_line = conf.root_lines[1]
        assert interface_line.has_children is True
        assert interface_line.direct_children_count == 2

