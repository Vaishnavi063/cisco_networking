#!/usr/bin/env python3
"""
Quick Start Script for Network Simulator

This script provides a guided introduction to the network simulator,
running through basic functionality with the sample configurations.
"""

import os
import sys
import time

def print_banner():
    """Print welcome banner"""
    print("=" * 80)
    print("🚀 NETWORK SIMULATOR - QUICK START")
    print("=" * 80)
    print()
    print("Welcome to the Network Simulator! This script will guide you through")
    print("the basic features using the sample router configurations.")
    print()

def check_installation():
    """Check if the simulator is properly installed"""
    print("🔍 Checking installation...")
    
    try:
        # Try to import core modules
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from core import ConfigParser, TopologyGenerator, NetworkValidator
        print("✅ Core modules imported successfully")
        
        # Check if sample configs exist
        if os.path.exists("conf/R1/config.dump"):
            print("✅ Sample configurations found")
        else:
            print("❌ Sample configurations not found")
            return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please ensure all dependencies are installed:")
        print("  pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def run_demo():
    """Run a demonstration of the network simulator"""
    print("\n🎯 Running Network Simulator Demo...")
    print()
    
    try:
        from core import (
            ConfigParser, TopologyGenerator, NetworkValidator, 
            NetworkSimulator, LogUtils, FileUtils
        )
        
        # Step 1: Parse configurations
        print("📋 Step 1: Parsing router configurations...")
        config_parser = ConfigParser()
        configs = {}
        
        config_dir = "conf"
        for item in os.listdir(config_dir):
            item_path = os.path.join(config_dir, item)
            if os.path.isdir(item_path):
                config_file = os.path.join(item_path, "config.dump")
                if os.path.exists(config_file):
                    hostname = item
                    config = config_parser.parse_config_file(config_file)
                    configs[hostname] = config
                    print(f"   ✅ Parsed {hostname}: {len(config.interfaces)} interfaces")
        
        print(f"   📊 Total devices: {len(configs)}")
        
        # Step 2: Generate topology
        print("\n🕸️  Step 2: Generating network topology...")
        topology_generator = TopologyGenerator()
        topology = topology_generator.generate_topology(configs)
        
        analysis = topology_generator.analyze_topology()
        print(f"   📊 Topology generated: {analysis['total_devices']} devices, {analysis['total_links']} links")
        print(f"   🌐 Connectivity: {analysis['connectivity']['status']}")
        print(f"   📡 Total subnets: {analysis['total_subnets']}")
        print(f"   🏷️  Total VLANs: {analysis['total_vlans']}")
        
        # Step 3: Validate network
        print("\n✅ Step 3: Validating network configuration...")
        validator = NetworkValidator()
        issues, recommendations = validator.validate_network(topology)
        
        print(f"   📊 Found {len(issues)} issues and {len(recommendations)} recommendations")
        
        if issues:
            print("   ⚠️  Sample issues found:")
            for i, issue in enumerate(issues[:3]):  # Show first 3
                print(f"      {i+1}. {issue.message}")
        
        if recommendations:
            print("   💡 Sample recommendations:")
            for i, rec in enumerate(recommendations[:3]):  # Show first 3
                print(f"      {i+1}. {rec.description}")
        
        # Step 4: Run simulation
        print("\n🎮 Step 4: Running network simulation...")
        simulator = NetworkSimulator(topology)
        
        print("   🚀 Starting simulation...")
        simulator.start_simulation()
        
        print("   🔍 Running Day-1 network discovery scenario...")
        simulator.run_day1_scenario()
        
        print("   ⏱️  Running simulation for 10 seconds...")
        time.sleep(10)
        
        print("   🛑 Stopping simulation...")
        simulator.stop_simulation()
        
        # Get final status
        status = simulator.get_network_status()
        print(f"   📊 Final status: {status['statistics']['devices_online']} devices online")
        
        # Export results
        print("\n📤 Step 5: Exporting results...")
        
        # Ensure output directory exists
        FileUtils.ensure_directory("output")
        
        # Export topology
        topology_generator.export_topology("output/demo_topology.json")
        print("   ✅ Topology exported to output/demo_topology.json")
        
        # Export validation report
        validator.export_validation_report("output/demo_validation.json")
        print("   ✅ Validation report exported to output/demo_validation.json")
        
        # Export simulation log
        simulator.export_simulation_log("output/demo_simulation.json")
        print("   ✅ Simulation log exported to output/demo_simulation.json")
        
        print("\n🎉 Demo completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_next_steps():
    """Show users what they can do next"""
    print("\n" + "=" * 80)
    print("🚀 WHAT'S NEXT?")
    print("=" * 80)
    print()
    print("Now that you've seen the basic functionality, here are some things")
    print("you can try:")
    print()
    print("📋 BASIC USAGE:")
    print("  python main.py                    # Run the main application")
    print("  python ui/cli.py --help          # View all CLI options")
    print()
    print("🔍 ANALYSIS:")
    print("  python ui/cli.py --config-dir conf --validate")
    print("  python ui/cli.py --config-dir conf --topology")
    print("  python ui/cli.py --config-dir conf --export-topology")
    print()
    print("🎮 SIMULATION:")
    print("  python ui/cli.py --config-dir conf --day1-scenario")
    print("  python ui/cli.py --config-dir conf --fault-scenario link_failure")
    print("  python ui/cli.py --config-dir conf --simulate --duration 60")
    print()
    print("🧪 TESTING:")
    print("  python test_installation.py      # Run comprehensive tests")
    print("  pytest tests/ -v                 # Run unit tests")
    print()
    print("📚 DOCUMENTATION:")
    print("  README.md                        # Comprehensive guide")
    print("  Inline code documentation        # API reference")
    print()
    print("🔧 CUSTOMIZATION:")
    print("  Add your own router configs to conf/ directory")
    print("  Modify validation rules in core/validator.py")
    print("  Extend simulation scenarios in core/simulator.py")
    print()

def main():
    """Main quick start function"""
    print_banner()
    
    # Check installation
    if not check_installation():
        print("\n❌ Installation check failed. Please fix the issues above.")
        return 1
    
    print("✅ Installation check passed!")
    
    # Ask user if they want to run the demo
    print("\nWould you like to run a demonstration? (y/n): ", end='')
    response = input().lower().strip()
    
    if response in ['y', 'yes']:
        if run_demo():
            show_next_steps()
        else:
            print("\n❌ Demo failed. Please check the error messages above.")
            return 1
    else:
        print("\nSkipping demo. You can run it later with:")
        print("  python quick_start.py")
        show_next_steps()
    
    print("\n🎯 Quick start completed! Happy networking!")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Quick start interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1) 