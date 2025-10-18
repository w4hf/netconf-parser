"""
Tests for the compare module.
"""

import pytest
from netconf_parser import Conf, compare_confs


class TestCompareConfs:
    """Tests for compare_confs function."""
    
    def test_identical_configs(self):
        """Test comparing identical configurations."""
        config = """hostname router1
interface GigabitEthernet0/1
 ip address 192.168.1.1 255.255.255.0"""
        
        ref_conf = Conf.from_string(config)
        cmp_conf = Conf.from_string(config)
        
        deleted, added, modified_root, modified_children = compare_confs(ref_conf, cmp_conf)
        
        assert len(deleted) == 0
        assert len(added) == 0
        assert len(modified_root) == 0
        assert len(modified_children) == 0
    
    def test_deleted_lines(self):
        """Test detection of deleted ROOT-LEVEL lines only."""
        ref_config = """hostname router1
interface GigabitEthernet0/1
 ip address 192.168.1.1 255.255.255.0
 no shutdown
router bgp 65000
 neighbor 192.168.1.1"""
        
        cmp_config = """hostname router1
interface GigabitEthernet0/1
 ip address 192.168.1.1 255.255.255.0"""
        
        ref_conf = Conf.from_string(ref_config)
        cmp_conf = Conf.from_string(cmp_config)
        
        deleted, added, modified_root, modified_children = compare_confs(ref_conf, cmp_conf)
        
        # Only root-level lines should be in deleted
        # "router bgp 65000" was completely removed
        assert len(deleted) == 1
        assert deleted[0].content == ["router", "bgp", "65000"]
        assert deleted[0].level == 0
        # Children are included when root is deleted
        assert len(deleted[0].children) == 1
        assert len(added) == 0
    
    def test_added_lines(self):
        """Test detection of added ROOT-LEVEL lines only."""
        ref_config = """hostname router1
interface GigabitEthernet0/1
 ip address 192.168.1.1 255.255.255.0"""
        
        cmp_config = """hostname router1
interface GigabitEthernet0/1
 ip address 192.168.1.1 255.255.255.0
 no shutdown
router ospf 1
 network 10.0.0.0"""
        
        ref_conf = Conf.from_string(ref_config)
        cmp_conf = Conf.from_string(cmp_config)
        
        deleted, added, modified_root, modified_children = compare_confs(ref_conf, cmp_conf)
        
        assert len(deleted) == 0
        # Only root-level lines should be in added
        # "router ospf 1" was completely added
        assert len(added) == 1
        assert added[0].content == ["router", "ospf", "1"]
        assert added[0].level == 0
        # Children are included when root is added
        assert len(added[0].children) == 1
    
    def test_modified_root_lines(self):
        """Test detection of modified root lines."""
        ref_config = """hostname router1
interface GigabitEthernet0/1
 ip address 192.168.1.1 255.255.255.0"""
        
        cmp_config = """hostname router2
interface GigabitEthernet0/1
 ip address 192.168.1.1 255.255.255.0"""
        
        ref_conf = Conf.from_string(ref_config)
        cmp_conf = Conf.from_string(cmp_config)
        
        deleted, added, modified_root, modified_children = compare_confs(ref_conf, cmp_conf)
        
        assert len(modified_root) == 1
        assert modified_root[0]["reference"].content == ["hostname", "router1"]
        assert modified_root[0]["compared"].content == ["hostname", "router2"]
        assert len(deleted) == 0
        assert len(added) == 0
    
    def test_modified_children(self):
        """Test detection of modified child lines."""
        ref_config = """interface GigabitEthernet0/1
 ip address 192.168.1.1 255.255.255.0
 description Old Description"""
        
        cmp_config = """interface GigabitEthernet0/1
 ip address 192.168.1.1 255.255.255.0
 description New Description"""
        
        ref_conf = Conf.from_string(ref_config)
        cmp_conf = Conf.from_string(cmp_config)
        
        deleted, added, modified_root, modified_children = compare_confs(ref_conf, cmp_conf)
        
        # New structure: modified_children is a list of dicts with 4 keys
        assert len(modified_children) == 1
        assert modified_children[0]["parent"].content == ["interface", "GigabitEthernet0/1"]
        assert len(modified_children[0]["modified_children"]) == 1
        assert modified_children[0]["modified_children"][0]["reference"].content == ["description", "Old", "Description"]
        assert modified_children[0]["modified_children"][0]["compared"].content == ["description", "New", "Description"]
    
    def test_ignore_regex(self):
        """Test ignoring lines based on regex."""
        ref_config = """hostname router1
! Configuration comment
interface GigabitEthernet0/1
 ip address 192.168.1.1 255.255.255.0"""
        
        cmp_config = """hostname router2
! Different comment
interface GigabitEthernet0/1
 ip address 10.0.0.1 255.255.255.0"""
        
        ref_conf = Conf.from_string(ref_config)
        cmp_conf = Conf.from_string(cmp_config)
        
        # Ignore comment lines (starting with !)
        deleted, added, modified_root, modified_children = compare_confs(
            ref_conf, cmp_conf, ignore_regex=r"^!"
        )
        
        # Comments should be ignored, but we should still see hostname change
        assert len(modified_root) == 1
        assert modified_root[0]["reference"].content[0] == "hostname"
    
    def test_complex_comparison(self):
        """Test a complex comparison with multiple types of changes."""
        ref_config = """hostname router1
interface GigabitEthernet0/1
 ip address 192.168.1.1 255.255.255.0
 no shutdown
router bgp 65000
 neighbor 192.168.1.1"""
        
        cmp_config = """hostname router2
interface GigabitEthernet0/1
 ip address 192.168.1.2 255.255.255.0
 no shutdown
router ospf 1
 network 10.0.0.0"""
        
        ref_conf = Conf.from_string(ref_config)
        cmp_conf = Conf.from_string(cmp_config)
        
        deleted, added, modified_root, modified_children = compare_confs(ref_conf, cmp_conf)
        
        # hostname changed
        assert len(modified_root) >= 1
        assert any(pair["reference"].content == ["hostname", "router1"] for pair in modified_root)
        
        # router bgp and router ospf both start with "router" so they're matched as modified
        # (not deleted/added - per spec: lines starting with same keywords are modified)
        assert any(pair["reference"].content[0] == "router" for pair in modified_root)
        
        # ip address under interface changed
        assert len(modified_children) >= 1
    
    def test_deeply_nested_changes(self):
        """Test comparison with deeply nested structures (level 2+)."""
        ref_config = """router bgp 65000
 neighbor 192.168.1.1
  remote-as 65001
  description Peer1"""
        
        cmp_config = """router bgp 65000
 neighbor 192.168.1.1
  remote-as 65002
  description Peer1"""
        
        ref_conf = Conf.from_string(ref_config)
        cmp_conf = Conf.from_string(cmp_config)
        
        deleted, added, modified_root, modified_children = compare_confs(ref_conf, cmp_conf)
        
        # With flattened structure, should have an entry for neighbor as parent
        # neighbor 192.168.1.1 is IDENTICAL in both, so it's a common parent
        assert len(modified_children) >= 1
        
        # Find the entry where parent is neighbor
        found_neighbor_parent = False
        for diff_dict in modified_children:
            if diff_dict["parent"].content[0] == "neighbor":
                found_neighbor_parent = True
                # Should have remote-as as modified child
                assert len(diff_dict["modified_children"]) >= 1
                remote_as_pair = diff_dict["modified_children"][0]
                assert remote_as_pair["reference"].content == ["remote-as", "65001"]
                assert remote_as_pair["compared"].content == ["remote-as", "65002"]
        
        assert found_neighbor_parent, "Should have neighbor as parent in modified_children"
    
    def test_multiple_modified_children_same_parent(self):
        """Test multiple modified children under the same parent."""
        ref_config = """interface GigabitEthernet0/1
 ip address 192.168.1.1 255.255.255.0
 description Old Desc
 bandwidth 1000"""
        
        cmp_config = """interface GigabitEthernet0/1
 ip address 192.168.1.2 255.255.255.0
 description New Desc
 bandwidth 10000"""
        
        ref_conf = Conf.from_string(ref_config)
        cmp_conf = Conf.from_string(cmp_config)
        
        deleted, added, modified_root, modified_children = compare_confs(ref_conf, cmp_conf)
        
        # All three children are modified
        assert len(modified_children) >= 1
        
        # Count total modified lines (need to look at the 'modified_children' key in each dict)
        total_modified = sum(
            len([item for item in diff_dict["modified_children"] if isinstance(item, dict) and "reference" in item])
            for diff_dict in modified_children
        )
        assert total_modified == 3
    
    def test_empty_configs(self):
        """Test comparing empty configurations."""
        ref_conf = Conf.from_string("")
        cmp_conf = Conf.from_string("")
        
        deleted, added, modified_root, modified_children = compare_confs(ref_conf, cmp_conf)
        
        assert len(deleted) == 0
        assert len(added) == 0
        assert len(modified_root) == 0
        assert len(modified_children) == 0
    
    def test_one_empty_config(self):
        """Test comparing when one config is empty."""
        ref_config = """hostname router1
interface GigabitEthernet0/1
 ip address 192.168.1.1 255.255.255.0"""
        
        ref_conf = Conf.from_string(ref_config)
        cmp_conf = Conf.from_string("")
        
        deleted, added, modified_root, modified_children = compare_confs(ref_conf, cmp_conf)
        
        # Only root-level lines from reference should be deleted (but with their children)
        assert len(deleted) == 2  # hostname and interface (root level only)
        assert all(line.level == 0 for line in deleted)
        # The interface has 1 child
        assert sum(len(line.children) for line in deleted) == 1
        assert len(added) == 0
    
    def test_partial_match_not_deleted(self):
        """Test that lines with partial matches are not marked as deleted."""
        ref_config = """interface GigabitEthernet0/1
 ip address 192.168.1.1 255.255.255.0"""
        
        cmp_config = """interface GigabitEthernet0/1
 ip address 10.0.0.1 255.255.255.0"""
        
        ref_conf = Conf.from_string(ref_config)
        cmp_conf = Conf.from_string(cmp_config)
        
        deleted, added, modified_root, modified_children = compare_confs(ref_conf, cmp_conf)
        
        # ip address line should be in modified, not deleted
        assert len(deleted) == 0
        assert len(added) == 0
        assert len(modified_children) == 1
    
    def test_recursive_child_comparison(self):
        """Test that children only appear in modified_children if parents are IDENTICAL."""
        ref_config = """router bgp 65000
 neighbor 192.168.1.2
  remote-as 65001
  description Peer Router
  update-source Loopback0
 network 10.0.0.0"""
        
        cmp_config = """router bgp 65000
 neighbor 192.168.1.3
  remote-as 65003
  description Peer Router
  update-source Loopback0
 network 10.0.0.0"""
        
        ref_conf = Conf.from_string(ref_config)
        cmp_conf = Conf.from_string(cmp_config)
        
        deleted, added, modified_root, modified_children = compare_confs(ref_conf, cmp_conf)
        
        # Identical children (description, update-source, network) should not appear
        assert len(deleted) == 0, "Identical children should not be deleted"
        assert len(added) == 0, "Identical children should not be added"
        
        # neighbor line (level 1) has same parent (router bgp 65000) so should be in modified_children
        assert len(modified_children) == 1
        neighbor_modified = False
        for diff_dict in modified_children:
            for item in diff_dict["modified_children"]:
                if isinstance(item, dict) and "reference" in item:
                    if item["reference"].content[0] == "neighbor":
                        neighbor_modified = True
                        # Verify parents are identical
                        assert item["reference"].parent.content == ["router", "bgp", "65000"]
                        assert item["compared"].parent.content == ["router", "bgp", "65000"]
        assert neighbor_modified, "Neighbor line should be in modified_children"
        
        # remote-as should NOT be in modified_children because its parents are DIFFERENT
        # (neighbor 192.168.1.2 vs neighbor 192.168.1.3)
        remote_as_in_modified = False
        for diff_dict in modified_children:
            for item in diff_dict["modified_children"]:
                if isinstance(item, dict) and "reference" in item:
                    if item["reference"].content[0] == "remote-as":
                        remote_as_in_modified = True
        assert not remote_as_in_modified, "Remote-as should NOT be in modified_children (different parents)"
    
    def test_deep_nesting_with_mixed_changes(self):
        """Test comparison with deep nesting - children with IDENTICAL parents."""
        ref_config = """router bgp 65000
 neighbor 192.168.1.1
  remote-as 65001
  address-family ipv4
   activate
   send-community
  description Main Peer"""
        
        cmp_config = """router bgp 65000
 neighbor 192.168.1.1
  remote-as 65002
  address-family ipv4
   activate
   send-community both
  description Main Peer"""
        
        ref_conf = Conf.from_string(ref_config)
        cmp_conf = Conf.from_string(cmp_config)
        
        deleted, added, modified_root, modified_children = compare_confs(ref_conf, cmp_conf)
        
        # Identical children should not appear in deleted/added
        activate_in_deleted = any(
            "activate" in line.content for line in deleted
        )
        activate_in_added = any(
            "activate" in line.content for line in added
        )
        assert not activate_in_deleted, "Identical 'activate' should not be deleted"
        assert not activate_in_added, "Identical 'activate' should not be added"
        
        # neighbor is IDENTICAL (192.168.1.1 in both), so its children can be compared
        # Should have separate entries for neighbor (level 1) and address-family (level 2)
        remote_as_modified = False
        send_community_modified = False
        
        for diff_dict in modified_children:
            parent = diff_dict["parent"]
            
            # Check for remote-as under neighbor
            if parent.content[0] == "neighbor":
                for item in diff_dict["modified_children"]:
                    if item["reference"].content[0] == "remote-as":
                        remote_as_modified = True
                        assert item["reference"].parent.content == ["neighbor", "192.168.1.1"]
                        assert item["compared"].parent.content == ["neighbor", "192.168.1.1"]
            
            # Check for send-community under address-family
            if parent.content[0] == "address-family":
                for item in diff_dict["modified_children"]:
                    if item["reference"].content[0] == "send-community":
                        send_community_modified = True
        
        assert remote_as_modified, "remote-as should be in modified_children (same parent)"
        assert send_community_modified, "send-community should be in modified_children (same parent)"
        
        # description is identical, should not appear
        description_in_deleted = any(
            line.content[0] == "description" for line in deleted
        )
        description_in_added = any(
            line.content[0] == "description" for line in added
        )
        assert not description_in_deleted, "Identical 'description' should not be deleted"
        assert not description_in_added, "Identical 'description' should not be added"

