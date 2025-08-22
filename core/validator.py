import ipaddress
import logging
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from .config_parser import ParsedConfig, ParsedInterface
from .topology_generator import NetworkTopology, NetworkLink
import networkx as nx

@dataclass
class ValidationIssue:
    severity: str  # 'error', 'warning', 'info'
    category: str  # 'ip', 'vlan', 'routing', 'performance', 'security'
    message: str
    affected_devices: List[str]
    affected_interfaces: List[str]
    recommendation: str

@dataclass
class OptimizationRecommendation:
    category: str
    priority: str  # 'high', 'medium', 'low'
    description: str
    impact: str
    implementation: str
    estimated_effort: str

class NetworkValidator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.issues = []
        self.recommendations = []
    
    def validate_network(self, topology: NetworkTopology) -> Tuple[List[ValidationIssue], List[OptimizationRecommendation]]:
        """Comprehensive network validation"""
        self.logger.info("Starting network validation...")
        
        # Reset previous results
        self.issues = []
        self.recommendations = []
        
        # Perform various validation checks
        self._validate_ip_configurations(topology)
        self._validate_vlan_configurations(topology)
        self._validate_routing_configurations(topology)
        self._validate_performance_configurations(topology)
        self._validate_security_configurations(topology)
        self._validate_network_redundancy(topology)
        
        # Generate optimization recommendations
        self._generate_optimization_recommendations(topology)
        
        self.logger.info(f"Validation complete. Found {len(self.issues)} issues and {len(self.recommendations)} recommendations")
        
        return self.issues, self.recommendations
    
    def _validate_ip_configurations(self, topology: NetworkTopology):
        """Validate IP addressing configurations"""
        self.logger.info("Validating IP configurations...")
        
        # Check for duplicate IP addresses
        ip_addresses = {}
        for hostname, config in topology.devices.items():
            for interface in config.interfaces:
                if interface.ip_address:
                    if interface.ip_address in ip_addresses:
                        self.issues.append(ValidationIssue(
                            severity='error',
                            category='ip',
                            message=f"Duplicate IP address {interface.ip_address}",
                            affected_devices=[hostname, ip_addresses[interface.ip_address]['device']],
                            affected_interfaces=[interface.name, ip_addresses[interface.ip_address]['interface']],
                            recommendation="Ensure each interface has a unique IP address"
                        ))
                    else:
                        ip_addresses[interface.ip_address] = {
                            'device': hostname,
                            'interface': interface.name
                        }
        
        # Check for invalid IP addresses
        for hostname, config in topology.devices.items():
            for interface in config.interfaces:
                if interface.ip_address:
                    try:
                        ipaddress.IPv4Address(interface.ip_address)
                    except ipaddress.AddressValueError:
                        self.issues.append(ValidationIssue(
                            severity='error',
                            category='ip',
                            message=f"Invalid IP address format: {interface.ip_address}",
                            affected_devices=[hostname],
                            affected_interfaces=[interface.name],
                            recommendation="Use valid IPv4 address format (e.g., 192.168.1.1)"
                        ))
        
        # Check for subnet mask issues
        for hostname, config in topology.devices.items():
            for interface in config.interfaces:
                if interface.subnet_mask:
                    try:
                        mask = ipaddress.IPv4Address(interface.subnet_mask)
                        # Check if it's a valid subnet mask
                        mask_int = int(mask)
                        if not self._is_valid_subnet_mask(mask_int):
                            self.issues.append(ValidationIssue(
                                severity='warning',
                                category='ip',
                                message=f"Questionable subnet mask: {interface.subnet_mask}",
                                affected_devices=[hostname],
                                affected_interfaces=[interface.name],
                                recommendation="Verify subnet mask is appropriate for network size"
                            ))
                    except ipaddress.AddressValueError:
                        self.issues.append(ValidationIssue(
                            severity='error',
                            category='ip',
                            message=f"Invalid subnet mask format: {interface.subnet_mask}",
                            affected_devices=[hostname],
                            affected_interfaces=[interface.name],
                            recommendation="Use valid subnet mask format (e.g., 255.255.255.0)"
                        ))
        
        # Check for network overlap
        networks = {}
        for hostname, config in topology.devices.items():
            for interface in config.interfaces:
                if interface.ip_address and interface.subnet_mask:
                    try:
                        network = ipaddress.IPv4Network(
                            f"{interface.ip_address}/{interface.subnet_mask}", 
                            strict=False
                        )
                        network_key = str(network)
                        
                        if network_key in networks:
                            # Check if networks overlap
                            existing_network = networks[network_key]['network']
                            if network.overlaps(existing_network):
                                self.issues.append(ValidationIssue(
                                    severity='warning',
                                    category='ip',
                                    message=f"Potential network overlap detected",
                                    affected_devices=[hostname, networks[network_key]['device']],
                                    affected_interfaces=[interface.name, networks[network_key]['interface']],
                                    recommendation="Review network addressing plan to avoid overlaps"
                                ))
                        else:
                            networks[network_key] = {
                                'network': network,
                                'device': hostname,
                                'interface': interface.name
                            }
                    except ValueError:
                        continue
    
    def _validate_vlan_configurations(self, topology: NetworkTopology):
        """Validate VLAN configurations"""
        self.logger.info("Validating VLAN configurations...")
        
        # Check for VLAN consistency
        vlan_interfaces = {}
        for hostname, config in topology.devices.items():
            for interface in config.interfaces:
                if interface.vlan:
                    vlan_id = interface.vlan
                    if vlan_id not in vlan_interfaces:
                        vlan_interfaces[vlan_id] = []
                    vlan_interfaces[vlan_id].append({
                        'device': hostname,
                        'interface': interface.name
                    })
        
        # Check for VLANs with only one interface
        for vlan_id, interfaces in vlan_interfaces.items():
            if len(interfaces) == 1:
                self.issues.append(ValidationIssue(
                    severity='warning',
                    category='vlan',
                    message=f"VLAN {vlan_id} has only one interface",
                    affected_devices=[interfaces[0]['device']],
                    affected_interfaces=[interfaces[0]['interface']],
                    recommendation="Consider removing VLAN or adding more interfaces"
                ))
        
        # Check for missing VLAN definitions
        defined_vlans = set(topology.vlans.keys())
        used_vlans = set(vlan_interfaces.keys())
        
        undefined_vlans = used_vlans - defined_vlans
        for vlan_id in undefined_vlans:
            affected = vlan_interfaces[vlan_id]
            self.issues.append(ValidationIssue(
                severity='warning',
                category='vlan',
                message=f"VLAN {vlan_id} is used but not defined",
                affected_devices=[item['device'] for item in affected],
                affected_interfaces=[item['interface'] for item in affected],
                recommendation="Define VLAN in switch configuration"
            ))
    
    def _validate_routing_configurations(self, topology: NetworkTopology):
        """Validate routing configurations"""
        self.logger.info("Validating routing configurations...")
        
        # Check for routing protocol conflicts
        routing_devices = {}
        for hostname, config in topology.devices.items():
            protocols = config.routing_protocols
            if protocols:
                routing_devices[hostname] = protocols
        
        # Check for multiple protocols on same device
        for hostname, protocols in routing_devices.items():
            if len(protocols) > 1:
                self.issues.append(ValidationIssue(
                    severity='warning',
                    category='routing',
                    message=f"Multiple routing protocols configured: {', '.join(protocols)}",
                    affected_devices=[hostname],
                    affected_interfaces=[],
                    recommendation="Consider using route redistribution or standardizing on one protocol"
                ))
        
        # Check for OSPF area consistency
        ospf_devices = {}
        for hostname, config in topology.devices.items():
            if 'OSPF' in config.routing_protocols:
                ospf_devices[hostname] = config.ospf_areas
        
        # Check if OSPF areas are consistent across devices
        if len(ospf_devices) > 1:
            all_areas = set()
            for areas in ospf_devices.values():
                all_areas.update(areas)
            
            for hostname, areas in ospf_devices.items():
                if not areas:
                    self.issues.append(ValidationIssue(
                        severity='warning',
                        category='routing',
                        message="OSPF configured but no areas defined",
                        affected_devices=[hostname],
                        affected_interfaces=[],
                        recommendation="Configure OSPF areas for better network organization"
                    ))
        
        # Check for BGP ASN consistency
        bgp_devices = {}
        for hostname, config in topology.devices.items():
            if config.bgp_asn:
                bgp_devices[hostname] = config.bgp_asn
        
        if len(bgp_devices) > 1:
            asns = list(bgp_devices.values())
            if len(set(asns)) > 1:
                self.issues.append(ValidationIssue(
                    severity='warning',
                    category='routing',
                    message="Multiple BGP ASNs detected",
                    affected_devices=list(bgp_devices.keys()),
                    affected_interfaces=[],
                    recommendation="Verify BGP ASN configuration for external BGP sessions"
                ))
    
    def _validate_performance_configurations(self, topology: NetworkTopology):
        """Validate performance-related configurations"""
        self.logger.info("Validating performance configurations...")
        
        # Check for MTU mismatches
        mtu_by_subnet = {}
        for hostname, config in topology.devices.items():
            for interface in config.interfaces:
                if interface.ip_address and interface.subnet_mask and interface.mtu:
                    try:
                        network = ipaddress.IPv4Network(
                            f"{interface.ip_address}/{interface.subnet_mask}", 
                            strict=False
                        )
                        network_key = str(network)
                        
                        if network_key not in mtu_by_subnet:
                            mtu_by_subnet[network_key] = []
                        
                        mtu_by_subnet[network_key].append({
                            'device': hostname,
                            'interface': interface.name,
                            'mtu': interface.mtu
                        })
                    except ValueError:
                        continue
        
        # Check for MTU inconsistencies in same subnet
        for subnet, interfaces in mtu_by_subnet.items():
            if len(interfaces) > 1:
                mtus = [intf['mtu'] for intf in interfaces]
                if len(set(mtus)) > 1:
                    self.issues.append(ValidationIssue(
                        severity='warning',
                        category='performance',
                        message=f"MTU mismatch in subnet {subnet}",
                        affected_devices=[intf['device'] for intf in interfaces],
                        affected_interfaces=[intf['interface'] for intf in interfaces],
                        recommendation="Standardize MTU values within subnets for optimal performance"
                    ))
        
        # Check for bandwidth bottlenecks
        low_bandwidth_links = []
        for link in topology.links:
            if link.bandwidth < 100:  # Less than 100 Mbps
                low_bandwidth_links.append(link)
        
        if low_bandwidth_links:
            self.issues.append(ValidationIssue(
                severity='warning',
                category='performance',
                message=f"Low bandwidth links detected: {len(low_bandwidth_links)} links < 100 Mbps",
                affected_devices=list(set([link.source_device for link in low_bandwidth_links] + 
                                        [link.target_device for link in low_bandwidth_links])),
                affected_interfaces=list(set([link.source_interface for link in low_bandwidth_links] + 
                                           [link.target_interface for link in low_bandwidth_links])),
                recommendation="Consider upgrading low-bandwidth links for better performance"
            ))
    
    def _validate_security_configurations(self, topology: NetworkTopology):
        """Validate security-related configurations"""
        self.logger.info("Validating security configurations...")
        
        # Check for missing access lists
        devices_without_acls = []
        for hostname, config in topology.devices.items():
            if not config.access_lists:
                devices_without_acls.append(hostname)
        
        if devices_without_acls:
            self.issues.append(ValidationIssue(
                severity='info',
                category='security',
                message=f"No access lists configured on {len(devices_without_acls)} devices",
                affected_devices=devices_without_acls,
                affected_interfaces=[],
                recommendation="Consider implementing access lists for traffic filtering"
            ))
        
        # Check for default gateway configurations
        devices_without_gateway = []
        for hostname, config in topology.devices.items():
            if not config.default_gateway:
                devices_without_gateway.append(hostname)
        
        if devices_without_gateway:
            self.issues.append(ValidationIssue(
                severity='warning',
                category='security',
                message=f"No default gateway configured on {len(devices_without_gateway)} devices",
                affected_devices=devices_without_gateway,
                affected_interfaces=[],
                recommendation="Configure default gateways for proper routing"
            ))
    
    def _validate_network_redundancy(self, topology: NetworkTopology):
        """Validate network redundancy and failover capabilities"""
        self.logger.info("Validating network redundancy...")
        
        # Check for single points of failure
        graph = topology.graph
        
        # Find articulation points (single points of failure)
        articulation_points = list(nx.articulation_points(graph))
        if articulation_points:
            self.issues.append(ValidationIssue(
                severity='warning',
                category='redundancy',
                message=f"Single points of failure detected: {', '.join(articulation_points)}",
                affected_devices=articulation_points,
                affected_interfaces=[],
                recommendation="Implement redundant paths to eliminate single points of failure"
            ))
        
        # Check for isolated devices
        isolated_nodes = [node for node in graph.nodes() if graph.degree(node) == 0]
        if isolated_nodes:
            self.issues.append(ValidationIssue(
                severity='error',
                category='redundancy',
                message=f"Isolated devices detected: {', '.join(isolated_nodes)}",
                affected_devices=isolated_nodes,
                affected_interfaces=[],
                recommendation="Connect isolated devices to the network"
            ))
        
        # Check for redundant links
        redundant_links = []
        for link in topology.links:
            # Check if there are multiple paths between source and target
            source = link.source_device
            target = link.target_device
            
            # Remove this link temporarily to check for alternative paths
            graph_temp = graph.copy()
            graph_temp.remove_edge(source, target)
            
            if nx.has_path(graph_temp, source, target):
                redundant_links.append(link)
        
        if redundant_links:
            self.issues.append(ValidationIssue(
                severity='info',
                category='redundancy',
                message=f"Redundant links detected: {len(redundant_links)} links provide backup paths",
                affected_devices=list(set([link.source_device for link in redundant_links] + 
                                        [link.target_device for link in redundant_links])),
                affected_interfaces=list(set([link.source_interface for link in redundant_links] + 
                                           [link.target_interface for link in redundant_links])),
                recommendation="Consider implementing load balancing across redundant links"
            ))
    
    def _generate_optimization_recommendations(self, topology: NetworkTopology):
        """Generate optimization recommendations"""
        self.logger.info("Generating optimization recommendations...")
        
        # Bandwidth optimization
        total_bandwidth = sum(link.bandwidth for link in topology.links)
        avg_bandwidth = total_bandwidth / len(topology.links) if topology.links else 0
        
        if avg_bandwidth < 1000:  # Less than 1 Gbps average
            self.recommendations.append(OptimizationRecommendation(
                category='performance',
                priority='medium',
                description="Upgrade low-bandwidth links to improve network performance",
                impact="Significant improvement in data transfer speeds and reduced latency",
                implementation="Replace FastEthernet links with GigabitEthernet or higher",
                estimated_effort="Medium - requires hardware upgrades"
            ))
        
        # Routing protocol optimization
        ospf_count = sum(1 for config in topology.devices.values() if 'OSPF' in config.routing_protocols)
        bgp_count = sum(1 for config in topology.devices.values() if 'BGP' in config.routing_protocols)
        
        if ospf_count > 5 and bgp_count == 0:
            self.recommendations.append(OptimizationRecommendation(
                category='routing',
                priority='low',
                description="Consider implementing BGP for large-scale routing",
                impact="Better scalability and policy-based routing for large networks",
                implementation="Configure BGP on border routers and implement route redistribution",
                estimated_effort="High - requires routing protocol changes"
            ))
        
        # VLAN optimization
        if len(topology.vlans) > 10:
            self.recommendations.append(OptimizationRecommendation(
                category='management',
                priority='low',
                description="Consolidate VLANs for better management",
                impact="Simplified network management and reduced configuration complexity",
                implementation="Review VLAN assignments and merge similar-purpose VLANs",
                estimated_effort="Medium - requires careful planning and testing"
            ))
        
        # Security optimization
        devices_without_acls = sum(1 for config in topology.devices.values() if not config.access_lists)
        if devices_without_acls > len(topology.devices) * 0.5:  # More than 50% without ACLs
            self.recommendations.append(OptimizationRecommendation(
                category='security',
                priority='medium',
                description="Implement access control lists for traffic filtering",
                impact="Improved network security and traffic control",
                implementation="Configure standard and extended ACLs based on security requirements",
                estimated_effort="Medium - requires security policy definition and implementation"
            ))
    
    def _is_valid_subnet_mask(self, mask_int: int) -> bool:
        """Check if an integer represents a valid subnet mask"""
        # Convert to binary and check if it's a valid subnet mask
        binary = bin(mask_int)[2:].zfill(32)
        
        # Check if it's all 1s followed by all 0s
        found_zero = False
        for bit in binary:
            if bit == '0':
                found_zero = True
            elif found_zero and bit == '1':
                return False
        
        return True
    
    def export_validation_report(self, output_file: str):
        """Export validation results to a report file"""
        import json
        
        report = {
            'summary': {
                'total_issues': len(self.issues),
                'total_recommendations': len(self.recommendations),
                'issues_by_severity': {},
                'issues_by_category': {}
            },
            'issues': [
                {
                    'severity': issue.severity,
                    'category': issue.category,
                    'message': issue.message,
                    'affected_devices': issue.affected_devices,
                    'affected_interfaces': issue.affected_interfaces,
                    'recommendation': issue.recommendation
                }
                for issue in self.issues
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
                for rec in self.recommendations
            ]
        }
        
        # Calculate statistics
        for issue in self.issues:
            if issue.severity not in report['summary']['issues_by_severity']:
                report['summary']['issues_by_severity'][issue.severity] = 0
            report['summary']['issues_by_severity'][issue.severity] += 1
            
            if issue.category not in report['summary']['issues_by_category']:
                report['summary']['issues_by_category'][issue.category] = 0
            report['summary']['issues_by_category'][issue.category] += 1
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Validation report exported to {output_file}")

# Example usage
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    print("NetworkValidator module loaded successfully")
    print("Use with TopologyGenerator to validate network configurations") 