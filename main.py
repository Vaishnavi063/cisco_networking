#!/usr/bin/env python3
"""
Network Simulator - Main Entry Point

This is the main entry point for the network simulator application.
It provides a high-level interface for running simulations, validating
configurations, and analyzing network topologies.
"""

import os
import sys
import logging
import time
from typing import Dict, List, Any, Optional

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core import (
    ConfigParser, TopologyGenerator, NetworkValidator, 
    NetworkSimulator, LogUtils, FileUtils
)

class NetworkSimulatorApp:
    def __init__(self):
        self.config_parser = ConfigParser()
        self.topology_generator = TopologyGenerator()
        self.validator = NetworkValidator()
        self.simulator = None
        
        # Setup logging
        self.logger = self._setup_logging()
        
        # Configuration
        self.config_dir = "conf"
        self.output_dir = "output"
        self.log_dir = "logs"
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        log_file = "logs/simulator.log"
        return LogUtils.setup_logging(log_file, "INFO")
    
    def _ensure_directories(self):
        """Ensure required directories exist"""
        directories = [self.config_dir, self.output_dir, self.log_dir]
        for directory in directories:
            FileUtils.ensure_directory(directory)
    
    def run_full_analysis(self, config_dir: Optional[str] = None) -> Dict[str, Any]:
        """Run complete network analysis including parsing, validation, and topology generation"""
        if config_dir:
            self.config_dir = config_dir
        
        self.logger.info("Starting full network analysis...")
        
        try:
            # Step 1: Parse configurations
            self.logger.info("Step 1: Parsing network configurations...")
            configs = self._parse_configurations()
            if not configs:
                raise ValueError("No valid configurations found")
            
            # Step 2: Generate topology
            self.logger.info("Step 2: Generating network topology...")
            topology = self._generate_topology(configs)
            if not topology:
                raise ValueError("Failed to generate topology")
            
            # Step 3: Validate network
            self.logger.info("Step 3: Validating network configuration...")
            validation_results = self._validate_network(topology)
            
            # Step 4: Analyze topology
            self.logger.info("Step 4: Analyzing network topology...")
            topology_analysis = self.topology_generator.analyze_topology()
            
            # Compile results
            results = {
                'configurations': {
                    'total_devices': len(configs),
                    'devices': list(configs.keys())
                },
                'topology': {
                    'total_devices': topology_analysis['total_devices'],
                    'total_links': topology_analysis['total_links'],
                    'total_subnets': topology_analysis['total_subnets'],
                    'total_vlans': topology_analysis['total_vlans'],
                    'routing_domains': topology_analysis['routing_domains'],
                    'connectivity': topology_analysis['connectivity'],
                    'bandwidth_analysis': topology_analysis['bandwidth_analysis'],
                    'potential_issues': topology_analysis['potential_issues']
                },
                'validation': validation_results,
                'timestamp': time.time()
            }
            
            self.logger.info("Full network analysis completed successfully")
            return results
            
        except Exception as e:
            self.logger.error(f"Error during full analysis: {e}")
            raise
    
    def run_simulation(self, config_dir: Optional[str] = None, 
                      duration: int = 300, scenario: Optional[str] = None) -> Dict[str, Any]:
        """Run network simulation"""
        if config_dir:
            self.config_dir = config_dir
        
        self.logger.info(f"Starting network simulation for {duration} seconds...")
        
        try:
            # Parse configurations and generate topology
            configs = self._parse_configurations()
            if not configs:
                raise ValueError("No valid configurations found")
            
            topology = self._generate_topology(configs)
            if not topology:
                raise ValueError("Failed to generate topology")
            
            # Create and start simulator
            self.simulator = NetworkSimulator(topology)
            self.simulator.start_simulation()
            
            # Run specific scenario if requested
            if scenario:
                if scenario == 'day1':
                    self.logger.info("Running Day-1 network discovery scenario...")
                    self.simulator.run_day1_scenario()
                elif scenario in ['link_failure', 'interface_failure', 'device_failure']:
                    self.logger.info(f"Running fault scenario: {scenario}")
                    self.simulator.run_fault_scenario(scenario)
            
            # Run simulation for specified duration
            start_time = time.time()
            while time.time() - start_time < duration:
                time.sleep(1)
            
            # Stop simulation
            self.simulator.stop_simulation()
            
            # Get final status
            final_status = self.simulator.get_network_status()
            
            # Export simulation log
            log_file = os.path.join(self.output_dir, "simulation_log.json")
            self.simulator.export_simulation_log(log_file)
            
            self.logger.info("Network simulation completed successfully")
            
            return {
                'simulation_duration': duration,
                'final_status': final_status,
                'log_file': log_file,
                'timestamp': time.time()
            }
            
        except Exception as e:
            self.logger.error(f"Error during simulation: {e}")
            if self.simulator:
                self.simulator.stop_simulation()
            raise
    
    def inject_fault(self, fault_type: str, target_device: str, 
                    target_interface: Optional[str] = None, 
                    duration: Optional[int] = None) -> bool:
        """Inject a fault into the network"""
        if not self.simulator:
            self.logger.error("No active simulation to inject fault into")
            return False
        
        try:
            self.simulator.inject_fault(
                fault_type, target_device, target_interface, 
                duration=duration
            )
            self.logger.info(f"Fault injected: {fault_type} on {target_device}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error injecting fault: {e}")
            return False
    
    def export_results(self, results: Dict[str, Any], filename: str) -> bool:
        """Export analysis results to JSON file"""
        try:
            output_file = os.path.join(self.output_dir, filename)
            FileUtils.safe_write_json(results, output_file)
            self.logger.info(f"Results exported to {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting results: {e}")
            return False
    
    def _parse_configurations(self) -> Dict[str, Any]:
        """Parse configuration files from the config directory"""
        self.logger.info(f"Parsing configurations from {self.config_dir}")
        
        if not os.path.exists(self.config_dir):
            raise FileNotFoundError(f"Configuration directory not found: {self.config_dir}")
        
        configs = {}
        config_files = FileUtils.find_config_files(self.config_dir)
        
        if not config_files:
            raise FileNotFoundError(f"No configuration files found in {self.config_dir}")
        
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
        
        if not configs:
            raise ValueError("No valid configurations could be parsed")
        
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
            
            return topology
            
        except Exception as e:
            self.logger.error(f"Error generating topology: {e}")
            raise
    
    def _validate_network(self, topology) -> Dict[str, Any]:
        """Validate network configuration"""
        self.logger.info("Validating network configuration...")
        
        try:
            issues, recommendations = self.validator.validate_network(topology)
            
            validation_results = {
                'issues': [
                    {
                        'severity': issue.severity,
                        'category': issue.category,
                        'message': issue.message,
                        'affected_devices': issue.affected_devices,
                        'affected_interfaces': issue.affected_interfaces,
                        'recommendation': issue.recommendation
                    }
                    for issue in issues
                ],
                'recommendations': [
                    {
                        'category': rec.category,
                        'priority': rec.priority,
                        'description': rec.description,
                        'impact': rec.impact,
                        'implementation': rec.implementation,
                        'estimated_effort': rec.estimated_effort
                    }
                    for rec in recommendations
                ],
                'summary': {
                    'total_issues': len(issues),
                    'total_recommendations': len(recommendations),
                    'issues_by_severity': {},
                    'issues_by_category': {}
                }
            }
            
            # Calculate statistics
            for issue in issues:
                if issue.severity not in validation_results['summary']['issues_by_severity']:
                    validation_results['summary']['issues_by_severity'][issue.severity] = 0
                validation_results['summary']['issues_by_severity'][issue.severity] += 1
                
                if issue.category not in validation_results['summary']['issues_by_category']:
                    validation_results['summary']['issues_by_category'][issue.category] = 0
                validation_results['summary']['issues_by_category'][issue.category] += 1
            
            self.logger.info(f"Validation completed: {len(issues)} issues, {len(recommendations)} recommendations")
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Error during validation: {e}")
            raise
    
    def print_summary(self, results: Dict[str, Any]):
        """Print a summary of the analysis results"""
        print("\n" + "="*80)
        print("NETWORK SIMULATOR ANALYSIS SUMMARY")
        print("="*80)
        
        # Configuration summary
        config = results['configurations']
        print(f"\n📋 CONFIGURATION SUMMARY")
        print(f"   Total Devices: {config['total_devices']}")
        print(f"   Devices: {', '.join(config['devices'])}")
        
        # Topology summary
        topology = results['topology']
        print(f"\n🕸️  TOPOLOGY SUMMARY")
        print(f"   Total Devices: {topology['total_devices']}")
        print(f"   Total Links: {topology['total_links']}")
        print(f"   Total Subnets: {topology['total_subnets']}")
        print(f"   Total VLANs: {topology['total_vlans']}")
        print(f"   Routing Domains: {topology['routing_domains']}")
        
        print(f"   Connectivity: {topology['connectivity']['status']}")
        
        print(f"   Bandwidth Analysis:")
        print(f"     Total: {topology['bandwidth_analysis']['total_bandwidth_mbps']} Mbps")
        print(f"     Average: {topology['bandwidth_analysis']['average_bandwidth_mbps']:.1f} Mbps")
        
        if topology['potential_issues']:
            print(f"   Potential Issues: {len(topology['potential_issues'])}")
            for issue in topology['potential_issues'][:3]:  # Show first 3
                print(f"     - {issue}")
        
        # Validation summary
        validation = results['validation']
        print(f"\n✅ VALIDATION SUMMARY")
        print(f"   Total Issues: {validation['summary']['total_issues']}")
        print(f"   Total Recommendations: {validation['summary']['total_recommendations']}")
        
        if validation['issues']:
            print(f"   Issues by Severity:")
            for severity, count in validation['summary']['issues_by_severity'].items():
                print(f"     {severity.upper()}: {count}")
        
        if validation['recommendations']:
            print(f"   Recommendations by Priority:")
            priority_counts = {}
            for rec in validation['recommendations']:
                priority = rec['priority']
                priority_counts[priority] = priority_counts.get(priority, 0) + 1
            
            for priority, count in priority_counts.items():
                print(f"     {priority.upper()}: {count}")
        
        print("="*80)

def main():
    """Main entry point for the application"""
    print("Network Simulator - Starting...")
    
    try:
        # Create application instance
        app = NetworkSimulatorApp()
        
        # Run full analysis
        print("Running network analysis...")
        results = app.run_full_analysis()
        
        # Print summary
        app.print_summary(results)
        
        # Export results
        app.export_results(results, "analysis_results.json")
        
        # Ask user if they want to run simulation
        print("\nWould you like to run a network simulation? (y/n): ", end='')
        response = input().lower().strip()
        
        if response in ['y', 'yes']:
            print("Running network simulation...")
            simulation_results = app.run_simulation(duration=60, scenario='day1')
            print(f"Simulation completed. Log saved to: {simulation_results['log_file']}")
        
        print("\nNetwork Simulator completed successfully!")
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        logging.error(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 