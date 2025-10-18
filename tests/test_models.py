"""
Tests for the models module.
"""

import pytest
from netconf_parser.models import ConfLine, Conf


class TestConfLine:
    """Tests for ConfLine class."""
    
    def test_confline_basic_properties(self):
        """Test basic ConfLine properties."""
        line = ConfLine(content=["interface", "GigabitEthernet0/1"], line_num=5, level=0)
        
        assert line.content == ["interface", "GigabitEthernet0/1"]
        assert line.line_num == 5
        assert line.level == 0
        assert line.parent is None
        assert line.children == []
    
    def test_confline_has_children_property(self):
        """Test has_children property."""
        parent = ConfLine(content=["interface", "GigabitEthernet0/1"], line_num=1, level=0)
        child = ConfLine(content=["ip", "address", "192.168.1.1"], line_num=2, level=1)
        
        assert parent.has_children is False
        
        parent.children.append(child)
        child.parent = parent
        
        assert parent.has_children is True
        assert child.has_children is False
    
    def test_confline_has_parent_property(self):
        """Test has_parent property."""
        parent = ConfLine(content=["interface", "GigabitEthernet0/1"], line_num=1, level=0)
        child = ConfLine(content=["ip", "address", "192.168.1.1"], line_num=2, level=1)
        
        assert parent.has_parent is False
        assert child.has_parent is False
        
        child.parent = parent
        parent.children.append(child)
        
        assert parent.has_parent is False
        assert child.has_parent is True
    
    def test_confline_siblings_property(self):
        """Test siblings property."""
        parent = ConfLine(content=["interface", "GigabitEthernet0/1"], line_num=1, level=0)
        child1 = ConfLine(content=["ip", "address", "192.168.1.1"], line_num=2, level=1)
        child2 = ConfLine(content=["no", "shutdown"], line_num=3, level=1)
        child3 = ConfLine(content=["description", "Test"], line_num=4, level=1)
        
        parent.children = [child1, child2, child3]
        child1.parent = parent
        child2.parent = parent
        child3.parent = parent
        
        assert len(child1.siblings) == 2
        assert child2 in child1.siblings
        assert child3 in child1.siblings
        assert child1 not in child1.siblings
        
        # Root level has no siblings
        assert parent.siblings == []
    
    def test_confline_lone_line_property(self):
        """Test lone_line property."""
        lone = ConfLine(content=["hostname", "router1"], line_num=1, level=0)
        parent = ConfLine(content=["interface", "GigabitEthernet0/1"], line_num=2, level=0)
        child = ConfLine(content=["ip", "address", "192.168.1.1"], line_num=3, level=1)
        
        assert lone.lone_line is True
        
        parent.children.append(child)
        child.parent = parent
        
        assert parent.lone_line is False
        assert child.lone_line is False
    
    def test_confline_children_counts(self):
        """Test direct_children_count and all_children_count."""
        root = ConfLine(content=["router", "bgp", "65000"], line_num=1, level=0)
        child1 = ConfLine(content=["neighbor", "192.168.1.1"], line_num=2, level=1)
        child2 = ConfLine(content=["network", "10.0.0.0"], line_num=3, level=1)
        grandchild = ConfLine(content=["remote-as", "65001"], line_num=4, level=2)
        
        root.children = [child1, child2]
        child1.parent = root
        child2.parent = root
        child1.children = [grandchild]
        grandchild.parent = child1
        
        assert root.direct_children_count == 2
        assert root.all_children_count == 3
        assert child1.direct_children_count == 1
        assert child1.all_children_count == 1
        assert grandchild.direct_children_count == 0
        assert grandchild.all_children_count == 0
    
    def test_confline_children_lists(self):
        """Test direct_children and all_children properties."""
        root = ConfLine(content=["router", "bgp", "65000"], line_num=1, level=0)
        child1 = ConfLine(content=["neighbor", "192.168.1.1"], line_num=2, level=1)
        child2 = ConfLine(content=["network", "10.0.0.0"], line_num=3, level=1)
        grandchild = ConfLine(content=["remote-as", "65001"], line_num=4, level=2)
        
        root.children = [child1, child2]
        child1.parent = root
        child2.parent = root
        child1.children = [grandchild]
        grandchild.parent = child1
        
        assert root.direct_children == [
            ["neighbor", "192.168.1.1"],
            ["network", "10.0.0.0"]
        ]
        assert root.all_children == [
            ["neighbor", "192.168.1.1"],
            ["remote-as", "65001"],
            ["network", "10.0.0.0"]
        ]
    
    def test_confline_str_repr(self):
        """Test string representations."""
        line = ConfLine(content=["interface", "GigabitEthernet0/1"], line_num=5, level=0)
        
        assert str(line) == "interface GigabitEthernet0/1"
        assert "ConfLine" in repr(line)
        assert "line_num=5" in repr(line)
        assert "level=0" in repr(line)


class TestConf:
    """Tests for Conf class."""
    
    def test_conf_initialization(self):
        """Test Conf initialization."""
        conf = Conf()
        
        assert conf.lines == []
        assert conf.root_lines == []
    
    def test_conf_from_string(self):
        """Test creating Conf from string."""
        config_text = """hostname router1
interface GigabitEthernet0/1
 ip address 192.168.1.1 255.255.255.0
 no shutdown"""
        
        conf = Conf.from_string(config_text)
        
        assert len(conf.lines) == 4
        assert len(conf.root_lines) == 2
    
    def test_conf_root_lines_property(self):
        """Test root_lines property."""
        config_text = """hostname router1
interface GigabitEthernet0/1
 ip address 192.168.1.1 255.255.255.0
interface GigabitEthernet0/2
 ip address 192.168.2.1 255.255.255.0"""
        
        conf = Conf.from_string(config_text)
        
        assert len(conf.root_lines) == 3
        assert all(line.level == 0 for line in conf.root_lines)
    
    def test_conf_str_repr(self):
        """Test string representations."""
        conf = Conf()
        
        assert "Conf" in repr(conf)
        assert "Configuration" in str(conf)

