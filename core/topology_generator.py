import networkx as nx
import ipaddress
import logging
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from .config_parser import ParsedConfig, ParsedInterface

@dataclass
class NetworkLink:
    source_device: str
    source_interface: str
    target_device: str
    target_interface: str
    bandwidth: int
    latency: float
    reliability: float
    link_type: str  # 'ethernet', 'serial', 'fiber', etc.

@dataclass
class NetworkTopology:
    devices: Dict[str, ParsedConfig]
    links: List[NetworkLink]
    graph: nx.Graph
    subnets: Dict[str, List[str]]
    vlans: Dict[int, List[str]]
    routing_domains: Dict[str, List[str]]

class TopologyGenerator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.topology = None
        
    def generate_topology(self, configs: Dict[str, ParsedConfig]) -> NetworkTopology:
        """Generate network topology from device configurations"""
        self.logger.info("Generating network topology...")
        
        # Create network graph
        graph = nx.Graph()
        
        # Add devices to graph
        for hostname, config in configs.items():
            graph.add_node(hostname, config=config)
        
        # Generate links based on IP addressing
        links = self._generate_links(configs)
        
        # Add links to graph
        for link in links:
            graph.add_edge(
                link.source_device, 
                link.target_device,
                bandwidth=link.bandwidth,
                latency=link.latency,
                reliability=link.reliability,
                link_type=link.link_type
            )
        
        # Identify subnets
        subnets = self._identify_subnets(configs)
        
        # Identify VLANs
        vlans = self._identify_vlans(configs)
        
        # Identify routing domains
        routing_domains = self._identify_routing_domains(configs)
        
        # Create topology object
        self.topology = NetworkTopology(
            devices=configs,
            links=links,
            graph=graph,
            subnets=subnets,
            vlans=vlans,
            routing_domains=routing_domains
        )
        
        self.logger.info(f"Topology generated with {len(configs)} devices and {len(links)} links")
        return self.topology
    
    def _generate_links(self, configs: Dict[str, ParsedConfig]) -> List[NetworkLink]:
        """Generate network links based on IP addressing and subnet analysis"""
        links = []
        
        # Get all interfaces with IP addresses
        all_interfaces = []
        for hostname, config in configs.items():
            for interface in config.interfaces:
                if interface.ip_address and not interface.shutdown:
                    all_interfaces.append((hostname, interface))
        
        # Find potential links based on subnet membership
        for i, (device1, intf1) in enumerate(all_interfaces):
            for j, (device2, intf2) in enumerate(all_interfaces[i+1:], i+1):
                if device1 != device2:
                    # Check if interfaces are in the same subnet
                    if self._interfaces_in_same_subnet(intf1, intf2):
                        link = self._create_link(device1, intf1, device2, intf2)
                        if link:
                            links.append(link)
        
        # Remove duplicate links (bidirectional)
        unique_links = []
        for link in links:
            duplicate = False
            for existing_link in unique_links:
                if (link.source_device == existing_link.target_device and 
                    link.target_device == existing_link.source_device):
                    duplicate = True
                    break
            if not duplicate:
                unique_links.append(link)
        
        return unique_links
    
    def _interfaces_in_same_subnet(self, intf1: ParsedInterface, intf2: ParsedInterface) -> bool:
        """Check if two interfaces are in the same subnet"""
        try:
            # Create network objects
            network1 = ipaddress.IPv4Network(
                f"{intf1.ip_address}/{intf1.subnet_mask}", 
                strict=False
            )
            network2 = ipaddress.IPv4Network(
                f"{intf2.ip_address}/{intf2.subnet_mask}", 
                strict=False
            )
            
            # Check if they're in the same network
            return network1 == network2
            
        except ValueError as e:
            self.logger.warning(f"Error checking subnet: {e}")
            return False
    
    def _create_link(self, device1: str, intf1: ParsedInterface, 
                     device2: str, intf2: ParsedInterface) -> Optional[NetworkLink]:
        """Create a network link between two devices"""
        try:
            # Determine link characteristics
            bandwidth = min(intf1.bandwidth, intf2.bandwidth)
            
            # Estimate latency based on link type and distance
            latency = self._estimate_latency(intf1, intf2)
            
            # Estimate reliability
            reliability = self._estimate_reliability(intf1, intf2)
            
            # Determine link type
            link_type = self._determine_link_type(intf1, intf2)
            
            link = NetworkLink(
                source_device=device1,
                source_interface=intf1.name,
                target_device=device2,
                target_interface=intf2.name,
                bandwidth=bandwidth,
                latency=latency,
                reliability=reliability,
                link_type=link_type
            )
            
            return link
            
        except Exception as e:
            self.logger.warning(f"Error creating link between {device1} and {device2}: {e}")
            return None
    
    def _estimate_latency(self, intf1: ParsedInterface, intf2: ParsedInterface) -> float:
        """Estimate link latency in milliseconds"""
        # Base latency for different interface types
        base_latencies = {
            'GigabitEthernet': 0.1,
            'FastEthernet': 0.5,
            'Ethernet': 1.0,
            'Serial': 5.0,
            'Loopback': 0.01
        }
        
        # Get base latency for interface types
        latency1 = base_latencies.get(intf1.name.split('/')[0], 1.0)
        latency2 = base_latencies.get(intf2.name.split('/')[0], 1.0)
        
        # Return average latency
        return (latency1 + latency2) / 2
    
    def _estimate_reliability(self, intf1: ParsedInterface, intf2: ParsedInterface) -> float:
        """Estimate link reliability (0.0 to 1.0)"""
        # Base reliability for different interface types
        base_reliability = {
            'GigabitEthernet': 0.9999,
            'FastEthernet': 0.9995,
            'Ethernet': 0.9990,
            'Serial': 0.9980,
            'Loopback': 1.0
        }
        
        # Get base reliability for interface types
        rel1 = base_reliability.get(intf1.name.split('/')[0], 0.9990)
        rel2 = base_reliability.get(intf2.name.split('/')[0], 0.9990)
        
        # Return combined reliability
        return rel1 * rel2
    
    def _determine_link_type(self, intf1: ParsedInterface, intf2: ParsedInterface) -> str:
        """Determine the type of link between interfaces"""
        intf1_type = intf1.name.split('/')[0]
        intf2_type = intf2.name.split('/')[0]
        
        if 'GigabitEthernet' in [intf1_type, intf2_type]:
            return 'gigabit_ethernet'
        elif 'FastEthernet' in [intf1_type, intf2_type]:
            return 'fast_ethernet'
        elif 'Serial' in [intf1_type, intf2_type]:
            return 'serial'
        elif 'Loopback' in [intf1_type, intf2_type]:
            return 'loopback'
        else:
            return 'ethernet'
    
    def _identify_subnets(self, configs: Dict[str, ParsedConfig]) -> Dict[str, List[str]]:
        """Identify subnets and the devices in each subnet"""
        subnets = {}
        
        for hostname, config in configs.items():
            for interface in config.interfaces:
                if interface.ip_address and interface.subnet_mask:
                    try:
                        network = ipaddress.IPv4Network(
                            f"{interface.ip_address}/{interface.subnet_mask}", 
                            strict=False
                        )
                        subnet_key = str(network)
                        
                        if subnet_key not in subnets:
                            subnets[subnet_key] = []
                        
                        subnets[subnet_key].append(f"{hostname}:{interface.name}")
                        
                    except ValueError as e:
                        self.logger.warning(f"Error parsing subnet for {hostname}:{interface.name}: {e}")
        
        return subnets
    
    def _identify_vlans(self, configs: Dict[str, ParsedConfig]) -> Dict[int, List[str]]:
        """Identify VLANs and the devices/interfaces in each VLAN"""
        vlans = {}
        
        for hostname, config in configs.items():
            for interface in config.interfaces:
                if interface.vlan:
                    vlan_id = interface.vlan
                    if vlan_id not in vlans:
                        vlans[vlan_id] = []
                    
                    vlans[vlan_id].append(f"{hostname}:{interface.name}")
        
        return vlans
    
    def _identify_routing_domains(self, configs: Dict[str, ParsedConfig]) -> Dict[str, List[str]]:
        """Identify routing domains based on routing protocols"""
        routing_domains = {
            'OSPF': [],
            'BGP': [],
            'EIGRP': [],
            'RIP': [],
            'Static': []
        }
        
        for hostname, config in configs.items():
            # Add to routing protocol domains
            for protocol in config.routing_protocols:
                if protocol in routing_domains:
                    routing_domains[protocol].append(hostname)
            
            # Check for static routes
            if config.default_gateway:
                routing_domains['Static'].append(hostname)
        
        # Remove empty domains
        routing_domains = {k: v for k, v in routing_domains.items() if v}
        
        return routing_domains
    
    def analyze_topology(self) -> Dict[str, Any]:
        """Analyze the generated topology for insights"""
        if not self.topology:
            return {}
        
        analysis = {
            'total_devices': len(self.topology.devices),
            'total_links': len(self.topology.links),
            'total_subnets': len(self.topology.subnets),
            'total_vlans': len(self.topology.vlans),
            'routing_domains': len(self.topology.routing_domains),
            'connectivity': {},
            'bandwidth_analysis': {},
            'potential_issues': []
        }
        
        # Analyze connectivity
        graph = self.topology.graph
        
        # Check if network is connected
        if nx.is_connected(graph):
            analysis['connectivity']['status'] = 'Fully Connected'
            analysis['connectivity']['components'] = 1
        else:
            components = list(nx.connected_components(graph))
            analysis['connectivity']['status'] = f'Disconnected ({len(components)} components)'
            analysis['connectivity']['components'] = len(components)
        
        # Analyze bandwidth
        total_bandwidth = sum(link.bandwidth for link in self.topology.links)
        avg_bandwidth = total_bandwidth / len(self.topology.links) if self.topology.links else 0
        
        analysis['bandwidth_analysis'] = {
            'total_bandwidth_mbps': total_bandwidth,
            'average_bandwidth_mbps': avg_bandwidth,
            'bandwidth_distribution': self._analyze_bandwidth_distribution()
        }
        
        # Identify potential issues
        analysis['potential_issues'] = self._identify_potential_issues()
        
        return analysis
    
    def _analyze_bandwidth_distribution(self) -> Dict[str, int]:
        """Analyze bandwidth distribution across links"""
        distribution = {
            'low': 0,      # < 100 Mbps
            'medium': 0,   # 100 Mbps - 1 Gbps
            'high': 0,     # 1 Gbps - 10 Gbps
            'ultra': 0     # > 10 Gbps
        }
        
        for link in self.topology.links:
            if link.bandwidth < 100:
                distribution['low'] += 1
            elif link.bandwidth < 1000:
                distribution['medium'] += 1
            elif link.bandwidth < 10000:
                distribution['high'] += 1
            else:
                distribution['ultra'] += 1
        
        return distribution
    
    def _identify_potential_issues(self) -> List[str]:
        """Identify potential network issues"""
        issues = []
        
        if not self.topology:
            return issues
        
        # Check for single points of failure
        graph = self.topology.graph
        articulation_points = list(nx.articulation_points(graph))
        if articulation_points:
            issues.append(f"Single points of failure detected: {', '.join(articulation_points)}")
        
        # Check for bandwidth bottlenecks
        low_bandwidth_links = [link for link in self.topology.links if link.bandwidth < 100]
        if low_bandwidth_links:
            issues.append(f"Low bandwidth links detected: {len(low_bandwidth_links)} links < 100 Mbps")
        
        # Check for isolated devices
        isolated_nodes = [node for node in self.topology.graph.nodes() 
                         if self.topology.graph.degree(node) == 0]
        if isolated_nodes:
            issues.append(f"Isolated devices detected: {', '.join(isolated_nodes)}")
        
        # Check for routing protocol conflicts
        routing_domains = self.topology.routing_domains
        if 'OSPF' in routing_domains and 'BGP' in routing_domains:
            issues.append("Multiple routing protocols detected - potential for routing conflicts")
        
        return issues
    
    def export_topology(self, output_file: str):
        """Export topology to JSON format"""
        if not self.topology:
            self.logger.error("No topology to export")
            return
        
        import json
        
        export_data = {
            'devices': {
                hostname: {
                    'hostname': config.hostname,
                    'interfaces': [
                        {
                            'name': intf.name,
                            'ip_address': intf.ip_address,
                            'subnet_mask': intf.subnet_mask,
                            'bandwidth': intf.bandwidth,
                            'mtu': intf.mtu,
                            'vlan': intf.vlan
                        }
                        for intf in config.interfaces
                    ],
                    'routing_protocols': config.routing_protocols
                }
                for hostname, config in self.topology.devices.items()
            },
            'links': [
                {
                    'source_device': link.source_device,
                    'source_interface': link.source_interface,
                    'target_device': link.target_device,
                    'target_interface': link.target_interface,
                    'bandwidth': link.bandwidth,
                    'latency': link.latency,
                    'reliability': link.reliability,
                    'link_type': link.link_type
                }
                for link in self.topology.links
            ],
            'subnets': self.topology.subnets,
            'vlans': self.topology.vlans,
            'routing_domains': self.topology.routing_domains
        }
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        self.logger.info(f"Topology exported to {output_file}")
    
    def get_shortest_path(self, source: str, target: str) -> Optional[List[str]]:
        """Get shortest path between two devices"""
        if not self.topology:
            return None
        
        try:
            path = nx.shortest_path(self.topology.graph, source, target)
            return path
        except nx.NetworkXNoPath:
            self.logger.warning(f"No path found between {source} and {target}")
            return None
    
    def get_device_neighbors(self, device: str) -> List[str]:
        """Get list of neighboring devices"""
        if not self.topology:
            return []
        
        if device in self.topology.graph:
            return list(self.topology.graph.neighbors(device))
        return []

# Example usage
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # This would be used with actual parsed configurations
    print("TopologyGenerator module loaded successfully")
    print("Use with ConfigParser to generate network topologies") 