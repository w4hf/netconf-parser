"""
Tests for the search module.
"""

import pytest
from netconf_parser import Conf, search_line_start_with


class TestSearchLineStartWith:
    """Tests for search_line_start_with function."""
    
    @pytest.fixture
    def sample_conf(self):
        """Create a sample configuration for testing."""
        config = """hostname router1
interface GigabitEthernet0/1
 ip address 192.168.1.1 255.255.255.0
 no shutdown
 description WAN Link
interface GigabitEthernet0/2
 ip address 10.0.0.1 255.255.255.0
 no shutdown
 description LAN Link
router bgp 65000
 neighbor 192.168.1.2
  remote-as 65001
  description Peer
 network 10.0.0.0"""
        return Conf.from_string(config)
    
    def test_search_by_level_only(self, sample_conf):
        """Test searching by level only."""
        results = search_line_start_with(sample_conf, "", level=0)
        
        # Should return all root level lines
        assert len(results) == 4  # hostname, interface x2, router
    
    def test_search_by_string_and_level(self, sample_conf):
        """Test searching by string and level."""
        results = search_line_start_with(sample_conf, "interface", level=0)
        
        assert len(results) == 2
        assert all(line.content[0] == "interface" for line in results)
        assert all(line.level == 0 for line in results)
    
    def test_search_with_parent_filter(self, sample_conf):
        """Test searching with parent filter."""
        results = search_line_start_with(
            sample_conf, 
            "ip address", 
            level=1, 
            parent_start_with="interface"
        )
        
        assert len(results) == 2
        assert all(line.content[0:2] == ["ip", "address"] for line in results)
        assert all(line.parent.content[0] == "interface" for line in results)
    
    def test_search_specific_parent(self, sample_conf):
        """Test searching with specific parent content."""
        results = search_line_start_with(
            sample_conf,
            "description",
            level=1,
            parent_start_with="interface GigabitEthernet0/1"
        )
        
        assert len(results) == 1
        assert results[0].content[0] == "description"
        assert " ".join(results[0].parent.content) == "interface GigabitEthernet0/1"
    
    def test_search_deeper_level(self, sample_conf):
        """Test searching at deeper nesting level."""
        results = search_line_start_with(sample_conf, "remote-as", level=2)
        
        assert len(results) == 1
        assert results[0].content == ["remote-as", "65001"]
        assert results[0].level == 2
    
    def test_search_no_results(self, sample_conf):
        """Test search that returns no results."""
        results = search_line_start_with(sample_conf, "nonexistent", level=0)
        
        assert len(results) == 0
    
    def test_search_wrong_level(self, sample_conf):
        """Test search with wrong level."""
        results = search_line_start_with(sample_conf, "interface", level=1)
        
        assert len(results) == 0  # interfaces are at level 0
    
    def test_search_with_wrong_parent(self, sample_conf):
        """Test search with parent that doesn't match."""
        results = search_line_start_with(
            sample_conf,
            "ip address",
            level=1,
            parent_start_with="router"
        )
        
        assert len(results) == 0  # ip address is under interface, not router
    
    def test_search_partial_match(self, sample_conf):
        """Test that partial matches work correctly."""
        results = search_line_start_with(sample_conf, "ip", level=1)
        
        assert len(results) == 2
        assert all(line.content[0] == "ip" for line in results)
    
    def test_search_exact_match_needed(self, sample_conf):
        """Test that search requires start match, not substring."""
        results = search_line_start_with(sample_conf, "address", level=1)
        
        # Should not match "ip address" because it doesn't START with "address"
        assert len(results) == 0
    
    def test_search_case_sensitive(self, sample_conf):
        """Test that search is case-sensitive."""
        results = search_line_start_with(sample_conf, "Interface", level=0)
        
        # Should not match because of case difference
        assert len(results) == 0
    
    def test_search_multiple_criteria(self, sample_conf):
        """Test search with all criteria specified."""
        results = search_line_start_with(
            sample_conf,
            "no shutdown",
            level=1,
            parent_start_with="interface"
        )
        
        assert len(results) == 2
        assert all(line.content == ["no", "shutdown"] for line in results)
        assert all(line.level == 1 for line in results)
        assert all(line.parent.content[0] == "interface" for line in results)

