#!/usr/bin/env python3
"""
Command Line Interface for Network Simulator

This module provides a command-line interface for the network simulator,
allowing users to run simulations, validate configurations, and analyze
network topologies.
"""

import argparse
import sys
import os
import time
import logging
from typing import Dict, List, Any, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import (
    ConfigParser, TopologyGenerator, NetworkValidator, 
    NetworkSimulator, LogUtils, FileUtils
)

class NetworkSimulatorCLI:
    def __init__(self):
        self.parser = None
        self.args = None
        self.config_parser = ConfigParser()
        self.topology_generator = TopologyGenerator()
        self.validator = NetworkValidator()
        self.simulator = None
        
        # Setup logging
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        log_file = "logs/simulator.log"
        return LogUtils.setup_logging(log_file, "INFO")
    
    def parse_arguments(self):
        """Parse command line arguments"""
        parser = argparse.ArgumentParser(
            description="Network Simulator - Analyze and simulate network configurations",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Parse and validate configurations
  python cli.py --config-dir conf --validate
  
  # Generate topology and run simulation
  python cli.py --config-dir conf --simulate --duration 60
  
  # Run Day-1 scenario
  python cli.py --config-dir conf --day1-scenario
  
  # Inject faults and test
  python cli.py --config-dir conf --fault-scenario link_failure
            """
        )
        
        # Configuration options
        parser.add_argument(
            '--config-dir', '-c',
            default='conf',
            help='Directory containing configuration files (default: conf)'
        )
        
        parser.add_argument(
            '--output-dir', '-o',
            default='output',
            help='Output directory for results (default: output)'
        )
        
        # Action options
        parser.add_argument(
            '--validate', '-v',
            action='store_true',
            help='Validate network configurations'
        )
        
        parser.add_argument(
            '--topology', '-t',
            action='store_true',
            help='Generate network topology'
        )
        
        parser.add_argument(
            '--simulate', '-s',
            action='store_true',
            help='Run network simulation'
        )
        
        parser.add_argument(
            '--day1-scenario',
            action='store_true',
            help='Run Day-1 network discovery scenario'
        )
        
        parser.add_argument(
            '--fault-scenario',
            choices=['link_failure', 'interface_failure', 'device_failure'],
            help='Run predefined fault injection scenario'
        )
        
        # Simulation options
        parser.add_argument(
            '--duration', '-d',
            type=int,
            default=300,
            help='Simulation duration in seconds (default: 300)'
        )
        
        parser.add_argument(
            '--fault-injection',
            nargs=3,
            metavar=('TYPE', 'DEVICE', 'INTERFACE'),
            help='Inject specific fault: TYPE DEVICE INTERFACE'
        )
        
        # Output options
        parser.add_argument(
            '--export-json',
            action='store_true',
            help='Export results to JSON format'
        )
        
        parser.add_argument(
            '--export-topology',
            action='store_true',
            help='Export topology to JSON format'
        )
        
        parser.add_argument(
            '--export-validation',
            action='store_true',
            help='Export validation report to JSON format'
        )
        
        parser.add_argument(
            '--verbose', '-V',
            action='store_true',
            help='Enable verbose output'
        )
        
        parser.add_argument(
            '--quiet', '-q',
            action='store_true',
            help='Suppress output except errors'
        )
        
        self.parser = parser
        self.args = parser.parse_args()
        
        # Set log level based on arguments
        if self.args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        elif self.args.quiet:
            logging.getLogger().setLevel(logging.ERROR)
    
    def run(self):
        """Main CLI execution"""
        try:
            # Ensure output directory exists
            FileUtils.ensure_directory(self.args.output_dir)
            
            # Parse configurations
            configs = self._parse_configurations()
            if not configs:
                self.logger.error("No valid configurations found")
                return 1
            
            # Generate topology
            topology = None
            if self.args.topology or self.args.simulate or self.args.day1_scenario:
                topology = self._generate_topology(configs)
                if not topology:
                    self.logger.error("Failed to generate topology")
                    return 1
            
            # Validate configurations
            if self.args.validate:
                if not topology:
                    # Generate topology for validation if not already generated
                    topology = self._generate_topology(configs)
                    if not topology:
                        self.logger.error("Failed to generate topology for validation")
                        return 1
                self._validate_network(topology)
            
            # Export topology
            if self.args.export_topology:
                self._export_topology(topology)
            
            # Export validation report
            if self.args.export_validation and self.args.validate:
                self._export_validation_report()
            
            # Run simulation
            if self.args.simulate:
                self._run_simulation(topology)
            
            # Run Day-1 scenario
            if self.args.day1_scenario:
                self._run_day1_scenario(topology)
            
            # Run fault scenario
            if self.args.fault_scenario:
                self._run_fault_scenario(topology)
            
            # Inject specific fault
            if self.args.fault_injection:
                self._inject_specific_fault(topology)
            
            self.logger.info("CLI execution completed successfully")
            return 0
            
        except KeyboardInterrupt:
            self.logger.info("Operation cancelled by user")
            return 1
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            if self.args.verbose:
                import traceback
                traceback.print_exc()
            return 1
    
    def _parse_configurations(self) -> Dict[str, Any]:
        """Parse configuration files from the config directory"""
        self.logger.info(f"Parsing configurations from {self.args.config_dir}")
        
        if not os.path.exists(self.args.config_dir):
            self.logger.error(f"Configuration directory not found: {self.args.config_dir}")
            return {}
        
        configs = {}
        config_files = FileUtils.find_config_files(self.args.config_dir)
        
        if not config_files:
            self.logger.error(f"No configuration files found in {self.args.config_dir}")
            return {}
        
        for config_file in config_files:
            try:
                # Extract hostname from path (e.g., conf/R1/config.dump -> R1)
                hostname = os.path.basename(os.path.dirname(config_file))
                config = self.config_parser.parse_config_file(config_file)
                configs[hostname] = config
                self.logger.info(f"Parsed configuration for {hostname}")
                
            except Exception as e:
                self.logger.error(f"Error parsing {config_file}: {e}")
                continue
        
        self.logger.info(f"Successfully parsed {len(configs)} configurations")
        return configs
    
    def _generate_topology(self, configs: Dict[str, Any]):
        """Generate network topology from configurations"""
        self.logger.info("Generating network topology...")
        
        try:
            topology = self.topology_generator.generate_topology(configs)
            
            # Analyze topology
            analysis = self.topology_generator.analyze_topology()
            self.logger.info(f"Topology generated: {analysis['total_devices']} devices, {analysis['total_links']} links")
            
            # Print topology summary
            if not self.args.quiet:
                self._print_topology_summary(topology, analysis)
            
            return topology
            
        except Exception as e:
            self.logger.error(f"Error generating topology: {e}")
            return None
    
    def _print_topology_summary(self, topology, analysis):
        """Print a summary of the generated topology"""
        print("\n" + "="*60)
        print("NETWORK TOPOLOGY SUMMARY")
        print("="*60)
        
        print(f"Total Devices: {analysis['total_devices']}")
        print(f"Total Links: {analysis['total_links']}")
        print(f"Total Subnets: {analysis['total_subnets']}")
        print(f"Total VLANs: {analysis['total_vlans']}")
        print(f"Routing Domains: {analysis['routing_domains']}")
        
        print(f"\nConnectivity: {analysis['connectivity']['status']}")
        
        print(f"\nBandwidth Analysis:")
        print(f"  Total Bandwidth: {analysis['bandwidth_analysis']['total_bandwidth_mbps']} Mbps")
        print(f"  Average Bandwidth: {analysis['bandwidth_analysis']['average_bandwidth_mbps']:.1f} Mbps")
        
        if analysis['potential_issues']:
            print(f"\nPotential Issues:")
            for issue in analysis['potential_issues']:
                print(f"  - {issue}")
        
        print("="*60)
    
    def _validate_network(self, topology):
        """Validate network configuration"""
        self.logger.info("Validating network configuration...")
        
        try:
            issues, recommendations = self.validator.validate_network(topology)
            
            if not self.args.quiet:
                self._print_validation_results(issues, recommendations)
            
            # Store validation results for export
            self._validation_issues = issues
            self._validation_recommendations = recommendations
            
        except Exception as e:
            self.logger.error(f"Error during validation: {e}")
    
    def _print_validation_results(self, issues, recommendations):
        """Print validation results"""
        print("\n" + "="*60)
        print("NETWORK VALIDATION RESULTS")
        print("="*60)
        
        if not issues:
            print("✅ No validation issues found!")
        else:
            print(f"❌ Found {len(issues)} validation issues:")
            for issue in issues:
                severity_icon = {
                    'error': '🔴',
                    'warning': '🟡',
                    'info': '🔵'
                }.get(issue.severity, '⚪')
                
                print(f"\n{severity_icon} {issue.severity.upper()}: {issue.message}")
                print(f"   Category: {issue.category}")
                print(f"   Affected Devices: {', '.join(issue.affected_devices)}")
                if issue.affected_interfaces:
                    print(f"   Affected Interfaces: {', '.join(issue.affected_interfaces)}")
                print(f"   Recommendation: {issue.recommendation}")
        
        if recommendations:
            print(f"\n💡 {len(recommendations)} optimization recommendations:")
            for rec in recommendations:
                priority_icon = {
                    'high': '🔴',
                    'medium': '🟡',
                    'low': '🟢'
                }.get(rec.priority, '⚪')
                
                print(f"\n{priority_icon} {rec.priority.upper()} PRIORITY: {rec.description}")
                print(f"   Impact: {rec.impact}")
                print(f"   Implementation: {rec.implementation}")
                print(f"   Estimated Effort: {rec.estimated_effort}")
        
        print("="*60)
    
    def _export_topology(self, topology):
        """Export topology to JSON file"""
        output_file = os.path.join(self.args.output_dir, "topology.json")
        try:
            topology.export_topology(output_file)
            self.logger.info(f"Topology exported to {output_file}")
        except Exception as e:
            self.logger.error(f"Error exporting topology: {e}")
    
    def _export_validation_report(self):
        """Export validation report to JSON file"""
        output_file = os.path.join(self.args.output_dir, "validation_report.json")
        try:
            self.validator.export_validation_report(output_file)
            self.logger.info(f"Validation report exported to {output_file}")
        except Exception as e:
            self.logger.error(f"Error exporting validation report: {e}")
    
    def _run_simulation(self, topology):
        """Run network simulation"""
        self.logger.info(f"Starting network simulation for {self.args.duration} seconds...")
        
        try:
            # Create simulator
            self.simulator = NetworkSimulator(topology)
            
            # Start simulation
            self.simulator.start_simulation()
            
            # Run for specified duration
            start_time = time.time()
            while time.time() - start_time < self.args.duration:
                if not self.args.quiet:
                    self._print_simulation_status()
                time.sleep(5)
            
            # Stop simulation
            self.simulator.stop_simulation()
            
            # Export simulation log
            if self.args.export_json:
                log_file = os.path.join(self.args.output_dir, "simulation_log.json")
                self.simulator.export_simulation_log(log_file)
            
            self.logger.info("Simulation completed")
            
        except Exception as e:
            self.logger.error(f"Error during simulation: {e}")
            if self.simulator:
                self.simulator.stop_simulation()
    
    def _print_simulation_status(self):
        """Print current simulation status"""
        if not self.simulator:
            return
        
        status = self.simulator.get_network_status()
        print(f"\rSimulation Time: {status['simulation_time']:.1f}s | "
              f"Devices Online: {status['statistics']['devices_online']} | "
              f"Active Faults: {status['active_faults']}", end='', flush=True)
    
    def _run_day1_scenario(self, topology):
        """Run Day-1 network discovery scenario"""
        self.logger.info("Running Day-1 network discovery scenario...")
        
        try:
            # Create simulator
            self.simulator = NetworkSimulator(topology)
            
            # Start simulation
            self.simulator.start_simulation()
            
            # Run Day-1 scenario
            self.simulator.run_day1_scenario()
            
            # Let it run for a bit to see discovery
            time.sleep(10)
            
            # Stop simulation
            self.simulator.stop_simulation()
            
            self.logger.info("Day-1 scenario completed")
            
        except Exception as e:
            self.logger.error(f"Error during Day-1 scenario: {e}")
            if self.simulator:
                self.simulator.stop_simulation()
    
    def _run_fault_scenario(self, topology):
        """Run predefined fault injection scenario"""
        self.logger.info(f"Running fault scenario: {self.args.fault_scenario}")
        
        try:
            # Create simulator
            self.simulator = NetworkSimulator(topology)
            
            # Start simulation
            self.simulator.start_simulation()
            
            # Run fault scenario
            self.simulator.run_fault_scenario(self.args.fault_scenario)
            
            # Let it run to see fault effects
            time.sleep(15)
            
            # Stop simulation
            self.simulator.stop_simulation()
            
            self.logger.info(f"Fault scenario {self.args.fault_scenario} completed")
            
        except Exception as e:
            self.logger.error(f"Error during fault scenario: {e}")
            if self.simulator:
                self.simulator.stop_simulation()
    
    def _inject_specific_fault(self, topology):
        """Inject a specific fault"""
        fault_type, device, interface = self.args.fault_injection
        
        self.logger.info(f"Injecting fault: {fault_type} on {device}:{interface}")
        
        try:
            # Create simulator
            self.simulator = NetworkSimulator(topology)
            
            # Start simulation
            self.simulator.start_simulation()
            
            # Inject fault
            self.simulator.inject_fault(fault_type, device, interface, duration=30)
            
            # Let it run to see fault effects
            time.sleep(20)
            
            # Stop simulation
            self.simulator.stop_simulation()
            
            self.logger.info(f"Specific fault injection completed")
            
        except Exception as e:
            self.logger.error(f"Error during fault injection: {e}")
            if self.simulator:
                self.simulator.stop_simulation()

def main():
    """Main entry point for CLI"""
    cli = NetworkSimulatorCLI()
    cli.parse_arguments()
    sys.exit(cli.run())

if __name__ == "__main__":
    main() 