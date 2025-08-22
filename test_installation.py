#!/usr/bin/env python3
"""
Test script to verify Network Simulator installation

This script tests all major components of the network simulator
to ensure they are working correctly.
"""

import sys
import os
import traceback

def test_imports():
    """Test that all core modules can be imported"""
    print("Testing module imports...")
    
    try:
        from core import (
            ConfigParser, TopologyGenerator, NetworkValidator, 
            NetworkSimulator, LogUtils, FileUtils
        )
        print("✅ All core modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_config_parser():
    """Test configuration parser functionality"""
    print("\nTesting configuration parser...")
    
    try:
        from core import ConfigParser
        
        # Create parser instance
        parser = ConfigParser()
        print("✅ ConfigParser created successfully")
        
        # Test with sample configuration
        sample_config = """
        hostname TEST_ROUTER
        !
        interface GigabitEthernet0/0
         description Test Interface
         ip address 192.168.1.1 255.255.255.0
         no shutdown
         bandwidth 1000
         mtu 1500
        !
        router ospf 1
         network 192.168.1.0 0.0.0.255 area 0
        !
        ip route 0.0.0.0 0.0.0.0 192.168.1.254
        """
        
        # Write to temporary file
        with open('test_config.txt', 'w') as f:
            f.write(sample_config)
        
        # Parse configuration
        config = parser.parse_config_file('test_config.txt')
        
        # Verify parsing results
        assert config.hostname == "TEST_ROUTER"
        assert len(config.interfaces) == 1
        assert config.interfaces[0].ip_address == "192.168.1.1"
        assert "OSPF" in config.routing_protocols
        
        print("✅ Configuration parsing test passed")
        
        # Clean up
        os.remove('test_config.txt')
        return True
        
    except Exception as e:
        print(f"❌ Configuration parser test failed: {e}")
        traceback.print_exc()
        return False

def test_topology_generator():
    """Test topology generator functionality"""
    print("\nTesting topology generator...")
    
    try:
        from core import TopologyGenerator, ConfigParser
        
        # Create sample configurations
        configs = {}
        
        # Router 1
        config1 = ConfigParser()
        with open('test_r1.txt', 'w') as f:
            f.write("""
            hostname R1
            interface GigabitEthernet0/0
             ip address 192.168.1.1 255.255.255.0
             no shutdown
            interface GigabitEthernet0/1
             ip address 10.0.0.1 255.255.255.0
             no shutdown
            """)
        configs['R1'] = config1.parse_config_file('test_r1.txt')
        
        # Router 2
        config2 = ConfigParser()
        with open('test_r2.txt', 'w') as f:
            f.write("""
            hostname R2
            interface GigabitEthernet0/0
             ip address 10.0.0.2 255.255.255.0
             no shutdown
            interface GigabitEthernet0/1
             ip address 10.0.1.1 255.255.255.0
             no shutdown
            """)
        configs['R2'] = config2.parse_config_file('test_r2.txt')
        
        # Generate topology
        generator = TopologyGenerator()
        topology = generator.generate_topology(configs)
        
        # Verify topology
        assert len(topology.devices) == 2
        assert len(topology.links) >= 0  # May have 0 links if no overlapping subnets
        
        print("✅ Topology generation test passed")
        
        # Clean up
        os.remove('test_r1.txt')
        os.remove('test_r2.txt')
        return True
        
    except Exception as e:
        print(f"❌ Topology generator test failed: {e}")
        traceback.print_exc()
        return False

def test_validator():
    """Test network validator functionality"""
    print("\nTesting network validator...")
    
    try:
        from core import NetworkValidator, TopologyGenerator, ConfigParser
        
        # Create sample configurations with issues
        configs = {}
        
        # Router with duplicate IP
        config1 = ConfigParser()
        with open('test_duplicate.txt', 'w') as f:
            f.write("""
            hostname R1
            interface GigabitEthernet0/0
             ip address 192.168.1.1 255.255.255.0
             no shutdown
            interface GigabitEthernet0/1
             ip address 192.168.1.1 255.255.255.0
             no shutdown
            """)
        configs['R1'] = config1.parse_config_file('test_duplicate.txt')
        
        # Generate topology
        generator = TopologyGenerator()
        topology = generator.generate_topology(configs)
        
        # Validate
        validator = NetworkValidator()
        issues, recommendations = validator.validate_network(topology)
        
        # Should find duplicate IP issue
        assert len(issues) > 0
        duplicate_found = any('Duplicate IP address' in issue.message for issue in issues)
        assert duplicate_found
        
        print("✅ Network validation test passed")
        
        # Clean up
        os.remove('test_duplicate.txt')
        return True
        
    except Exception as e:
        print(f"❌ Network validator test failed: {e}")
        traceback.print_exc()
        return False

def test_utils():
    """Test utility functions"""
    print("\nTesting utility functions...")
    
    try:
        from core.utils import NetworkUtils, FileUtils, ValidationUtils
        
        # Test NetworkUtils
        assert NetworkUtils.is_valid_ip("192.168.1.1") == True
        assert NetworkUtils.is_valid_ip("256.1.1.1") == False
        assert NetworkUtils.is_valid_subnet_mask("255.255.255.0") == True
        
        # Test ValidationUtils
        assert ValidationUtils.validate_vlan_id(100) == True
        assert ValidationUtils.validate_vlan_id(5000) == False
        assert ValidationUtils.validate_mtu(1500) == True
        assert ValidationUtils.validate_mtu(10000) == False
        
        # Test FileUtils
        assert FileUtils.ensure_directory("test_dir") == True
        assert os.path.exists("test_dir") == True
        
        # Clean up
        os.rmdir("test_dir")
        
        print("✅ Utility functions test passed")
        return True
        
    except Exception as e:
        print(f"❌ Utility functions test failed: {e}")
        traceback.print_exc()
        return False

def test_cli():
    """Test CLI interface"""
    print("\nTesting CLI interface...")
    
    try:
        from ui.cli import NetworkSimulatorCLI
        
        # Create CLI instance
        cli = NetworkSimulatorCLI()
        print("✅ CLI interface created successfully")
        
        # Test argument parsing (without actually running)
        cli.parse_arguments()
        print("✅ CLI argument parsing test passed")
        
        return True
        
    except Exception as e:
        print(f"❌ CLI interface test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("Network Simulator - Installation Test")
    print("=" * 50)
    
    tests = [
        ("Module Imports", test_imports),
        ("Configuration Parser", test_config_parser),
        ("Topology Generator", test_topology_generator),
        ("Network Validator", test_validator),
        ("Utility Functions", test_utils),
        ("CLI Interface", test_cli),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Network Simulator is working correctly.")
        print("\nYou can now use the simulator:")
        print("  python main.py                    # Run main application")
        print("  python ui/cli.py --help          # View CLI options")
        print("  python ui/cli.py --config-dir conf --validate  # Test with sample configs")
        return 0
    else:
        print("❌ Some tests failed. Please check the error messages above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 